import os
import subprocess
from typing import Tuple

from server.app.utils.perform_measurements import parse_ntp_versions_response_to_dict

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
                #TODO: analyse the reference ID to see if it is true NTPv2 response or another version
                conf = "100"
                analysis = f"It supports NTPv2."

    except Exception as e:
        conf = "0"
        analysis = "Not supported, error in measurement."
    return conf, analysis, m_data