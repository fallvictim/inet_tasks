import socketserver
import socket
import sys
import threading
import time
import datetime
import dns_parser, dns_packet_creator, cache


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
            query = dns_parser.parse(data)
            from_cache = None
            if query is not None:
                from_cache = cache.get_answers(query.get('questions'))
            if from_cache is not None:
                answer_data = dns_packet_creator.create(query, from_cache)
                self.send_data(answer_data)
            else:
                answer_data = self.query(data)
                answer = dns_parser.parse(answer_data)
                cache.add_answers(answer, datetime.datetime.now())
                self.send_data(answer_data)
        except(TypeError, AttributeError):
            print('quest', data)
            try:
                print('ans', answer_data)
            except UnboundLocalError:
                pass


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
        cache.save_cache()
