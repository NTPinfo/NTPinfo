from pydantic import BaseModel, model_validator
from typing import Self

class AdvancedSettings(BaseModel):
    """
    Settings for advances measurements. If a field is invalid, then it would not be considered,
    and it would be overridden. This class is used internally.
    Attributes:
        wanted_ip_type (int): The wanted IP address type (4 ot 6) in case the "server" is a domain name.
        measurement_type (str): The measurement type of the NTP measurement. Example: nts, ntpv4, ntpv5.
        ntp_versions_to_analyze (list[str]): The NTP version to analyze.
        analyse_all_ntp_versions (bool): whether to analyze all NTP versions.
        ntp_versions_analysis_on_each_ip (bool): If you want an analysis on each IP address of the domain name.
        nts_analysis_on_each_ip (bool): If you want an analysis on each IP address of the domain name.
        ntpv5_draft (str): The draft name for NTPv5.
        custom_probes_asn (str): The custom ASN for probes.
        custom_probes_country (str): The custom country for probes.
        custom_client_ip (str): If you want to get probes close to a specific IP address.
    """
    wanted_ip_type: int = 4
    measurement_type: str = "ntpv4"  # ntpv1, ntpv2 ... ntpv5
    # NTP versions
    ntp_versions_to_analyze: list[str] = []
    analyse_all_ntp_versions: bool = True
    ntp_versions_analysis_on_each_ip: bool = False
    # NTS (by default, it is done on the server/ip you input, but not on each IP)
    nts_analysis_on_each_ip: bool = False

    ntpv5_draft: str = ""
    # custom parameters for RIPE probes
    custom_probes_asn: str = ""
    custom_probes_country: str = ""
    custom_client_ip: str = ""

    @model_validator(mode='after')
    def validate_after(self) -> Self:
        """
        Checks that the arguments are valid.
        Args:
            self (Self): Instance of the class.
        Returns:
            Self: the AdvancedSettings instance.

        Raises:
            TypeError: if the server is not a string.
            TypeError: if the flag for ipv6 measurement is not a bool.

        """
        if not isinstance(self.wanted_ip_type, int):
            raise TypeError(f"wanted_ip_type must be int, got {type(self.wanted_ip_type).__name__}")
        if not isinstance(self.measurement_type, str):
            raise TypeError(f"measurement_type must be str, got {type(self.measurement_type).__name__}")
        if not isinstance(self.analyse_all_ntp_versions, bool):
            raise TypeError(f"analyse_all_ntp_versions must be bool, got {type(self.analyse_all_ntp_versions).__name__}")
        return self