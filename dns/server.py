import socketserver
import socket
import sys
import os
import threading
import time
import dns_parser
import dns_packet_creator
import cache


class BaseRequestHandler(socketserver.BaseRequestHandler):

    def get_data(self):
        raise NotImplementedError

    def send_data(self, data):
        raise NotImplementedError

    def handle(self):
        data = self.get_data()
        if len(data) < 12:
            return
        parsed = dns_parser.parse(data)
        qr = None
        if parsed is not None:
            qr = parsed.get('header', dict()).get('qr')
        if qr == 'QUERY':
            from_cache = None
            if parsed is not None:
                from_cache = cache.get_answers(parsed.get('questions'))
            if from_cache is not None:
                print('send from cache')
                answer_data = dns_packet_creator.create(parsed, from_cache)
                self.send_data(answer_data)
            else:
                answer_data = self.query(data)
                answer = dns_parser.parse(answer_data)
                opcode = parsed.get('header', dict()).get('opcode')
                if opcode != 'IQUERY':
                    cache.add_answers(answer)
                self.send_data(answer_data)

    def query(self, data):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_address = ('8.8.8.8', 53)
        s.sendto(data, server_address)
        data, server = s.recvfrom(4096)
        return data


class UDPRequestHandler(BaseRequestHandler):

    def get_data(self):
        return self.request[0].strip()

    def send_data(self, data):
        return self.request[1].sendto(data, self.client_address)


if __name__ == '__main__':
    host, port = '127.0.0.1', 53
    servers = [
        socketserver.ThreadingUDPServer(('', port), UDPRequestHandler)
    ]
    for s in servers:
        thread = threading.Thread(target=s.serve_forever)
        thread.daemon = True
        thread.start()
        print("%s server loop running in thread: %s" % (s.RequestHandlerClass.__name__[:3], thread.name))
    try:
        while 1:
            time.sleep(1)
            sys.stderr.flush()
            sys.stdout.flush()

    except KeyboardInterrupt:
        for s in servers:
            s.shutdown()
        cache.save_cache()
        os._exit(0)
