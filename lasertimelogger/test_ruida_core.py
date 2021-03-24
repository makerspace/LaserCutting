import unittest
from ruida_core import swizzle, unswizzle, get_checksum, command_checksum_valid
from pathlib import Path


_dir = Path(__file__).parent


class TestSwizzling(unittest.TestCase):
    def test_back_and_forth(self):
        for expected_value in range(256):
            self.assertEqual(expected_value, unswizzle(swizzle(expected_value)))


class TestChecksum(unittest.TestCase):
    def test_zeros(self):
        self.assertSequenceEqual(b'\x00\x00', get_checksum(b'\x00'))
        self.assertSequenceEqual(b'\x00\x00', get_checksum(b'\x00\x00\x00'))

    def test_ones(self):
        self.assertSequenceEqual(b'\x00\x01', get_checksum(b'\x01'))
        self.assertSequenceEqual(b'\x00\x02', get_checksum(b'\x01\x01'))
        self.assertSequenceEqual(b'\x00\x03', get_checksum(b'\x01\x01\x01'))

    def test_check_checksum(self):
        with open(_dir.joinpath("..", "lightburn", "commands.txt")) as f:
            for i, r in enumerate(f.readlines()):
                msg = bytearray.fromhex(r)
                self.assertTrue(command_checksum_valid(msg), f"Valid checksum {i}")


if __name__ == '__main__':
    unittest.main()
