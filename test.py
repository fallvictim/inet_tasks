import socketserver
import socket
import sys
import threading
from binascii import hexlify, unhexlify
import time


def hex2int(data):
    return int(hexlify(data), 16)


def hex2bin(data):
    try:
        return bin(int(hexlify(data), 16))[2:].zfill(16)
    except ValueError:
        print(data)

domain_cache = []
ip_cache = []


class BaseRequestHandler(socketserver.BaseRequestHandler):
    def get_data(self):
        raise NotImplementedError

    def send_data(self, data):
        raise NotImplementedError

    def handle(self):
        data = self.get_data()

        # Try to read questions - if they're invalid, don't respond.
        if len(data) < 12:
            return
        try:
            quest = self.parse(data)
            ans_data = self.query(data)
            print(ans_data)
            ans = self.parse(ans_data)
            self.send_data(ans_data)
            print('quest',quest)
            print('ans',ans)
        except TypeError:
            pass

    def parse(self, data):

        def read_name(pointer):
            name = ''
            while True:
                temp = hex2bin(data[pointer:pointer + 2])
                if temp[0:2] == '11':
                    temp_point = int(temp[2:], 2)
                    name += read_name(temp_point)[0]
                    pointer += 2
                    break
                else:
                    length = int(data[pointer])
                    pointer += 1
                    if length == 0:
                        break
                    temp = unhexlify(hexlify(data[pointer:pointer + length])).decode()
                    name += temp + '.'
                    pointer += length
            return name, pointer

        id = hex2int(data[0:2])
        flags = hex2bin(data[2:4])
        qcount = hex2int(data[4:6])
        ancount = hex2int(data[6:8])
        nscount = hex2int(data[8:10])
        arcount = hex2int(data[10:12])
        result = [id, flags, qcount]
        name = ''
        pointer = 12

        for i in range(qcount):
            name, pointer = read_name(pointer)
            result.append(name)
            qtype = data[pointer:pointer+2]
            qclass = data[pointer+2:pointer+4]
            result.append(qtype)
            result.append(qclass)
            pointer += 4

        for i in range(ancount):
            name, pointer = read_name(pointer)
            result.append(name)
            type = data[pointer:pointer+2]
            r_class = data[pointer+2:pointer+4]
            ttl = data[pointer+4:pointer+8]
            rdlength = data[pointer+8:pointer+10]
            rdata = data[pointer+10:pointer+10+hex2int(rdlength)]
            result.append([type,r_class,ttl,rdlength,rdata])
            pointer += 10 + hex2int(rdlength)

        for i in range(nscount):
            name, pointer = read_name(pointer)
            result.append(name)
            type = data[pointer:pointer+2]
            r_class = data[pointer+2:pointer+4]
            ttl = data[pointer+4:pointer+8]
            rdlength = data[pointer+8:pointer+10]
            rdata = data[pointer+10:pointer+10+hex2int(rdlength)]
            result.append([type,r_class,ttl,rdlength,rdata])
            pointer += 10 + hex2int(rdlength)

        for i in range(arcount):
            name, pointer = read_name(pointer)
            result.append(name)
            type = data[pointer:pointer + 2]
            r_class = data[pointer + 2:pointer + 4]
            ttl = data[pointer + 4:pointer + 8]
            rdlength = data[pointer + 8:pointer + 10]
            rdata = data[pointer + 10:pointer + 10 + hex2int(rdlength)]
            result.append([type, r_class, ttl, rdlength, rdata])
            pointer += 10 + hex2int(rdlength)

        return result





    def query(self, data):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_address = ('8.8.8.8', 53)
        s.sendto(data, server_address)
        data, server = s.recvfrom(4096)
        return data


class TCPRequestHandler(BaseRequestHandler):

    def get_data(self):
        data = self.request.recv(8192).strip()
        sz = int(data[:2].encode('hex'), 16)
        if sz < len(data) - 2:
            raise Exception("Wrong size of TCP packet")
        elif sz > len(data) - 2:
            raise Exception("Too big TCP packet")
        return data[2:]

    def send_data(self, data):
        sz = hex(len(data))[2:].zfill(4).decode('hex')
        return self.request.sendall(sz + data)


class UDPRequestHandler(BaseRequestHandler):

    def get_data(self):
        return self.request[0].strip()

    def send_data(self, data):
        return self.request[1].sendto(data, self.client_address)


if __name__ == '__main__':
    host, port = '127.0.0.1', 53
    servers = [
        socketserver.ThreadingUDPServer(('', port), UDPRequestHandler),
        socketserver.ThreadingTCPServer(('', port), TCPRequestHandler),
    ]
    for s in servers:
        thread = threading.Thread(target=s.serve_forever)  # that thread will start one more thread for each request
        thread.daemon = True  # exit the server thread when the main thread terminates
        thread.start()
        print(
        "%s server loop running in thread: %s" % (s.RequestHandlerClass.__name__[:3], thread.name))
    try:
        while 1:
            time.sleep(1)
            sys.stderr.flush()
            sys.stdout.flush()

    except KeyboardInterrupt:
        pass
    finally:
        for s in servers:
            s.shutdown()

