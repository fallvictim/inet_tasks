import struct


packet = b''

TYPE = {1:'A', 2:'NS', 5:'CNAME', 6:'SOA', 12:'PTR', 15:'MX',
        16:'TXT', 17:'RP', 18:'AFSDB', 24:'SIG', 25:'KEY', 28:'AAAA',
        29:'LOC', 33:'SRV', 35:'NAPTR', 36:'KX', 37:'CERT', 39:'DNAME',
        41:'OPT', 42:'APL', 43:'DS', 44:'SSHFP', 45:'IPSECKEY',
        46:'RRSIG', 47:'NSEC', 48:'DNSKEY', 49:'DHCID', 50:'NSEC3',
        51:'NSEC3PARAM', 52:'TLSA', 55:'HIP', 99:'SPF', 249:'TKEY',
        250:'TSIG', 251:'IXFR', 252:'AXFR', 255:'ANY', 257:'TYPE257',
        32768:'TA', 32769:'DLV'}

CLASS = {1:'IN', 2:'CS', 3:'CH', 4:'Hesiod', 254:'None', 255:'*'}

QR = {0:'QUERY', 1:'RESPONSE'}

RCODE = {0:'NOERROR', 1:'FORMERR', 2:'SERVFAIL', 3:'NXDOMAIN',
         4:'NOTIMP', 5:'REFUSED', 6:'YXDOMAIN', 7:'YXRRSET',
         8:'NXRRSET', 9:'NOTAUTH', 10:'NOTZONE'}

OPCODE = {0:'QUERY', 1:'IQUERY', 2:'STATUS', 5:'UPDATE'}


def int2bin(data, pad):
    return bin(data)[2:].zfill(pad)


def unpack_from(fmt, data, offset=0):
    return struct.unpack_from(fmt, data, offset)


def parse_flags(flags):
    qr = QR.get(int(flags[0]))
    opcode = OPCODE.get(int(flags[1:5], 2))
    aa = bool(int(flags[5]))
    tc = bool(int(flags[6]))
    rd = bool(int(flags[7]))
    ra = bool(int(flags[8]))
    z = int(flags[9:12])
    rcode = RCODE.get(int(flags[12:], 2))
    return {'qr': qr, 'opcode': opcode, 'aa': aa, 'tc': tc, 'rd': rd, 'ra': ra, 'z': z, 'rcode': rcode}


def parse_header():
    packet_id, flags, qcount, ancount, nscount, arcount = unpack_from('!HHHHHH', packet, 0)
    flags = int2bin(flags, 16)
    header = {'id': packet_id, 'qcount': qcount, 'ancount': ancount, 'nscount': nscount, 'arcount': arcount}
    header.update(parse_flags(flags))
    return {'header':header}


def read_name(offset):
    name = ''
    while True:
        marker = unpack_from('!B', packet, offset)[0]
        temp = int2bin(unpack_from('!H', packet, offset)[0], 16)
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
            fmt = '!{}s'.format(length)
            piece = unpack_from(fmt, packet, offset)[0].decode()
            name += piece + '.'
            offset += length
    return name, offset


def parse_questions(qcount, offset):
    result = {'questions': []}
    for i in range(qcount):
        name, offset = read_name(offset)
        qtype, qclass = unpack_from('!HH', packet, offset)
        offset += 4
        result.get('questions').append({'name': name, 'qtype': TYPE.get(qtype), 'qclass': CLASS.get(qclass)})
    return result, offset


def parse_rdata(type, length, offset):
    if type == 'CNAME' or type == 'NS' or type == 'PTR':
        return read_name(offset)[0]
    elif type == 'A':
        return '.'.join(str(num) for num in unpack_from('!4B', packet, offset))
    elif type == 'AAAA':
        return ':'.join('{0:04x}'.format(num) for num in unpack_from('!8H', packet, offset))
    elif type == 'MX':
        preference = unpack_from('!H', packet, offset)[0]
        exchange = read_name(offset + 1)
        return {'PREFERENCE':preference, 'EXCHANGE':exchange}
    elif type == 'SOA':
        mname, offset = read_name(offset)
        rname, offset = read_name(offset)
        serial, refresh, retry, expire, minimum = unpack_from('!HHHHH', packet, offset)
        return {'MNAME':mname, 'RNAME':rname,
                'SERIAL':serial, 'REFRESH':refresh, 'RETRY':retry, 'EXPIRE':expire, 'MINIMUM':minimum}
    elif type == 'TXT':
        return unpack_from('!{}s'.format(length), packet, offset)[0].decode()
    else:
        return unpack_from('!{}s'.format(length), packet, offset)[0]


def parse_answers(res_type, ancount, offset):
    result = {res_type: []}
    for i in range(ancount):
        name, offset = read_name(offset)
        type, r_class, ttl, rdlength = unpack_from('!HHIH', packet, offset)
        type = TYPE.get(type)
        rdata = parse_rdata(type, rdlength, offset + 10)
        offset += 10 + rdlength
        result.get(res_type).append({'name': name, 'type': type,
                                     'rclass': r_class, 'ttl': ttl, 'rdlength':rdlength, 'rdata': rdata})
    return result, offset


def parse(data):
    global packet
    packet = data
    if len(packet) < 12:
        return
    parsed = {}
    header = parse_header()
    offset = 12
    temp_header = header.get('header')
    try:
        questions, offset = parse_questions(temp_header.get('qcount'), offset)
        answers, offset = parse_answers('answers', temp_header.get('ancount'), offset)
        nses, offset = parse_answers('nss', temp_header.get('nscount'), offset)
        arrs, offset = parse_answers('arrs', temp_header.get('arcount'), offset)
        parsed.update(header)
        parsed.update(questions)
        parsed.update(answers)
        parsed.update(nses)
        parsed.update(arrs)
        return parsed
    except struct.error:
        return None
