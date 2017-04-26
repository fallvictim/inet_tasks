import socket
import datetime
from datetime import timedelta


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('localhost', 123))
with open('config') as f:
    secs = int(f.readline())
delta = timedelta(seconds=secs)

while True:
    data, address = s.recvfrom(1024)
    time = datetime.datetime.now()
    if data:
        sent = s.sendto(str(time + delta).encode(), address)
