from ruida import RuidaCommand, MSG_ACK, MSG_ERROR
from datetime import timedelta
from dataclasses import dataclass
from struct import pack


@dataclass
class LaserMock:
    runtime: timedelta = timedelta(hours=169, minutes=11, seconds=22)

    def get_response(self, command: RuidaCommand):
        if command == RuidaCommand.GET_RUN_TIME:
            runtime_seconds = int(self.runtime.total_seconds())
            data_packed = ((runtime_seconds << 3) & 0x3F000000) | ((runtime_seconds << 2) & 0x003F0000) | ((runtime_seconds << 1) & 0x00003F00) | (runtime_seconds & 0x0000007F)
            data_packed = pack("!q", data_packed)
            return bytes([MSG_ACK]), bytearray.fromhex("da010411") + data_packed[-5:]
        else:
            return bytes([MSG_ERROR])
