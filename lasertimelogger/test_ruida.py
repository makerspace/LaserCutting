import unittest
from ruida import RuidaCommand


class TestRuidaCommand(unittest.TestCase):
    def test_encoded_run_time(self):
        self.assertEqual(bytearray.fromhex("0203d4898d19"), RuidaCommand.GET_RUN_TIME.bytes)


if __name__ == '__main__':
    unittest.main()
