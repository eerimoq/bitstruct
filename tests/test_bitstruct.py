from __future__ import print_function
import sys
import timeit
import unittest
from bitstruct import *
import bitstruct

class BitStructTest(unittest.TestCase):

    def test_pack(self):
        """Pack values.

        """

        packed = pack('u1u1s6u7u9', 0, 0, -2, 65, 22)
        self.assertEqual(packed, b'\x3e\x82\x16')

        packed = pack('u1', 1)
        self.assertEqual(packed, b'\x80')

        packed = pack('u77', 0x100000000001000000)
        ref = b'\x00\x80\x00\x00\x00\x00\x08\x00\x00\x00'
        self.assertEqual(packed, ref)

        packed = pack('u8000', int(8000 * '1', 2))
        ref = 1000 * b'\xff'
        self.assertEqual(packed, ref)

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

        # Too many values to pack.
        with self.assertRaises(Error) as cm:
            pack('b1t24', False)

        self.assertEqual(str(cm.exception),
                         'pack expected 2 item(s) for packing (got 1)')

        # Cannot convert argument to integer.
        with self.assertRaises(ValueError) as cm:
            pack('u1', 'foo')

        self.assertEqual(str(cm.exception),
                         "invalid literal for int() with base 10: 'foo'")

        # Cannot convert argument to float.
        with self.assertRaises(ValueError) as cm:
            pack('f32', 'foo')

        if sys.version_info[0] < 3:
            self.assertEqual(str(cm.exception),
                             'could not convert string to float: foo')
        else:
            self.assertEqual(str(cm.exception),
                             "could not convert string to float: 'foo'")

        # Cannot convert argument to bytearray.
        with self.assertRaises(TypeError) as cm:
            pack('r5', 1.0)

        self.assertIn("'float' has no", str(cm.exception))

        # Cannot encode argument as utf-8.
        with self.assertRaises(AttributeError) as cm:
            pack('t8', 1.0)

        self.assertEqual(str(cm.exception),
                         "'float' object has no attribute 'encode'")

    def test_unpack(self):
        """Unpack values.

        """

        unpacked = unpack('u1u1s6u7u9', b'\x3e\x82\x16')
        self.assertEqual(unpacked, (0, 0, -2, 65, 22))

        unpacked = unpack('u1', bytearray(b'\x80'))
        self.assertEqual(unpacked, (1, ))

        packed = b'\x00\x80\x00\x00\x00\x00\x08\x00\x00\x00'
        unpacked = unpack('u77', packed)
        self.assertEqual(unpacked, (0x100000000001000000,))

        packed = 1000 * b'\xff'
        unpacked = unpack('u8000', packed)
        self.assertEqual(unpacked, (int(8000 * '1', 2), ))

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

        packed = b'\x7c\x80\xe0\x00\x00\x01\xfe\x01\xfe\x01\xc0'
        unpacked = unpack('u1s6f32r43', packed)
        self.assertEqual(unpacked, (0, -2, 3.75, b'\x00\xff\x00\xff\x00\xe0'))

        packed = bytearray(b'\x80')
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

        # Bad float size.
        with self.assertRaises(Error) as cm:
            unpack('f33', b'\x00\x00\x00\x00\x00')

        self.assertEqual(str(cm.exception),
                         'expected float size of 16, 32, or 64 bits (got 33)')

        # Too many bits to unpack.
        with self.assertRaises(Error) as cm:
            unpack('u9', b'\x00')

        self.assertEqual(str(cm.exception),
                         'unpack requires at least 9 bits to unpack (got 8)')

        # gcc packed struct with bitfields
        #
        # struct foo_t {
        #     int a;
        #     char b;
        #     uint32_t c : 7;
        #     uint32_t d : 25;
        # } foo;
        #
        # foo.a = 1;
        # foo.b = 1;
        # foo.c = 0x67;
        # foo.d = 0x12345;
        unpacked = unpack('s32s8u25u7',
                          byteswap('414',
                                   b'\x01\x00\x00\x00\x01\xe7\xa2\x91\x00'))
        self.assertEqual(unpacked, (1, 1, 0x12345, 0x67))

    def test_pack_unpack(self):
        """Pack and unpack values.

        """

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

        size = calcsize('u1u1s6u7u9')
        self.assertEqual(size, 24)

        size = calcsize('u1')
        self.assertEqual(size, 1)

        size = calcsize('u77')
        self.assertEqual(size, 77)

        size = calcsize('u1s6u7u9')
        self.assertEqual(size, 23)

        size = calcsize('b1s6u7u9p1t8')
        self.assertEqual(size, 32)

        size = calcsize('b1s6u7u9P1t8')
        self.assertEqual(size, 32)

    def test_byteswap(self):
        """Byte swap.

        """

        res = b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a'
        ref = b'\x01\x03\x02\x04\x08\x07\x06\x05\x0a\x09'
        self.assertEqual(byteswap('12142', ref), res)

        packed = pack('u1u5u2u16', 1, 2, 3, 4)
        unpacked = unpack('u1u5u2u16', byteswap('12', packed))
        self.assertEqual(unpacked, (1, 2, 3, 1024))

    def test_endianness(self):
        """Test pack/unpack with endianness information in the format string.

        """

        # Big endian.
        ref = b'\x02\x46\x9a\xfe\x00\x00\x00'
        packed = pack('>u19s3f32', 0x1234, -2, -1.0)
        self.assertEqual(packed, ref)
        unpacked = unpack('>u19s3f32', packed)
        self.assertEqual(unpacked, (0x1234, -2, -1.0))

        # Little endian.
        ref = b'\x2c\x48\x0c\x00\x00\x07\xf4'
        packed = pack('<u19s3f32', 0x1234, -2, -1.0)
        self.assertEqual(packed, ref)
        unpacked = unpack('<u19s3f32', packed)
        self.assertEqual(unpacked, (0x1234, -2, -1.0))

        # Mixed endianness.
        ref = b'\x00\x00\x2f\x3f\xf0\x00\x00\x00\x00\x00\x00\x80'
        packed = pack('>u19<s5>f64r3p4', 1, -2, 1.0, b'\x80')
        self.assertEqual(packed, ref)
        unpacked = unpack('>u19<s5>f64r3p4', packed)
        self.assertEqual(unpacked, (1, -2, 1.0, b'\x80'))

        # Opposite endianness of the 'mixed endianness' test.
        ref = b'\x80\x00\x1e\x00\x00\x00\x00\x00\x00\x0f\xfc\x20'
        packed = pack('<u19>s5<f64r3p4', 1, -2, 1.0, b'\x80')
        self.assertEqual(packed, ref)
        unpacked = unpack('<u19>s5<f64r3p4', packed)
        self.assertEqual(unpacked, (1, -2, 1.0, b'\x80'))

        # Pack as big endian, unpack as little endian.
        ref = b'\x40'
        packed = pack('u2', 1)
        self.assertEqual(packed, ref)
        unpacked = unpack('<u2', packed)
        self.assertEqual(unpacked, (2, ))

    def test_byte_order(self):
        """Test pack/unpack with byte order information in the format string.

        """

        # Most significant byte first (default).
        ref = b'\x02\x46\x9a\xfe\x00\x00\x00'
        packed = pack('u19s3f32>', 0x1234, -2, -1.0)
        self.assertEqual(packed, ref)
        unpacked = unpack('u19s3f32>', packed)
        self.assertEqual(unpacked, (0x1234, -2, -1.0))

        # Least significant byte first.
        ref = b'\x34\x12\x18\x00\x00\xe0\xbc'
        packed = pack('u19s3f32<', 0x1234, -2, -1.0)
        self.assertEqual(packed, ref)
        unpacked = unpack('u19s3f32<', packed)
        self.assertEqual(unpacked, (0x1234, -2, -1.0))

        # Least significant byte first.
        ref = b'\x34\x12'
        packed = pack('u8s8<', 0x34, 0x12)
        self.assertEqual(packed, ref)
        unpacked = unpack('u8s8<', packed)
        self.assertEqual(unpacked, (0x34, 0x12))

        # Least significant byte first.
        ref = b'\x34\x22'
        packed = pack('u3u12<', 1, 0x234)
        self.assertEqual(packed, ref)
        unpacked = unpack('u3s12<', packed)
        self.assertEqual(unpacked, (1, 0x234))

        # Least significant byte first.
        ref = b'\x34\x11\x00'
        packed = pack('u3u17<', 1, 0x234)
        self.assertEqual(packed, ref)
        unpacked = unpack('u3s17<', packed)
        self.assertEqual(unpacked, (1, 0x234))

        # Least significant byte first.
        ref = b'\x80'
        packed = pack('u1<', 1)
        self.assertEqual(packed, ref)
        unpacked = unpack('u1<', packed)
        self.assertEqual(unpacked, (1, ))

        # Least significant byte first.
        ref = b'\x45\x23\x25\x82'
        packed = pack('u19u5u1u7<', 0x12345, 5, 1, 2)
        self.assertEqual(packed, ref)
        unpacked = unpack('u19u5u1u7<', packed)
        self.assertEqual(unpacked, (0x12345, 5, 1, 2))

        # Least significant byte first does not affect raw and text.
        ref = b'123abc'
        packed = pack('r24t24<', b'123', 'abc')
        self.assertEqual(packed, ref)
        unpacked = unpack('r24t24<', packed)
        self.assertEqual(unpacked, (b'123', 'abc'))

    def test_compile(self):
        cf = bitstruct.compile('u1u1s6u7u9')

        packed = cf.pack(0, 0, -2, 65, 22)
        self.assertEqual(packed, b'\x3e\x82\x16')

        unpacked = cf.unpack(b'\x3e\x82\x16')
        self.assertEqual(unpacked, (0, 0, -2, 65, 22))

    def test_signed_integer(self):
        """Pack and unpack signed integer values.

        """

        datas = [
            ('s2', 0x01, b'\x40'),
            ('s3', 0x03, b'\x60'),
            ('s4', 0x07, b'\x70'),
            ('s5', 0x0f, b'\x78'),
            ('s6', 0x1f, b'\x7c'),
            ('s7', 0x3f, b'\x7e'),
            ('s8', 0x7f, b'\x7f'),
            ('s9', 0xff, b'\x7f\x80'),
            ('s1',   -1, b'\x80'),
            ('s2',   -1, b'\xc0')
        ]

        for fmt, value, packed in datas:
            self.assertEqual(pack(fmt, value), packed)
            self.assertEqual(unpack(fmt, packed), (value, ))

    def test_unsigned_integer(self):
        """Pack and unpack unsigned integer values.

        """

        datas = [
            ('u1', 0x001, b'\x80'),
            ('u2', 0x003, b'\xc0'),
            ('u3', 0x007, b'\xe0'),
            ('u4', 0x00f, b'\xf0'),
            ('u5', 0x01f, b'\xf8'),
            ('u6', 0x03f, b'\xfc'),
            ('u7', 0x07f, b'\xfe'),
            ('u8', 0x0ff, b'\xff'),
            ('u9', 0x1ff, b'\xff\x80')
        ]

        for fmt, value, packed in datas:
            self.assertEqual(pack(fmt, value), packed)
            self.assertEqual(unpack(fmt, packed), (value, ))

    def test_bad_float_size(self):
        """Test of bad float size.

        """

        with self.assertRaises(Error) as cm:
            pack('f31', 1.0)

        self.assertEqual(str(cm.exception),
                         'expected float size of 16, 32, or 64 bits (got 31)')

        with self.assertRaises(Error) as cm:
            unpack('f33', 8 * b'\x00')

        self.assertEqual(str(cm.exception),
                         'expected float size of 16, 32, or 64 bits (got 33)')

    def test_bad_format(self):
        """Test of bad format.

        """

        formats = [
            ('g1', "bad char 'g' in format"),
            ('s1u1f32b1t8r8G13', "bad char 'G' in format"),
            ('s1u1f32b1t8r8G13S3', "bad char 'G' in format"),
            ('s', "bad format 's'"),
            ('1', "bad format '1'"),
            ('ss1', "bad format 'ss1'"),
            ('1s', "bad format '1s'"),
            ('foo', "bad format 'foo'"),
            ('s>1>', "bad format 's>1>'"),
            ('s0', "bad format 's0'")
        ]

        for fmt, expected_error in formats:
            with self.assertRaises(Error) as cm:
                bitstruct.compile(fmt)

            self.assertEqual(str(cm.exception), expected_error)

    def test_empty_format(self):
        """Test of empty format type.

        """

        cf = bitstruct.compile('')

        self.assertEqual(cf.pack(), b'')
        self.assertEqual(cf.pack(1), b'')

        self.assertEqual(cf.unpack(b''), ())
        self.assertEqual(cf.unpack(b'\x00'), ())

    def test_byte_order_format(self):
        """Test of a format with only byte order information.

        """

        cf = bitstruct.compile('>')

        self.assertEqual(cf.pack(), b'')
        self.assertEqual(cf.pack(1), b'')

        self.assertEqual(cf.unpack(b''), ())
        self.assertEqual(cf.unpack(b'\x00'), ())

    def test_pack_into(self):
        """Pack values into a buffer.

        """

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

        packed = bytearray(b'\xff\xff\xff')
        pack_into('p4u4p4u4p4u4', packed, 0, 1, 2, 3, fill_padding=False)
        self.assertEqual(packed, b'\xf1\xf2\xf3')

        packed = bytearray(b'\xff\xff\xff')
        pack_into('p4u4p4u4p4u4', packed, 0, 1, 2, 3, fill_padding=True)
        self.assertEqual(packed, b'\x01\x02\x03')

        packed = bytearray(2)

        with self.assertRaises(Error) as cm:
            pack_into('u17', packed, 0, 1)

        self.assertEqual(str(cm.exception),
                         'pack_into requires a buffer of at least 17 bits')

        packed = bytearray(b'\x00')
        pack_into('P4u4', packed, 0, 1)
        self.assertEqual(packed, b'\xf1')

        # Too many values to pack.
        with self.assertRaises(Error) as cm:
            packed = bytearray(b'\x00')
            pack_into('b1t24', packed, 0, False)

        self.assertEqual(str(cm.exception),
                         'pack expected 2 item(s) for packing (got 1)')

    def test_unpack_from(self):
        """Unpack values at given bit offset.

        """

        unpacked = unpack_from('u1u1s6u7u9', b'\x1f\x41\x0b\x00', 1)
        self.assertEqual(unpacked, (0, 0, -2, 65, 22))

        with self.assertRaises(Error) as cm:
            unpack_from('u1u1s6u7u9', b'\x1f\x41\x0b', 1)

        self.assertEqual(str(cm.exception),
                         'unpack requires at least 24 bits to unpack '
                         '(got 23)')

    def test_pack_integers_value_checks(self):
        """Pack integer values range checks.

        """

        # Formats with minimum and maximum allowed values.
        datas = [
            ('s1', -1, 0),
            ('s2', -2, 1),
            ('s3', -4, 3),
            ('u1',  0, 1),
            ('u2',  0, 3),
            ('u3',  0, 7)
        ]

        for fmt, minimum, maximum in datas:
            # No exception should be raised for numbers in range.
            pack(fmt, minimum)
            pack(fmt, maximum)

            # Numbers out of range.
            for number in [minimum - 1, maximum + 1]:
                with self.assertRaises(Error) as cm:
                    pack(fmt, number)

                self.assertEqual(
                    str(cm.exception),
                    '"{}" requires {} <= integer <= {} (got {})'.format(
                        fmt,
                        minimum,
                        maximum,
                        number))

    def test_pack_unpack_raw(self):
        """Pack and unpack raw values.

        """

        packed = pack('r24', b'')
        self.assertEqual(packed, b'\x00\x00\x00')
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

    def test_pack_unpack_text(self):
        """Pack and unpack text values.

        """

        packed = pack('t24', '')
        self.assertEqual(packed, b'\x00\x00\x00')
        packed = pack('t24', '12')
        self.assertEqual(packed, b'12\x00')
        packed = pack('t24', '123')
        self.assertEqual(packed, b'123')
        packed = pack('t24', '1234')
        self.assertEqual(packed, b'123')

        unpacked = unpack('t24', b'\x00\x00\x00')[0]
        self.assertEqual(unpacked, '\x00\x00\x00')
        unpacked = unpack('t24', b'12\x00')[0]
        self.assertEqual(unpacked, '12\x00')
        unpacked = unpack('t24', b'123')[0]
        self.assertEqual(unpacked, '123')
        unpacked = unpack('t24', b'1234')[0]
        self.assertEqual(unpacked, '123')

    def test_pack_unpack_dict(self):
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

    def test_pack_dict_missing_key(self):
        unpacked = {
            'foo': 0,
            'bar': 0,
            'fie': -2,
            'fum': 65
        }
        fmt = 'u1u1s6u7u9'
        names = ['foo', 'bar', 'fie', 'fum', 'fam']

        with self.assertRaises(Error) as cm:
            pack_dict(fmt, names, unpacked)

        self.assertEqual(str(cm.exception),
                         "'fam' not found in data dictionary")

        with self.assertRaises(Error) as cm:
            data = bytearray(3)
            pack_into_dict(fmt, names, data, 0, unpacked)

        self.assertEqual(str(cm.exception),
                         "'fam' not found in data dictionary")

    def test_compile_pack_unpack_formats(self):
        fmts = [
            ('u1s2p3',         None, (1, -1)),
            ('u1 s2 p3',       None, (1, -1)),
            ('u1s2p3',   ['a', 'b'], {'a': 1, 'b': -1})
        ]

        for fmt, names, decoded in fmts:
            if names is None:
                cf = bitstruct.compile(fmt)
                packed_1 = cf.pack(*decoded)
                packed_2 = pack(fmt, *decoded)
            else:
                cf = bitstruct.compile(fmt, names)
                packed_1 = cf.pack(decoded)
                packed_2 = pack_dict(fmt, names, decoded)

            self.assertEqual(packed_1, b'\xe0')
            self.assertEqual(packed_2, b'\xe0')

    def test_compile_formats(self):
        bitstruct.compile('p1u1')
        bitstruct.compile('p1u1', ['a'])

    def test_pack_unpack_signed(self):
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
        datas = [
            ('u1', 0, b'\x00'),
            ('u1', 1, b'\x80'),
            ('u63', 0x1234567890abcdef, b'$h\xac\xf1!W\x9b\xde'),
            ('u64', 0x1234567890abcdef, b'\x124Vx\x90\xab\xcd\xef')
        ]

        for fmt, value, packed in datas:
            self.assertEqual(pack(fmt, value), packed)
            self.assertEqual(unpack(fmt, packed), (value, ))


if __name__ == '__main__':
    unittest.main()
