import json
import os
import pprint
import subprocess
from typing import Tuple

from server.app.utils.ip_utils import translate_ref_id
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
        data: dict = json.loads(content)
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

def directly_analyze_all_ntp_versions(server: str, binary_nts_tool: str, ntpv5_draft: str="") -> dict:
    """
    This method simply runs the ntp-nts-tool and analyse the output.
    If an error field is present in the response, then the analysis failed.
    If a measurement for a version failed, confidence will be 0 and the result will contain the same content as "analysis"
    So, if confidence is 0, ignore the "result" field as it is useless
    Args:
        server (str): The server that you want to measure.
        binary_nts_tool (str): The binary NTP tool name.
        ntpv5_draft (str): The NTP version you want to measure.
    Returns:
        dict: One dictionary with the analysis results for each NTP version (from 1 to 5).
    """
    m_data: dict = {}
    ntp_versions_analysis: dict = {}
    try:
        result = subprocess.run(
            [str(binary_nts_tool), "allntpv", server, "-draft", ntpv5_draft],
            capture_output=True, text=True,
            env=os.environ.copy()
        )
        if result.returncode != 0: #we should never arrive here, but just to be sure
            raise Exception(f"all ntp analysis failed")
    except Exception as e:
        m_data["error"] = "Error: " + str(e)
        return m_data
    try:
        m_data = parse_ntp_versions_response_to_dict(result.stdout.strip())
        #in this mode, the tool provide more details than just the result. So we need to extract it manually
        ntp_versions_analysis["ntpv1_m_result"] = m_data.get("ntpv1", {}).get("result")
        ntp_versions_analysis["ntpv2_m_result"] = m_data.get("ntpv2", {}).get("result")
        ntp_versions_analysis["ntpv3_m_result"] = m_data.get("ntpv3", {}).get("result")
        ntp_versions_analysis["ntpv4_m_result"] = m_data.get("ntpv4", {}).get("result")
        ntp_versions_analysis["ntpv5_m_result"] = m_data.get("ntpv5", {}).get("result")
        # ntpv2_data: dict = m_data.get("ntpv2")
        # ntpv3_data: dict = m_data.get("ntpv3")
        # ntpv4_data: dict = m_data.get("ntpv4")
        # ntpv5_data: dict = m_data.get("ntpv5")

        (ntp_versions_analysis["ntpv1_supported_confidence"],
        ntp_versions_analysis["ntpv1_analysis"]) = analyse_ntpv1_response(ntp_versions_analysis["ntpv1_m_result"])
        (ntp_versions_analysis["ntpv2_supported_confidence"],
        ntp_versions_analysis["ntpv2_analysis"]) = analyse_ntpv2_response(ntp_versions_analysis["ntpv2_m_result"])
        (ntp_versions_analysis["ntpv3_supported_confidence"],
        ntp_versions_analysis["ntpv3_analysis"]) = analyse_ntpv3_response(ntp_versions_analysis["ntpv3_m_result"])
        (ntp_versions_analysis["ntpv4_supported_confidence"],
        ntp_versions_analysis["ntpv4_analysis"]) = analyse_ntpv4_response(ntp_versions_analysis["ntpv4_m_result"])
        (ntp_versions_analysis["ntpv5_supported_confidence"],
        ntp_versions_analysis["ntpv5_analysis"]) = analyse_ntpv5_response(ntp_versions_analysis["ntpv5_m_result"])
        return ntp_versions_analysis
    except Exception as e:
        m_data["error"] = "Error: " + str(e)
        return m_data

def run_tool_on_ntp_version(server: str, binary_nts_tool: str, ntp_version: str, ntpv5_draft: str="") -> Tuple[str, str, dict]:
    """
    This method runs the tool on the specified NTP version and then analyses the response.
    If conf is 0, then the result will not contain anything useful (a dict with "error": <error>)
    Args:
        server (str): The server name.
        ntp_version (str): The NTP version you want to measure.
        binary_nts_tool (str): The binary NTP tool name.
        ntpv5_draft (str): The NTP version you want to measure.
    Returns:
        Tuple[str, str, dict]: The confidence that the server truly support this NTP version, the analysis results, and
                                the result.
    Raises:
        InputError: If the ntp_version is invalid.
    """
    if ntp_version not in ["ntpv1", "ntpv2", "ntpv3", "ntpv4", "ntpv5"]:
        raise InputError(f"ntp_version {ntp_version} is invalid")
    conf: str = "0"
    analysis: str = ""
    m_data: dict = {}
    try:
        if ntp_version == "ntpv5" and ntpv5_draft != "":
            result = subprocess.run(
                [str(binary_nts_tool), ntp_version, server, "-draft", ntpv5_draft],
                capture_output=True, text=True,
                env=os.environ.copy()
            )
        else:
            result = subprocess.run(
                [str(binary_nts_tool), ntp_version, server],
                capture_output=True, text=True,
                env=os.environ.copy()
            )
    except Exception as e:
        conf = "0"
        analysis = "Not supported, error in measurement."
        return conf, analysis, m_data
    # parse the response and analyse it
    try:
        if result.returncode != 0:  # clearly a failed measurement
            conf = "0"
            analysis = result.stdout.strip()
            m_data["error"] = analysis

        else: # success
            m_data = parse_ntp_versions_response_to_dict(result.stdout.strip())
            conf, analysis = analyse_ntp_version_response(m_data, ntp_version)
    except Exception as e:
        conf = "0"
        analysis = "Received something, but could not parse the response."
    return conf, analysis, m_data

def analyse_ntp_version_response(m_data: dict, ntp_version: str) -> Tuple[str, str]:
    """
    This method analyses the data according to the specified NTP version
    Args:
        m_data (dict): The parsed response.
        ntp_version (str): The NTP version you want to measure.
    Returns:
        Tuple[str, str]: The confidence that the server truly support this NTP version and the analysis.
    Raises:
        InputError: If the ntp_version is invalid.
    """
    if ntp_version not in ["ntpv1", "ntpv2", "ntpv3", "ntpv4", "ntpv5"]:
        raise InputError(f"ntp_version {ntp_version} is invalid")
    if ntp_version == "ntpv1":
        return analyse_ntpv1_response(m_data)
    elif ntp_version == "ntpv2":
        return analyse_ntpv2_response(m_data)
    elif ntp_version == "ntpv3":
        return analyse_ntpv3_response(m_data)
    elif ntp_version == "ntpv4":
        return analyse_ntpv4_response(m_data)
    #elif ntp_version == "ntpv5":
    return analyse_ntpv5_response(m_data)

def analyse_ntpv1_response(m_data: dict) -> Tuple[str, str]:
    """
    This method analyses the data according to NTPv1 version
    Args:
        m_data (dict): The parsed response.
    Returns:
        Tuple[str, str]: The confidence that the server truly support this NTP version and the analysis.
    """
    conf: str = "0"
    analysis: str = ""
    # analyzing
    if m_data.get("error") is not None:
        conf = "0"
        analysis = str(m_data.get("error"))
    elif m_data.get("version") is not None:
        conf = "25"
        analysis = f"The received result is not NTPv1. The version is: {m_data.get("version")}"
    else:
        # ntpv1 is very limited, so if we arrived here, I think it is supported
        conf = "100"
        analysis = f"It supports NTPv1."
    return conf, analysis

def analyse_ntpv2_response(m_data: dict) -> Tuple[str, str]:
    """
    This method analyses the data according to NTPv2 version
    Args:
        m_data (dict): The parsed response.
    Returns:
        Tuple[str, str]: The confidence that the server truly support this NTP version and the analysis.
    """
    conf: str = "0"
    analysis: str = ""
    # analyzing
    if m_data.get("error") is not None:
        conf = "0"
        analysis = str(m_data.get("error"))
    elif str(m_data.get("version")) != "2":  # does not have the same version
        conf = "50"
        analysis = f"Received an NTP response, but with a different NTP version: version {m_data.get("version")}"
    else:
        # the result says it is NTPv2.
        conf = "100"
        analysis = f"It supports NTPv2."
    # update ref id to a string
    try:
        r: str = translate_ref_id(int(m_data["ref_id"]), int(m_data["stratum"]), 4)
        m_data["ref_id"] = r
    except Exception as e:
        analysis = analysis + f"\nCould not translate ref id"
    return conf, analysis

def analyse_ntpv3_response(m_data: dict) -> Tuple[str, str]:
    """
    This method analyses the data according to NTPv3 version
    Args:
        m_data (dict): The parsed response.
    Returns:
        Tuple[str, str]: The confidence that the server truly support this NTP version and the analysis.
    """
    conf: str = "0"
    analysis: str = ""
    # analyzing
    if m_data.get("error") is not None:
        conf = "0"
        analysis = str(m_data.get("error"))
    elif str(m_data.get("version")) != "3":  # does not have the same version
        conf = "50"
        analysis = f"Received an NTP response, but with a different NTP version: version {m_data.get("version")}"
    else:
        # the result says it is NTPv3.
        conf = "100"
        analysis = f"It supports NTPv3."
    # update ref id to a string
    try:
        r: str = translate_ref_id(int(m_data["ref_id"]), int(m_data["stratum"]), 4)
        m_data["ref_id"] = r
    except Exception as e:
        conf = "75"
        analysis = analysis + f"\nCould not translate ref id"
    return conf, analysis

def analyse_ntpv4_response(m_data: dict) -> Tuple[str, str]:
    """
    This method analyses the data according to NTPv4 version
    Args:
        m_data (dict): The parsed response.
    Returns:
        Tuple[str, str]: The confidence that the server truly support this NTP version and the analysis.
    """
    conf: str = "0"
    analysis: str = ""
    # analyzing
    if m_data.get("error") is not None:
        conf = "0"
        analysis = str(m_data.get("error"))
    elif str(m_data.get("version")) != "4":  # does not have the same version
        conf = "50"
        analysis = f"Received an NTP response, but with a different NTP version: version {m_data.get("version")}"
    else:
        # the result says it is NTPv4.
        conf = "75 or 100"
        analysis = f"It supports NTPv4."
    # update ref id to a string
    try:
        r: str = translate_ref_id(int(m_data["ref_id"]), int(m_data["stratum"]), 4)
        m_data["ref_id"] = r
    except Exception as e:
        analysis = analysis + f"\nCould not translate ref id"
    return conf, analysis
def analyse_ntpv5_response(m_data: dict) -> Tuple[str, str]:
    """
    This method analyses the data according to NTPv5 version
    Args:
        m_data (dict): The parsed response.
    Returns:
        Tuple[str, str]: The confidence that the server truly support this NTP version and the analysis.
    """
    conf: str = "0"
    analysis: str = ""
    # analyzing
    if m_data.get("error") is not None:
        conf = "0"
        analysis = str(m_data.get("error"))
    elif str(m_data.get("version")) != "5":  # does not have the same version
        conf = "50"
        analysis = f"Received an NTP response, but with a different NTP version: version {m_data.get("version")}"
    else:
        # the result says it is NTPv5. But the content could still be NTPv4
        try:
            if int(m_data["era"]) > 1:
                conf = "75"
                analysis = f"era is invalid"
            elif int(m_data["timescale"]) > 4:
                conf = "75"
                analysis = f"timescale is invalid"
            elif int(m_data["client_cookie"]) == 0:
                conf = "75"
                analysis = f"client_cookie is 0, which is not good"
            else:
                conf = "100"
                analysis = f"It supports NTPv5. Format seems ok"
        except Exception as e:
            conf = "25"
            analysis = f"It may support NTPv5, but response format is invalid: {e}"
    return conf, analysis


# def prob_to_be_ntpv5(data: dict) -> float:
#     if data.get("era") != 0:
#         return 0
#     if str(data.get("version")) == "4":
#         return 0
    #     ntpv4              ntpv5 draft 05
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