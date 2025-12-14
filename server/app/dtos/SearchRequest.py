from datetime import datetime
from pydantic import BaseModel, Field, model_validator
from typing import Self, Optional


class SearchRequest(BaseModel):
    """
    Data model for an NTP measurement request.
    At least one of these attributes: server, measurement_id must not be None.
    If one of date_range_start or date_range_end is not specified, an infinite boundary applies.

    Attributes:
        server (Optional[str]): The IP address or domain name of the NTP server(s) that we search for.
        measurement_id (Optional[str]): The measurement ID of the measurement (ex: ip234 or dn73).
        measurement_type (Optional[str]): The measurement type of the NTP measurement. Example: nts, ntpv4, ntpv5.
        ntpv5_draft (Optional[str]): The draft name for NTPv5.
        reference_id (Optional[str]): The reference field of the NTP measurement
        wanted_ip_type (Optional[int]): The wanted IP address type (4 ot 6) in case the "server" is a domain name.
        stratum (Optional[str]): Search for measurements with this stratum. (use "4+" for stratum >3)
        asn (Optional[str]): The ASN of the NTP server(s) that we search for.
        country_code (Optional[str]): The country code of the NTP server(s) that we search for.
        nts_support (Optional[bool]): Search for measurements which support NTS.
        ntp_versions_supported (Optional[list[str]]): Search for measurements which support these NTP versions.
        offset_mins (Optional[int]): Search for measurements with this minimum offset in seconds.
        offset_max (Optional[int]): Search for measurements with this maximum offset in seconds.
        date_range_start (Optional[datetime]): Search for measurements after this date.
        date_range_end (Optional[datetime]): Search for measurements before this date.
    """
    server: Optional[str] = None
    measurement_id: Optional[str] = None #if this value is provided, then we ignore all other values.
    measurement_type: Optional[str] = None

    ntpv5_draft: Optional[str] = None
    reference_id: Optional[str] = None
    wanted_ip_type: Optional[int] = None

    stratum: Optional[str] = None #use "4+" for stratum>=4
    asn: Optional[str] = None
    country_code: Optional[str] = None

    nts_support: Optional[bool] = None
    ntp_versions_supported: Optional[list[str]] = None

    offset_mins: Optional[float] = None
    offset_max: Optional[float] = None

    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None