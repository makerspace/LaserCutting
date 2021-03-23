MAGIC = 0x88


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
