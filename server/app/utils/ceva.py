import pprint
import socket, time, struct, os

import ntplib
from cryptography.hazmat.primitives.ciphers.aead import AESSIV
import certifi
from OpenSSL import SSL

from app.utils.domain_name_to_ip import domain_name_to_ip_list
from app.utils.perform_measurements import convert_ntp_response_to_measurement, print_ntp_measurement, \
    perform_ntp_measurement_domain_name_list

NTP_DELTA  = 2208988800

def nts_ke_record2(type_id, critical, body=b""):
    type_field = (1 << 15) | type_id if critical else type_id
    # ">H" means big endian and ">HH" is also big endian, but you input 2 numbers
    return struct.pack(">HH", type_field, len(body)) + body

def parse_nts_kee_openSSL(host, timeout=5):
    # perform key exchange and get the "keys"
    context = SSL.Context(SSL.TLS_CLIENT_METHOD)
    context.set_verify(SSL.VERIFY_PEER, lambda conn, cert, errno, depth, ok: ok)
    context.load_verify_locations(cafile=certifi.where())
    context.set_min_proto_version(SSL.TLS1_3_VERSION)
    context.set_alpn_protos([b"ntske/1"])

    # Create TCP socket and connect
    sock = socket.create_connection((host, 4460), timeout=timeout)
    conn = SSL.Connection(context, sock)
    conn.set_connect_state() # important
    conn.set_tlsext_host_name(host.encode())

    # handshake
    while True:
        try:
            conn.do_handshake()
            break
        except SSL.WantReadError:
            continue
        except SSL.WantWriteError:
            continue


    proto = conn.get_alpn_proto_negotiated()
    if proto != b"ntske/1":
        raise Exception("ntske/1 ALPN failed")


    result = {
        "aead": None,
        "cookies": [],
        "alternate_server": None,
        "alternate_port": None,
        "socket": None,
    }
    records = b"".join([
        nts_ke_record2(1, True, struct.pack(">H", 0)),     # Protocol Negotiation, critical, NTP=0
        nts_ke_record2(4, False, struct.pack(">H", 15)),   # AEAD algorithm list, AES-SIV-CMAC-256 (0x000f)
        nts_ke_record2(0, True, b"")
    ])
    conn.send(records)

    data = b""
    while True:
        try:
            chunk = conn.recv(4096)
            if not chunk:
                # Peer closed cleanly (empty read)
                break
            data += chunk
        except SSL.ZeroReturnError:
            # Clean SSL/TLS closure
            break
        except (SSL.WantReadError, SSL.WantWriteError):
            # Try again
            continue
        except socket.timeout:
            # Nothing else coming
            break

    # --- Parse response ---
    # print("data is: ", data)
    offset = 0
    # see each record
    while offset + 4 <= len(data):
        type_field, body_len = struct.unpack(">HH", data[offset:offset+4])
        offset += 4
        body = data[offset:offset+body_len]
        offset += body_len

        # critical_bit = bool(type_field & 0x8000)
        type_id = type_field & 0x7FFF # ignore the critical bit

        if type_id == 4 and body_len >= 2:  # AEAD
            result["aead"] = struct.unpack(">H", body[:2])[0]
        elif type_id == 5:  # new Cookie
            result["cookies"].append(body)
        elif type_id == 6:  # Alternate Server
            result["alternate_server"] = body.decode(errors="ignore")
        elif type_id == 7 and body_len >= 2:  # Alternate Port
            result["alternate_port"] = struct.unpack(">H", body[:2])[0]
    label = b"EXPORTER-network-time-security"
    result["c2s_key"] = conn.export_keying_material(label, 64,
                                b"\x00\x00" + struct.pack("!H", result["aead"]) + b"\x00")
    result["s2c_key"] = conn.export_keying_material(label, 64,
                                b"\x00\x00" + struct.pack("!H", result["aead"]) + b"\x01")
    # result["c2s_key"] = conn.export_keying_material(label, 64,  b'\x00')
    # result["s2c_key"] = conn.export_keying_material(label, 64, b'\x01')
    print("c2s_key:", result["c2s_key"].hex())
    print("s2c_key:", result["s2c_key"].hex())
    conn.shutdown()
    conn.close()
    sock.close()
    return result


def to_ntp_ts(t: float) -> bytes:
    ntp = t + NTP_DELTA
    sec  = int(ntp)
    frac = int((ntp - sec) * (1<<32))
    return struct.pack("!II", sec, frac)

def pad4(data: bytes) -> bytes:
    return data + b'\x00' * ((4 - len(data) % 4) % 4)
#
# from cryptography.hazmat.primitives.ciphers.aead import AESSIV
def build_nts_request2(kee):

    # header part
    t1 = time.time()
    header = bytearray(48)
    header[0] = (0<<6)|(4<<3)|3
    header[40:48] = to_ntp_ts(t1) # timestamp
    header = bytes(header)

    # single cookie
    cookie = kee['cookies'][0]
    uid_ef = pad4(struct.pack("!HH", 0x0104, 32+4) + os.urandom(32))
    cookie_ef = pad4(struct.pack("!HH", 0x0204, len(cookie)+4) + cookie)
    # I found out this placeholder is not useful (here)
    #ph_ef = pad4(struct.pack("!HH", 0x0304, len(cookie)+4) + b'\x00'*len(cookie))

    fields = uid_ef + cookie_ef

    # Authenticator extension field (ef)
    aes = AESSIV(kee['c2s_key'])
    ct = aes.encrypt(fields, [header])
    aef_body = pad4(struct.pack("!HH", 0, len(ct)) + ct) # with padding
    aef = pad4(struct.pack("!HH", 0x0404, len(aef_body) + 4) + aef_body) # with padding

    print(len(cookie))
    print(f"[+] Total packet size: {len(header + fields + aef)}")
    print(f"    UID EF length: {len(uid_ef)}")
    print(f"    Cookie EF length: {len(cookie_ef)}")
    # print(f"    Placeholder EF length: {len(ph_ef)}")
    print(f"    AEAD EF (body) length: {len(aef_body)}")
    print(f"    AEAD EF (total) length: {len(aef)}")
    return header + fields + aef, t1
def build_nts_request(kee):
    # header part
    t1 = time.time()
    header = bytearray(48)
    header[0] = (0<<6)|(4<<3)|3
    header[40:48] = to_ntp_ts(t1) # timestamp
    header = bytes(header)

    # single cookie
    cookie = kee['cookies'][0]
    uid = os.urandom(32)
    # uid_ef = pad4(struct.pack("!HH", 0x0104, len(uid)) + uid)
    # uid_ef = pad4(struct.pack("!HH", 0x0104, len(uid)) + uid)
    uid_ef = struct.pack("!HH", 0x0104, len(uid)) + pad4(uid)
    # cookie_ef = pad4(struct.pack("!HH", 0x0204, len(cookie)) + cookie)
    cookie_ef = struct.pack("!HH", 0x0204, len(cookie)) + pad4(cookie)
    # ph_body = b"\x00" * len(cookie)
    # ph_ef = pad4(struct.pack("!HH", 0x0304, len(ph_body)) + ph_body)
    fields = header + uid_ef + cookie_ef# + ph_ef

    # Authenticator extension field (ef)
    print("Header:", header.hex())
    print("Header length:", len(header))
    aes = AESSIV(kee['c2s_key'])
    ciphertext_and_tag = aes.encrypt(fields, [header])

    # aead_body_raw = ciphertext_and_tag
    # aead_body_padded = pad4(aead_body_raw)
    # aead_ef = struct.pack("!HH", 0x0404, len(ciphertext_and_tag)) + aead_body_padded
    # aead_ef = pad4(struct.pack("!HH", 0x0404, len(ciphertext_and_tag)) + aead_body_padded)
    # aead_ef = struct.pack("!HH", 0x0404, len(ciphertext_and_tag)) + pad4(ciphertext_and_tag)
    aead_ef = struct.pack("!HH", 0x0404, len(ciphertext_and_tag)) + pad4(ciphertext_and_tag)

    packet = header + fields + aead_ef

    print("C2S key length:", len(kee['c2s_key']))  # should be 64
    print(len(cookie))
    print("UID EF:", len(uid_ef))  # should be 36
    print("Cookie EF:", len(cookie_ef))  # should be 100
    # print("PH EF:", len(ph_ef))  # should be 100
    print("Fields total:", len(fields))  # should be 236
    print("Ciphertext+tag:", len(ciphertext_and_tag))  # e.g., 252
    # print("AEAD body padded:", len(aead_body_padded))  # multiple of 4
    print("AEAD EF total:", len(aead_ef))
    print("Final packet:", len(packet))

    print("Associated data (header):", header.hex())
    print("Packet starts with:      ", packet[:48].hex())
    print("Cookie from server:", kee["cookies"][0].hex())
    print("Cookie in EF:      ", cookie.hex())
    print("UID:        ", uid.hex())
    print("UID EF body:", uid_ef[4:].hex())

    return packet, t1

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
        return resp, time.time()
    finally:
        sock.close()

def parse_nts_response(data: bytes, server, s2c_key: bytes, t1: float, t4: float):
    # decode it like in ntplib
    # if len(data) < 48:
    #     raise RuntimeError(f"Response too short ({len(data)} bytes): {data.hex()}")
    # if len(data) > 48:
    #     print("this server is good",server)
    print(f"verified {server}: {verify_nts_response(data, s2c_key)}")
    try:
        unpacked = struct.unpack(
            "!B B B b 11I",
            data[0:struct.calcsize("!B B B b 11I")]
        )
    except struct.error:
        raise Exception("Invalid NTP packet.")
    dest_timestamp = ntplib.system_to_ntp_time(time.time())
    stats = ntplib.NTPStats()
    stats.from_data(data)
    stats.dest_timestamp = dest_timestamp

    # print(stats)
    # unpack response....
    leap = unpacked[0] >> 6 & 0x3
    version = unpacked[0] >> 3 & 0x7
    mode = unpacked[0] & 0x7
    stratum = unpacked[1]
    poll = unpacked[2]
    precision = unpacked[3]
    root_delay = float(unpacked[4]) / 2 ** 16
    root_dispersion = float(unpacked[5]) / 2 ** 16
    ref_id = unpacked[6]
    ref_timestamp = ntplib._to_time(unpacked[7], unpacked[8])
    orig_timestamp = ntplib._to_time(unpacked[9], unpacked[10])
    recv_timestamp = ntplib._to_time(unpacked[11], unpacked[12])
    tx_timestamp = ntplib._to_time(unpacked[13], unpacked[14])

    # now we have the results like NTPStats, print them (put some dummy ip 1.0.0.0)
    ans = convert_ntp_response_to_measurement(stats,"1.0.0.0", server)
    return ans
def verify_nts_response(response: bytes, s2c_key: bytes) -> bool:
    """
    Verify the integrity and authenticity of an NTS-protected NTP response.

    :param response: Full UDP payload from NTS server (header + AEAD extension).
    :param s2c_key: Server-to-client AEAD key from NTS-KE exchange.
    :return: True if valid and authenticated; False otherwise.
    """
    # NTP header is always 48 bytes
    if len(response) < 48:
        return False

    header = response[:48]
    ef_blob = response[48:]
    offset = 0
    print("extensions data:", ef_blob)
    while offset + 4 <= len(ef_blob):
        t, length = struct.unpack("!HH", ef_blob[offset:offset + 4])
        body = ef_blob[offset + 4: offset + 4 + length]
        offset += 4 + length
        print(t, length, body)
    print("====")
    # Must have at least an AEAD EF header (4 bytes)
    if len(ef_blob) < 4:
        print("len(ef_blob) < 4")
        return False

    # Parse outer EF: type and length
    try:
        ef_type, ef_len = struct.unpack("!HH", ef_blob[:4])
    except struct.error:
        print("error in parse outer EF")
        return False

    # Check it is an AEAD EF (type 0x0404)
    if ef_type != 0x0404:
        print(f"not AEAD EF: {ef_type}")
        return False

    # Ensure full EF body is present
    if len(ef_blob) < ef_len + 4:
        print("full body not present")
        return False

    ef_body = ef_blob[4:4 + ef_len]

    # Inner: first two bytes zero, next two bytes is ciphertext length
    try:
        _zero, ct_len = struct.unpack("!HH", ef_body[:4])
    except struct.error:
        print("first 2 bytes must be 0, then cypher text length")
        return False

    ciphertext = ef_body[4:4 + ct_len]

    # Decrypt and authenticate
    aes = AESSIV(s2c_key)
    try:
        # associated_data is the raw 48-byte NTP header
        aes.decrypt(ciphertext, [header])
    except Exception:
        # Decryption/authentication failed
        print("Decryption/authentication failed")
        return False

    # If we reach here, authentication passed
    return True

def measure_nts_server(server):
    # server="time.cloudflare.com"
    kee = parse_nts_kee_openSSL(server)

    pprint.pprint(kee)
    if kee['alternate_server'] is None:
        kee['alternate_server']=server
    if kee['alternate_port'] is None:
        kee['alternate_port']=123

    packet, t1 = build_nts_request(kee)
    resp, t4 = send_nts(packet, kee['alternate_server'], kee['alternate_port'])
    if not resp:
        print("No response -> timeout", server)
        raise Exception("No response -> timeout")
    print(f"Response length: {len(resp)}")
    measurement = parse_nts_response(resp, server, kee['s2c_key'], t1, t4)
    # print_ntp_measurement(measurement)
    print("ok")

# measure_nts_server("ntp.trifence.ch")
#"nts.netnod.se"
servers=[
         "time.cloudflare.com",
"1.ntp.ubuntu.com",
"2.ntp.ubuntu.com",
"3.ntp.ubuntu.com",
"4.ntp.ubuntu.com",
"nts.teambelgium.net",
"a.st1.ntp.br",
"b.st1.ntp.br",
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
bad_servers = ["2.ntp.ubuntu.com"]#['1.ntp.ubuntu.com', 'a.st1.ntp.br', 'b.st1.ntp.br', 'c.st1.ntp.br', 'ntp3.fau.de', 'ntp3.ipv6.fau.de', 'ptbtime1.ptb.de', 'ptbtime2.ptb.de', 'ntp.nanosrvr.cloud', 'ntpmon.dcs1.biz', 'ntp.trifence.ch', 'ntp01.maillink.ch', 'ntp02.maillink.ch', 'ntp03.maillink.ch', 'ntp2.glypnod.com', 'ntp1.dmz.terryburton.co.uk', 'ntp2.dmz.terryburton.co.uk', 'ntp1.glypnod.com', 'time.xargs.org']
bad_bad_servers = []
#['1.ntp.ubuntu.com', 'a.st1.ntp.br', 'b.st1.ntp.br', 'c.st1.ntp.br', 'ntp3.fau.de', 'ntp3.ipv6.fau.de', 'ptbtime1.ptb.de', 'ptbtime2.ptb.de', 'ntp.nanosrvr.cloud', 'ntpmon.dcs1.biz', 'ntp.trifence.ch', 'ntp01.maillink.ch', 'ntp02.maillink.ch', 'ntp03.maillink.ch', 'ntp2.glypnod.com', 'ntp1.dmz.terryburton.co.uk', 'ntp2.dmz.terryburton.co.uk', 'ntp1.glypnod.com', 'time.xargs.org']
# for server in servers:
#     try:
#         measure_nts_server(server)
#         print(f"Server {server} is NTS")
#     except Exception as e:
#         #no NTS
#         #try normal
#         print(e)
#         continue
#         try:
#             m=perform_ntp_measurement_domain_name_list(server, None, 4, 4)
#             if m is None or len(m)==0:
#                 bad_bad_servers.append(server)
#             else:
#                 print(f"Server {server} is NTP simple")
#         except Exception:
#             bad_bad_servers.append(server)
# print(len(bad_bad_servers))
# print(bad_bad_servers)
