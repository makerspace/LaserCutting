import unittest
from ruida import RuidaCommand, MSG_ACK
from laser_mock import LaserMock
from datetime import timedelta


class TestLaserMock(unittest.TestCase):
    def setUp(self) -> None:
        self.lasermock = LaserMock(runtime=timedelta(hours=169, minutes=11, seconds=20))

    def test_laser_time(self):
        ack, response = self.lasermock.get_response(RuidaCommand.GET_RUN_TIME)
        self.assertEqual(bytes([MSG_ACK]), ack)
        self.assertSequenceEqual(bytearray.fromhex("da0104110000251638"), response)


if __name__ == '__main__':
    unittest.main()
