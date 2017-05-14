import socket


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('localhost', 123)
message = 'hello'

try:
    print('sending "%s"' % message)
    sent = s.sendto(message.encode(), server_address)

    print('waiting to receive')
    data, server = s.recvfrom(4096)
    print( 'received "%s"' % data.decode())

finally:
    print('closing socket')
    s.close()
