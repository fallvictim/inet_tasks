from binascii import hexlify, unhexlify
import struct


packet = b'\xa2G\x81\x80\x00\x01\x00\x01\x00\x02\x00\x03\x07storage\x03mds\x06yandex\x03net\x00\x00\x01\x00\x01\xc0\x0c\x00\x01\x00\x01\x00\x00\x01\xa6\x00\x04\xd5\xb4\xcc\x9e\xc0\x14\x00\x02\x00\x01\x00\x00\r\xcb\x00\x0f\x03ns4\x06yandex\x02ru\x00\xc0\x14\x00\x02\x00\x01\x00\x00\r\xcb\x00\x06\x03ns3\xc0H\x03ns3\x06YANDEX\xc0O\x00\x01\x00\x01\x00\x00\x0f\xa8\x00\x04W\xfa\xfa\x01\xc0e\x00\x1c\x00\x01\x00\x00\x01\xd6\x00\x10*\x02\x06\xb8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x01\x03ns4\xc0i\x00\x01\x00\x01\x00\x00\x03\x16\x00\x04MX\x15\x01'


def hex2int(data):
    return int(hexlify(data), 16)


def hex2bin(data, pad):
    try:
        return bin(int(hexlify(data), 16))[2:].zfill(pad)
    except ValueError:
        print(data)


def int2bin(data, pad):
    return bin(data)[2:].zfill(pad)


def unpack(fmt, data):
    return struct.unpack(fmt, data)[0]


def unpack_from(fmt, data, offset=0):
    return struct.unpack_from(fmt, data, offset)[0]


def parse_flags(flags):
    qr = int(flags[0])
    opcode = int(flags[1:5], 2)
    aa = bool(int(flags[5]))
    tc = bool(int(flags[6]))
    rd = bool(int(flags[7]))
    ra = bool(int(flags[8]))
    z = int(flags[9:12])
    rcode = int(flags[12:], 2)
    return {'qr': qr, 'opcode': opcode, 'aa': aa, 'tc': tc, 'rd': rd, 'ra': ra, 'z': z, 'rcode': rcode}


def parse_header():
    packet_id = unpack_from('!H', packet, 0)
    flags = int2bin(unpack_from('!H', packet, 2), 16)
    qcount = unpack_from('!H', packet, 4)
    ancount = unpack_from('!H', packet, 6)
    nscount = unpack_from('!H', packet, 8)
    arcount = unpack_from('!H', packet, 10)
    result = {'id': packet_id, 'qcount': qcount, 'ancount': ancount, 'nscount': nscount, 'arcount': arcount}
    result.update(parse_flags(flags))
    return result


def read_name(offset):
    name = ''
    while True:
        marker = unpack_from('!B', packet, offset)
        temp = int2bin(unpack_from('!H', packet, offset), 16)
        if temp[0:2] == '11':
            prev_offset = int(temp[2:], 2)
            name += read_name(prev_offset)[0]
            offset += 2
            break
        else:
            length = marker
            offset += 1
            if length == 0:
                break
            fmt = '!' + '{}s'.format(length)
            piece = unpack_from(fmt, packet, offset).decode()
            name += piece + '.'
            offset += length
    return name, offset


def parse_questions(qcount, offset):
    result = {'questions': []}
    for i in range(qcount):
        name, offset = read_name(offset)
        qtype = unpack_from('!H', packet, offset)
        qclass = unpack_from('!H', packet, offset + 2)
        offset += 4
        result.get('questions').append({'name': name, 'qtype': qtype, 'qclass': qclass})
    return result, offset


def parse_answers(res_type, ancount, offset):
    result = {res_type: []}
    for i in range(ancount):
        name, offset = read_name(offset)
        type = unpack_from('!H', packet, offset)
        r_class = unpack_from('!H', packet, offset + 2)
        ttl = unpack_from('!I', packet, offset + 4)
        rdlength = unpack_from('!H', packet, offset + 8)
        #TODO parse rdata
        rdata = unpack_from('!{}s'.format(rdlength), packet, offset + 10)
        offset += 10 + rdlength
        result.get(res_type).append({'name': name, 'type': type, 'rclass': r_class, 'ttl': ttl, 'rdlength':rdlength, 'rdata': rdata})
    return result, offset


def parse():
    header = parse_header()
    offset = 12
    qcount = header.get('qcount')
    questions, offset = parse_questions(qcount, offset)
    answers, offset = parse_answers('answers', header.get('ancount'), offset)
    nses, offset = parse_answers('nss', header.get('nscount'), offset)
    arrs, offset = parse_answers('arrs', header.get('arcount'), offset)
    #TODO make updates in one expression
    header.update(questions)
    header.update(answers)
    header.update(nses)
    header.update(arrs)
    return header

print(parse())
