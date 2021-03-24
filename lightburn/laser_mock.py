from ruida import RuidaCommand, RuidaCommunicator, MSG_ACK, MSG_ERROR, swizzle
from datetime import timedelta, datetime, time
from dataclasses import dataclass
from struct import pack
from socket import socket, AF_INET, SOCK_DGRAM, timeout as SocketTimeout
import logging

logger = logging.getLogger(__name__)


@dataclass
class LaserMock:
    runtime: timedelta = timedelta(hours=0, minutes=0, seconds=0)

    def get_response(self, command: RuidaCommand):
        if command == RuidaCommand.GET_RUN_TIME:
            runtime_seconds = int(self.runtime.total_seconds())
            logger.debug(f"Runtime: {runtime_seconds} s")
            data_packed = ((runtime_seconds << 3) & 0x3F000000) | ((runtime_seconds << 2) & 0x003F0000) | (
                        (runtime_seconds << 1) & 0x00003F00) | (runtime_seconds & 0x0000007F)
            data_packed = pack("!q", data_packed)
            return bytes([MSG_ACK]), bytearray.fromhex("da010411") + data_packed[-5:]
        else:
            return bytes([MSG_ERROR]), b""

    def main(self, port: int = RuidaCommunicator.DEST_PORT):
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.bind(("", port))
        sock.settimeout(0.01)

        while True:
            now = datetime.now()
            self.runtime = now - datetime.combine(now.date(), time(0, 0, 0))
            try:
                command, address = sock.recvfrom(1400)
            except SocketTimeout:
                continue
            try:
                command = RuidaCommand.from_bytes(command)
                print(f"Responding to {command} from {address}")
            except ValueError as e:
                logger.error(f"Could not convert to RuidaCommand. Got {command}")
                continue
            ack, resp = self.get_response(command)
            sock.sendto(bytes([swizzle(b) for b in ack]), address)
            sock.sendto(bytes([swizzle(b) for b in resp]), address)


if __name__ == "__main__":
    lasermock = LaserMock()
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s (%(levelname)s): %(module)s[%(lineno)d]: %(message)s')
    lasermock.main()
