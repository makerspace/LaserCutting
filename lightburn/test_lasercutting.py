import unittest
from lasercutting import swizzle, unswizzle


class TestSwizzling(unittest.TestCase):
    def test_back_and_forth(self):
        for expected_value in range(256):
            self.assertEqual(expected_value, unswizzle(swizzle(expected_value)))


if __name__ == '__main__':
    unittest.main()
