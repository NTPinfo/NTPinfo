from typing import Optional

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, CheckConstraint, JSON, SmallInteger, Boolean
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy.sql import func
from server.app.models.Base import Base


class NTPv4Measurement(Base):
    __tablename__ = "ntpv4_measurement"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ntpv_data = Column(JSON, nullable=False)


class NTPv5Measurement(Base):
    __tablename__ = "ntpv5_measurement"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    draft_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ntpv5_data = Column(JSON, nullable=False)
    analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

class NTSMeasurement(Base):
    __tablename__ = "nts_measurement"

    id_nts: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    succeeded = Column(Boolean, nullable=False, default=False)
    measurement_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=False) # ex: "ntpv4"
    nts_data = Column(JSON, nullable=True)
    analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
