/**
 * CPython 3 C extension.
 */

#include <Python.h>
#include "bitstream.h"

struct field_info_t;

typedef int (*pack_field_t)(struct bitstream_writer_t *self_p,
                            PyObject *value_p,
                            struct field_info_t *field_info_p);

typedef int (*unpack_field_t)(struct bitstream_reader_t *self_p,
                              PyObject *unpacked_p,
                              int index,
                              struct field_info_t *field_info_p);

struct field_info_t {
    pack_field_t pack;
    unpack_field_t unpack;
    int kind;
    int number_of_bits;
};

struct info_t {
    int number_of_bits;
    int number_of_fields;
    int number_of_non_padding_fields;
    struct field_info_t fields[1];
};

static int pack_signed_integer(struct bitstream_writer_t *self_p,
                               PyObject *value_p,
                               struct field_info_t *field_info_p)
{
    uint64_t value;

    value = PyLong_AsLongLong(value_p);

    if (field_info_p->number_of_bits < 64) {
        value &= ((1ull << field_info_p->number_of_bits) - 1);
    }

    bitstream_writer_write_u64_bits(self_p,
                                    value,
                                    field_info_p->number_of_bits);

    return (1);
}

static int unpack_signed_integer(struct bitstream_reader_t *self_p,
                                 PyObject *unpacked_p,
                                 int index,
                                 struct field_info_t *field_info_p)
{
    uint64_t value;
    uint64_t sign_bit;

    value = bitstream_reader_read_u64_bits(self_p, field_info_p->number_of_bits);
    sign_bit = (1ull << (field_info_p->number_of_bits - 1));

    if (value & sign_bit) {
        value |= ~(((sign_bit) << 1) - 1);
    }

    PyTuple_SET_ITEM(unpacked_p, index, PyLong_FromLongLong(value));

    return (1);
}

static int pack_unsigned_integer(struct bitstream_writer_t *self_p,
                                 PyObject *value_p,
                                 struct field_info_t *field_info_p)
{
    bitstream_writer_write_u64_bits(self_p,
                                    PyLong_AsUnsignedLongLong(value_p),
                                    field_info_p->number_of_bits);

    return (1);
}

static int unpack_unsigned_integer(struct bitstream_reader_t *self_p,
                                   PyObject *unpacked_p,
                                   int index,
                                   struct field_info_t *field_info_p)
{
    uint64_t value;

    value = bitstream_reader_read_u64_bits(self_p,
                                           field_info_p->number_of_bits);
    PyTuple_SET_ITEM(unpacked_p, index, PyLong_FromUnsignedLongLong(value));

    return (1);
}

static int pack_float_16(struct bitstream_writer_t *self_p,
                         PyObject *value_p,
                         struct field_info_t *field_info_p)
{
    uint8_t buf[2];

    _PyFloat_Pack2(PyFloat_AsDouble(value_p),
                   &buf[0],
                   PY_BIG_ENDIAN);
    bitstream_writer_write_bytes(self_p, &buf[0], sizeof(buf));

    return (1);
}

static int unpack_float_16(struct bitstream_reader_t *self_p,
                           PyObject *unpacked_p,
                           int index,
                           struct field_info_t *field_info_p)
{
    uint8_t buf[2];
    double value;

    bitstream_reader_read_bytes(self_p, &buf[0], sizeof(buf));
    value = _PyFloat_Unpack2(&buf[0], PY_BIG_ENDIAN);
    PyTuple_SET_ITEM(unpacked_p, index, PyFloat_FromDouble(value));

    return (1);
}

static int pack_float_32(struct bitstream_writer_t *self_p,
                         PyObject *value_p,
                         struct field_info_t *field_info_p)
{
    float value;
    uint32_t data;

    value = (float)PyFloat_AsDouble(value_p);
    memcpy(&data, &value, sizeof(data));
    bitstream_writer_write_u32(self_p, data);

    return (1);
}

static int unpack_float_32(struct bitstream_reader_t *self_p,
                           PyObject *unpacked_p,
                           int index,
                           struct field_info_t *field_info_p)
{
    PyTuple_SET_ITEM(unpacked_p,
                     index,
                     PyFloat_FromDouble(bitstream_reader_read_u32(self_p)));

    return (1);
}

static int pack_float_64(struct bitstream_writer_t *self_p,
                         PyObject *value_p,
                         struct field_info_t *field_info_p)
{
    double value;
    uint64_t data;

    value = PyFloat_AsDouble(value_p);
    memcpy(&data, &value, sizeof(data));
    bitstream_writer_write_u64_bits(self_p,
                                    data,
                                    field_info_p->number_of_bits);

    return (1);
}

static int unpack_float_64(struct bitstream_reader_t *self_p,
                           PyObject *unpacked_p,
                           int index,
                           struct field_info_t *field_info_p)
{
    PyTuple_SET_ITEM(unpacked_p,
                     index,
                     PyFloat_FromDouble(bitstream_reader_read_u64(self_p)));

    return (1);
}

static int pack_bool(struct bitstream_writer_t *self_p,
                     PyObject *value_p,
                     struct field_info_t *field_info_p)
{
    bitstream_writer_write_u64_bits(self_p,
                                    PyObject_IsTrue(value_p),
                                    field_info_p->number_of_bits);

    return (1);
}

static int unpack_bool(struct bitstream_reader_t *self_p,
                       PyObject *unpacked_p,
                       int index,
                       struct field_info_t *field_info_p)
{
    PyTuple_SET_ITEM(unpacked_p,
                     index,
                     PyBool_FromLong((long)bitstream_reader_read_u64_bits(
                                         self_p,
                                         field_info_p->number_of_bits)));

    return (1);
}

static int pack_text(struct bitstream_writer_t *self_p,
                     PyObject *value_p,
                     struct field_info_t *field_info_p)
{
    Py_ssize_t size;
    const char* buf_p;

    buf_p = PyUnicode_AsUTF8AndSize(value_p, &size);

    if (buf_p != NULL) {
        if (size < (field_info_p->number_of_bits / 8)) {
            PyErr_SetString(PyExc_NotImplementedError, "Short text.");
        } else {
            bitstream_writer_write_bytes(self_p,
                                         (uint8_t *)buf_p,
                                         field_info_p->number_of_bits / 8);
        }
    }

    return (1);
}

static int unpack_text(struct bitstream_reader_t *self_p,
                       PyObject *unpacked_p,
                       int index,
                       struct field_info_t *field_info_p)
{
    uint8_t *buf_p;
    PyObject *value_p;
    int number_of_bytes;

    number_of_bytes = (field_info_p->number_of_bits / 8);
    buf_p = PyMem_RawMalloc(number_of_bytes);

    if (buf_p == NULL) {
        return (1);
    }

    bitstream_reader_read_bytes(self_p, buf_p, number_of_bytes);
    value_p = PyUnicode_FromStringAndSize((const char *)buf_p, number_of_bytes);

    if (value_p != NULL) {
        PyTuple_SET_ITEM(unpacked_p, index, value_p);
    }

    PyMem_RawFree(buf_p);

    return (1);
}

static int pack_raw(struct bitstream_writer_t *self_p,
                    PyObject *value_p,
                    struct field_info_t *field_info_p)
{
    Py_ssize_t size;
    char* buf_p;
    int res;

    res = PyBytes_AsStringAndSize(value_p, &buf_p, &size);

    if (res != -1) {
        if (size < (field_info_p->number_of_bits / 8)) {
            PyErr_SetString(PyExc_NotImplementedError, "Short raw data.");
        } else {
            bitstream_writer_write_bytes(self_p,
                                         (uint8_t *)buf_p,
                                         field_info_p->number_of_bits / 8);
        }
    }

    return (1);
}

static int unpack_raw(struct bitstream_reader_t *self_p,
                      PyObject *unpacked_p,
                      int index,
                      struct field_info_t *field_info_p)
{
    uint8_t *buf_p;
    PyObject *value_p;
    int number_of_bytes;

    number_of_bytes = (field_info_p->number_of_bits / 8);
    value_p = PyBytes_FromStringAndSize(NULL, number_of_bytes);
    buf_p = (uint8_t *)PyBytes_AS_STRING(value_p);
    bitstream_reader_read_bytes(self_p, buf_p, number_of_bytes);
    PyTuple_SET_ITEM(unpacked_p, index, value_p);

    return (1);
}

static int pack_zero_padding(struct bitstream_writer_t *self_p,
                             PyObject *value_p,
                             struct field_info_t *field_info_p)
{
    bitstream_writer_write_repeated_bit(self_p,
                                        0,
                                        field_info_p->number_of_bits);

    return (0);
}

static int pack_one_padding(struct bitstream_writer_t *self_p,
                            PyObject *value_p,
                            struct field_info_t *field_info_p)
{
    bitstream_writer_write_repeated_bit(self_p,
                                        1,
                                        field_info_p->number_of_bits);

    return (0);
}

static int unpack_padding(struct bitstream_reader_t *self_p,
                          PyObject *unpacked_p,
                          int index,
                          struct field_info_t *field_info_p)
{
    bitstream_reader_seek(self_p, field_info_p->number_of_bits);

    return (0);
}

static int field_info_init_signed(struct field_info_t *self_p,
                                  int number_of_bits)
{
    self_p->pack = pack_signed_integer;
    self_p->unpack = unpack_signed_integer;

    if (number_of_bits > 64) {
        PyErr_SetString(PyExc_NotImplementedError,
                        "Signed integer over 64 bits.");
        return (-1);
    }

    return (0);
}

static int field_info_init_unsigned(struct field_info_t *self_p,
                                    int number_of_bits)
{
    self_p->pack = pack_unsigned_integer;
    self_p->unpack = unpack_unsigned_integer;

    if (number_of_bits > 64) {
        PyErr_SetString(PyExc_NotImplementedError,
                        "Unsigned integer over 64 bits.");
        return (-1);
    }

    return (0);
}

static int field_info_init_float(struct field_info_t *self_p,
                                 int number_of_bits)
{
    switch (number_of_bits) {

    case 16:
        self_p->pack = pack_float_16;
        self_p->unpack = unpack_float_16;
        break;

    case 32:
        self_p->pack = pack_float_32;
        self_p->unpack = unpack_float_32;
        break;

    case 64:
        self_p->pack = pack_float_64;
        self_p->unpack = unpack_float_64;
        break;

    default:
        PyErr_SetString(PyExc_NotImplementedError,
                        "Float not 16, 32 or 64 bits.");
        return (-1);
    }

    return (0);
}

static int field_info_init_bool(struct field_info_t *self_p,
                                int number_of_bits)
{
    self_p->pack = pack_bool;
    self_p->unpack = unpack_bool;

    if (number_of_bits > 64) {
        PyErr_SetString(PyExc_NotImplementedError, "Bool over 64 bits.");
        return (-1);
    }

    return (0);
}

static int field_info_init_text(struct field_info_t *self_p,
                                int number_of_bits)
{
    self_p->pack = pack_text;
    self_p->unpack = unpack_text;

    if ((number_of_bits % 8) != 0) {
        PyErr_SetString(PyExc_NotImplementedError,
                        "Text not multiple of 8 bits.");
        return (-1);
    }

    return (0);
}

static int field_info_init_raw(struct field_info_t *self_p,
                               int number_of_bits)
{
    self_p->pack = pack_raw;
    self_p->unpack = unpack_raw;

    if ((number_of_bits % 8) != 0) {
        PyErr_SetString(PyExc_NotImplementedError,
                        "Raw not multiple of 8 bits.");
        return (-1);
    }

    return (0);
}

static int field_info_init_zero_padding(struct field_info_t *self_p)
{
    self_p->pack = pack_zero_padding;
    self_p->unpack = unpack_padding;

    return (0);
}

static int field_info_init_one_padding(struct field_info_t *self_p)
{
    self_p->pack = pack_one_padding;
    self_p->unpack = unpack_padding;

    return (0);
}

static int field_info_init(struct field_info_t *self_p,
                           int kind,
                           int number_of_bits)
{
    int res;

    switch (kind) {

    case 's':
        res = field_info_init_signed(self_p, number_of_bits);
        break;

    case 'u':
        res = field_info_init_unsigned(self_p, number_of_bits);
        break;

    case 'f':
        res = field_info_init_float(self_p, number_of_bits);
        break;

    case 'b':
        res = field_info_init_bool(self_p, number_of_bits);
        break;

    case 't':
        res = field_info_init_text(self_p, number_of_bits);
        break;

    case 'r':
        res = field_info_init_raw(self_p, number_of_bits);
        break;

    case 'p':
        res = field_info_init_zero_padding(self_p);
        break;

    case 'P':
        res = field_info_init_one_padding(self_p);
        break;

    default:
        PyErr_Format(PyExc_ValueError, "Bad format field type '%c'.", kind);
        res = -1;
        break;
    }

    self_p->kind = kind;
    self_p->number_of_bits = number_of_bits;

    return (res);
}

static int count_number_of_fields(const char *format_p,
                                  int *number_of_padding_fields_p)
{
    int count;

    count = 0;
    *number_of_padding_fields_p = 0;

    while (*format_p != '\0') {
        if ((*format_p >= 'A') && (*format_p <= 'z')) {
            count++;

            if ((*format_p == 'p') || (*format_p == 'P')) {
                (*number_of_padding_fields_p)++;
            }
        }

        format_p++;
    }

    return (count);
}

const char *parse_field(const char *format_p,
                        int *kind_p,
                        int *number_of_bits_p)
{
    if (*format_p == '\0') {
        PyErr_SetString(PyExc_ValueError, "Bad format.");

        return (NULL);
    }

    *kind_p = *format_p;
    *number_of_bits_p = 0;
    format_p++;

    while (isdigit(*format_p)) {
        if (*number_of_bits_p > (INT_MAX / 100)) {
            PyErr_SetString(PyExc_ValueError, "Field too long.");

            return (NULL);
        }

        *number_of_bits_p *= 10;
        *number_of_bits_p += (*format_p - '0');
        format_p++;
    }

    return (format_p);
}

static struct info_t *parse_format(PyObject *format_obj_p)
{
    int number_of_fields;
    struct info_t *info_p;
    const char *format_p;
    int i;
    int kind;
    int number_of_bits;
    int number_of_padding_fields;
    int res;

    format_p = PyUnicode_AsUTF8(format_obj_p);
    number_of_fields = count_number_of_fields(format_p,
                                              &number_of_padding_fields);

    info_p = PyMem_RawMalloc(
        sizeof(*info_p) + number_of_fields * sizeof(info_p->fields[0]));

    if (info_p == NULL) {
        return (NULL);
    }

    info_p->number_of_bits = 0;
    info_p->number_of_fields = number_of_fields;
    info_p->number_of_non_padding_fields = (
        number_of_fields - number_of_padding_fields);

    for (i = 0; i < info_p->number_of_fields; i++) {
        format_p = parse_field(format_p, &kind, &number_of_bits);

        if (format_p == NULL) {
            PyMem_RawFree(info_p);

            return (NULL);
        }

        res = field_info_init(&info_p->fields[i], kind, number_of_bits);

        if (res != 0) {
            PyMem_RawFree(info_p);

            return (NULL);
        }

        info_p->number_of_bits += number_of_bits;
    }

    return (info_p);
}

static PyObject *pack(PyObject *module_p, PyObject *args_p)
{
    struct bitstream_writer_t writer;
    Py_ssize_t number_of_args;
    PyObject *packed_p;
    struct info_t *info_p;
    int i;
    int consumed_args;

    packed_p = NULL;
    number_of_args = PyTuple_GET_SIZE(args_p);

    if (number_of_args < 1) {
        PyErr_SetString(PyExc_ValueError, "No format string.");

        goto out1;
    }

    info_p = parse_format(PyTuple_GET_ITEM(args_p, 0));

    if (info_p == NULL) {
        goto out1;
    }

    if ((number_of_args - 1) < info_p->number_of_non_padding_fields) {
        PyErr_SetString(PyExc_ValueError, "Too few arguments.");

        goto out2;
    }

    packed_p = PyBytes_FromStringAndSize(NULL, (info_p->number_of_bits + 7) / 8);
    bitstream_writer_init(&writer, (uint8_t *)PyBytes_AS_STRING(packed_p));
    consumed_args = 1;

    for (i = 0; i < info_p->number_of_fields; i++) {
        consumed_args += info_p->fields[i].pack(
            &writer,
            PyTuple_GET_ITEM(args_p, consumed_args),
            &info_p->fields[i]);
    }

 out2:
    PyMem_RawFree(info_p);

 out1:
    if ((packed_p != NULL) && (PyErr_Occurred() != NULL)) {
        Py_DECREF(packed_p);
        packed_p = NULL;
    }

    return (packed_p);
}

static PyObject *unpack(PyObject *module_p, PyObject *args_p)
{
    struct bitstream_reader_t reader;
    PyObject *format_p;
    PyObject *data_p;
    PyObject *unpacked_p;
    char *packed_p;
    struct info_t *info_p;
    int i;
    int produced_args;
    Py_ssize_t size;
    int res;

    unpacked_p = NULL;
    res = PyArg_ParseTuple(args_p, "OO", &format_p, &data_p);

    if (res == 0) {
        goto out1;
    }

    info_p = parse_format(format_p);

    if (info_p == NULL) {
        goto out1;
    }

    unpacked_p = PyTuple_New(info_p->number_of_non_padding_fields);

    if (unpacked_p == NULL) {
        goto out2;
    }

    res = PyBytes_AsStringAndSize(data_p, &packed_p, &size);

    if (res == -1) {
        goto out2;
    }

    if (size < ((info_p->number_of_bits + 7) / 8)) {
        goto out2;
    }

    bitstream_reader_init(&reader, (uint8_t *)packed_p);
    produced_args = 0;

    for (i = 0; i < info_p->number_of_fields; i++) {
        produced_args += info_p->fields[i].unpack(&reader,
                                                  unpacked_p,
                                                  produced_args,
                                                  &info_p->fields[i]);
    }

 out2:
    PyMem_RawFree(info_p);

 out1:
    if ((unpacked_p != NULL) && (PyErr_Occurred() != NULL)) {
        Py_DECREF(unpacked_p);
        unpacked_p = NULL;
    }

    return (unpacked_p);
}

static struct PyMethodDef methods[] = {
    { "pack", pack, METH_VARARGS },
    { "unpack", unpack, METH_VARARGS },
    { NULL }
};

static PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    .m_name = "bitstruct.c",
    .m_doc = "bitstruct C extension",
    .m_size = -1,
    .m_methods = methods
};

PyMODINIT_FUNC PyInit_c(void)
{
    PyObject *module_p;

    /* Module creation. */
    module_p = PyModule_Create(&module);

    if (module_p == NULL) {
        return (NULL);
    }

    return (module_p);
}
