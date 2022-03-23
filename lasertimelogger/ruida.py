import logging
from enum import Enum
import time

from ruida_core import get_checksum, swizzle, unswizzle, ruida_bytes_to_unsigned
from socket import socket, AF_INET, SOCK_DGRAM, timeout as SocketTimeout
from multiprocessing import Process, Lock, Value

logger = logging.getLogger(__name__)

class MSGTypes(Enum):
    MSG_ACK = b'\xcc'
    MSG_ERROR = b'\xcd'
    MSG_PROPERTY = b'\xda'
    MSG_PROPERTY_QUERY = b'\x00'
    MSG_PROPERTY_SET = b'\x01'
    MSG_COMMAND_THRESHOLD = b'\x80'

class CMDTypes(Enum):
    RUN_TIME = b'\x04\x11'
    MACHINE_STATUS = b'\x04\x00'

class RuidaCommand(Enum):
    GET_RUN_TIME = MSGTypes.MSG_PROPERTY.value + MSGTypes.MSG_PROPERTY_QUERY.value +  CMDTypes.RUN_TIME.value
    GET_MACHINE_STATUS = MSGTypes.MSG_PROPERTY.value + MSGTypes.MSG_PROPERTY_QUERY.value + CMDTypes.MACHINE_STATUS.value

    def __init__(self, value):
        data = bytes([swizzle(b) for b in value])
        cs = get_checksum(data)
        self.bytes = cs + data
        self.checksum = cs

    @classmethod
    def from_bytes(cls, b: bytes):
        for e in cls:
            if e.bytes == b:
                return e
        else:
            raise ValueError(f"The value does not match a value in the Enum {cls.__name__}")


class RuidaCommunicator:
    NETWORK_TIMEOUT = 10000
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
            resp = bytes([unswizzle(b) for b in self.sock.recv(self.MTU)])
        except SocketTimeout:
            logger.info("No new response received")
            return
        except ConnectionRefusedError:
            # https://stackoverflow.com/a/2373630/4713758
            # If the remote server does not have the port open, we get an ICMP response
            logger.error(f"The server at {self.host}:{self.DEST_PORT} is refusing the message")
            return

        if len(resp) == 0:
            logger.warning("Received empty packet")
            return

        if resp[0] == int.from_bytes(MSGTypes.MSG_ACK.value, "big"):
            logger.info("Received ACK")
            return
        elif resp[0] == int.from_bytes(MSGTypes.MSG_ERROR.value, "big"):
            logger.warning("Received error response")
            return
        else:
            logger.info(f"Got response 0x{resp.hex()}")
            return resp

def server(ruida: RuidaCommunicator, received_msg_lock):
    done = False
    while True:
        resp = ruida.receive()
        if resp == None:
            continue
        received_cmd = resp[0:4] #The first four bytes correspond with the command that was sent
        
        #Check what cmd we got response for
        if received_cmd[0] == int.from_bytes(MSGTypes.MSG_PROPERTY.value, "big"):
            logger.info(f"Got property cmd")
            #The response is for a command of the msg property type
            if received_cmd[2:4] == CMDTypes.RUN_TIME.value:
                logger.info(f"Got run time cmd")
                runtime = ruida_bytes_to_unsigned(resp[-5:])

                minutes, seconds = divmod(runtime, 60)
                hours, minutes = divmod(minutes, 60)
                days, hours = divmod(hours, 24)
                print(f"{cmd} -> {runtime} s ({days} days, {hours:2}h {minutes:2}m {seconds:2} s)")

                done = True

        #Are we done? If yes change the mutex and quit
        if done:
            logger.info(f"Done")
            with msg_received.get_lock():
                msg_received.value = True
            break

def client(ruida: RuidaCommunicator, received_msg_lock, cmd):
    while True:
        logger.info(f"Send cmd")
        ruida.send(cmd)
        time.sleep(60)

        with msg_received.get_lock():
            if msg_received.value:
                break

if __name__ == "__main__":
    ip = "10.20.0.252"
    cmd = RuidaCommand.GET_RUN_TIME
    
    logging.basicConfig(format="%(asctime)s - %(module)-8s %(levelname)5s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.DEBUG)
    
    ruida = RuidaCommunicator(ip)
    msg_received = Value('i', False)

    server_process = Process(target = server, args = (ruida, msg_received))
    server_process.start()

    client_process = Process(target = client, args = (ruida, msg_received, cmd))
    client_process.start()
