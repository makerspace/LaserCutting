from struct import pack
from typing import ByteString

MAGIC = 0x88


def unswizzle(b):
    b = (b - 1) & 0xFF
    b ^= MAGIC
    b ^= (b >> 7) & 0xFF
    b ^= (b << 7) & 0xFF
    b ^= (b >> 7) & 0xFF
    return b


def get_checksum(msg):
    _sum = sum(msg[:])
    return pack("!H", _sum & 0xFFFF)


def command_checksum_valid(msg):
    return msg[:2] == get_checksum(msg[2:])


def swizzle(b):
    b ^= (b >> 7) & 0xFF
    b ^= (b << 7) & 0xFF
    b ^= (b >> 7) & 0xFF
    b ^= MAGIC
    b = (b + 1) & 0xFF
    return b


def ruida_bytes_to_unsigned(data):
    seconds = 0
    i = len(data) - 1
    for byte in data:
        num = int(byte)

        s = num * 2 ** (7 * i)
        seconds = seconds + s
        i = i - 1
    return seconds
