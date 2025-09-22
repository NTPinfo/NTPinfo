from pydantic import BaseModel, Field, model_validator
from typing import Self, Optional


class MeasurementRequest(BaseModel):
    """
    Data model for an NTP measurement request.

    Attributes:
        server (str): The IP address or domain name of the NTP server to be measured.
        ipv6_measurement (bool): True if the type of IPs that we want to measure is IPv6. False otherwise.
    """
    server: str
    ipv6_measurement: bool = False

    # ntpv5_draft: Optional[str] = None #it will look like this

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
