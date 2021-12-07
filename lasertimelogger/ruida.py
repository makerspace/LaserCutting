import logging
from typing import ByteString
from enum import Enum
import time
from ruida_core import get_checksum, swizzle, unswizzle, ruida_bytes_to_unsigned
from socket import socket, AF_INET, SOCK_DGRAM, timeout as SocketTimeout
from multiprocessing import Process, Lock, Value

logger = logging.getLogger(__name__)

class MSGTypes(Enum):
    MSG_ACK = 0xCC
    MSG_ERROR = 0xCD
    MSG_PROPERTY = 0xDA
    MSG_PROPERTY_QUERY = 0x00
    MSG_PROPERTY_SET = 0x01
    MSG_COMMAND_THRESHOLD = 0x80

    def __init__(self, value):
        self.bytes = bytes(value)

class CMDTypes(Enum):
    RUN_TIME = 0x0411
    MACHINE_STATUS =0x0400

    def __init__(self, value):
        self.bytes = bytes(value)

class RuidaCommand(Enum):
    GET_RUN_TIME = '{:02x}'.format(MSGTypes.MSG_PROPERTY) + '{:02x}'.format(MSGTypes.MSG_PROPERTY_QUERY) + '{:04x}'.format(CMDTypes.RUN_TIME)
    GET_MACHINE_STATUS = '{:02x}'.format(MSGTypes.MSG_PROPERTY) + '{:02x}'.format(MSGTypes.MSG_PROPERTY_QUERY) + '{:04x}'.format(CMDTypes.MACHINE_STATUS)

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

    def send(self, cmd: RuidaCommand):
        self.sock.send(cmd.bytes)

    def receive(self):
        try:
            ack = bytes([unswizzle(b) for b in self.sock.recv(self.MTU)])
        except SocketTimeout:
            logger.error("No new response received")
            return
        except ConnectionRefusedError:
            # https://stackoverflow.com/a/2373630/4713758
            # If the remote server does not have the port open, we get an ICMP response
            logger.error(f"The server at {self.host}:{self.DEST_PORT} is refusing the message")
            return

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
            return
        logger.info(f"Got response: 0x{resp.hex()}")
        return resp

def server(ruida: RuidaCommunicator, received_msg_lock):
    done = False
    while True:
        resp = ruida.receive() #TODO might need to improve exception handling
        if resp == None:
            continue
        
        print("recived something")
        print(resp)
        print(RuidaCommand.GET_RUN_TIME.value)
        print(bytes(bytearray.fromhex(RuidaCommand.GET_RUN_TIME.value)))
        #Check what cmd we got response for
        received_cmd = resp[0:4]
        print(received_cmd)
        print(received_cmd == bytes(bytearray.fromhex(RuidaCommand.GET_RUN_TIME.value)))
        
        #TODO need updating
        if received_cmd[0] == bytes(bytearray.fromhex(MSGTypes.MSG_PROPERTY)):
            logger.info(f"Got property cmd")
            #The response is for a command of the msg property type
            if received_cmd[2:3] == bytes(bytearray.fromhex(CMDTypes.RUN_TIME.value)):
                logger.info(f"Got run time cmd")
                print("get run time")
                runtime = ruida_bytes_to_unsigned(resp[-5:])
                print(runtime)
                done = True

        #Are we done? If yes change the mutex and quit
        if done:
            with msg_received.get_lock():
                msg_received.value = True
            break

def client(ruida: RuidaCommunicator, received_msg_lock, cmd):
    while True:
        ruida.send(cmd)
        print("client sleep")
        time.sleep(5)

        with msg_received.get_lock():
            if msg_received.value:
                break

if __name__ == "__main__":
    ip = "10.20.0.252"
    cmd = RuidaCommand.GET_RUN_TIME
    
    ruida = RuidaCommunicator(ip)
    msg_received = Value('i', False)

    server_process = Process(target = server, args = (ruida, msg_received))
    server_process.start()

    client_process = Process(target = client, args = (ruida, msg_received, cmd))
    client_process.start()
