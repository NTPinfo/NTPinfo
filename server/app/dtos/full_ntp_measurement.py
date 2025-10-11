from typing import Optional

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, CheckConstraint, JSON, SmallInteger, \
    Boolean, BigInteger, Double, Numeric
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy.sql import func
from server.app.models.Base import Base


class NTPv4Measurement(Base):
    __tablename__ = "ntpv4_measurement"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    host: Mapped[str] = mapped_column(Text, nullable=False)
    measured_server_ip: Mapped[str] = mapped_column(String(45), nullable=False)

    offset: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    rtt: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    stratum: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    poll: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)

    client_sent_time: Mapped[Optional[str]] = mapped_column(Numeric, nullable=True)
    server_recv_time: Mapped[Optional[str]] = mapped_column(Numeric, nullable=True)
    server_sent_time: Mapped[Optional[str]] = mapped_column(Numeric, nullable=True)
    client_recv_time: Mapped[Optional[str]] = mapped_column(Numeric, nullable=True)
    ref_time: Mapped[Optional[str]] = mapped_column(Numeric, nullable=True)

    leap: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    mode: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    version: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)

    precision: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    root_delay: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    root_disp: Mapped[Optional[float]] = mapped_column(Double, nullable=True)

    ref_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    extensions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    @classmethod
    def from_dict(cls, data: dict, analysis: Optional[str] = None, host: Optional[str] = None,
                  ip: Optional[str] = None) -> "NTPv4Measurement":
        """
        It creates a new NTPv4Measurement object from the given JSON data. The optional fields are used
        in case the dict does not contain them.
        Args:
            data (dict): JSON data
            analysis (Optional[str]): The analysis of the results
            host (Optional[str]): The host of the server (domain name, but can also be IP address)
            ip (Optional[str]): The measured server ip
        Returns:
            NTPv4Measurement: NTPv4Measurement object
        """
        return cls(
            analysis=data.get("analysis", analysis),
            host=data.get("host", host),
            measured_server_ip=data.get("measured_server_ip", ip),

            offset=data.get("offset"),
            rtt=data.get("rtt"),
            stratum=data.get("stratum"),
            poll=data.get("poll"),

            client_sent_time=data.get("orig_timestamp"), # careful about the notations
            server_recv_time=data.get("recv_timestamp"),
            server_sent_time=data.get("tx_timestamp"),
            client_recv_time=data.get("client_recv_time"),
            ref_time=data.get("ref_timestamp"),

            leap=data.get("leap"),
            mode=data.get("mode"),
            version=data.get("version"),

            precision=data.get("precision"),
            root_delay=data.get("root_delay"),
            root_disp=data.get("root_disp"),
            ref_name=data.get("ref_id"),

            extensions=data.get("extensions")
        )


class NTPv5Measurement(Base):
    __tablename__ = "ntpv5_measurement"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    draft_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    host: Mapped[str] = mapped_column(Text, nullable=False)
    measured_server_ip: Mapped[str] = mapped_column(String(45), nullable=False)

    offset: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    rtt: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    stratum: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    poll: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)

    client_sent_time: Mapped[Optional[str]] = mapped_column(Numeric, nullable=True)
    server_recv_time: Mapped[Optional[str]] = mapped_column(Numeric, nullable=True)
    server_sent_time: Mapped[Optional[str]] = mapped_column(Numeric, nullable=True)
    client_recv_time: Mapped[Optional[str]] = mapped_column(Numeric, nullable=True)

    client_cookie: Mapped[Optional[str]] = mapped_column(Numeric, nullable=True)
    server_cookie: Mapped[Optional[str]] = mapped_column(Numeric, nullable=True)

    leap: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    mode: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    version: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)

    precision: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    root_delay: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    root_disp: Mapped[Optional[float]] = mapped_column(Double, nullable=True)

    timescale: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    era: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    flags_raw: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    flags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    extensions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    @classmethod
    def from_dict(cls, data: dict, analysis: Optional[str]=None, host: Optional[str]=None,
                  ip: Optional[str]=None) -> "NTPv5Measurement":
        """
        It creates a new NTPv5Measurement object from the given JSON data. The optional fields are used
        in case the dict does not contain them.
        Args:
            data (dict): JSON data
            analysis (Optional[str]): The analysis of the results
            host (Optional[str]): The host of the server (domain name, but can also be IP address)
            ip (Optional[str]): The measured server ip
        Returns:
            NTPv5Measurement: NTPv5Measurement object
        """
        return cls(

            draft_name=data.get("draft_name"),
            analysis=data.get("analysis", analysis),
            host=data.get("host", host),
            measured_server_ip=data.get("measured_server_ip", ip),

            offset=data.get("offset"),
            rtt=data.get("rtt"),
            stratum=data.get("stratum"),
            poll=data.get("poll"),

            client_sent_time=data.get("orig_timestamp"),
            server_recv_time=data.get("recv_timestamp"),
            server_sent_time=data.get("tx_timestamp"),
            client_recv_time=data.get("client_recv_time"),

            client_cookie=data.get("client_cookie"),
            server_cookie=data.get("server_cookie"),

            leap=data.get("leap"),
            mode=data.get("mode"),
            version=data.get("version"),

            precision=data.get("precision"),
            root_delay=data.get("root_delay"),
            root_disp=data.get("root_disp"),

            timescale=data.get("timescale"),
            era=data.get("era"),
            flags_raw=data.get("flags_raw"),
            flags=data.get("flags_decoded"),  # here you could add a better logic in future

            extensions=data.get("extensions")
        )

class NTSMeasurement(Base):
    __tablename__ = "nts_measurement"

    id_nts: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    succeeded = Column(Boolean, nullable=False, default=False)
    analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # measurement_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=False) # ex: "ntpv4"
    # nts_data = Column(JSON, nullable=True)
    host: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    measured_server_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    measured_server_port: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)

    offset: Mapped[Optional[float]] = mapped_column("offset", Double, nullable=True)  # column name "offset"
    rtt: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    kiss_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    stratum: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    poll: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    measurement_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    client_sent_time: Mapped[Optional[int]] = mapped_column(Numeric, nullable=True)
    server_recv_time: Mapped[Optional[int]] = mapped_column(Numeric, nullable=True)
    server_sent_time: Mapped[Optional[int]] = mapped_column(Numeric, nullable=True)
    client_recv_time: Mapped[Optional[int]] = mapped_column(Numeric, nullable=True)
    ref_time: Mapped[Optional[int]] = mapped_column(Numeric, nullable=True)

    leap: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    mode: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    version: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)

    min_error: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    precision: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    root_delay: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    root_disp: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    root_dist: Mapped[Optional[float]] = mapped_column(Double, nullable=True)

    ref_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ref_id_raw: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    @classmethod
    def from_dict(cls, data: dict) -> "NTSMeasurement":
        """
        It creates a new NTSMeasurement object from the given JSON data.
        Args:
            data (dict): JSON data
        Returns:
            NTSMeasurement: NTSMeasurement object
        """
        return cls(
            succeeded=bool(data.get("NTS succeeded", False)),
            analysis=data.get("NTS analysis", ""),

            host=data.get("Host"),
            measured_server_ip=data.get("Measured server IP"),
            measured_server_port=(int(data["Measured server port"]) if data.get("Measured server port") else None),

            offset=data.get("offset"),
            rtt=data.get("rtt"),
            kiss_code=data.get("kissCode"),
            stratum=data.get("stratum"),
            poll=data.get("poll"),
            measurement_type=data.get("ntpv4"), # currently we only support NTS with ntpv4

            client_sent_time=data.get("client_sent_time"),
            server_recv_time=data.get("server_recv_time"),
            server_sent_time=data.get("server_sent_time"),
            client_recv_time=data.get("client_recv_time"),
            ref_time=data.get("ref_time"),

            leap=data.get("leap"),
            mode=data.get("mode"),
            version=data.get("version"),

            min_error=data.get("minError"),
            precision=data.get("precision"),
            root_delay=data.get("root_delay"),
            root_disp=data.get("root_disp"),
            root_dist=data.get("root_dist"),

            ref_id=data.get("ref_id"),
            ref_id_raw=data.get("ref_id_raw"),
        )
class NTPVersions(Base):
    __tablename__ = "ntp_versions"
    id_vs: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    id_v4_1: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ntpv4_measurement.id"), nullable=True)
    id_v4_2: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ntpv4_measurement.id"), nullable=True)
    id_v4_3: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ntpv4_measurement.id"), nullable=True)
    id_v4_4: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ntpv4_measurement.id"), nullable=True)
    id_v5: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ntpv5_measurement.id"), nullable=True)

    ntpv1_response_version: Mapped[Optional[str]] = mapped_column(String(7), nullable=True) # ex: ntpv1
    ntpv2_response_version: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    ntpv3_response_version: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    ntpv4_response_version: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    ntpv5_response_version: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)

    ntpv1_supported_conf: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True) # ex: 0 or 100
    ntpv2_supported_conf: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    ntpv3_supported_conf: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    ntpv4_supported_conf: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    ntpv5_supported_conf: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)

    ntpv1_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ntpv2_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ntpv3_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ntpv4_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ntpv5_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class FullMeasurementIP(Base):
    __tablename__ = "full_ntp_measurement_ip"
    id_m_ip: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    server_ip: Mapped[str] = mapped_column(Text, nullable=False)
    created_at_time = Column(DateTime(timezone=True), server_default=func.now())
    id_nts: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    id_vs: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ntp_versions.id_vs"), nullable=True)
    id_ripe: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_version: Mapped[Optional[str]] = mapped_column(String(12), nullable=True) # the ntp version
    ripe_error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    response_error: Mapped[Optional[str]] = mapped_column(String, nullable=True) # if there is an error when performing the main measurement
    id_main_measurement: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) #if there was an error, this is null
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # it will contain the requested versions


class FullMeasurementDN(Base):
    __tablename__ = "full_ntp_measurement_dn"
    id_m_dn: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    server: Mapped[str] = mapped_column(Text, nullable=False)
    created_at_time = Column(DateTime(timezone=True), server_default=func.now())
    id_nts: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    id_vs: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ntp_versions.id_vs"), nullable=True)
    id_ripe: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ripe_error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    response_error: Mapped[Optional[str]] = mapped_column(String, nullable=True) # if there is an error with the input
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    ip_measurements = relationship("FullMeasurementIP",
                                   secondary="dn_ip_link",
                                   backref="domains")


class DNIPLink(Base):
    __tablename__ = "dn_ip_link"
    id_dn = Column(Integer, ForeignKey("full_ntp_measurement_dn.id_m_dn"), primary_key=True)
    id_ip = Column(Integer, ForeignKey("full_ntp_measurement_ip.id_m_ip"), primary_key=True)
