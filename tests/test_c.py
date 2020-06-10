from __future__ import print_function
import sys
import timeit
import unittest
import platform
import copy


def is_cpython_3():
    if platform.python_implementation() != 'CPython':
        return False

    if sys.version_info[0] < 3:
        return False

    return True


if is_cpython_3():
    import bitstruct.c
    from bitstruct.c import *
else:
    print('Skipping C extension tests for non-CPython 3.')


class CTest(unittest.TestCase):

    def test_pack(self):
        """Pack values.

        """

        if not is_cpython_3():
            return

        packed = pack('u1u1s6u7u9', 0, 0, -2, 65, 22)
        self.assertEqual(packed, b'\x3e\x82\x16')

        packed = pack('u1', 1)
        self.assertEqual(packed, b'\x80')

        with self.assertRaises(NotImplementedError):
            packed = pack('u77', 0x100000000001000000)
            ref = b'\x00\x80\x00\x00\x00\x00\x08\x00\x00\x00'
            self.assertEqual(packed, ref)

        with self.assertRaises(NotImplementedError):
            packed = pack('u8000', int(8000 * '1', 2))
            ref = 1000 * b'\xff'
            self.assertEqual(packed, ref)

        with self.assertRaises(NotImplementedError):
            packed = pack('s4000', int(8000 * '0', 2))
            ref = 500 * b'\x00'
            self.assertEqual(packed, ref)

        packed = pack('p1u1s6u7u9', 0, -2, 65, 22)
        self.assertEqual(packed, b'\x3e\x82\x16')

        packed = pack('P1u1s6u7u9', 0, -2, 65, 22)
        self.assertEqual(packed, b'\xbe\x82\x16')

        packed = pack('p1u1s6p7u9', 0, -2, 22)
        self.assertEqual(packed, b'\x3e\x00\x16')

        packed = pack('P1u1s6p7u9', 0, -2, 22)
        self.assertEqual(packed, b'\xbe\x00\x16')

        with self.assertRaises(NotImplementedError):
            packed = pack('u1s6f32r43', 0, -2, 3.75, b'\x00\xff\x00\xff\x00\xff')
            self.assertEqual(packed, b'\x7c\x80\xe0\x00\x00\x01\xfe\x01\xfe\x01\xc0')

        packed = pack('b1', True)
        self.assertEqual(packed, b'\x80')

        packed = pack('b1p6b1', True, True)
        self.assertEqual(packed, b'\x81')

        packed = pack('b1P6b1', True, True)
        self.assertEqual(packed, b'\xff')

        packed = pack('u5b2u1', 31, False, 1)
        self.assertEqual(packed, b'\xf9')

        packed = pack('b1t24', False, u'Hi!')
        self.assertEqual(packed, b'$4\x90\x80')

        packed = pack('b1t24', False, 'Hi!')
        self.assertEqual(packed, b'$4\x90\x80')

        packed = pack('t8000', 1000 * '7')
        self.assertEqual(packed, 1000 * b'\x37')

        if sys.version_info >= (3, 6):
            packed = pack('f16', 1.0)
            self.assertEqual(packed, b'\x3c\x00')

        packed = pack('f32', 1.0)
        self.assertEqual(packed, b'\x3f\x80\x00\x00')

        packed = pack('f64', 1.0)
        self.assertEqual(packed, b'\x3f\xf0\x00\x00\x00\x00\x00\x00')

    def test_unpack(self):
        """Unpack values.

        """

        if not is_cpython_3():
            return

        unpacked = unpack('u1u1s6u7u9', b'\x3e\x82\x16')
        self.assertEqual(unpacked, (0, 0, -2, 65, 22))

        # unpacked = unpack('u1', bytearray(b'\x80'))
        unpacked = unpack('u1', b'\x80')
        self.assertEqual(unpacked, (1, ))

        with self.assertRaises(NotImplementedError):
            packed = b'\x00\x80\x00\x00\x00\x00\x08\x00\x00\x00'
            unpacked = unpack('u77', packed)
            self.assertEqual(unpacked, (0x100000000001000000,))

        with self.assertRaises(NotImplementedError):
            packed = 1000 * b'\xff'
            unpacked = unpack('u8000', packed)
            self.assertEqual(unpacked, (int(8000 * '1', 2), ))

        with self.assertRaises(NotImplementedError):
            packed = 500 * b'\x00'
            unpacked = unpack('s4000', packed)
            self.assertEqual(unpacked, (0, ))

        packed = b'\xbe\x82\x16'
        unpacked = unpack('P1u1s6u7u9', packed)
        self.assertEqual(unpacked, (0, -2, 65, 22))

        packed = b'\x3e\x82\x16'
        unpacked = unpack('P1u1s6u7u9', packed)
        self.assertEqual(unpacked, (0, -2, 65, 22))

        packed = b'\xbe\x82\x16'
        unpacked = unpack('p1u1s6u7u9', packed)
        self.assertEqual(unpacked, (0, -2, 65, 22))

        packed = b'\x3e\x82\x16'
        unpacked = unpack('p1u1s6u7u9', packed)
        self.assertEqual(unpacked, (0, -2, 65, 22))

        packed = b'\x3e\x82\x16'
        unpacked = unpack('p1u1s6p7u9', packed)
        self.assertEqual(unpacked, (0, -2, 22))

        with self.assertRaises(NotImplementedError):
            packed = b'\x7c\x80\xe0\x00\x00\x01\xfe\x01\xfe\x01\xc0'
            unpacked = unpack('u1s6f32r43', packed)
            self.assertEqual(unpacked, (0, -2, 3.75, b'\x00\xff\x00\xff\x00\xe0'))

        # packed = bytearray(b'\x80')
        packed = b'\x80'
        unpacked = unpack('b1', packed)
        self.assertEqual(unpacked, (True, ))

        packed = b'\x80'
        unpacked = unpack('b1p6b1', packed)
        self.assertEqual(unpacked, (True, False))

        packed = b'\x06'
        unpacked = unpack('u5b2u1', packed)
        self.assertEqual(unpacked, (0, True, 0))

        packed = b'\x04'
        unpacked = unpack('u5b2u1', packed)
        self.assertEqual(unpacked, (0, True, 0))

        packed = b'$4\x90\x80'
        unpacked = unpack('b1t24', packed)
        self.assertEqual(unpacked, (False, u'Hi!'))

        packed = 1000 * b'7'
        unpacked = unpack('t8000', packed)
        self.assertEqual(packed, 1000 * b'\x37')

        if sys.version_info >= (3, 6):
            unpacked = unpack('f16', b'\x3c\x00')
            self.assertEqual(unpacked, (1.0, ))

        unpacked = unpack('f32', b'\x3f\x80\x00\x00')
        self.assertEqual(unpacked, (1.0, ))

        unpacked = unpack('f64', b'\x3f\xf0\x00\x00\x00\x00\x00\x00')
        self.assertEqual(unpacked, (1.0, ))

    def test_pack_unpack(self):
        """Pack and unpack values.

        """

        if not is_cpython_3():
            return

        packed = pack('u1u1s6u7u9', 0, 0, -2, 65, 22)
        unpacked = unpack('u1u1s6u7u9', packed)
        self.assertEqual(unpacked, (0, 0, -2, 65, 22))

        packed = pack('f64', 1.0)
        unpacked = unpack('f64', packed)
        self.assertEqual(unpacked, (1.0, ))

        if sys.version_info >= (3, 6):
            packed = pack('f16', 1.0)
            unpacked = unpack('f16', packed)
            self.assertEqual(unpacked, (1.0, ))

    def test_calcsize(self):
        """Calculate size.

        """

        if not is_cpython_3():
            return

        size = calcsize('u1u1s6u7u9')
        self.assertEqual(size, 24)

        size = calcsize('u1')
        self.assertEqual(size, 1)

        size = calcsize('u1s6u7u9')
        self.assertEqual(size, 23)

        size = calcsize('b1s6u7u9p1t8')
        self.assertEqual(size, 32)

        size = calcsize('b1s6u7u9P1t8')
        self.assertEqual(size, 32)

    def test_compiled_calcsize(self):
        """Calculate size.

        """

        if not is_cpython_3():
            return

        cf = bitstruct.c.compile('u1u1s6u7u9')
        self.assertEqual(cf.calcsize(), 24)

        cf = bitstruct.c.compile('u1u1s6u7u9', ['a', 'b', 'c', 'd', 'e'])
        self.assertEqual(cf.calcsize(), 24)

    def test_byteswap(self):
        """Byte swap.

        """

        if not is_cpython_3():
            return

        res = b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a'
        ref = b'\x01\x03\x02\x04\x08\x07\x06\x05\x0a\x09'
        self.assertEqual(byteswap('12142', ref), res)

        packed = pack('u1u5u2u16', 1, 2, 3, 4)
        unpacked = unpack('u1u5u2u16', byteswap('12', packed))
        self.assertEqual(unpacked, (1, 2, 3, 1024))

        res = b'\x01\x02\x03\x04\x05\x06\x07\x08'
        ref = b'\x08\x07\x06\x05\x04\x03\x02\x01'
        self.assertEqual(byteswap('8', ref), res)

    def test_pack_into(self):
        """Pack values into a buffer.

        """

        if not is_cpython_3():
            return

        packed = bytearray(3)
        pack_into('u1u1s6u7u9', packed, 0, 0, 0, -2, 65, 22)
        self.assertEqual(packed, b'\x3e\x82\x16')

        datas = [
            (0,  b'\x80\x00'),
            (1,  b'\x40\x00'),
            (7,  b'\x01\x00'),
            (15, b'\x00\x01')
        ]

        for offset, expected in datas:
            packed = bytearray(2)
            pack_into('u1', packed, offset, 1)
            self.assertEqual(packed, expected)

        with self.assertRaises(AssertionError):
            packed = bytearray(b'\xff\xff\xff')
            pack_into('p4u4p4u4p4u4', packed, 0, 1, 2, 3, fill_padding=False)
            self.assertEqual(packed, b'\xf1\xf2\xf3')

        packed = bytearray(b'\xff\xff\xff')
        pack_into('p4u4p4u4p4u4', packed, 0, 1, 2, 3, fill_padding=True)
        self.assertEqual(packed, b'\x01\x02\x03')

        packed = bytearray(2)

        with self.assertRaises(ValueError) as cm:
            pack_into('u17', packed, 0, 1)

        self.assertEqual(str(cm.exception),
                         'pack_into requires a buffer of at least 17 bits')

        packed = bytearray(b'\x00')
        pack_into('P4u4', packed, 0, 1)
        self.assertEqual(packed, b'\xf1')

        datas = [
            (0, b'\x7f\xff\xff\xff'),
            (1, b'\xbf\xff\xff\xff'),
            (7, b'\xfe\xff\xff\xff'),
            (8, b'\xff\x7f\xff\xff'),
            (15, b'\xff\xfe\xff\xff'),
            (16, b'\xff\xff\x7f\xff'),
            (31, b'\xff\xff\xff\xfe')
        ]

        for offset, expected in datas:
            packed = bytearray(b'\xff\xff\xff\xff')
            pack_into('u1', packed, offset, 0)
            self.assertEqual(packed, expected)

        # Check for non-writable buffer.
        with self.assertRaises(TypeError):
            pack_into('u1', b'\x00', 0, 0)

    def test_unpack_from(self):
        """Unpack values at given bit offset.

        """

        if not is_cpython_3():
            return

        unpacked = unpack_from('u1u1s6u7u9', b'\x1f\x41\x0b\x00', 1)
        self.assertEqual(unpacked, (0, 0, -2, 65, 22))

        unpacked = unpack_from('u1', b'\x80')
        self.assertEqual(unpacked, (1, ))

        unpacked = unpack_from('u1', b'\x08', 4)
        self.assertEqual(unpacked, (1, ))

        with self.assertRaises(ValueError):
            unpack_from('u1', b'\xff', 8)

        with self.assertRaises(TypeError):
            unpack_from('u1', b'\xff', None)

    def test_compiled_pack_into(self):
        """Pack values at given bit offset.

        """

        if not is_cpython_3():
            return

        cf = bitstruct.c.compile('u2')
        packed = bytearray(2)
        cf.pack_into(packed, 7, 3)
        self.assertEqual(packed, b'\x01\x80')

    def test_compiled_unpack_from(self):
        """Unpack values at given bit offset.

        """

        if not is_cpython_3():
            return

        cf = bitstruct.c.compile('u1')
        unpacked = cf.unpack_from(b'\x40', 1)
        self.assertEqual(unpacked, (1, ))

        unpacked = cf.unpack_from(b'\x80')
        self.assertEqual(unpacked, (1, ))

    def test_pack_unpack_raw(self):
        """Pack and unpack raw values.

        """

        if not is_cpython_3():
            return

        with self.assertRaises(NotImplementedError):
            packed = pack('r24', b'')
            self.assertEqual(packed, b'\x00\x00\x00')

        with self.assertRaises(NotImplementedError):
            packed = pack('r24', b'12')
            self.assertEqual(packed, b'12\x00')

        packed = pack('r24', b'123')
        self.assertEqual(packed, b'123')
        packed = pack('r24', b'1234')
        self.assertEqual(packed, b'123')

        unpacked = unpack('r24', b'\x00\x00\x00')[0]
        self.assertEqual(unpacked, b'\x00\x00\x00')
        unpacked = unpack('r24', b'12\x00')[0]
        self.assertEqual(unpacked, b'12\x00')
        unpacked = unpack('r24', b'123')[0]
        self.assertEqual(unpacked, b'123')
        unpacked = unpack('r24', b'1234')[0]
        self.assertEqual(unpacked, b'123')

    def test_pack_unpack_dict(self):
        if not is_cpython_3():
            return

        unpacked = {
            'foo': 0,
            'bar': 0,
            'fie': -2,
            'fum': 65,
            'fam': 22
        }
        packed = b'\x3e\x82\x16'
        fmt = 'u1u1s6u7u9'
        names = ['foo', 'bar', 'fie', 'fum', 'fam']

        self.assertEqual(pack_dict(fmt, names, unpacked), packed)
        self.assertEqual(unpack_dict(fmt, names, packed), unpacked)

    def test_pack_into_unpack_from_dict(self):
        if not is_cpython_3():
            return

        unpacked = {
            'foo': 0,
            'bar': 0,
            'fie': -2,
            'fum': 65,
            'fam': 22
        }
        packed = b'\x3e\x82\x16'
        fmt = 'u1u1s6u7u9'
        names = ['foo', 'bar', 'fie', 'fum', 'fam']

        actual = bytearray(3)
        pack_into_dict(fmt, names, actual, 0, unpacked)
        self.assertEqual(actual, packed)

        self.assertEqual(unpack_from_dict(fmt, names, packed), unpacked)

    def test_compiled_pack_into_unpack_from_dict(self):
        if not is_cpython_3():
            return

        unpacked = {
            'foo': 0,
            'bar': 0,
            'fie': -2,
            'fum': 65,
            'fam': 22
        }
        packed = b'\x3e\x82\x16'
        fmt = 'u1u1s6u7u9'
        names = ['foo', 'bar', 'fie', 'fum', 'fam']
        cf = bitstruct.c.compile(fmt, names)

        actual = bytearray(3)
        cf.pack_into(actual, 0, unpacked)
        self.assertEqual(actual, packed)

        self.assertEqual(cf.unpack_from(packed), unpacked)

    def test_compile(self):
        if not is_cpython_3():
            return

        cf = bitstruct.c.compile('u1u1s6u7u9')

        packed = cf.pack(0, 0, -2, 65, 22)
        self.assertEqual(packed, b'\x3e\x82\x16')

        unpacked = cf.unpack(b'\x3e\x82\x16')
        self.assertEqual(unpacked, (0, 0, -2, 65, 22))

    def test_compile_pack_unpack_formats(self):
        if not is_cpython_3():
            return

        fmts = [
            ('u1s2p3',         None, (1, -1)),
            ('u1 s2 p3',       None, (1, -1)),
            ('u1s2p3',   ['a', 'b'], {'a': 1, 'b': -1})
        ]

        for fmt, names, decoded in fmts:
            if names is None:
                cf = bitstruct.c.compile(fmt)
                packed_1 = cf.pack(*decoded)
                packed_2 = pack(fmt, *decoded)
            else:
                cf = bitstruct.c.compile(fmt, names)
                packed_1 = cf.pack(decoded)
                packed_2 = pack_dict(fmt, names, decoded)

            self.assertEqual(packed_1, b'\xe0')
            self.assertEqual(packed_2, b'\xe0')

            if names is None:
                unpacked_1 = cf.unpack(packed_1)
                unpacked_2 = unpack(fmt, packed_2)
            else:
                unpacked_1 = cf.unpack(packed_1)
                unpacked_2 = unpack_dict(fmt, names, packed_2)

            self.assertEqual(unpacked_1, decoded)
            self.assertEqual(unpacked_2, decoded)

    def test_compile_formats(self):
        if not is_cpython_3():
            return

        bitstruct.c.compile('p1u1')
        bitstruct.c.compile('p1u1', ['a'])

        with self.assertRaises(TypeError):
            bitstruct.c.compile()

    def test_pack_unpack_signed(self):
        if not is_cpython_3():
            return

        datas = [
            ('s1', 0, b'\x00'),
            ('s1', -1, b'\x80'),
            ('s63', -1, b'\xff\xff\xff\xff\xff\xff\xff\xfe'),
            ('s64', -1, b'\xff\xff\xff\xff\xff\xff\xff\xff')
        ]

        for fmt, value, packed in datas:
            self.assertEqual(pack(fmt, value), packed)
            self.assertEqual(unpack(fmt, packed), (value, ))

    def test_pack_unpack_unsigned(self):
        if not is_cpython_3():
            return

        datas = [
            ('u1', 0, b'\x00'),
            ('u1', 1, b'\x80'),
            ('u63', 0x1234567890abcdef, b'$h\xac\xf1!W\x9b\xde'),
            ('u64', 0x1234567890abcdef, b'\x124Vx\x90\xab\xcd\xef')
        ]

        for fmt, value, packed in datas:
            self.assertEqual(pack(fmt, value), packed)
            self.assertEqual(unpack(fmt, packed), (value, ))

    def test_various(self):
        if not is_cpython_3():
            return

        with self.assertRaises(ValueError):
            pack('u89999888888888888888899', 1)

        # Fewer names than fields in the format.
        with self.assertRaises(ValueError):
            pack_dict('u1u1', ['foo'], {'foo': 1})

        # Missing value for name.
        with self.assertRaises(KeyError):
            pack_dict('u1', ['foo'], {})

        # Fewer names than fields in the format.
        with self.assertRaises(ValueError):
            unpack_dict('u1u1', ['foo'], b'\xff')

        # Short data.
        with self.assertRaises(ValueError):
            unpack_dict('u1', ['foo'], b'')

        # Padding last.
        self.assertEqual(pack('u1p1', 1), b'\x80')
        self.assertEqual(pack_dict('u1p1', ['foo'], {'foo': 1}), b'\x80')

        # Short text.
        with self.assertRaises(NotImplementedError) as cm:
            pack('t16', '1')

        self.assertEqual(str(cm.exception), 'Short text.')

        # Bad float length.
        with self.assertRaises(NotImplementedError) as cm:
            pack('f1', 1.0)

        if sys.version_info >= (3, 6):
            self.assertEqual(str(cm.exception), 'Float not 16, 32 or 64 bits.')
        else:
            self.assertEqual(str(cm.exception), 'Float not 32 or 64 bits.')

        # Long bool.
        with self.assertRaises(NotImplementedError) as cm:
            pack('b65', True)

        self.assertEqual(str(cm.exception), 'Bool over 64 bits.')

        # Text not multiple of 8 bits.
        with self.assertRaises(NotImplementedError) as cm:
            pack('t1', '')

        self.assertEqual(str(cm.exception), 'Text not multiple of 8 bits.')

        # Bad format kind.
        with self.assertRaises(ValueError) as cm:
            pack('x1', '')

        self.assertEqual(str(cm.exception), "Bad format field type 'x'.")

        # Too few arguments.
        with self.assertRaises(ValueError) as cm:
            pack('u1u1', 1)

        self.assertEqual(str(cm.exception), 'Too few arguments.')

        # No format string.
        with self.assertRaises(ValueError) as cm:
            pack()

        self.assertEqual(str(cm.exception), 'No format string.')

        # No format string.
        with self.assertRaises(ValueError) as cm:
            unpack('u1', b'')

        self.assertEqual(str(cm.exception), 'Short data.')

        # Bad format in compile.
        with self.assertRaises(ValueError) as cm:
            bitstruct.c.compile('x1')

        self.assertEqual(str(cm.exception), "Bad format field type 'x'.")

        # Bad format in compile dict.
        with self.assertRaises(ValueError) as cm:
            bitstruct.c.compile('x1', ['foo'])

        self.assertEqual(str(cm.exception), "Bad format field type 'x'.")

        # Offset too big.
        with self.assertRaises(ValueError) as cm:
            packed = bytearray(1)
            pack_into('u1', packed, 0x80000000, 1)

        self.assertIn("Offset must be less or equal to ", str(cm.exception))

        # Offset too big.
        with self.assertRaises(ValueError) as cm:
            packed = bytearray(1)
            pack_into_dict('u1', ['a'], packed, 0x80000000, {'a': 1})

        self.assertIn("Offset must be less or equal to ", str(cm.exception))

        # Offset too big.
        with self.assertRaises(ValueError) as cm:
            unpack_from('u1', b'\x00', 0x80000000)

        self.assertIn("Offset must be less or equal to ", str(cm.exception))

        # Offset too big.
        with self.assertRaises(ValueError) as cm:
            packed = bytearray(1)
            unpack_from_dict('u1', ['a'], b'\x00', 0x80000000)

        self.assertIn("Offset must be less or equal to ", str(cm.exception))

        # Out of data to swap.
        datas = ['11', '2', '4', '8']

        for fmt in datas:
            with self.assertRaises(ValueError) as cm:
                byteswap(fmt, b'\x00')

            self.assertEqual(str(cm.exception), 'Out of data to swap.')

        # Bad swap format.
        with self.assertRaises(ValueError) as cm:
            byteswap('3', b'\x00')

        # Bad swap format type.
        with self.assertRaises(TypeError):
            byteswap(None, b'\x00')

        self.assertEqual(str(cm.exception), 'Expected 1, 2, 4 or 8, but got 3.')

        # Bad format type.
        with self.assertRaises(TypeError):
            pack(None, 1)

        # Out of range checks.
        datas = [
            ('s64', (1 << 63)),
            ('s64', -(1 << 63) - 1),
            ('u64', 1 << 64),
            ('u64', -1),
            ('u1', 2),
            ('s1', 1),
            ('s1', -2),
            ('s2', 2)
        ]

        for fmt, value in datas:
            with self.assertRaises(OverflowError) as cm:
                pack(fmt, value)

        # Bad value types.
        with self.assertRaises(TypeError) as cm:
            pack('s1', None)

        with self.assertRaises(TypeError) as cm:
            pack('u1', None)

        with self.assertRaises(TypeError) as cm:
            pack('f32', None)

        with self.assertRaises(TypeError) as cm:
            pack('r8', None)

        with self.assertRaises(TypeError) as cm:
            pack('t8', None)

        # Everything can be bool.
        self.assertEqual(pack('b8', None), b'\x00')

        # Zero bits bool.
        with self.assertRaises(ValueError) as cm:
            pack('b0', None)

        self.assertEqual(str(cm.exception), 'Field of size 0.')

        # pack/unpack dict with names as a non-list. Caused an segfault.
        with self.assertRaises(TypeError) as cm:
            pack_into_dict('u1', None, bytearray(b'\x00'), 0, {'a': 1})

        self.assertEqual(str(cm.exception), 'Names is not a list.')

        with self.assertRaises(TypeError) as cm:
            pack_dict('u1', None, {'a': 1})

        self.assertEqual(str(cm.exception), 'Names is not a list.')

        with self.assertRaises(TypeError) as cm:
            bitstruct.c.compile('u1', 1)

        self.assertEqual(str(cm.exception), 'Names is not a list.')

    def test_whitespaces(self):
        if not is_cpython_3():
            return

        fmts = [
            ' ',
            ' u1     s2 p3 '
        ]

        for fmt in fmts:
            bitstruct.c.compile(fmt)

    def test_copy(self):
        if not is_cpython_3():
            return

        cf = bitstruct.c.compile('u1u1s6u7u9')

        cf = copy.copy(cf)
        packed = cf.pack(0, 0, -2, 65, 22)
        self.assertEqual(packed, b'\x3e\x82\x16')

        cf = copy.deepcopy(cf)
        packed = cf.pack(0, 0, -2, 65, 22)
        self.assertEqual(packed, b'\x3e\x82\x16')

    def test_copy_dict(self):
        if not is_cpython_3():
            return

        unpacked = {
            'foo': 0,
            'bar': 0,
            'fie': -2,
            'fum': 65,
            'fam': 22
        }
        names = ['foo', 'bar', 'fie', 'fum', 'fam']
        cf = bitstruct.c.compile('u1u1s6u7u9', names)

        cf = copy.copy(cf)
        packed = cf.pack(unpacked)
        self.assertEqual(packed, b'\x3e\x82\x16')
        self.assertEqual(cf.unpack(packed), unpacked)

        cf = copy.deepcopy(cf)
        packed = cf.pack(unpacked)
        self.assertEqual(packed, b'\x3e\x82\x16')
        self.assertEqual(cf.unpack(packed), unpacked)


if __name__ == '__main__':
    unittest.main()
