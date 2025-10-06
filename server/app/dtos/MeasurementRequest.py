from pydantic import BaseModel, Field, model_validator
from typing import Self, Optional


class MeasurementRequest(BaseModel):
    """
    Data model for an NTP measurement request.

    Attributes:
        server (str): The IP address or domain name of the NTP server to be measured.
        ipv6_measurement (bool): True if the type of IPs that we want to measure is IPv6. False otherwise.
        wanted_ip_type (Optional[int]): The wanted IP address type (4 ot 6) in case the "server" is a domain name.
        measurement_type (Optional[str]): The measurement type of the NTP measurement. Example: nts, ntpv4, ntpv5.
        ntp_versions_to_analyze (Optional[list[str]]): The NTP version to analyze.
        analyse_all_ntp_versions (Optional[bool]): whether to analyze all NTP versions.
        ntp_versions_analysis_on_each_ip (Optional[bool]): If you want an analysis on each IP address of the domain name.
        nts_analysis_on_each_ip (Optional[bool]): If you want an analysis on each IP address of the domain name.
        ntpv5_draft (Optional[str]): The draft name for NTPv5.
        custom_probes_asn (Optional[str]): The custom ASN for probes.
        custom_probes_country (Optional[str]): The custom country for probes.
        custom_client_ip (Optional[str]): If you want to get probes close to a specific IP address.
    """
    server: str
    ipv6_measurement: bool = False
    wanted_ip_type: int = 4
    measurement_type: Optional[str] = None
    # NTP versions
    ntp_versions_to_analyze: Optional[list[str]] = None
    analyse_all_ntp_versions: Optional[bool] = None
    ntp_versions_analysis_on_each_ip: Optional[bool] = None
    nts_analysis_on_each_ip: Optional[bool] = None

    ntpv5_draft: Optional[str] = None
    # custom parameters for RIPE probes
    custom_probes_asn: Optional[str] = None
    custom_probes_country: Optional[str] = None
    custom_client_ip: Optional[str] = None


    @model_validator(mode='after')
    def validate_after(self) -> Self:
        """
        Checks that the server is a string.
        Args:
            self (Self): Instance of the class.
        Returns:
            Self: the MeasurementRequest instance.

        Raises:
            TypeError: if the server is not a string.
            TypeError: if the flag for ipv6 measurement is not a bool.

        """
        if not isinstance(self.server, str):
            raise TypeError(f"server must be str, got {type(self.server).__name__}")
        if not isinstance(self.ipv6_measurement, bool):
            raise TypeError(f"Flag for ipv6 measurement must be bool, got {type(self.ipv6_measurement).__name__}")
        return self
