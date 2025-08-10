import ctypes
import os
import pprint
import socket
import struct
import time

import certifi
from OpenSSL import SSL
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, AESSIV

from app.utils.aes_siv_utils import get_encrypted_data_and_tag_AES_SIV_256, get_encrypted_data_and_tag_AES_GSM_256, \
    get_encrypted_data_and_tag_new_aessiv
from server.app.utils.domain_name_to_ip import domain_name_to_ip_list
from docs.source.conf import extensions


# measuring an NTS server has 2 steps:
# 1) Key Exchange -> get the cookies and basically the keys for a secure connection
# 2) Encrypt the NTP request with the keys and measure it.

def perform_nts_key_exchange(server: str):
    """
    This method tries to perform the Key Exchange (according to RFC8915) to this server.
    If it succeeds, then it means that this server is an NTS server.
    We perform Key Exchange on port 4460. We also use OpenSSL as it is more powerful than ssl.
    (It has export_keying_material method to get c2s and s2c keys)

    Args:
        server (str): The server that you want to check.
    Returns:
        None if it fails
    """
    nts_ke_timeout = 5
    context = SSL.Context(SSL.TLS_CLIENT_METHOD)
    context.set_verify(SSL.VERIFY_PEER, lambda conn, cert, errno, depth, ok: ok)
    context.load_verify_locations(cafile=certifi.where())
    context.set_min_proto_version(SSL.TLS1_3_VERSION)
    context.set_alpn_protos([b"ntske/1"])

    # Create TCP socket and connect
    sock = socket.create_connection((server, 4460), timeout=nts_ke_timeout)
    ssl_connection = SSL.Connection(context, sock)
    ssl_connection.set_connect_state()
    ssl_connection.set_tlsext_host_name(server.encode())

    # handshake (we need this "while" because it may not start immediately)
    while True:
        try:
            ssl_connection.do_handshake()
            break
        except (SSL.WantReadError, SSL.WantWriteError):
            continue
    proto = ssl_connection.get_alpn_proto_negotiated()
    if proto != b"ntske/1":
        print("NTS-KE ALPN failed")
        return None

    result = {
        "aead": None,
        "cookies": [],
        "alternative_server": None,
        "alternative_port": None,
    }
    # prepare the request for Key Exchange.
    # aead_ids = [15, 16]  # ordered by preference
    # body = b"".join(struct.pack(">H", aead_id) for aead_id in aead_ids)
    # record_aead = build_nts_ke_record(4, False, body)
    records = b"".join([
        build_nts_ke_record(1, True, struct.pack(">H", 0)),  # Protocol Negotiation, NTP=0
        #record_aead,
        build_nts_ke_record(4, False, struct.pack(">H", 15)),  # AEAD algorithm list, AES-SIV-CMAC-256 (0x000f)
        build_nts_ke_record(0, True, b"")  # End of Message
    ])

    ssl_connection.send(records)

    data = b""
    while True:
        try:
            chunk = ssl_connection.recv(4096)
            if not chunk:
                # Peer closed cleanly (empty read)
                break
            data += chunk
        except (SSL.ZeroReturnError, socket.timeout):
            # Clean SSL/TLS closure or Nothing else is coming
            break
        except (SSL.WantReadError, SSL.WantWriteError):
            # Try again
            continue

    # --- Parse response ---
    print("data is: ", data)
    print(result)
    offset = 0 # iterate with this offset
    # see each record
    while offset + 4 <= len(data):
        type_field, body_len = struct.unpack(">HH", data[offset:offset + 4])
        offset += 4
        body = data[offset:offset + body_len] # the body of the record
        offset += body_len
        type_id = type_field & 0x7FFF  # ignore critical bit

        # take the data from this record
        result = handle_record(type_id, body, result)

    # get the client to server and server to client keys
    label = b"EXPORTER-network-time-security"
    result["c2s_key"] = ssl_connection.export_keying_material(label, 32, b'\x00')
    result["s2c_key"] = ssl_connection.export_keying_material(label, 32, b'\x01')
    ssl_connection.shutdown()
    ssl_connection.close()
    sock.close()
    return result

def build_nts_ke_record(type_id: int, critical_bit_status: bool, body):
    """
    This method creates an NTS key exchange record with the specified type,
    body and the critical bit status. Used in Key Exchange part.
    """
    type_field = (1 << 15) | type_id if critical_bit_status else type_id
    # ">H" means big endian and ">HH" is also big endian, but you input 2 numbers
    return struct.pack(">HH", type_field, len(body)) + body

def handle_record(type_id, body, current_result):
    """
    Handle this record and add it to the result data. (We collect the data from this record)

    Args:
        type_id (int): The type of the record.
        body (bytes): The body of the record.
        current_result (dict): The current result, which we will update.

    Returns:
        dict: The updated result for Key Exchange.
    """
    # see table 4 from RFC8915 for more info
    body_length = len(body)
    if type_id == 4 and body_length >= 2:  # AEAD
        current_result["aead"] = struct.unpack(">H", body[:2])[0]
    elif type_id == 5:  # new Cookies
        current_result["cookies"].append(body)
    elif type_id == 6:  # Alternative Server
        current_result["alternative_server"] = body.decode(errors="ignore")
    elif type_id == 7 and body_length >= 2:  # NTPv4 Port Negotiation
        current_result["alternative_port"] = struct.unpack(">H", body[:2])[0]
    return current_result

def pad4(data: bytes) -> bytes:
    return data + b'\x00' * ((4 - len(data) % 4) % 4)
NTP_DELTA  = 2208988800

def to_ntp_ts(t: float) -> bytes:
    ntp = t + NTP_DELTA
    sec  = int(ntp)
    frac = int((ntp - sec) * (1<<32))
    return struct.pack("!II", sec, frac),sec,frac

def padded_len(length: int) -> int:
    return (length + 3) & ~3

def write_ext_uid(uid):
    total_len = 4 + len(uid)
    data = bytes([])
    data += struct.pack('!HH', 0x0104, total_len)
    data += uid
    print(f"len uid ext: {len(data)}")
    return data
def construct_nonce(ntp_seconds, ntp_fraction):
    # Pack seconds and fraction as big endian 4-byte each
    ts_bytes = struct.pack('!II', ntp_seconds, ntp_fraction)
    # Append 4 zero bytes
    nonce = ts_bytes + b'\x00' * 4
    return nonce
def write_all_cookies(cookies):
    data = b''
    i=0
    for cookie in cookies:
        data += write_ext_cookie(cookie)
        i+=1
        #if i==2:
        return data
    return data
def write_ext_cookie(cookie):
    cookie_padded_len = padded_len(len(cookie))
    total_len = 4 + cookie_padded_len
    data = bytes([])
    data += struct.pack('!HH', 0x0204, total_len)
    data += cookie
    data += (b'\x00' * (cookie_padded_len - len(cookie)))
    print(f"len cookie ext: {len(data)}")
    return data

def write_ext_cookie_placeholder(placeholder):
    total_len = 4 + len(placeholder)
    data = bytes([])
    data += struct.pack('!HH', 0x0304, total_len)
    data += placeholder
    print(f"len placeholder ext: {len(data)}")

    return data

def write_ext_aead(nonce, ciphertext):
    padded_nonce_len = padded_len(len(nonce))
    print("padded nonce length", padded_nonce_len)
    padded_ciphertext_len = padded_len(len(ciphertext))

    total_len = 4 + 4 + padded_nonce_len + padded_ciphertext_len
    data = bytes([])
    data += struct.pack('!HH', 0x0404, total_len)
    data += struct.pack('!HH', len(nonce), len(ciphertext))
    data += nonce
    data += (b'\x00' * (padded_nonce_len - len(nonce)))
    data += ciphertext
    data += (b'\x00' * (padded_ciphertext_len - len(ciphertext)))
    print(f"len aead ext: {len(data)}")
    return data


def to_ntp_header(t1: float) -> bytes:
    """Build a minimal NTP mode‑3 header with Originate Timestamp = t1."""
    ntp_ts = t1 + NTP_DELTA
    sec, frac = int(ntp_ts), int((ntp_ts - int(ntp_ts)) * (1<<32))
    hdr = bytearray(48)
    hdr[0] = (0 << 6) | (4 << 3) | 3  # LI=0, VN=4, Mode=3
    hdr[40:48] = struct.pack('!II', sec, frac)
    return bytes(hdr)

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from cryptography.hazmat.primitives.ciphers.aead import AESSIV
def build_nts_measuring_request(keys):
    # header part
    t1 = time.time()
    header = bytearray(48)
    header[0] = (0 << 6) | (4 << 3) | 3
    # header[2] = 6
    header[3] = 0x20
    timpBytes,sec,frac=to_ntp_ts(t1)
    header[40:48] = timpBytes #to_ntp_ts(t1)  # timestamp
    # header[40:48] = to_ntp_ts(t1)
    # query = bytes(header)
    extensions = bytes([])
    extensions_array = [bytes(header)]
    # print(len(extensions))
    # header = to_ntp_header(t1)

    # uid
    unique_id = os.urandom(32)
    a = write_ext_uid(unique_id)
    print("uid ext")
    hexdump(a)
    extensions += a
    extensions_array.append(a)
    print(len(extensions))

    # cookie
    for c in keys['cookies']:
        print(f"cookie len {len(c)}")
    #     hexdump(c)
    cookie = keys['cookies'][2]
    # print("cookie len", len(cookie))
    a = write_ext_cookie(cookie)
    # a = write_all_cookies(keys['cookies'])
    # print(cookie)
    print("cookie ext")

    hexdump(a)
    extensions += a
    extensions_array.append(a)
    print(len(extensions))
    # cookie placeholder
    ph_count = 0
    if ph_count > 0:
        cookie = b''#!!!!!
        placeholder_len = padded_len(len(cookie))
        # placeholder = bytes(placeholder_len)
        placeholder = os.urandom(placeholder_len)
        for _ in range(ph_count):
            extensions += write_ext_cookie_placeholder(placeholder)#!!!ex array
            print(len(extensions))
    # aead
    # associated_data = bytes(header) + extensions
    # plaintext = extensions
    associated_data = bytes(header) + extensions
    #plaintext = b''
    dummy_ef = struct.pack(">HH", 0x0000, 4)
    plaintext = b''#associated_data
    nonce = os.urandom(16)
    # nonce = construct_nonce(sec,frac)

    # aead = aes_siv.AES_SIV()

    # nonce = os.urandom(16) # it is good.!!!!

    # aead.
    # cipher = AES.new(keys['c2s_key'], AES.MODE_SIV, nonce=nonce)
    # cipher.update(associated_data)
    # ciphertext, tag = cipher.encrypt_and_digest(plaintext)

    # aead 2
    # aessiv = AESSIV(keys['c2s_key'])
    enc, tag = get_encrypted_data_and_tag_new_aessiv(keys['c2s_key'], plaintext, associated_data, nonce)
    # enc, tag = get_encrypted_data_and_tag_AES_GSM_256(keys['c2s_key'], plaintext, associated_data, nonce)
    # ciphertext  = aessiv.encrypt(plaintext, [associated_data, nonce])
    # ciphertext=ciphertext[:16]
    nonce_len = len(nonce)
    ct_len = len(enc+tag)
    print("ct len", ct_len)
    print("nonce len", nonce_len)

    nonce_p = pad4(nonce)
    ct_p = pad4(enc+tag)
    print("ct_p ", ct_p)
    hexdump(ct_p)
    print("/////")
    body = struct.pack(">HH", nonce_len, ct_len) + nonce_p + ct_p
    nts_auth_ef = make_ef(0x0404, body)
    # nts_auth_field_type = 0x0404
    # nts_auth_field = struct.pack(">HH", nts_auth_field_type, len(raw) + 4) + raw

    # nonce = raw[:16]  # synthetic IV
    # ciphertext = raw[16:]
    # a = write_ext_aead(nonce, ciphertext)
    # print("aead ext")
    # hexdump(a)
    # aead_ext = a
    print("aead req size", len(nts_auth_ef))
    hexdump(nts_auth_ef)
    query = bytes(header) + extensions + nts_auth_ef
    # query = bytes(header) + extensions + nts_auth_field
    print("total len query:", len(query))
    print("==== OUTGOING UDP REQUEST ====")
    print("total len query:", len(query))
    hexdump(query)
    # also show the AEAD EF internal lengths you already print:
    print("AEAD nonce_len:", nonce_len, "ciphertext_len:", ct_len)
    # print_nts_raw(query)

    return query, t1
def make_ef(field_type: int, body: bytes) -> bytes:
    return struct.pack(">HH", field_type, len(body) + 4) + body
def pad4_2(b: bytes) -> bytes:
    pad = (-len(b)) % 4
    return b + (b'\x00' * pad)
def parse_aead_extension(data: bytes) -> (bytes, bytes, bytes):
    """
    Parse an AEAD extension field from NTS measurement request/response.
    Returns (nonce, ciphertext, associated_data) components.

    Args:
        data: full UDP payload starting at the 48-byte NTP header + extensions.

    Raises:
        ValueError if extension not found or malformed.
    """
    # Skip NTP header (48 bytes) and any preceding extensions
    offset = 48
    while offset + 4 <= len(data):
        t, length = struct.unpack_from('!HH', data, offset)
        print(f"t is{t}")
        if t == 0x0404:
            # AEAD extension found
            ext_start = offset
            # Unpack nonce and ciphertext lengths
            nonce_len, ct_len = struct.unpack_from('!HH', data, offset + 4)
            # Calculate padded lengths
            def padded(x): return (x + 3) & ~3
            n_pad = padded(nonce_len)
            ct_pad = padded(ct_len)
            # Extract
            nonce = data[offset+8 : offset+8+nonce_len]
            ciphertext = data[offset+8+n_pad : offset+8+n_pad+ct_len]
            #print("aead found")
            return nonce, ciphertext, data[:offset]  # AAD = header + prev extensions
        offset += length
    raise ValueError("AEAD extension not found")
def decrypt_aead_ext(key: bytes, data: bytes) -> bytes:
    """
    Attempt to decrypt and authenticate the AEAD extension field in-place.

    Args:
        key: 32-byte AEAD key (c2s or s2c)
        data: full UDP payload including NTP header + extensions + AEAD ext

    Returns:
        The plaintext (the original extensions) on success, or raises an exception.
    """
    print("this we decrypt")
    hexdump(data)
    nonce, ciphertext, aad = parse_aead_extension(data)
    # For AES-SIV, ciphertext already includes the SIV tag at front or end?
    # In RFC8915, payload = ciphertext || tag, but AESSIV.encrypt returns tag||ciphertext.
    # So we reassemble raw = tag||ciphertext for decrypt
    # If your write_ext_aead stored ciphertext||tag, swap here:
    # raw = tag + ciphertext
    raw = ciphertext  # if you passed raw=tag||ct as ciphertext
    aessiv = AESSIV(key)
    # decrypt returns plaintext
    print("until here is ok")
    plaintext = aessiv.decrypt(raw, [aad])
    print("until here is ok2")
    return plaintext
def alloc_aligned(size, align=8):
    buf = bytearray(size + align)
    addr = ctypes.addressof(ctypes.c_char.from_buffer(buf))
    offset = (align - (addr % align)) % align
    aligned_buf = memoryview(buf)[offset:offset + size]
    return bytes(aligned_buf)  # Convert to immutable bytes if needed

def encrypt_aead(key, aad, plaintext):
    cipher = AES.new(key, AES.MODE_SIV)
    cipher.update(aad)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return ciphertext, tag
def measure_nts_server(server):
    # server="time.cloudflare.com"
    kee = perform_nts_key_exchange(server)
    for i, c in enumerate(kee['cookies']):
        print(f"KE cookie[{i}] len={len(c)}")
        hexdump(c)
    print("c2s_key len:", len(kee['c2s_key']), "s2c_key len:", len(kee['s2c_key']))

    # print("c2s key length: ",len(kee['c2s_key']))
    # print("first cookie length: ",len(kee['cookies'][0]))

    pprint.pprint(kee)
    if kee['alternative_server'] is None:
        kee['alternative_server']=server
    if kee['alternative_port'] is None:
        kee['alternative_port']=123

    packet, t1 = build_nts_measuring_request(kee)
    try:
        print("daaa", kee['c2s_key'])
        ext_plain = decrypt_aead_ext(kee['c2s_key'], packet)
        print("AEAD ext decrypted successfully; original extensions:", ext_plain)
    except Exception as e:
        print("Decryption/authentication failed:", e)
    print(f"query length: {len(packet)}")
    resp= send_nts(packet, kee['alternative_server'], kee['alternative_port'])
    print("==== INCOMING UDP RESPONSE ====")
    print("resp len:", len(resp))
    hexdump(resp)
    hdr = resp[:48]
    print("resp stratum:", hdr[1], "refid:", hdr[12:16])
    t4 =time.time()
    if not resp:
        print("No response -> timeout", server)
        raise Exception("No response -> timeout")
    print(f"Response length: {len(resp)}")
    hexdump(resp)
    parse_responsee(resp, kee)
    # measurement = parse_nts_response(resp, server, kee['s2c_key'], t1, t4)
    # print_ntp_measurement(measurement)
    print("ok")

def send_nts(req, host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # some basic logic to get an IP (demo code)
    sock.settimeout(5)
    print(f"Sending request of length {len(req)}")
    host = domain_name_to_ip_list(host,None,4)[0]
    print(host)
    sock.sendto(req, (host, port))
    try:
        resp, _ = sock.recvfrom(2048)
        return resp
    except Exception as e:
        print(e)
        return None
    finally:
        sock.close()

def print_nts_raw(data: bytes):
    print("header")
    hexdump(data)
    # for i in range(0, 48, 4):
    #     print(data[i:i+4]," ")

def hexdump(data: bytes, width: int = 16, group: int = 4) -> None:
    """
    Print bytes in a hex dump style, with 'width' bytes per line,
    grouped into 'group'-byte clusters separated by double spaces.

    Example output for width=16, group=4:
    aa bb cc dd  ee ff 00 11  22 33 44 55  66 77 88 99
    ...
    """
    # data = b'#\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xec)\xf5\x18\xebC\xd0\x00'
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("data must be bytes or bytearray")

    for offset in range(0, len(data), width):
        line_bytes = data[offset : offset + width]
        # split into groups
        groups = [
            line_bytes[i : i + group]
            for i in range(0, len(line_bytes), group)
        ]
        # format each group as hex, then join with double spaces
        hex_groups = []
        for g in groups:
            hex_groups.append(' '.join(f"{b:02x}" for b in g))
        print('  '.join(hex_groups))
def parse_responsee(data: bytes, kee, t1: float=2, t4: float=3) -> dict:
        # unwrap NTP header
        if len(data) < 48:
            raise RuntimeError("Response too short")
        header = data[:48]
        cur = data[48:]

        # variables
        unique_id = None
        new_cookies = []

        # first, detect crypto-NAK
        stratum = header[1]
        if stratum == 0:
            kiss = struct.unpack('!I', header[12:16])[0]
            if kiss == 0x4e54534e:
                print("is NTSN")
        if len(data) == 84:
                raise RuntimeError("NTS response too short")
        print(f"stratum: {stratum}")
measure_nts_server("time.cloudflare.com")
# measure_nts_server("ntppool1.time.nl")

def perform_nts_measurement(server):
    keys = perform_nts_key_exchange(server)
    if keys['alternative_server'] is None:
        keys['alternative_server']=server
    if keys['alternative_port'] is None:
        keys['alternative_port']=123

    request = build_nts_measuring_request(keys)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    # get IP address
    server_ip = domain_name_to_ip_list(server,None,4)[0]
    sock.sendto(request, (server_ip, keys['alternative_port']))
    try:
        resp, _ = sock.recvfrom(2048)
        return resp, time.time()
    finally:
        sock.close()


# a list of known NTS servers according to https://github.com/jauderho/nts-servers
nts_servers=[
         "time.cloudflare.com",
"1.ntp.ubuntu.com",
"2.ntp.ubuntu.com",
"3.ntp.ubuntu.com",
"4.ntp.ubuntu.com",
"nts.teambelgium.net",
"a.st1.ntp.br",
"b.st1.ntp.br", # except this one which is strange. (Might not be a valid NTS)
"c.st1.ntp.br",
"d.st1.ntp.br",
"gps.ntp.br",
"brazil.time.system76.com",
"time.bolha.one",
"time.web-clock.ca",
"ntp.miuku.net",
"paris.time.system76.com",
"ntp3.fau.de",
"ntp3.ipv6.fau.de",
"ptbtime1.ptb.de",
"ptbtime2.ptb.de",
"ptbtime3.ptb.de",
"ptbtime4.ptb.de",
"www.jabber-germany.de",
"www.masters-of-cloud.de",
"ntp.nanosrvr.cloud",
"ntppool1.time.nl",
"ntppool2.time.nl",
"ntpmon.dcs1.biz",
"nts.netnod.se",
"gbg1.nts.netnod.se",
"gbg2.nts.netnod.se",
"lul1.nts.netnod.se",
"lul2.nts.netnod.se",
"mmo1.nts.netnod.se",
"mmo2.nts.netnod.se",
"sth1.nts.netnod.se",
"sth2.nts.netnod.se",
"svl1.nts.netnod.se",
"svl2.nts.netnod.se",
"ntp.3eck.net",
"ntp.trifence.ch",
"ntp.zeitgitter.net",
"ntp01.maillink.ch",
"ntp02.maillink.ch",
"ntp03.maillink.ch",
"time.signorini.ch",
"ntp2.glypnod.com",
"ntp1.dmz.terryburton.co.uk",
"ntp2.dmz.terryburton.co.uk",
"ntp1.glypnod.com",
"ohio.time.system76.com",
"oregon.time.system76.com",
"virginia.time.system76.com",
"stratum1.time.cifelli.xyz",
"time.cifelli.xyz",
"time.txryan.com",
"ntp.viarouge.net",
"time.xargs.org"]
