import ipaddress
import os
import random
import socket
from ipaddress import ip_address, IPv4Address, IPv6Address
from typing import Optional
import ntplib
import requests
import dns.resolver
import dns.reversename

from server.app.utils.load_config_data import get_ipv4_edns_server, get_ipv6_edns_server
from server.app.utils.load_config_data import get_mask_ipv4, get_mask_ipv6
from server.app.utils.location_resolver import get_asn_for_ip, get_country_for_ip, get_continent_for_ip
from server.app.models.CustomError import InputError
from server.app.utils.validate import is_ip_address
from fastapi import HTTPException, Request


def ref_id_to_ip_or_name(ref_id: int, stratum: int) \
        -> tuple[None, str] | tuple[IPv4Address | IPv6Address, None] | tuple[None, None]:
    """
    Represents a method that converts the reference id to the reference ip or reference name.
    If the stratum is 0 or 1 then we can convert the reference id to it's name (ex: Geostationary Orbit Environment Satellite).
    If the stratum is between 1 and 256 then we can convert the reference id to it's ip.
    If the stratum is greater than 255, then we have an invalid stratum.

    Args:
        ref_id (int): the reference id of the ntp server
        stratum (int): the stratum level of the ntp server

    Returns:
        a tuple of the ip and name of the ntp server. At least one of them is None. If both are None then the stratum is invalid.
    """
    if 0 <= stratum <= 1:  # we can get the name
        # from ntplib, but without "Unidentified reference source" part
        fields = (ref_id >> 24 & 0xff, ref_id >> 16 & 0xff,
                  ref_id >> 8 & 0xff, ref_id & 0xff)
        text = "%c%c%c%c" % fields
        if text in ntplib.NTP.REF_ID_TABLE:
            return None, ntplib.NTP.REF_ID_TABLE[text]
        else:
            return None, text  # ntplib.ref_id_to_text(ref_id, stratum)
    else:
        if stratum < 256:  # we can get an IP address
            return ip_address(socket.inet_ntoa(ref_id.to_bytes(4, 'big'))), None  # 'big' is from big endian
        else:
            return None, None  # invalid stratum!!


def get_ip_family(ip_str: Optional[str]) -> int:
    """
    This method returns the IP family of the given IP address. It returns 4 if we have an IPv4, and
    it returns 6 if we have an IPv6 address. Otherwise, it raises an exception.

    Args:
        ip_str (Optional[str]): The IP address

    Returns:
        int: The ip family or an exception if we do not get an IP address

    Raises:
        InputError: If the IP provided is not an IPv4 or IPv6 address.
    """
    ans = is_ip_address(ip_str)
    if ans is None:
        raise InputError(f"{ip_str} is not an IP address")
    if ans == "ipv4":
        return 4
    return 6


def get_ip_network_details(ip_str: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    This method gets the ASN, the country code and the continent code of an IP address.

    Args:
        ip_str: The ip address

    Returns:
        tuple[Optional[str], Optional[str], Optional[str]]: the ASN, the country code and the continent
        of an IP address if they can be taken.
    """
    try:
        asn: Optional[str] = get_asn_for_ip(ip_str)
        country: Optional[str] = get_country_for_ip(ip_str)
        continent: Optional[str] = get_continent_for_ip(ip_str)
        return asn, country, get_area_of_ip(country, continent)
    except Exception as e:
        print(e)
        return None, None, None


def get_area_of_ip(ip_country: Optional[str], ip_continent: Optional[str]) -> str:
    """
    This method tries to get the area of an IP address based on its country and continent.

    Args:
        ip_country (Optional[str]): The country code of the IP address.
        ip_continent (Optional[str]): The continent code of the IP address.

    Returns:
        str: The area of an IP address.
    """
    # default is WW (world wide)
    if ip_continent is None or ip_country is None:
        return "WW"
    area_map = {
        "EU": "North-Central",
        "AF": "South-Central",
        "NA": "West",
        "SA": "West",
        "OC": "South-East"
    }
    # According to RIPE Atlas map, for Asia most of the countries are in South-East, but some are in North-East.
    north_east_countries = ["RU", "KZ", "MN"]
    if ip_continent in area_map:
        return area_map[ip_continent]
    # For Asia
    if ip_country in north_east_countries:
        return "North-East"
    return "South-East"


def get_prefix_from_ip(ip_str: str) -> Optional[str]:
    """
    This method returns the prefix of an IP address. It randomizes it before sending it to stat.ripe.net

    Args:
        ip_str: The ip address.

    Returns:
        Optional[str]: the prefix of an IP address.
    """
    try:
        ip_str_to_ask = ip_to_str(randomize_ip(ip_address(ip_str)))
        response = requests.get(f"https://stat.ripe.net/data/prefix-overview/data.json?resource={ip_str_to_ask}")
        response.raise_for_status()
        data = response.json()["data"]
        prefix: str = data.get("resource", None)
        return prefix
    except Exception as e:
        print(e)
        return None


def ip_to_str(ip: Optional[IPv4Address | IPv6Address]) -> Optional[str]:
    """
    Converts an IP address (either IPv4 or IPv6) to its string representation.
    This function takes an `IPv4Address` or `IPv6Address` object and converts it to
    a string. If the input IP is `None`, it returns `None`.

    Args:
        ip (Optional[IPv4Address | IPv6Address]): The IP address to be converted.

    Returns:
        Optional[str]: The string representation of the IP address, or `None` if the input is `None`.
    """
    return str(ip) if ip is not None else None


def get_server_ip(wanted_ip_type: int) -> IPv4Address | IPv6Address | None:
    """
    It determines the public IP address of this server by opening a dummy UDP socket
    connection to DNS (taken from the config). It has fallbacks to ipify.org. If you want IPv4,
    it will open an IPv4 connection, otherwise it will open an IPv6 connection.
    It is **strict**, and it will return None if it could not return the type you wanted.

    Args:
        wanted_ip_type (int): The type of IP address we are looking for.

    Returns:
        Optional[IPv4Address | IPv6Address]: The server's external IP address.
        as an IPv4Address or IPv6Address object, or None if detection fails.
    """
    # use a dummy connection to get the outward-facing IP (IPv4 or IPv6 connection)
    family = socket.AF_INET6 if wanted_ip_type == 6 else socket.AF_INET
    dns_server_used: Optional[str]
    if wanted_ip_type == 6:
        # search for IPv6 DNS IP addresses in the config
        dns_server_used = get_ipv6_edns_server()
    else:
        # search for IPv4 DNS IP addresses in the config
        dns_server_used = get_ipv4_edns_server()
    s = socket.socket(family, socket.SOCK_DGRAM) # with wanted connection type and Data socket (UDP)
    ip: Optional[str] = None
    try:
        s.connect((dns_server_used, 80))
        ip = s.getsockname()[0]
    except Exception as e:
        print(f"Socket failed. Trying from ipify...")
    finally:
        s.close()

    try:
        # if it is public
        if ip is not None and is_private_ip(ip) == False:
            return ip_address(ip)
        # if it is private
        ip_public = get_server_ip_from_ipify(wanted_ip_type)
        # print(f"fallback to public IP: {ip_to_str(ip_public)}")
        return ip_public
    except ValueError:
        return None

def get_server_ip_if_possible(wanted_ip_type: int) -> Optional[IPv4Address | IPv6Address]:
    """
    This method returns the IP address of this server. If it has both IPv6 and IPv4, it will return whatever
    type you wanted. If not, it returns the type it has. (It has at least one IP address which is either IPv4 or IPv6)

    Args:
        wanted_ip_type (int): The type of IP address that you want to get. (4 or 6)

    Returns:
        Optional[IPv4Address | IPv6Address]: The IP address of this server with the desired IP type if possible.
    """
    try:
        ip = get_server_ip(wanted_ip_type)
        if ip is None: # try the other IP
            ip = get_server_ip(10 - wanted_ip_type)
        return ip
    except Exception as e:
        return None



def get_server_ip_from_ipify(wanted_ip_type: int) -> Optional[IPv4Address | IPv6Address]:
    """
    This method is a fallback to try to get the public IP address of our server from ipify.org

    Args:
        wanted_ip_type (int): The type of IP address that you want to get. (4 or 6)

    Returns:
        Optional[IPv4Address | IPv6Address]: The public IP address of our server.
    """
    try:
        ip_type: str = "" # which means 4
        if wanted_ip_type == 6:
            ip_type = "6"
        # api64 will return ipv4 or ipv6 if it is available, but we want exactly ipv4 or ipv6
        response = requests.get(f"https://api{ip_type}.ipify.org?format=json", timeout=3)
        response.raise_for_status()

        data = response.json()
        ip_str: str = data.get("ip", None)
        return ip_address(ip_str.strip())
    except Exception as e:
        print(e)
        return None


def client_ip_fetch(request: Request, wanted_ip_type: int) -> str | None:
    """
    Attempts to determine the client's IP address from the request.

    Args:
        request (Request): The FastAPI Request object, containing information
                           about the incoming client request.
        wanted_ip_type (int): The type of IP address that you want to get (4 or 6).

    Returns:
        str | None: The determined IP address of the client (or a fallback server IP).

    Raises:
         HTTPException: 503: If neither the client's IP from headers/request nor the fallback server IP can be successfully resolved.
    """
    try:
        client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else None)
        if client_ip:
            client_ip = client_ip.split(',')[0].strip()
        # if it is None or if it is private (a private IP is useless for us) or invalid
        if client_ip is None or is_private_ip(client_ip) or is_ip_address(client_ip) is None:
            client_ip = ip_to_str(get_server_ip(wanted_ip_type))

        # test if you got the desired IP address type
        if get_ip_family(client_ip) == wanted_ip_type:
            return client_ip
        else: # try to convert it. If conversion fails, it returns the original IP address
            return try_converting_ip(client_ip, wanted_ip_type)

    except Exception as e:
        print(e)
        raise HTTPException(status_code=503, detail="Could not resolve client IP or fallback IP.")

def try_converting_ip(client_ip: Optional[str], wanted_ip_type: int) -> Optional[str]:
    """
    This method tries to convert an IPv4 into IPv6 or an IPv6 into an IPv4 using reverse DNS from dnspython.
    It only works if there is a configured PTR record + AAAA record.

    Args:
        client_ip (Optional[str]): The client IP to convert.
        wanted_ip_type (int): The type of IP address that we want.

    Returns:
        Optional[str]: The converted IPv6 or IPv4 as a string or the original IP if the process failed.
    """
    if client_ip is None:
        return None
    try: #getting PTR record
        reverse_name = dns.reversename.from_address(client_ip)
        answer = dns.resolver.resolve(reverse_name, 'PTR')
        client_domain_name = str(answer[0]).rstrip('.')
        # try getting IPv4 or IPv6
        rdtype = "A"
        if wanted_ip_type == 6:
            rdtype = "AAAA"
        new_ip = dns.resolver.resolve(client_domain_name, rdtype)
        return str(new_ip[0])
    except Exception as e:
        # It failed. Return the original IP address
        return client_ip

def is_private_ip(ip_str: str) -> bool:
    """
    This method checks whether an IP address is a private IP.

    Args:
        ip_str (str): The IP address to check.

    Returns:
        bool: Whether the IP address is a private IP.
    """
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return ip_obj.is_private
    except Exception:
        return False

def is_this_ip_anycast(searched_ip: Optional[str]) -> bool:
    """
    This method checks whether an IP address is anycast or not, by searching in the local anycast prefix databases.
    This method would never throw an exception (If the databases don't exist, it will return False).

    Args:
        searched_ip (Optional[str]): The IP address to check.

    Returns:
        bool: Whether the IP address is anycast or not.
    """
    if searched_ip is None:
        return False
    try:
        ip_family = get_ip_family(searched_ip)
        ip = ip_address(searched_ip)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # get the correct database
        if ip_family == 4:
            file_path = os.path.abspath(os.path.join(current_dir, "..", "..", "anycast-v4-prefixes.txt"))
        else:
            file_path = os.path.abspath(os.path.join(current_dir, "..", "..", "anycast-v6-prefixes.txt"))

        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                try:
                    whole_network: ipaddress._BaseNetwork
                    if ip_family == 4:
                        whole_network = ipaddress.IPv4Network(line, strict=False)
                    else:
                        whole_network = ipaddress.IPv6Network(line, strict=False)
                    if ip in whole_network:
                        return True
                except Exception:
                    continue
        return False
    except Exception as e:
        print(f"Error (safe) in is_anycast: {e}")
        return False


def randomize_ip(ip: IPv4Address | IPv6Address) -> IPv4Address | IPv6Address | None:
    """
    Randomizes the host bits of an IPv4 or IPv6 address based on a subnet mask length.

    Args:
        ip (IPv4Address | IPv6Address): The IPv4 or IPv6 address to randomize.

    Returns:
        IPv4Address | IPv6Address | None: A new IPv4 or IPv6 address with the same network bits and randomized host bits.
    """
    try:
        if get_ip_family(str(ip)) == 4:
            mask_length = get_mask_ipv4()
            network_mask = (2 ** 32 - 1) << (32 - mask_length) & 0xFFFFFFFF
            random_host = random.getrandbits(32 - mask_length)
        else:
            mask_length = get_mask_ipv6()
            network_mask = (2 ** 128 - 1) << (128 - mask_length) & (2 ** 128 - 1)
            random_host = random.getrandbits(128 - mask_length)

        ip_int = int(ip)
        network_part = ip_int & network_mask
        randomized_ip_int = network_part | random_host
        return ip_address(randomized_ip_int)

    except InputError as e:
        print(f"IP cannot be randomized. {e}")
        return None
