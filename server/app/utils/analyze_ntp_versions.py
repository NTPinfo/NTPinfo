import json
import os
import subprocess
from typing import Tuple

from server.app.models.CustomError import InputError


def parse_ntp_versions_response_to_dict(content: str) -> dict:
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
        data = json.loads(content)
        return data
    except Exception as e:
        raise InputError(f"could not parse json {e}")
# packet = struct.pack(
#         "!B B H I I I Q Q Q Q",
#         0,  # LI + Status
#         1,  # Type (client request)
#         0,  # Precision
#         0,  # Estimated Error
#         0,  # Estimated Drift Rate
#         0,  # Reference Clock ID
#         0,  # Reference Timestamp
#         0,  # Originate Timestamp
#         0,  # Receive Timestamp
#         current_ntp_time  # Transmit Timestamp
#     )
def analyse_ntpv1(server: str, binary_nts_tool: str) -> Tuple[str, str, dict]:
    """
    This method analyzes the data received from trying to perform a measurement with this specific NTP version.

    Args:
        server (str): The server name.
        binary_nts_tool (str): The binary NTP tool name.
    Returns:
        Tuple[str, str]: The confidence that the server truly support this NTP version and the analysis results.
    """

    conf: str = "0"
    analysis: str = ""
    m_data = {}
    try:
        result = subprocess.run(
            [str(binary_nts_tool), "ntpv1", server],
            capture_output=True, text=True,
            env=os.environ.copy()
        )
    except Exception as e:
        conf = "0"
        analysis = "Not supported, error in measurement."
        return conf, analysis, m_data
    try:
        if result.returncode != 0: # clearly a failed measurement
            analysis = result.stdout.strip()
        else:
            # analyzing
            m_data = parse_ntp_versions_response_to_dict(result.stdout.strip())
            if m_data.get("version") is not None:
                conf = "25"
                analysis = f"The received result is not NTPv1. The version is: {m_data.get("version")}"
            else:
                # ntpv1 is very limited, so if we arrived here, I think it is supported
                conf = "100"
                analysis = f"It supports NTPv1."

    except Exception as e:
        conf = "0"
        analysis = "Received something, but could not parse the response."
    return conf, analysis, m_data


def analyse_ntpv2(server: str, binary_nts_tool: str) -> Tuple[str, str, dict]:
    """
    This method analyzes the data received from trying to perform a measurement with this specific NTP version.

    Args:
        server (str): The server name.
        binary_nts_tool (str): The binary NTP tool name.
    Returns:
        Tuple[str, str]: The confidence that the server truly support this NTP version and the analysis results.
    """

    conf: str = "0"
    analysis: str = ""
    m_data = {}
    try:
        result = subprocess.run(
            [str(binary_nts_tool), "ntpv2", server],
            capture_output=True, text=True,
            env=os.environ.copy()
        )
        if result.returncode != 0:  # clearly a failed measurement
            analysis = result.stdout.strip()
        else:
            # analyzing
            m_data = parse_ntp_versions_response_to_dict(result.stdout.strip())
            if str(m_data.get("version")) != "2": # does not have the same version
                conf = "50"
                analysis = f"Received an NTP response, but with a different NTP version: version {m_data.get("version")}"
            else:
                # the result says it is NTPv2.
                #TODO: analyse the reference ID and to convert it
                conf = "100"
                analysis = f"It supports NTPv2."

    except Exception as e:
        conf = "0"
        analysis = "Not supported, error in measurement."
    return conf, analysis, m_data

def analyse_ntpv3(server: str, binary_nts_tool: str) -> Tuple[str, str, dict]:
    """
    This method analyzes the data received from trying to perform a measurement with this specific NTP version.

    Args:
        server (str): The server name.
        binary_nts_tool (str): The binary NTP tool name.
    Returns:
        Tuple[str, str]: The confidence that the server truly support this NTP version and the analysis results.
    """

    conf: str = "0"
    analysis: str = ""
    m_data = {}
    try:
        result = subprocess.run(
            [str(binary_nts_tool), "ntpv3", server],
            capture_output=True, text=True,
            env=os.environ.copy()
        )
        if result.returncode != 0:  # clearly a failed measurement
            analysis = result.stdout.strip()
        else:
            # analyzing
            m_data = parse_ntp_versions_response_to_dict(result.stdout.strip())
            if str(m_data.get("version")) != "3": # does not have the same version
                conf = "50"
                analysis = f"Received an NTP response, but with a different NTP version: version {m_data.get("version")}"
            else:
                # the result says it is NTPv3.
                #TODO: analyse the reference ID and to convert it
                conf = "75 or 100"
                analysis = f"It supports NTPv3."

    except Exception as e:
        conf = "0"
        analysis = "Not supported, error in measurement."
    return conf, analysis, m_data

def analyse_ntpv4(server: str, binary_nts_tool: str) -> Tuple[str, str, dict]:
    """
    This method analyzes the data received from trying to perform a measurement with this specific NTP version.

    Args:
        server (str): The server name.
        binary_nts_tool (str): The binary NTP tool name.
    Returns:
        Tuple[str, str]: The confidence that the server truly support this NTP version and the analysis results.
    """

    conf: str = "0"
    analysis: str = ""
    m_data = {}
    try:
        result = subprocess.run(
            [str(binary_nts_tool), "ntpv4", server],
            capture_output=True, text=True,
            env=os.environ.copy()
        )
        if result.returncode != 0:  # clearly a failed measurement
            analysis = result.stdout.strip()
        else:
            # analyzing
            m_data = parse_ntp_versions_response_to_dict(result.stdout.strip())
            if str(m_data.get("version")) != "4": # does not have the same version
                conf = "50"
                analysis = f"Received an NTP response, but with a different NTP version: version {m_data.get("version")}"
            else:
                # the result says it is NTPv4.
                #TODO: analyse the reference ID and to convert it
                conf = "75 or 100"
                analysis = f"It supports NTPv4."

    except Exception as e:
        conf = "0"
        analysis = "Not supported, error in measurement."
    return conf, analysis, m_data

def analyse_ntpv5(server: str, binary_nts_tool: str) -> Tuple[str, str, dict]:
    """
    This method analyzes the data received from trying to perform a measurement with this specific NTP version.

    Args:
        server (str): The server name.
        binary_nts_tool (str): The binary NTP tool name.
    Returns:
        Tuple[str, str]: The confidence that the server truly support this NTP version and the analysis results.
    """

    conf: str = "0"
    analysis: str = ""
    m_data = {}
    try:
        result = subprocess.run(
            [str(binary_nts_tool), "ntpv5", server],
            capture_output=True, text=True,
            env=os.environ.copy()
        )
        if result.returncode != 0:  # clearly a failed measurement
            analysis = result.stdout.strip()
        else:
            # analyzing
            m_data = parse_ntp_versions_response_to_dict(result.stdout.strip())
            if str(m_data.get("version")) != "5": # does not have the same version
                conf = "50"
                analysis = f"Received an NTP response, but with a different NTP version: version {m_data.get("version")}"
            else:
                # the result says it is NTPv5. But the content could still be NTPv4
                #if m_data.get("era") != 0
                conf = "75 or 100"
                analysis = f"It supports NTPv5."

    except Exception as e:
        conf = "0"
        analysis = "Not supported, error in measurement."
    return conf, analysis, m_data


def prob_to_be_ntpv5(data: dict) -> float:
    if data.get("era") != 0:
        return 0
    if str(data.get("version")) == "4":
        return 0
    #     ntpv4              ntpv5
    # root delay     vs   timescale|era|flags
    # root disp      vs   root delay
    # ref id         vs   root disp
    # reference tmp  vs   server cookie
    # origin tmp t1  vs   client cookie
    # recv tmp t2    vs   recv tmp t2   #same
    # sent tmp t3    vs   sent tmp t3   #same
    # rtt
    # offset


# simple model (data from ntpv5 compared to the data format of ntpv4):
# rtt, offset, server cookie -> reference tmp
# client cookie -> origin tmp