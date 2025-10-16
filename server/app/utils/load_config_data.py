import ipaddress
import os
import pathlib
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any, cast, Optional
import yaml
from dotenv import load_dotenv

load_dotenv()

ntp_nts_tools_dir_path = pathlib.Path(__file__).parent.parent.parent.parent / "tools" / "ntp-nts-tool"

def load_config() -> dict[str, Any]:
    """
    It loads the config from a YAML file.

    Raises:
        FileNotFoundError: If the config file does not exist.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "..", "..", "server_config.yaml")
    config_path = os.path.abspath(config_path)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, "r") as f:
        return cast(dict[str, Any], yaml.safe_load(f))


config = load_config()


def verify_if_config_is_set() -> bool:
    """
    This method ensures that the config file has all the required variables, and they are all correctly set. (the same data type)
    It will return true if everything is fine, else it will rise an exception,

    Raises:
        ValueError: If the config file does not have all the required variables or some of them are invalid.
    """
    # verify from .env (the secrets)
    get_ripe_account_email()
    get_ripe_api_token()

    # from config
    get_ntp_version()
    get_timeout_measurement_s()
    get_nr_of_measurements_for_jitter()
    get_mask_ipv4()
    get_mask_ipv6()
    get_edns_default_servers()
    get_edns_timeout_s()
    get_ripe_timeout_per_probe_ms()
    get_ripe_packets_per_probe()
    get_ripe_number_of_probes_per_measurement()
    get_ripe_server_timeout()
    get_anycast_prefixes_v4_url()
    get_anycast_prefixes_v6_url()
    get_max_mind_path_city()
    get_max_mind_path_country()
    get_max_mind_path_asn()

    check_geolite_account_id_and_key()

    # check fi ntp_nts tool exists:
    # commend these 3 lines if it is impossible to compile the file, and you do not care about NTS or other version than NTPv4
    ntp_nts_tool_path = get_right_ntp_nts_binary_tool_for_your_os()
    if not ntp_nts_tool_path.exists():
        raise FileNotFoundError(f"File not found. Please compile it manually. {str(ntp_nts_tool_path)}\n"
                                f"You could use command: GOOS=linux GOARCH=amd64 go build -o ntpnts_linux_amd64\n")
    # everything is fine
    return True


def get_ripe_account_email() -> str:
    """
    This function returns the RIPE Atlas account email. (one that has enough credits)

    Raises:
        ValueError: If the RIPE Atlas account email is not set.
    """
    ans = os.getenv('ripe_account_email')
    if ans is not None:
        return ans
    raise ValueError('ripe_account_email environment variable is not set')


def get_ripe_api_token() -> str:
    """
    This function returns the RIPE Atlas API token.

    Raises:
        ValueError: If the RIPE Atlas API token is not set.
    """
    ans = os.getenv('ripe_api_token')
    # print(ans)
    if ans is not None:
        return ans
    raise ValueError('ripe_api_token environment variable not set')


def get_ntp_version() -> int:
    """
    This method returns the ntp version that we use in measurements.

    Raises:
        ValueError: If the ntp version has not been correctly set.
    """
    if "ntp" not in config:
        raise ValueError("ntp section is missing")
    ntp = config["ntp"]
    if "version" not in ntp:
        raise ValueError("ntp 'version' is missing")
    if not isinstance(ntp["version"], int):
        raise ValueError("ntp 'version' must be an 'int'")
    if ntp["version"] <= 0:
        raise ValueError("ntp 'version' must be > 0")
    return ntp["version"]


def get_timeout_measurement_s() -> float | int:
    """
    This method returns the timeout for an NTP measurement.

    Raises:
        ValueError: If the ntp version has not been correctly set.
    """
    if "ntp" not in config:
        raise ValueError("ntp section is missing")
    ntp = config["ntp"]
    if "timeout_measurement_s" not in ntp:
        raise ValueError("ntp 'timeout_measurement_s' is missing")
    if not isinstance(ntp["timeout_measurement_s"], float | int):
        raise ValueError("ntp 'timeout_measurement_s' must be a 'float' or an 'int'")
    if ntp["timeout_measurement_s"] < 0:
        raise ValueError("ntp 'timeout_measurement_s' cannot be negative")
    return ntp["timeout_measurement_s"]


def get_nr_of_measurements_for_jitter() -> int:
    """
    This method returns the number of measurement requested for calculating the jitter.

    Raises:
        ValueError: If this variable has not been correctly set.
    """
    if "ntp" not in config:
        raise ValueError("ntp section is missing")
    ntp = config["ntp"]
    if "number_of_measurements_for_calculating_jitter" not in ntp:
        raise ValueError("ntp 'number_of_measurements_for_calculating_jitter' is missing")
    if not isinstance(ntp["number_of_measurements_for_calculating_jitter"], int):
        raise ValueError("ntp 'number_of_measurements_for_calculating_jitter' must be an 'int'")
    if ntp["number_of_measurements_for_calculating_jitter"] <= 0:
        raise ValueError("ntp 'number_of_measurements_for_calculating_jitter' must be > 0")
    return ntp["number_of_measurements_for_calculating_jitter"]


def get_rate_limit_per_client_ip() -> str:
    """
    This method returns the rate limit for queries per client IP to our server.

    Raises:
        ValueError: If this variable has not been correctly set.
    """
    if "ntp" not in config:
        raise ValueError("ntp section is missing")
    ntp = config["ntp"]
    if "rate_limit_per_client_ip" not in ntp:
        raise ValueError("ntp 'rate_limit_per_client_ip' is missing")
    if not isinstance(ntp["rate_limit_per_client_ip"], str):
        raise ValueError("ntp 'rate_limit_per_client_ip' must be a 'str'")
    r = ntp["rate_limit_per_client_ip"]

    if "/" not in r:
        raise ValueError("ntp 'rate_limit_per_client_ip' must contain 2 parts, separated by a '/'")
    try:
        number, unit = r.split("/")
    except Exception:
        raise ValueError("ntp 'rate_limit_per_client_ip' is in invalid format")
    if number.isdigit() is False:  # check whether all characters are digits
        raise ValueError("ntp 'rate_limit_per_client_ip' must have first part an integer")
    unit = unit.lower()
    if unit not in {"second", "minute"}:
        raise ValueError("ntp 'rate_limit_per_client_ip' unit must be either 'second' or 'minute'")
    return r


def get_mask_ipv4() -> int:
    """
    This method returns the mask we use for ipv4 IPs.

    Raises:
        ValueError: If this variable has not been correctly set.
    """
    if "edns" not in config:
        raise ValueError("edns section is missing")
    edns = config["edns"]
    if "mask_ipv4" not in edns:
        raise ValueError("edns 'mask_ipv4' is missing")
    if not isinstance(edns["mask_ipv4"], int):
        raise ValueError("edns 'mask_ipv4' must be an 'int'")
    if edns["mask_ipv4"] < 0 or edns["mask_ipv4"] > 32:
        raise ValueError("edns 'mask_ipv4' must be between 0 and 32 inclusive")
    return edns["mask_ipv4"]


def get_mask_ipv6() -> int:
    """
    This method returns the mask we use for ipv6 IPs.

    Raises:
        ValueError: If this variable has not been correctly set.
    """
    if "edns" not in config:
        raise ValueError("edns section is missing")
    edns = config["edns"]
    if "mask_ipv6" not in edns:
        raise ValueError("edns 'mask_ipv6' is missing")
    if not isinstance(edns["mask_ipv6"], int):
        raise ValueError("edns 'mask_ipv6' must be an 'int'")
    if edns["mask_ipv6"] < 0 or edns["mask_ipv6"] > 64:
        raise ValueError("edns 'mask_ipv6' must be between 0 and 64 inclusive")
    return edns["mask_ipv6"]


def get_edns_default_servers() -> list[str]:
    """
    This method returns the default list of EDNS servers. (in the order of their priorities)

    Raises:
        ValueError: If this variable has not been correctly set.
    """
    if "edns" not in config:
        raise ValueError("edns section is missing")
    edns = config["edns"]
    if "default_order_of_edns_servers" not in edns:
        raise ValueError("edns 'default_order_of_edns_servers' is missing")
    if not isinstance(edns["default_order_of_edns_servers"], list):
        raise ValueError("edns 'default_order_of_edns_servers' must be a 'list'")
    if len(edns["default_order_of_edns_servers"]) == 0:
        raise ValueError("edns 'default_order_of_edns_servers' cannot be empty")
    return edns["default_order_of_edns_servers"]


def get_ipv4_edns_server() -> Optional[str]:
    """
    This method returns the first IPv4 EDNS server available in the config.
    It returns None if no IPv4 EDNS server is available.
    """
    for ip_str in get_edns_default_servers():
        try:
            ip = ipaddress.ip_address(ip_str)
            if isinstance(ip, ipaddress.IPv4Address):
                return ip_str
        except Exception:
            continue
    return None


def get_ipv6_edns_server() -> Optional[str]:
    """
    This method returns the first IPv6 EDNS server available in the config.
    It returns None if no IPv6 EDNS server is available.
    """
    for ip_str in get_edns_default_servers():
        try:
            ip = ipaddress.ip_address(ip_str)
            if isinstance(ip, ipaddress.IPv6Address):
                return ip_str
        except Exception:
            continue
    return None


def get_edns_timeout_s() -> float | int:
    """
    This method returns the timeout for the EDNS query request.

    Raises:
        ValueError: If this variable has not been correctly set.
    """
    if "edns" not in config:
        raise ValueError("edns section is missing")
    edns = config["edns"]
    if "edns_timeout_s" not in edns:
        raise ValueError("edns 'edns_timeout_s' is missing")
    if not isinstance(edns["edns_timeout_s"], float | int):
        raise ValueError("edns 'edns_timeout_s' must be a 'float' or an 'int' in s")
    if edns["edns_timeout_s"] < 0:
        raise ValueError("edns 'edns_timeout_s' cannot be negative")
    return edns["edns_timeout_s"]


def get_right_ntp_nts_binary_tool_for_your_os() -> Path:
    """
    We use some binary tools to perform NTS measurements and analyse NTP versions. You need the one that
    is compatible with your operating system.
    Args:
        none
    Returns:
        Path: The path to the right ntp-nts binary tool for the specified system.
    """
    system = platform.system().lower()
    arch = platform.machine().lower()

    # binary_path = ntp_nts_tools_dir_path / "ntpnts_linux_amd64"
    if system == "windows":
        binary_path = ntp_nts_tools_dir_path / "ntpnts_windows_amd64.exe"
    elif system == "linux":
        binary_path = ntp_nts_tools_dir_path / "ntpnts_linux_amd64"
    elif system == "darwin":
        if arch == "arm64":
            binary_path = ntp_nts_tools_dir_path / "ntpnts_darwin_arm64"
        else:
            binary_path = ntp_nts_tools_dir_path / "ntpnts_darwin_amd64"
    else:
        raise Exception(f"Unsupported platform: {system} {arch}")

    if not binary_path.exists():
        return build_ntp_nts_binary_tool(system, arch, binary_path)
    return binary_path

def build_ntp_nts_binary_tool(system: str, arch: str, binary_path: Path) -> Path:
    """
    This method tries to compile the ntp-nts-tool into a binary
    Args:
        system (str): The system to build the ntp-nts tool for.
        arch (str): The architecture to build the ntp-nts tool for.
        binary_path (Path): The path to the ntp-nts binary tool.
    Returns:
        Path: The path to the right ntp-nts binary tool for the specified system.
    """
    print(f"[INFO] {binary_path} not found. Building it with Go...")

    # Check Go availability
    go_executable = shutil.which("go")
    if go_executable is None:
        raise RuntimeError("Go compiler not found in PATH. Install Go or add it to PATH.")

    if not ntp_nts_tools_dir_path.exists():
        raise RuntimeError(f"Build directory does not exist: {ntp_nts_tools_dir_path}")

    try:
        result = subprocess.run(
            [go_executable, "build", "-o", str(binary_path)],
            cwd=str(ntp_nts_tools_dir_path),
            env={**os.environ, "GOOS": system, "GOARCH": arch},
            check=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to build Go binary for {system}/{arch}")
        print(f"[INFO] Successfully built {binary_path}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to build NTS tool for {system}/{arch}: {e}")

    return binary_path

def get_ripe_timeout_per_probe_ms() -> float | int:
    """
    This method returns the timeout that a probe has to receive an answer from a measurement.

    Raises:
        ValueError: If this variable has not been correctly set.
    """
    if "ripe_atlas" not in config:
        raise ValueError("ripe_atlas section is missing")
    ripe_atlas = config["ripe_atlas"]
    if "timeout_per_probe_ms" not in ripe_atlas:
        raise ValueError("ripe_atlas 'timeout_per_probe_ms' is missing")
    if not isinstance(ripe_atlas["timeout_per_probe_ms"], float | int):
        raise ValueError("ripe_atlas 'timeout_per_probe_ms' must be a 'float' or an 'int' in ms")
    if ripe_atlas["timeout_per_probe_ms"] <= 0:
        raise ValueError("ripe_atlas 'timeout_per_probe_ms' must be > 0")
    return ripe_atlas["timeout_per_probe_ms"]


def get_ripe_packets_per_probe() -> int:
    """
    This method returns the number of tries that a probe will do for a measurement.
    It will send "packets_per_probe" queries for that NTP server. (see RIPE Atlas documentation for more information)

    Raises:
        ValueError: If this variable has not been correctly set.
    """
    if "ripe_atlas" not in config:
        raise ValueError("ripe_atlas section is missing")
    ripe_atlas = config["ripe_atlas"]
    if "packets_per_probe" not in ripe_atlas:
        raise ValueError("ripe_atlas 'packets_per_probe' is missing")
    if not isinstance(ripe_atlas["packets_per_probe"], int):
        raise ValueError("ripe_atlas 'packets_per_probe' must be an 'int'")
    if ripe_atlas["packets_per_probe"] <= 0:
        raise ValueError("ripe_atlas 'packets_per_probe' must be > 0")
    return ripe_atlas["packets_per_probe"]


def get_ripe_number_of_probes_per_measurement() -> int:
    """
    This method returns the number of probes requested and desired for a measurement.

    Raises:
        ValueError: If this variable has not been correctly set.
    """
    if "ripe_atlas" not in config:
        raise ValueError("ripe_atlas section is missing")
    ripe_atlas = config["ripe_atlas"]
    if "number_of_probes_per_measurement" not in ripe_atlas:
        raise ValueError("ripe_atlas 'number_of_probes_per_measurement' is missing")
    if not isinstance(ripe_atlas["number_of_probes_per_measurement"], int):
        raise ValueError("ripe_atlas 'number_of_probes_per_measurement' must be an 'int'")
    if ripe_atlas["number_of_probes_per_measurement"] <= 0:
        raise ValueError("ripe_atlas 'number_of_probes_per_measurement' must be > 0")
    return ripe_atlas["number_of_probes_per_measurement"]


def get_ripe_server_timeout() -> int:
    """
    This method returns the timeout (seconds) that the server has to get data from RIPE Atlas.

    Raises:
        ValueError: If this variable has not been correctly set.
    """
    if "ripe_atlas" not in config:
        raise ValueError("ripe_atlas section is missing")
    ripe_atlas = config["ripe_atlas"]
    if "server_timeout" not in ripe_atlas:
        raise ValueError("ripe_atlas 'server_timeout' is missing")
    if not isinstance(ripe_atlas["server_timeout"], int):
        raise ValueError("ripe_atlas 'server_timeout' must be an 'int' in s")
    if ripe_atlas["server_timeout"] <= 0:
        raise ValueError("ripe_atlas 'server_timeout' must be > 0")
    return ripe_atlas["server_timeout"]


# bgp_tools
def get_anycast_prefixes_v4_url() -> str:
    """
    This method returns the URL prefixes for anycast IPv4 servers.

    Raises:
        ValueError: If this variable has not been correctly set.
    """
    if "bgp_tools" not in config:
        raise ValueError("bgp_tools section is missing")
    bgp_tools = config["bgp_tools"]
    if "anycast_prefixes_v4_url" not in bgp_tools:
        raise ValueError("bgp_tools 'anycast_prefixes_v4_url' is missing")
    if not isinstance(bgp_tools["anycast_prefixes_v4_url"], str):
        raise ValueError("bgp_tools 'anycast_prefixes_v4_url' must be a 'str'")
    return bgp_tools["anycast_prefixes_v4_url"]


def get_anycast_prefixes_v6_url() -> str:
    """
    This method returns the URL prefixes for anycast IPv6 servers.

    Raises:
        ValueError: If this variable has not been correctly set.
    """
    if "bgp_tools" not in config:
        raise ValueError("bgp_tools section is missing")
    bgp_tools = config["bgp_tools"]
    if "anycast_prefixes_v6_url" not in bgp_tools:
        raise ValueError("bgp_tools 'anycast_prefixes_v6_url' is missing")
    if not isinstance(bgp_tools["anycast_prefixes_v6_url"], str):
        raise ValueError("bgp_tools 'anycast_prefixes_v6_url' must be a 'str'")
    return bgp_tools["anycast_prefixes_v6_url"]


def get_max_mind_path_city() -> str:
    """
    This method returns the path to the max_mind city database used for geolocation.

    Raises:
        ValueError: If this variable has not been correctly set.
    """
    if "max_mind" not in config:
        raise ValueError("max_mind section is missing")
    max_mind = config["max_mind"]
    if "path_city" not in max_mind:
        raise ValueError("max_mind 'path_city' is missing")
    # This assumes this file is in server/app/utils/
    server_dir = Path(__file__).resolve().parent.parent.parent
    relative_path = max_mind["path_city"]
    absolute_path = (server_dir / relative_path).resolve()
    return str(absolute_path)


def get_max_mind_path_country() -> str:
    """
    This method returns the path to the max_mind country database used for geolocation.

    Raises:
        ValueError: If this variable has not been correctly set.
    """
    if "max_mind" not in config:
        raise ValueError("max_mind section is missing")
    max_mind = config["max_mind"]
    if "path_country" not in max_mind:
        raise ValueError("max_mind 'path_country' is missing")
    # This assumes this file is in server/app/utils/
    server_dir = Path(__file__).resolve().parent.parent.parent
    relative_path = max_mind["path_country"]
    absolute_path = (server_dir / relative_path).resolve()
    return str(absolute_path)


def get_max_mind_path_asn() -> str:
    """
    This method returns the path to the max_mind ASN database used for geolocation.

    Raises:
        ValueError: If this variable has not been correctly set.
    """
    if "max_mind" not in config:
        raise ValueError("max_mind section is missing")
    max_mind = config["max_mind"]
    if "path_asn" not in max_mind:
        raise ValueError("max_mind 'path_asn' is missing")
    # This assumes this file is in server/app/utils/
    server_dir = Path(__file__).resolve().parent.parent.parent
    relative_path = max_mind["path_asn"]
    absolute_path = (server_dir / relative_path).resolve()
    return str(absolute_path)


def check_geolite_account_id_and_key() -> bool:
    """
    This function checks that we have the account id and key set.
    Only Warnings. It does not raise errors.

    Returns:
        bool: True if we have the account id and key set.
    """
    ans = os.getenv('ACCOUNT_ID')
    if ans is None:
        print("WARNING! ACCOUNT_ID environment variable not set")
        return False
    ans = os.getenv('LICENSE_KEY')
    if ans is None:
        print("WARNING! LICENSE_KEY environment variable not set")
        return False
    return True
