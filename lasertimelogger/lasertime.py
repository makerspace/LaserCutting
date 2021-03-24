from datetime import datetime

MAGIC = 0x88
logFilePath = "log.csv"

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


def ruidaBytesToSeconds(data):
    seconds = 0
    i = len(data) - 1
    for byte in data:
        byte = unswizzle(byte)
        num = int(byte)

        s = num * 2 ** (7 * i)
        seconds = seconds + s
        i = i - 1
    return seconds


def getLaserTime(data):
    laserTimeS = ruidaBytesToSeconds(data)

    laserTimeM, laserTimeS = divmod(laserTimeS, 60)
    laserTimeH, laserTimeM = divmod(laserTimeM, 60)
    return (laserTimeH, laserTimeM, laserTimeS)


if __name__ == "__main__":
    laserAcknowledged = False
    receivedLaserTime = False
    logFile = open(logFilePath, "a")

    while (not receivedLaserTime):
        try:
            data = self.sock.recv(16)  # TODO fix to correct socket
        except Exception as e:
            print("Receiving failed ", e)
            raise Exception(e)

        # Some test data
        # data = bytes([0xd4, 0x09, 0x8d, 0x19, 0x89, 0x89, 0x2d, 0x9f, 0xb1])

        firstByte = unswizzle(data[0])
        if firstByte == 0xCF:
            # Failed request try again
            # TODO retry functionality
            print("Fail")
        elif firstByte == 0xCC:
            # We received laser acknowledge package
            laserAcknowledged = True
        elif firstByte == 0xda and unswizzle(data[2]) == 0x04 and unswizzle(data[3]) == 0x11:
            # We got the total laser work time package
            receivedLaserTime = True
            laserTimeH, laserTimeM, laserTimeS = getLaserTime(data[4:9])
            todaysDateAndTime = datetime.now()
            logFile.write(
                todaysDateAndTime.strftime("%d/%m/%Y %H:%M:%S") + "," + str(laserTimeH) + "," + str(
                    laserTimeM) + "," + str(
                    laserTimeS) + "\n")
        else:
            raise Exception("Got a different package than expected")

    logFile.close()
