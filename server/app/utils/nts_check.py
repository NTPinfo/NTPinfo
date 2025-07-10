import os
import socket
import struct
import time

import certifi
from OpenSSL import SSL

from app.utils.domain_name_to_ip import domain_name_to_ip_list


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
    records = b"".join([
        build_nts_ke_record(1, True, struct.pack(">H", 0)),  # Protocol Negotiation, NTP=0
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

def build_nts_measuring_request(keys):
    # header part
    t1 = time.time()
    header = bytearray(48)
    header[0] = (0<<6)|(4<<3)|3
    # header[40:48] = to_ntp_ts(t1)
    header = bytes(header)

    # cookie and uid fields
    cookie = keys['cookies'][0]
    uid_field = pad4(struct.pack("!HH", 0x0104, 36) + os.urandom(32))
    cookie_field = pad4(struct.pack("!HH", 0x0204, len(cookie) + 4) + cookie)
    extension_fields = uid_field + cookie_field

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
