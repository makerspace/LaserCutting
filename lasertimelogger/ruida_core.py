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
