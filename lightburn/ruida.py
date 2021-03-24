import logging
from typing import ByteString
from struct import pack
from enum import Enum
from socket import socket, AF_INET, SOCK_DGRAM, timeout as SocketTimeout

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


def get_checksum(msg: ByteString):
    _sum = sum(msg[:])
    return pack("!H", _sum & 0xFFFF)


def command_checksum_valid(msg: ByteString):
    return msg[:2] == get_checksum(msg[2:])


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

    def send(self, cmd: RuidaCommand, retry=False):
        self.sock.send(cmd.bytes)
        while True:
            try:
                ack = bytes([unswizzle(b) for b in self.sock.recv(self.MTU)])
            except SocketTimeout:
                continue

        if len(ack) == 0:
            logger.warning("Received empty packet")
            return

        if ack[0] == MSG_ACK:
            logger.debug("Received ACK")
        elif ack[0] == MSG_ERROR:
            logger.warning("Received error response")
            return
        else:
            logger.info(f"Unknown response 0x{ack.hex()}")
            return

        try:
            resp = bytes([unswizzle(b) for b in self.sock.recv(self.MTU)])
        except SocketTimeout:
            logger.error("Got no data after the ACK")
        logger.info(f"Got response: 0x{resp.hex()}")
