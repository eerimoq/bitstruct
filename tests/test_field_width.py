import unittest

import bitstruct


class ShortFieldWidthTest(unittest.TestCase):

    def cases(self):
        for kind, values in [('r', [b'', b'A', b'AB']),
                             ('t', ['', 'A', 'AB'])]:
            for width in (1, 7, 8, 9, 13, 16, 17, 24):
                for value in values:
                    for endian in ('>', '<'):
                        raw = value.encode('utf-8') if kind == 't' else value
                        bits = ''.join(f'{byte:08b}' for byte in raw)
                        bits = bits[:width].ljust(width, '0')
                        if endian == '<':
                            bits = bits[::-1]
                        yield kind, width, value, endian, '101' + bits + '11101'

    @staticmethod
    def to_bytes(bits):
        padded = bits.ljust((len(bits) + 7) // 8 * 8, '0')
        return int(padded, 2).to_bytes(len(padded) // 8, 'big')

    def test_pack_short_fields(self):
        for kind, width, value, endian, bits in self.cases():
            fmt = f'u3{endian}{kind}{width}>u5'
            with self.subTest(fmt=fmt, value=value):
                expected = self.to_bytes(bits)
                self.assertEqual(bitstruct.pack(fmt, 5, value, 29), expected)
                self.assertEqual(bitstruct.compile(fmt).pack(5, value, 29), expected)
                self.assertEqual(bitstruct.pack_dict(
                    fmt, ['first', 'payload', 'last'],
                    {'first': 5, 'payload': value, 'last': 29}), expected)
                self.assertEqual(bitstruct.unpack(f'p{width + 3}u5', expected), (29,))

    def test_pack_short_fields_into_buffer(self):
        for kind, width, value, endian, bits in self.cases():
            fmt = f'u3{endian}{kind}{width}>u5'
            with self.subTest(fmt=fmt, value=value):
                output = bytearray(b'\xa5' * 8)
                original = ''.join(f'{byte:08b}' for byte in output)
                expected = self.to_bytes(original[:5] + bits + original[5 + len(bits):])
                bitstruct.pack_into(fmt, output, 5, 5, value, 29)
                self.assertEqual(output, expected)
