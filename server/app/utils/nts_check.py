import json
import os
import pprint
import subprocess
from typing import Tuple

from server.app.dtos.AdvancedSettings import AdvancedSettings
from server.app.utils.load_config_data import get_timeout_measurement_s
from server.app.utils.load_config_data import get_right_ntp_nts_binary_tool_for_your_os
from server.app.models.CustomError import InputError
from server.app.utils.validate import sanitize_string

# directory where you keep the NTS Go .exe tools
# nts_tools_dir_path = pathlib.Path(__file__).parent.parent.parent.parent / "tools" / "ntp-nts-tool"

# measuring an NTS server has 2 steps:
# 1) Key Exchange -> get the cookies and basically the keys for a secure connection
# 2) Encrypt the NTP request with the keys and measure it.


# def get_right_nts_binary_tool_for_your_os() -> Path:
#     """
#     We use some binary tools to perform NTS measurements. You need the one that
#     is compatible with your operating system.
#     Args:
#         none
#     Returns:
#         str: the right NTS tool for your OS.
#     """
#     # some useful lines that would help you for compiling Go code or running it in docker
#     # windows build in wsl with: GOOS=windows GOARCH=amd64 go build -o ntpnts_windows_amd64.exe
#     # linux build GOOS=linux GOARCH=amd64 go build -o ntpnts_linux_amd64
#     # ssh -i ~/parola2.pem ubuntu@<ip>
#     # scp -i ~/parola2.pem "...15d/ntscheck.zip" ubuntu@54.91.128.251:~
#     # unzip ntscheck.zip
#     # dos2unix docker-entrypoint.sh
#     # prepare .env with IP
#     # docker compose build
#     # docker compose up
#     #   in other wsl panel: docker compose exec backend bash
#     #   chmod +x /app/tools/measureNtsTool/ntstool_linux_amd64
#     #   inside the backend container: chmod +x /app/tools/measureNtsTool/ntstool_linux_amd64
#     # ctrl c and then docker compose down (in the first panel)
#     # build and up again

def parse_nts_response_to_dict(content: str) -> dict:
    """
    This method parses the response from the Go tool (which is a string looking like a json)

    Args:
        content (str): The response from the Go tool.
    Returns:
        dict: The parsed response.
    Raises:
        InputError: If the response is invalid.
    """
    try:
        data: dict = json.loads(content)
        return data
    except Exception as e:
        raise InputError(f"could not parse json {e}")

# def perform_nts_measurement(server: str, settings: AdvancedSettings)\
#         -> dict[str, str]:
#     """
#     Simply a method to combine both domain name and IP
#     :param server:
#     :param settings:
#     :return:
#     """
#     if is_ip_address(server) is None: #domain name
#         return perform_nts_measurement_domain_name(server, settings)
#     return perform_nts_measurement_ip(server)

def perform_nts_measurement_domain_name(server_domain_name: str, settings: AdvancedSettings)\
        -> dict[str, str]:
    """
    Perform the NTS measurement for a domain name. It returns the status of the NTS measurement on the overall server
    and a short analysis of the measurement.

    It verifies the TLS certificate.

    Args:
        server_domain_name (str): the domain name
        settings (AdvancedSettings): the settings for the measurement (wanted_ip_type)
    """
    nts_result_short: dict = {"NTS succeeded": False, "NTS analysis": "None"}
    timeout = get_timeout_measurement_s()
    try:
        binary_nts_tool = get_right_ntp_nts_binary_tool_for_your_os()
        if settings.wanted_ip_type == -1: # if the user does not want a specific IP type
            result = subprocess.run(
                [str(binary_nts_tool), "nts", server_domain_name,
                 "-t", str(timeout)],
                capture_output=True, text=True,
                env=os.environ.copy()#,
               # cwd=str(binary_nts_tool.parent)
            )
        else: # if the user wants a specific IP type
            result = subprocess.run(
                [str(binary_nts_tool), "nts", server_domain_name,
                 "-ipv", str(settings.wanted_ip_type), "-t", str(timeout)],
                capture_output=True, text=True,
                env=os.environ.copy()
            )
    except Exception as e:
        nts_result_short["NTS analysis"] = f"NTS test could not be performed (binary tool not available) {e}"
        return nts_result_short

    try:
        # analyse
        if result.returncode == 0: # it succeeded
            nts_result_short["NTS succeeded"] = True
            nts_data = parse_nts_response_to_dict(result.stdout.strip())
            nts_result_short["NTS analysis"] = f"It is NTS. One NTS IP is {nts_data.get("Measured server IP")}"
            # put the result data in the output
            nts_result_full = nts_data.copy()
            nts_result_full.update(nts_result_short)
            return nts_result_full
        elif result.returncode == 6: # it succeeded, but not with the wanted IP type
            nts_result_short["NTS succeeded"] = True
            nts_data = parse_nts_response_to_dict(result.stdout.strip())
            nts_result_short["NTS analysis"] = (f"It is NTS, but failed on ipv{settings.wanted_ip_type}. "
                                                f"One working NTS IP is {nts_data.get("Measured server IP")}")
            # put the result data in the output
            nts_result_full = nts_data.copy()
            nts_result_full.update(nts_result_short)
            return nts_result_full
        else: # something failed
            nts_result_short["NTS analysis"] = sanitize_string(result.stdout.strip())
            return nts_result_short

    except Exception as e:
        # error with parsing data. This piece of code is used in case there are problems with the output from
        # the Go tool
        #print(f"Probably a problem with parsing response from Go tool: {e}")
        if result.returncode == 0:
            nts_result_short["NTS analysis"] = "NTS measurement succeeded, but could not retrieve data"
        elif result.returncode == 6:
            nts_result_short["NTS analysis"] = (f"Measurement failed on ipv{settings.wanted_ip_type}, "
                                                f"but succeeded on the other type. Could not retrieve more data")
        else:
            nts_result_short["NTS analysis"] = "NTS measurement failed, but could not retrieve more data"
        return nts_result_short

def perform_nts_measurement_ip(server_ip_str: str) -> dict:
    """
    This method performs an NTS measurement on the given server IP.
    However, it does not verify the TLS certificate, because usually certificates only contain
    DNS Subject Alternative Names (SANs) like "time.cloudflare.com". They rarely contain IP SANs.

    So this method does not verify the TLS certificate. But it is good enough to tell you if this IP is NTS or not.
    If you want to verify the TLS certificate, please measure the domain name of this IP address.

    This method provides also the NTS result if the measurement succeeded, otherwise the error message.

    Args:
        server_ip_str (str): the server IP
    """
    timeout = get_timeout_measurement_s()
    nts_result_short: dict = {"NTS succeeded": False, "NTS analysis": "None"}
    try:
        binary_nts_tool = get_right_ntp_nts_binary_tool_for_your_os()
        result = subprocess.run(
            [str(binary_nts_tool), "nts", server_ip_str,
             "-t", str(timeout)],
            capture_output=True, text=True
        )
    except Exception as e:
        nts_result_short["NTS analysis"] = f"NTS test could not be performed (binary tool not available) {e}"
        return nts_result_short

    try:
        # analyse
        if result.returncode == 0:  # it succeeded
            nts_result_short["NTS succeeded"] = True
            nts_data = parse_nts_response_to_dict(result.stdout.strip())
            res, ke_ip = did_ke_performed_on_different_ip(server_ip_str, nts_data)
            if res:
                # check if the KE did not request another IP
                nts_result_short["NTS analysis"] = (f"Measurement succeeded, but Key Exchange forced it to "
                                                    f"be performed on {ke_ip}")
            else:
                nts_result_short["NTS analysis"] = "NTS measurement succeeded on this IP"
            # put the result data in the output
            nts_result_full = nts_data.copy()
            nts_result_full.update(nts_result_short)
            return nts_result_full
        else:  # something failed
            nts_result_short["NTS analysis"] = sanitize_string(result.stdout.strip()) # we get directly the message
            return nts_result_short

    except Exception as e:
        # error with parsing data. This piece of code is used in case there are problems with the output from
        # the Go tool
        #print(f"Probably a problem with parsing response from Go tool: {e}")
        if result.returncode == 0:
            nts_result_short["NTS analysis"] = "NTS measurement succeeded, but could not retrieve data"
        else:
            nts_result_short["NTS analysis"] = "NTS measurement failed, but could not retrieve more data"
        return nts_result_short



def did_ke_performed_on_different_ip(original_ip: str, nts_data: dict) -> Tuple[bool, str]:
    """
    This method tells you if the Key Exchange part changed the IP to a different one. If it is the case, then
    the measurement was continued on that IP address.

    Args:
        original_ip (str): the original IP address
        nts_data (dict): the response from the binary tool (text).
    Returns:
        (bool, str): True if the IP was changed, False otherwise, and the IP on which the measurement was continued.
    """
    ip: str = nts_data.get("Measured server IP", "")
    if ip == "":
        raise InputError("Measured server IP is missing")
    if original_ip != ip:
        return True, ip
    else:
        return False, original_ip

# measure_nts_server("time.cloudflare.com")1.ntp.ubuntu.com
# s=AdvancedSettings()
# s.wanted_ip_type=-1
# s.analyse_all_ntp_versions=True
# pprint.pprint(perform_nts_measurement_domain_name("time.cloudflare.com", s))
# perform_nts_measurement_domain_name("1.ntp.ubuntu.com")
# print(perform_nts_measurement_ip("ntppool1.time.nl"))

# print(perform_nts_measurement_ip("162.159.200.123"))
# print(perform_nts_measurement_ip(domain_name_to_ip_list("time.cloudflare.com", None, 4)[0]))



# a list of known NTS servers according to https://github.com/jauderho/nts-servers
nts_servers = [
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
