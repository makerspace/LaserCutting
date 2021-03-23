from ruida import unswizzle


with open("commands.txt") as f1, open("responses.txt") as f2:
    count = 0
    while True:
        count += 1
        command = bytearray.fromhex(f1.readline())
        ack = bytearray.fromhex(f2.readline())
        data = bytearray.fromhex(f2.readline())
        if not (command and ack and data):
            break
        print(f"\nCount: {count}")
        print("command: " + bytearray([unswizzle(b) for b in command]).hex())
        print("ack:     " + bytearray([unswizzle(b) for b in ack]).hex())
        print("data:    " + bytearray([unswizzle(b) for b in data]).hex())
