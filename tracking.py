import re
import socket
import subprocess
import sys


def perform_whois(server, query):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server, 43))
    s.send((query + '\r\n').encode())
    msg = b''
    while True:
        chunk = s.recv(2048)
        if not chunk:
            break
        msg += chunk
    return msg.decode()


def track(domain):
    servers = ['whois.lacnic.net', 'whois.ripe.net', 'whois.arin.net',
               'whois.apnic.net', 'whois.afrinic.net']
    trace = subprocess.Popen(['tracert', '-d', domain], stdout=subprocess.PIPE)
    for i in range(0, 32):
        line = trace.stdout.readline().decode().replace('\r\n', '')
        match_stars = re.search('\*.+\*.+\*', line)
        if (i >= 4 and line == '') or match_stars is not None:
            print(line)
            break
        match_ip = re.search('\d+\.\d+\.\d+\.\d+', line)
        if match_ip is not None:
            ip = match_ip.group(0)
            for server in servers:
                whois = perform_whois(server, ip)
                match_as = re.search('AS\d+', whois)
                if match_as is not None:
                    line += ' ' + match_as.group(0) #+ ' ' + country + ' ' + mnt
                    break
        print(line)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        if sys.argv[1] == 'help' or sys.argv[1] == '/?':
            print('''
            Usage: tracking.py help|ip|domain_name
            Autonomous system tracking.
            Just print domain name or ip get the tracing of your AS.
            Simple.
            ''')
        else:
            track(sys.argv[1])
    else:
        print('Invalid input')
