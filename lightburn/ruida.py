import time
import logging
from typing import ByteString
from enum import Enum
from socket import socket, AF_INET, SOCK_DGRAM

logger = logging.getLogger(__name__)

MAGIC = 0x88

MSG_ACK = 0xCC
MSG_ERROR = 0xCD


class RuidaCommand(Enum):
    GET_RUN_TIME = "890bda000411"

    def __init__(self, value):
        value = bytearray.fromhex(value)
        self.bytes = value
        self.checksum = value[:2]
        self.command = value[2:]

    @classmethod
    def from_bytes(cls, b: ByteString):
        for e in cls:
            if e.bytes == b:
                return e
        else:
            raise ValueError(f"The value does not match a value in the Enum {cls.__name__}")


def unswizzle(b):
    b = (b - 1) & 0xFF
    b ^= MAGIC
    b ^= (b >> 7) & 0xFF
    b ^= (b << 7) & 0xFF
    b ^= (b >> 7) & 0xFF
    return b


# def check_checksum(data):
#     sum = 0
#     for i in bytes(data[2:]):
#         sum += i & 0xff     # unsigned
#     seen = ((data[0] & 0xff) << 8) + (data[1] & 0xff)
#     if seen == sum:
#         return data[2:]
#     return None


def swizzle(b):
    b ^= (b >> 7) & 0xFF
    b ^= (b << 7) & 0xFF
    b ^= (b >> 7) & 0xFF
    b ^= MAGIC
    b = (b + 1) & 0xFF
    return b


class RuidaCommunicator:
    NETWORK_TIMEOUT = 3000
    INADDR_ANY_DOTTED = '0.0.0.0'  # bind to all interfaces.
    SOURCE_PORT = 40200  # Receive port
    DEST_PORT = 50200  # Ruida Board
    MTU = 1470  # max data length per datagram (minus checksum)

    def __init__(self, host, dest_port=DEST_PORT, recv_port=SOURCE_PORT):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind((self.INADDR_ANY_DOTTED, recv_port))
        self.sock.connect((host, dest_port))
        self.sock.settimeout(self.NETWORK_TIMEOUT * 0.001)

    def send(self, ary, retry=False):
        while True:
            self.sock.send(ary)
            try:
                data = self.sock.recv(8)  # timeout raises an exception
                d0 = unswizzle(data[0])
            except Exception:
                logger.exception("Failed to receive from socket")
                break
            if len(data) == 0:
                logger.warning("Received nothing (empty)")
                break
            if d0 == MSG_ERROR:
                logger.warning("Checksum error")
                if retry:
                    logger.info("Retrying...")
                    time.sleep(0.5)
                else:
                    raise IOError("Checksum error")
            elif d0 == MSG_ACK:
                logger.debug("Received ACK")
                break
            else:
                logger.info(f"Unknown response {d0:02x}")
                break
