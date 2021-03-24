from ruida_core import unswizzle
from pathlib import Path


TEXTFILE_DIR = Path(__file__).parent.joinpath("..", "lightburn")


def unswizzle_data(d):
    return bytes([unswizzle(b) for b in d])


with open(TEXTFILE_DIR.joinpath("commands.txt")) as f1, open(TEXTFILE_DIR.joinpath("responses.txt")) as f2:
    count = 0
    while True:
        count += 1
        command = unswizzle_data(bytearray.fromhex(f1.readline()))
        ack = unswizzle_data(bytearray.fromhex(f2.readline()))
        data = unswizzle_data(bytearray.fromhex(f2.readline()))
        if not (command and ack and data):
            break
        print(f"\nCount: {count}")
        print("command: " + command.hex())
        print("ack:     " + ack.hex())
        print("data:    " + data.hex())
