from __future__ import print_function

import re
import struct
from io import BytesIO
import binascii


__version__ = "4.1.0"


class Error(Exception):
    pass


class _Info(object):

    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.endianness = None


class _SignedInteger(_Info):

    def __init__(self, name, size):
        super(_SignedInteger, self).__init__(name, size)
        self.minimum = -2 ** (size - 1)
        self.maximum = -self.minimum - 1

    def pack(self, arg):
        value = int(arg)

        if value < self.minimum or value > self.maximum:
            raise Error(
                '"s{}" requires {} <= integer <= {} (got {})'.format(
                    self.size,
                    self.minimum,
                    self.maximum,
                    arg))

        if value < 0:
            value += (1 << self.size)

        value += (1 << self.size)

        return bin(value)[3:]

    def unpack(self, bits):
        value = int(bits, 2)

        if bits[0] == '1':
            value -= (1 << len(bits))

        return value


class _UnsignedInteger(_Info):

    def __init__(self, name, size):
        super(_UnsignedInteger, self).__init__(name, size)
        self.maximum = 2 ** size - 1

    def pack(self, arg):
        value = int(arg)

        if value < 0 or value > self.maximum:
            raise Error(
                '"u{}" requires 0 <= integer <= {} (got {})'.format(
                    self.size,
                    self.maximum,
                    arg))

        return bin(value + (1 << self.size))[3:]

    def unpack(self, bits):
        return int(bits, 2)


class _Boolean(_UnsignedInteger):

    def pack(self, arg):
        return super(_Boolean, self).pack(int(bool(arg)))

    def unpack(self, bits):
        return bool(super(_Boolean, self).unpack(bits))


class _Float(_Info):

    def pack(self, arg):
        value = float(arg)

        if self.size == 16:
            value = struct.pack('>e', value)
        elif self.size == 32:
            value = struct.pack('>f', value)
        elif self.size == 64:
            value = struct.pack('>d', value)
        else:
            raise Error('expected float size of 16, 32, or 64 bits (got {})'.format(
                self.size))

        return bin(int(b'01' + binascii.hexlify(value), 16))[3:]

    def unpack(self, bits):
        packed = _unpack_bytearray(self.size, bits)

        if self.size == 16:
            value = struct.unpack('>e', packed)[0]
        elif self.size == 32:
            value = struct.unpack('>f', packed)[0]
        elif self.size == 64:
            value = struct.unpack('>d', packed)[0]
        else:
            raise Error('expected float size of 16, 32, or 64 bits (got {})'.format(
                self.size))

        return value


class _Raw(_Info):

    def pack(self, arg):
        value = bytearray(arg)

        if 8 * len(value) < self.size:
            raise Error(
                '"r{}" requires at least {} bits (got {})'.format(
                    self.size,
                    self.size,
                    8 * len(value)))


        return bin(int(b'01' + binascii.hexlify(value), 16))[3:self.size + 3]

    def unpack(self, bits):
        rest = self.size % 8

        if rest > 0:
            bits += (8 - rest) * '0'

        return binascii.unhexlify(hex(int('10000000' + bits, 2))[4:].rstrip('L'))


class _Padding(_Info):

    pass


class _ZeroPadding(_Padding):

    def pack(self):
        return self.size * '0'


class _OnePadding(_Padding):

    def pack(self):
        return self.size * '1'


class _Text(_Info):

    def pack(self, arg):
        value = arg.encode('utf-8')

        return _pack_bytearray(self.size, bytearray(value))

    def unpack(self, bits):
        return _unpack_bytearray(self.size, bits).decode('utf-8')


def _parse_format(fmt):
    if fmt and fmt[-1] in '><':
        byte_order = fmt[-1]
        fmt = fmt[:-1]
    else:
        byte_order = ''

    parsed_infos = re.findall(r'([<>]?)([a-zA-Z])(\d+)(:\w+ ?| ?)?', fmt)

    if ''.join([''.join(info) for info in parsed_infos]) != fmt:
        raise Error("bad format '{}'".format(fmt + byte_order))

    # Use big endian as default and use the endianness of the previous
    # value if none is given for the current value.
    infos = []
    endianness = ">"
    i = 0

    for parsed_info in parsed_infos:
        if parsed_info[0] != "":
            endianness = parsed_info[0]

        type_ = parsed_info[1]
        size = int(parsed_info[2])
        name = parsed_info[3].strip(' :')

        if not name:
            name = i

        if type_ == 's':
            info = _SignedInteger(name, size)
            i += 1
        elif type_ == 'u':
            info = _UnsignedInteger(name, size)
            i += 1
        elif type_ == 'f':
            info = _Float(name, size)
            i += 1
        elif type_ == 'b':
            info = _Boolean(name, size)
            i += 1
        elif type_ == 't':
            info = _Text(name, size)
            i += 1
        elif type_ == 'r':
            info = _Raw(name, size)
            i += 1
        elif type_ == 'p':
            info = _ZeroPadding(name, size)
        elif type_ == 'P':
            info = _OnePadding(name, size)
        else:
            raise Error("bad char '{}' in format".format(type_))

        info.endianness = endianness

        infos.append(info)

    return infos, byte_order or '>'


def _pack_bytearray(size, arg):
    return bin(int(b'01' + binascii.hexlify(arg), 16))[3:size + 3]


def _unpack_bytearray(size, bits):
    rest = size % 8

    if rest > 0:
        bits += (8 - rest) * '0'

    return binascii.unhexlify(hex(int('10000000' + bits, 2))[4:].rstrip('L'))


class CompiledFormat(object):
    """A compiled format string that can be used to pack and/or unpack
    data multiple times.

    Instances of this class are created by the factory function
    :func:`~bitstruct.compile()`.

    """

    def __init__(self, fmt):
        infos, byte_order = _parse_format(fmt)
        self._infos = infos
        self._byte_order = byte_order
        self._number_of_bits_to_unpack = sum([info.size for info in infos])
        self._number_of_arguments = 0

        for info in infos:
            if not isinstance(info, _Padding):
                self._number_of_arguments += 1

    def _pack_value(self, info, value, bits):
        value_bits = info.pack(value)

        # Reverse the bit order in little endian values.
        if info.endianness == "<":
            value_bits = value_bits[::-1]

        # Reverse bytes order for least significant byte first.
        if self._byte_order == ">":
            bits += value_bits
        else:
            aligned_offset = len(value_bits) - (8 - (len(bits) % 8))

            while aligned_offset > 0:
                bits += value_bits[aligned_offset:]
                value_bits = value_bits[:aligned_offset]
                aligned_offset -= 8

            bits += value_bits

        return bits

    def _pack(self, values):
        bits = ''

        for info in self._infos:
            if isinstance(info, _Padding):
                bits += info.pack()
            else:
                bits = self._pack_value(info, values[info.name], bits)

        # Padding of last byte.
        tail = len(bits) % 8

        if tail != 0:
            bits += (8 - tail) * '0'

        return bytes(_unpack_bytearray(len(bits), bits))

    def _unpack_from(self, data, offset):
        bits = bin(int(b'01' + binascii.hexlify(bytearray(data)), 16))[3 + offset:]

        # Sanity check.
        if self._number_of_bits_to_unpack > len(bits):
            raise Error(
                "unpack requires at least {} bits to unpack (got {})".format(
                    self._number_of_bits_to_unpack,
                    len(bits)))

        offset = 0

        for info in self._infos:
            if isinstance(info, _Padding):
                pass
            else:
                # Reverse bytes order for least significant byte
                # first.
                if self._byte_order == ">":
                    value_bits = bits[offset:offset + info.size]
                else:
                    value_bits_tmp = bits[offset:offset + info.size]
                    aligned_offset = (info.size - ((offset + info.size) % 8))
                    value_bits = ''

                    while aligned_offset > 0:
                        value_bits += value_bits_tmp[aligned_offset:aligned_offset + 8]
                        value_bits_tmp = value_bits_tmp[:aligned_offset]
                        aligned_offset -= 8

                    value_bits += value_bits_tmp

                # Reverse the bit order in little endian values.
                if info.endianness == "<":
                    value_bits = value_bits[::-1]

                yield info, info.unpack(value_bits)

            offset += info.size

    def _pack_into(self, buf, offset, data, **kwargs):
        fill_padding = kwargs.get('fill_padding', True)
        buf_bits = _pack_bytearray(8 * len(buf), buf)
        bits = buf_bits[0:offset]
        i = 0

        for info in self._infos:
            if isinstance(info, _Padding):
                if fill_padding:
                    bits += info.pack()
                else:
                    bits += buf_bits[len(bits):len(bits) + info.size]
            else:
                bits = self._pack_value(info, data[info.name], bits)
                i += 1

        bits += buf_bits[len(bits):]

        if len(bits) > len(buf_bits):
            raise Error(
                'pack requires a buffer of at least {} bits'.format(
                    len(bits)))

        buf[:] = _unpack_bytearray(len(bits), bits)

    def pack(self, *args):
        """See :func:`pack()`.

        """

        # Sanity check of the number of arguments.
        if len(args) < self._number_of_arguments:
            raise Error(
                "pack expected {} item(s) for packing (got {})".format(
                    self._number_of_arguments,
                    len(args)))

        return self._pack(args)

    def unpack(self, data):
        """See :func:`unpack()`.

        """

        return self.unpack_from(data)

    def pack_into(self, buf, offset, *args, **kwargs):
        """See :func:`pack_into()`.

        """

        # Sanity check of the number of arguments.
        if len(args) < self._number_of_arguments:
            raise Error(
                "pack expected {} item(s) for packing (got {})".format(
                    self._number_of_arguments,
                    len(args)))

        self._pack_into(buf, offset, args, **kwargs)

    def unpack_from(self, data, offset=0):
        """See :func:`unpack_from()`.

        """

        return tuple([v[1] for v in self._unpack_from(data, offset)])

    def pack_dict(self, data):
        """See :func:`pack_dict()`.

        """

        try:
            return self._pack(data)
        except KeyError as e:
            raise Error('{} not found in data dictionary'.format(str(e)))

    def unpack_dict(self, data):
        """See :func:`unpack_dict()`.

        """

        return self.unpack_from_dict(data)

    def pack_into_dict(self, buf, offset, data, **kwargs):
        """See :func:`pack_into_dict()`.

        """

        try:
            self._pack_into(buf, offset, data, **kwargs)
        except KeyError as e:
            raise Error('{} not found in data dictionary'.format(str(e)))

    def unpack_from_dict(self, data, offset=0):
        """See :func:`unpack_from_dict()`.

        """

        return {info.name: v for info, v in self._unpack_from(data, offset)}

    def calcsize(self):
        """Return the number of bits in the compiled format string.

        """

        return self._number_of_bits_to_unpack


def pack(fmt, *args):
    """Return a byte string containing the values v1, v2, ... packed
    according to given format string `fmt`. If the total number of
    bits are not a multiple of 8, padding will be added at the end of
    the last byte.

    `fmt` is a string of bitorder-type-length groups, and optionally a
    byteorder identifier after the groups. Bitorder and byteorder may
    be omitted.

    Bitorder is either ``>`` or ``<``, where ``>`` means MSB first and
    ``<`` means LSB first. If bitorder is omitted, the previous
    values' bitorder is used for the current value. For example, in
    the format string ``'u1<u2u3'``, ``u1`` is MSB first and both
    ``u2`` and ``u3`` are LSB first.

    Byteorder is either ``>`` or ``<``, where ``>`` means most
    significant byte first and ``<`` means least significant byte
    first. If byteorder is omitted, most significant byte first is
    used.

    There are eight types; ``u``, ``s``, ``f``, ``b``, ``t``, ``r``,
    ``p`` and ``P``.

    - ``u`` -- unsigned integer
    - ``s`` -- signed integer
    - ``f`` -- floating point number of 16, 32, or 64 bits
    - ``b`` -- boolean
    - ``t`` -- text (ascii or utf-8)
    - ``r`` -- raw, bytes
    - ``p`` -- padding with zeros, ignore
    - ``P`` -- padding with ones, ignore

    Length is the number of bits to pack the value into.

    Example format string with default bit and byte ordering:
    ``'u1u3p7s16'``

    Same format string, but with least significant byte first:
    ``'u1u3p7s16<'``

    Same format string, but with LSB first (``<`` prefix) and least
    significant byte first (``<`` suffix): ``'<u1u3p7s16<'``

    It is allowed to separate groups with a single space for better
    readability.

    """

    return CompiledFormat(fmt).pack(*args)


def unpack(fmt, data):
    """Unpack `data` (byte string, bytearray or list of integers)
    according to given format string `fmt`. The result is a tuple even
    if it contains exactly one item.

    """

    return CompiledFormat(fmt).unpack(data)


def pack_into(fmt, buf, offset, *args, **kwargs):
    """Pack given values v1, v2, ... into `buf`, starting at given bit
    offset `offset`. Pack according to given format string `fmt`. Give
    `fill_padding` as ``False`` to leave padding bits in `buf`
    unmodified.

    """

    return CompiledFormat(fmt).pack_into(buf,
                                         offset,
                                         *args,
                                         **kwargs)


def unpack_from(fmt, data, offset=0):
    """Unpack `data` (byte string, bytearray or list of integers)
    according to given format string `fmt`, starting at given bit
    offset `offset`. The result is a tuple even if it contains exactly
    one item.

    """

    return CompiledFormat(fmt).unpack_from(data, offset)


def pack_dict(fmt, data):
    """Same as :func:`pack()`, but `fmt` must have named format groups and
    data is read from a dictionary.

    A named format group is a group (bitorder-type-length) with a
    ``:<name>`` suffix. Named format groups must be separated by a
    single space, as in the example below.

    >>> pack_dict('u4:foo u4:bar', {'foo': 1, 'bar': 2})
    b'\\x12'

    """

    return CompiledFormat(fmt).pack_dict(data)


def unpack_dict(fmt, data):
    """Same as :func:`unpack()`, but `fmt` must have named format groups
    and returns a dictionary.

    >>> unpack_dict('u4:foo u4:bar', b'\\x12')
    {'foo': 1, 'bar': 2}

    """

    return CompiledFormat(fmt).unpack_dict(data)


def pack_into_dict(fmt, buf, offset, data, **kwargs):
    """Same as :func:`pack_into()`, but `fmt` must have named format
    groups and data is read from a dictionary.

    """

    return CompiledFormat(fmt).pack_into_dict(buf,
                                              offset,
                                              data,
                                              **kwargs)


def unpack_from_dict(fmt, data, offset=0):
    """Same as :func:`unpack_from_dict()`, but `fmt` must have named
    format groups and returns a dictionary.

    """

    return CompiledFormat(fmt).unpack_from_dict(data, offset)


def calcsize(fmt):
    """Return the number of bits in given format string `fmt`.

    >>> calcsize('u1s3p4')
    8

    """

    return CompiledFormat(fmt).calcsize()


def byteswap(fmt, data, offset=0):
    """Swap bytes in `data` according to `fmt`, starting at byte `offset`
    and return the result. `fmt` must be an iterable, iterating over
    number of bytes to swap. For example, the format string ``'24'``
    applied to the byte string ``b'\\x00\\x11\\x22\\x33\\x44\\x55'``
    will produce the result ``b'\\x11\\x00\\x55\\x44\\x33\\x22'``.

    """

    data = BytesIO(data)
    data.seek(offset)
    data_swapped = BytesIO()

    for f in fmt:
        swapped = data.read(int(f))[::-1]
        data_swapped.write(swapped)

    return data_swapped.getvalue()


def compile(fmt):
    """Compile given format string `fmt` and return a
    :class:`~bitstruct.CompiledFormat` object that can be used to pack
    and/or unpack data multiple times.

    """

    return CompiledFormat(fmt)
