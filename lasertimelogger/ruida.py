import logging
from typing import ByteString
from enum import Enum
from lasertime import ruida_bytes_to_unsigned
import time
from ruida_core import get_checksum, swizzle, unswizzle
from socket import socket, AF_INET, SOCK_DGRAM, timeout as SocketTimeout

logger = logging.getLogger(__name__)

MSG_ACK = 0xCC
MSG_ERROR = 0xCD


class RuidaCommand(Enum):
    GET_RUN_TIME = "da000411"

    def __init__(self, value):
        value = bytearray.fromhex(value)
        data = bytes([swizzle(b) for b in value])
        cs = get_checksum(data)
        self.bytes = cs + data
        self.checksum = cs
        self.command = value

    @classmethod
    def from_bytes(cls, b: ByteString):
        for e in cls:
            if e.bytes == b:
                return e
        else:
            raise ValueError(f"The value does not match a value in the Enum {cls.__name__}")


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
        self.host = host

    def get_run_time(self):
        resp = self.send(RuidaCommand.GET_RUN_TIME)
        if resp:
            return ruida_bytes_to_unsigned(resp[-5:])

    def send(self, cmd: RuidaCommand, retry=False):
        self.sock.send(cmd.bytes)
        # Parse data in the buffer until we get to the ACK, or it's empty
        while True:
            try:
                ack = bytes([unswizzle(b) for b in self.sock.recv(self.MTU)])
            except SocketTimeout:
                logger.error("No response was received for command")
                return
            except ConnectionRefusedError:
                # https://stackoverflow.com/a/2373630/4713758
                # If the remote server does not have the port open, we get an ICMP response
                logger.error(f"The server at {self.host}:{self.DEST_PORT} is refusing the message")
                return

            if len(ack) == 0:
                logger.warning("Received empty packet")
                continue

            if ack[0] == MSG_ACK:
                logger.debug("Received ACK")
            elif ack[0] == MSG_ERROR:
                logger.warning("Received error response")
                continue
            else:
                logger.info(f"Unknown response 0x{ack.hex()}")
                continue

            try:
                resp = bytes([unswizzle(b) for b in self.sock.recv(self.MTU)])
            except SocketTimeout:
                logger.error("Got no data after the ACK")
                continue
            logger.info(f"Got response: 0x{resp.hex()}")
            return resp


if __name__ == "__main__":
    ruida = RuidaCommunicator("localhost")
    while True:
        cmd = RuidaCommand.GET_RUN_TIME
        runtime = ruida.get_run_time()
        if runtime:
            print(f"{cmd} -> {runtime} s")
        time.sleep(1)
