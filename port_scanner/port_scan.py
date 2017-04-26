from datetime import datetime
import _thread as thread
import socket


def child(thread_id, ip):
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    ports_to_check = 65536 // threads_count
    for port in range(ports_to_check * thread_id, (thread_id + 1) * ports_to_check):
        try:
            udp_sock.sendto(''.encode(), (ip, port))
        except Exception:
            print('Exception on port: ' + str(port))

        tcp_result = tcp_sock.connect_ex((ip, port))
        if tcp_result == 0:
            stdout_mutex.acquire()
            print("Port {}: Open".format(port))
            stdout_mutex.release()
    tcp_sock.close()
    udp_sock.close()
    exit_mutexes[thread_id] = True


def parent(server_ip):
    for i in range(threads_count):
        thread.start_new_thread(child, (i, server_ip,))
    while False in exit_mutexes:
        pass

threads_count = 16384

if (threads_count & threads_count - 1) != 0:
    raise AttributeError('Threads count should be power of 2')
if threads_count <= 0 or threads_count > 16384:
    raise AttributeError('Threads count should be > 0 and less than 8192')

server_ip = socket.gethostbyname('')

print("-" * 60)
print("Please wait, scanning remote host", server_ip)
print("-" * 60)

stdout_mutex = thread.allocate_lock()
exit_mutexes = [False] * threads_count

t1 = datetime.now()
parent(server_ip)

t2 = datetime.now()

total = t2 - t1

print('Scanning Completed in: ', total)
