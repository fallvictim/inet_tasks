import struct
from dns import dns_parser, cache

parsed = {'arrs': [{'rdata': '87.250.250.1', 'name': 'ns3.YANDEX.ru.', 'ttl': 4008, 'rdlength': 4, 'rclass': 1, 'type': 'A'}, {'rdata': '2a02:06b8:0000:0000:0000:0000:0000:1001', 'name': 'ns3.YANDEX.ru.', 'ttl': 470, 'rdlength': 16, 'rclass': 1, 'type': 'AAAA'}, {'rdata': '77.88.21.1', 'name': 'ns4.YANDEX.ru.', 'ttl': 790, 'rdlength': 4, 'rclass': 1, 'type': 'A'}], 'nss': [{'rdata': 'ns4.yandex.ru.', 'name': 'mds.yandex.net.', 'ttl': 3531, 'rdlength': 15, 'rclass': 1, 'type': 'NS'}, {'rdata': 'ns3.yandex.ru.', 'name': 'mds.yandex.net.', 'ttl': 3531, 'rdlength': 6, 'rclass': 1, 'type': 'NS'}], 'questions': [{'qtype': 'A', 'qclass': 'IN', 'name': 'storage.mds.yandex.net.'}], 'header': {'arcount': 3, 'aa': False, 'opcode': 'QUERY', 'z': 0, 'id': 41543, 'nscount': 2, 'qr': 'RESPONSE', 'qcount': 1, 'rd': True, 'tc': False, 'ancount': 1, 'ra': True, 'rcode': 'NOERROR'}, 'answers': [{'rdata': '213.180.204.158', 'name': 'storage.mds.yandex.net.', 'ttl': 422, 'rdlength': 4, 'rclass': 1, 'type': 'A'}]}

TYPE = {'NSEC3': 50, 'LOC': 29, 'TYPE257': 257, 'TSIG': 250, 'IPSECKEY': 45,
        'CNAME': 5, 'KEY': 25, 'CERT': 37, 'DLV': 32769, 'NS': 2, 'RP': 17,
        'TLSA': 52, 'ANY': 255, 'DS': 43, 'AFSDB': 18, 'A': 1, 'KX': 36,
        'TA': 32768, 'APL': 42, 'NAPTR': 35, 'SIG': 24, 'RRSIG': 46, 'HIP': 55,
        'NSEC': 47, 'SRV': 33, 'OPT': 41, 'PTR': 12, 'SPF': 99, 'SSHFP': 44,
        'NSEC3PARAM': 51, 'TXT': 16, 'AAAA': 28, 'IXFR': 251, 'DNAME': 39,
        'AXFR': 252, 'SOA': 6, 'DNSKEY': 48, 'TKEY': 249, 'MX': 15, 'DHCID': 49}

CLASS = {'None': 254, 'IN': 1, 'Hesiod': 4, 'CH': 3, 'CS': 2, '*': 255}

QR = {'QUERY': 0, 'RESPONSE': 1}

RCODE = {'NXDOMAIN': 3, 'YXRRSET': 7, 'FORMERR': 1, 'REFUSED': 5,
         'SERVFAIL': 2, 'NOTZONE': 10, 'NOTIMP': 4, 'NXRRSET': 8,
         'NOTAUTH': 9, 'NOERROR': 0, 'YXDOMAIN': 6}

OPCODE = {'QUERY': 0, 'IQUERY': 1, 'UPDATE': 5, 'STATUS': 2}

domain_names = []


def int2bin(data, pad):
    return bin(data)[2:].zfill(pad)


def create_flags(query):
    qr = '1'
    opcode = int2bin(OPCODE.get(query.get('opcode')), 4)
    aa = '0'
    tc = '0'
    rd = str(int(query.get('rd')))
    ra = '1'
    z = '000'
    rcode = '0000'
    return int(qr + opcode + aa + tc + rd + ra + z + rcode, 2)


def create_header(query_header, ancount, nscount, arcount):
    id = query_header.get('id')
    flags = create_flags(query_header)
    qcount = query_header.get('qcount')
    return struct.pack('!HHHHHH', id,flags,qcount,ancount,nscount,arcount)


def pack_name(name, offset):
    orig_name = name
    res = b''
    name = orig_name
    saved = False
    temp_offset = 0
    for word in name.split('.'):
        flag = False
        for dn in domain_names:
            if dn[0].endswith(name) and name != '':
                res += struct.pack('!H', int('11' + int2bin(dn[1] + dn[0].index(name), 14), 2))
                flag = True
                offset += 2
                break
        if flag:
            break
        if not saved and offset <= 16383:
            temp_offset = offset
            saved = True
        res += struct.pack('!B{}s'.format(len(word)), len(word), word.encode())
        name = name[len(word) + 1:]
        offset += len(word) + 1
    if saved:
        domain_names.append((orig_name, temp_offset))
    return res, offset


def create_questions(questions):
    offset = 12
    res = b''
    for q in questions:
        name = q.get('name')
        temp, offset = pack_name(name, offset)
        res += temp
        qtype, qclass = TYPE.get(q.get('qtype')), CLASS.get(q.get('qclass'))
        res += struct.pack('!HH', qtype, qclass)
        offset += 4
    return res, offset


def create_rdata(type, data, length, offset):
    if type == 'CNAME' or type == 'NS' or type == 'PTR':
        return pack_name(data, offset)[0]
    elif type == 'A':
        return struct.pack('!4B', *[int(x) for x in data.split('.')])
    elif type == 'AAAA':
        return struct.pack('!8H', *[int(x, 16) for x in data.split(':')])
    elif type == 'MX':
        preference = struct.pack('!H', data.get('PREFERENCE'))
        exchange = pack_name(data.get('EXCHANGE'), offset + 1)[0]
        return preference + exchange
    elif type == 'SOA':
        mname, offset = pack_name(data.get('MNAME'), offset)
        rname, offset = pack_name(data.get('RNAME'),  offset)
        other = struct.pack('!HHHHH', data.get('SERIAL', data.get('REFRESH'),
                                       data.get('RETRY'), data.get('EXPIRE'), data.get('MINIMUM')))
        return mname + rname + other
    elif type == 'TXT':
        return struct.pack('!{}s'.format(length), data.encode())
    else:
        return struct.pack('!{}s'.format(length), data)


def create_answers(answers, offset):
    res = b''
    for answer in answers:
        name = answer.get('name')
        temp, offset = pack_name(name, offset)
        res += temp
        type = TYPE.get(answer.get('type'))
        r_class = answer.get('rclass')
        ttl = answer.get('ttl')
        rdlength = answer.get('rdlength')
        offset += 10
        rdata = create_rdata(answer.get('type'), answer.get('rdata'), rdlength, offset)
        res += struct.pack('!HHIH', type, r_class, ttl, rdlength) + rdata
        offset += rdlength
    return res, offset


def create(query, response):
    header = create_header(query.get('header'), len(response.get('answers')),
                           len(response.get('nss')), len(response.get('arrs')))
    questions, offset = create_questions(query.get('questions'))
    answers, offset = create_answers((response.get('answers')), offset)
    nss, offset = create_answers((response.get('nss')), offset)
    arrs, offset = create_answers((response.get('arrs')), offset)
    return header + questions + answers + nss + arrs
