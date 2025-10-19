from socket import *
import os
import sys
import struct
import time
import select

ICMP_ECHO_REQUEST = 8


def checksum(source_string):
    csum = 0
    countTo = (len(source_string) // 2) * 2
    count = 0
    while count < countTo:
        thisVal = source_string[count + 1] * 256 + source_string[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(source_string):
        csum = csum + source_string[len(source_string) - 1]
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout
    while True:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []:
            return "Request timed out."

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        icmpHeader = recPacket[20:28]
        type, code, checksum_recv, packetID, sequence = struct.unpack("bbHHh", icmpHeader)

        if packetID == ID:
            bytesInDouble = struct.calcsize("d")
            timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
            rtt = (timeReceived - timeSent) * 1000
            return f"Reply from {addr[0]}: bytes={len(recPacket)} time={rtt:.2f}ms"

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "Request timed out."


def sendOnePing(mySocket, destAddr, ID):
    myChecksum = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    myChecksum = checksum(header + data)

    if sys.platform == 'darwin':
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    mySocket.sendto(packet, (destAddr, 1))


def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")
    try:
        mySocket = socket(AF_INET, SOCK_RAW, icmp)
    except PermissionError:
        sys.exit("You need to run this script as administrator/root to use raw sockets.")

    myID = os.getpid() & 0xFFFF
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return delay


def ping(host, timeout=1, count=4):
    dest = gethostbyname(host)
    print(f"\nPinging {host} [{dest}] with Python:\n")

    delays = []
    packets_sent = 0
    packets_received = 0

    for i in range(count):
        packets_sent += 1
        delay = doOnePing(dest, timeout)
        print(delay)
        if isinstance(delay, str) and "Request timed out" in delay:
            pass
        else:
            packets_received += 1
            try:
                time_ms = float(delay.split("time=")[-1].replace("ms", ""))
                delays.append(time_ms)
            except:
                pass
        time.sleep(1)

    print("\n--- Ping statistics ---")
    print(f"{packets_sent} packets transmitted, {packets_received} received, "
          f"{(packets_sent - packets_received) / packets_sent * 100:.0f}% packet loss")

    if delays:
        print(f"rtt min/avg/max = {min(delays):.2f}/{sum(delays)/len(delays):.2f}/{max(delays):.2f} ms")


targets = {
    "North America (Google)": "google.com",
    "Europe (BBC UK)": "bbc.co.uk",
    "Asia (Jeju Nat. Univ, Korea)": "jnu.ac.kr",
    "Australia (Univ. of Sydney)": "sydney.edu.au"
}

for location, host in targets.items():
    print(f"\n==================== {location} ====================")
    ping(host, count=4)