from dataclasses import dataclass
from ipaddress import IPv4Address, IPv6Address

@dataclass
class NtpServerInfo:
    """
    Represents the relevant metadata of an NTP server.

    Fields:
        ntp_version (int): The version of NTP the user chose to use (backwards compatible)
        ntp_server_ip (IPv4Address | IPv6Address): The IP of the server, either in IPv4 or IPv6 format
        ntp_server_name (str): The name of the server
        ntp_server_ref_parent_ip (None | IPv4Address | IPv6Address): The IP of the parent server (it is None if it is a root server)
        ref_name (str): The name of the parent (reference) server or None if we can only get the IP
    """
    ntp_version: int
    ntp_server_ip: IPv4Address | IPv6Address
    ntp_server_name: None | str
    ntp_server_ref_parent_ip: None | IPv4Address | IPv6Address
    ref_name: None | str