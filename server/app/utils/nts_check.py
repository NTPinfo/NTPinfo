import subprocess
import platform
import pathlib



# directory where you keep the NTS Go .exe tools
nts_tools_dir_path = pathlib.Path(__file__).parent.parent.parent.parent / "tools" / "measureNtsTool"

# measuring an NTS server has 2 steps:
# 1) Key Exchange -> get the cookies and basically the keys for a secure connection
# 2) Encrypt the NTP request with the keys and measure it.


def get_right_nts_binary_tool_for_your_os() -> str:
    """
    We use some binary tools to perform NTS measurements. You need the one that
    is compatible with your operating system.
    Args:
        none
    Returns:
        str: the right NTS tool for your OS.
    """
    # build in wsl with: GOOS=windows GOARCH=amd64 go build -o ntstool_windows_amd64.exe measure_nts.go
    system = platform.system().lower()
    arch = platform.machine().lower()
    print(system)
    if system == "windows":
        return nts_tools_dir_path / "ntstool_windows_amd64.exe"
    elif system == "linux":
        return nts_tools_dir_path / "ntstool_linux_amd64"
    elif system == "darwin":
        if arch == "arm64":
            return nts_tools_dir_path / "ntstool_darwin_arm64"
        else:
            return nts_tools_dir_path / "ntstool_darwin_amd64"
    else:
        raise Exception(f"Unsupported platform: {system} {arch}")

# def convert_nts_response_to_measurement_data(response_from_binary: str):
#     print("a")

def perform_nts_measurement_domain_name(server_domain_name: str, wanted_ip_type: int = -1) -> dict[str, str]:
    """
    Perform the NTS measurement for a domain name. It returns the status of the NTS measurement on the overall server
    and a short analysis of the measurement.

    It verifies the TLS certificate.

    Args:
        server_domain_name (str): the domain name
        wanted_ip_type (int): the IP address type (4 ot 6)
    """
    binary_nts_tool = get_right_nts_binary_tool_for_your_os()

    if wanted_ip_type == -1: # if the user does not want a specific IP type
        result = subprocess.run(
            [str(binary_nts_tool), server_domain_name],
            capture_output=True, text=True
        )
    else: # if the user wants a specific IP type
        result = subprocess.run(
            [str(binary_nts_tool), server_domain_name, "ipv" + str(wanted_ip_type)],
            capture_output=True, text=True
        )
    nts_result_short: dict = {"NTS succeeded": False, "NTS analysis": "None"}

    # analyse
    if result.returncode == 0: # it succeeded
        nts_result_short["NTS succeeded"] = True
        nts_result_short["NTS analysis"] = f"It is NTS. One NTS IP is {get_ip_from_nts_response(result.stdout.strip())}"
    elif result.returncode == 6: # it succeeded, but not with the wanted IP type
        nts_result_short["NTS succeeded"] = True
        nts_result_short["NTS analysis"] = f"It is NTS. Failed on ipv{wanted_ip_type}. One working NTS IP is {get_ip_from_nts_response(result.stdout.strip())}"
    else: # something failed
        nts_result_short["NTS analysis"] = result.stdout.strip()

    # full measurement details:
    print(result.stdout.strip())
    return nts_result_short


def perform_nts_measurement_ip(server_ip_str: str):
    """
    This method performs an NTS measurement on the given server IP.
    However, it does not verify the TLS certificate, because usually certificates only contain
    DNS Subject Alternative Names (SANs) like "time.cloudflare.com". They rarely contain IP SANs.

    So this method does not verify the TLS certificate. But it is good enough to tell you if this IP is NTS or not.
    If you want to verify the TLS certificate, please measure the domain name of this IP address.

    Args:
        server_ip_str (str): the server IP
    """
    # server_domain_name = try_converting_ip_to_domain_name(server_ip_str)
    binary_nts_tool = get_right_nts_binary_tool_for_your_os()
    nts_result_short: dict = {"NTS succeeded": False, "NTS analysis": "None"}

    result = subprocess.run(
        [str(binary_nts_tool), server_ip_str, server_ip_str],
        capture_output=True, text=True
    )
    # analyse
    if result.returncode == 0:  # it succeeded
        nts_result_short["NTS succeeded"] = True
        res, ke_ip = did_ke_performed_on_different_ip(server_ip_str, result.stdout.strip())
        if res:
            # check if the KE did not request another IP
            nts_result_short["NTS analysis"] = (f"Measurement succeeded, but Key Exchange forced it to "
                                                f"be performed on {ke_ip}")
        else:
            nts_result_short["NTS analysis"] = "NTS measurement succeeded on this IP"
    else:  # something failed
        nts_result_short["NTS analysis"] = result.stdout.strip()

    # bool NTS succeeded: true/false
    # NTS analysis: string
    # possible: NTS ok, but KE switched to a different IP address and port: <ip>
    print(result.stdout.strip())
    return nts_result_short

def get_ip_from_nts_response(response_from_binary: str) ->str:
    """
    It gets the IP address from the given response from using the (Go) NTS tool.

    Args:
        response_from_binary (str): the response from the binary tool (text).
    Returns:
        str: the IP address or ""
    """
    for line in response_from_binary.splitlines():
        if "Measured server IP" in line:
            return line.split(":", 1)[1].strip()
    return ""

def did_ke_performed_on_different_ip(original_ip: str, response_from_binary: str) -> (bool, str):
    """
    This method tells you if the Key Exchange part changed the IP to a different one. If it is the case, then
    the measurement was continued on that IP address.

    Args:
        original_ip (str): the original IP address
        response_from_binary (str): the response from the binary tool (text).
    Returns:
        (bool, str): True if the IP was changed, False otherwise, and the IP on which the measurement was continued.
    """
    ip: str = get_ip_from_nts_response(response_from_binary)
    if original_ip != ip:
        return True, ip
    else:
        return False, ip

# measure_nts_server("time.cloudflare.com")1.ntp.ubuntu.com
# print(perform_nts_measurement_domain_name("time.cloudflare.com",4))
# perform_nts_measurement_domain_name("1.ntp.ubuntu.com")
# print(perform_nts_measurement_ip("ntppool1.time.nl"))

# print(perform_nts_measurement_ip("162.159.200.123"))
# print(perform_nts_measurement_ip(domain_name_to_ip_list("time.cloudflare.com", None, 4)[0]))



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
