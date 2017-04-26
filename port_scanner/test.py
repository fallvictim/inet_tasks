from scapy.all import *


packet_count = 0
def custom_action(packet):
    global packet_count
    packet_count += 1
    return "Packet #%s: %s ==> %s" % (packet_count, packet[0][1].src, packet[0][1].dst)


## Setup sniff, filtering for IP traffic
sniff(filter="icmp", prn=custom_action)
