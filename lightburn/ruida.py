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
