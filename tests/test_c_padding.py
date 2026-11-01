import unittest

import bitstruct
import bitstruct.c as c


class CFieldPaddingTest(unittest.TestCase):
    def cases(self):
        for kind, values in [('r', [b'', b'A', b'AB', b'ABCDE']),
                             ('t', ['', 'A', 'AB', 'ABCDE', 'é'])]:
            for width in (8, 16, 24, 40):
                for value in values:
                    raw = value.encode('utf-8') if kind == 't' else value
                    field = ''.join(f'{byte:08b}' for byte in raw)
                    field = field[:width].ljust(width, '0')
                    yield kind, width, value, '101' + field + '11101'

    @staticmethod
    def to_bytes(bits):
        padded = bits.ljust((len(bits) + 7) // 8 * 8, '0')
        return int(padded, 2).to_bytes(len(padded) // 8, 'big')

    def test_pack_short_fields(self):
        for kind, width, value, bits in self.cases():
            fmt = f'u3{kind}{width}u5'
            values = (5, value, 29)
            names = ['before', 'payload', 'after']
            mapping = dict(zip(names, values))
            with self.subTest(fmt=fmt, value=value):
                expected = self.to_bytes(bits)
                self.assertEqual(c.pack(fmt, *values), expected)
                self.assertEqual(c.compile(fmt).pack(*values), expected)
                self.assertEqual(c.pack_dict(fmt, names, mapping), expected)
                self.assertEqual(c.compile(fmt, names).pack(mapping), expected)
                self.assertEqual(bitstruct.pack(fmt, *values), expected)
                self.assertEqual(c.unpack(f'p{width + 3}u5', expected), (29,))

    def test_pack_short_fields_into(self):
        for kind, width, value, bits in self.cases():
            fmt = f'u3{kind}{width}u5'
            names = ['before', 'payload', 'after']
            mapping = {'before': 5, 'payload': value, 'after': 29}
            for variant in range(4):
                with self.subTest(fmt=fmt, value=value, variant=variant):
                    output = bytearray(b'\xa5' * 12)
                    original = ''.join(f'{byte:08b}' for byte in output)
                    expected = self.to_bytes(original[:5] + bits + original[5 + len(bits):])
                    if variant == 0:
                        c.pack_into(fmt, output, 5, 5, value, 29)
                    elif variant == 1:
                        c.compile(fmt).pack_into(output, 5, 5, value, 29)
                    elif variant == 2:
                        c.pack_into_dict(fmt, names, output, 5, mapping)
                    else:
                        c.compile(fmt, names).pack_into(output, 5, mapping)
                    self.assertEqual(output, expected)

    def test_existing_restrictions(self):
        for fmt, value in [('r9', b''), ('t9', '')]:
            with self.subTest(fmt=fmt):
                with self.assertRaises(NotImplementedError):
                    c.pack(fmt, value)
        for fmt, value in [('r16', 'A'), ('r16', bytearray(b'A')),
                           ('t16', b'A')]:
            with self.subTest(fmt=fmt, value=value):
                with self.assertRaises(TypeError):
                    c.pack(fmt, value)
