from binascii import hexlify, unhexlify


def hex2int(data):
    return hexlify(data)


def hex2bin(data):
    return bin(int(hexlify(data), 16))[2:].zfill(16)

shit = b'\xc1\x85\x81\x80\x00\x01\x00\x02\x00\x04\x00\x04\x04docs\x06google\x03com\x00\x00\x01\x00\x01\xc0\x0c\x00\x05\x00\x01\x00\x00\x00\x0e\x00\x0e\twide-docs\x01l\xc0\x11\xc0-\x00\x01\x00\x01\x00\x00\x00i\x00\x04\xad\xc2I\xc2\xc0\x11\x00\x02\x00\x01\x00\x00\x1b.\x00\x06\x03ns3\xc0\x11\xc0\x11\x00\x02\x00\x01\x00\x00\x1b.\x00\x06\x03ns4\xc0\x11\xc0\x11\x00\x02\x00\x01\x00\x00\x1b.\x00\x06\x03ns1\xc0\x11\xc0\x11\x00\x02\x00\x01\x00\x00\x1b.\x00\x06\x03ns2\xc0\x11\xc0{\x00\x01\x00\x01\x00\x00\x1a[\x00\x04\xd8\xef \n\xc0\x8d\x00\x01\x00\x01\x00\x00\x0f\xd1\x00\x04\xd8\xef"\n\xc0W\x00\x01\x00\x01\x00\x00\x1aC\x00\x04\xd8\xef$\n\xc0i\x00\x01\x00\x01\x00\x00\x1a\xb0\x00\x04\xd8\xef&\n'


def parse(data):
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
                name += temp+'.'
                pointer += length
        return name, pointer

    id = hex2int(data[0:2])
    flags = hex2bin(data[2:4])
    qcount = hex2int(data[4:6])
    print(int(qcount))
    ancount = hex2int(data[6:8])
    nscount = hex2int(data[8:10])
    arcount = hex2int(data[10:12])
    result = [id, flags, qcount]
    name = ''
    pointer = 12
    for i in range(int(qcount)):
        name, pointer = read_name(pointer)
        result.append(name)
        qtype = data[pointer:pointer + 2]
        qclass = data[pointer + 2:pointer + 4]
        result.append(qtype)
        result.append(qclass)
        pointer += 4

    for i in range(int(ancount)):
        name, pointer = read_name(pointer)
        result.append(name)
        type = data[pointer:pointer + 2]
        r_class = data[pointer + 2:pointer + 4]
        ttl = data[pointer + 4:pointer + 8]
        rdlength = data[pointer + 8:pointer + 10]
        rdata = data[pointer + 10:pointer + 10 + int(hex2int(rdlength),16)]
        result.append([type, r_class, ttl, rdlength, rdata])
        pointer += 10 + int(hex2int(rdlength),16)

    return result

print(parse(shit))
