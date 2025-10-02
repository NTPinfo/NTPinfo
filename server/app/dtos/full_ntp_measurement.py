from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, CheckConstraint, JSON, SmallInteger, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from server.app.models.Base import Base


class NTPv4Measurement(Base):
    __tablename__ = "ntpv4_measurement"
    id_v = Column(Integer, primary_key=True, index=True)
    ntpv_data = Column(JSON, nullable=False)


class NTPv5Measurement(Base):
    __tablename__ = "ntpv5_measurement"
    id_v5 = Column(Integer, primary_key=True, index=True)
    draft_name = Column(String, nullable=True)
    ntpv5_data = Column(JSON, nullable=False)
    analysis = Column(Text, nullable=True)

class NTSMeasurement(Base):
    __tablename__ = "nts_measurement"

    id_nts = Column(Integer, primary_key=True, autoincrement=True)
    succeeded = Column(Boolean, nullable=False, default=False)
    measurement_type = Column(String(10), nullable=False)  # "ntpv4" or "ntpv5"
    nts_data = Column(JSON, nullable=True)
    analysis = Column(Text, nullable=True)

class NTPVersions(Base):
    __tablename__ = "ntp_versions"
    id_vs = Column(Integer, primary_key=True, index=True)
    id_v4_1 = Column(Integer, ForeignKey("ntpv4_measurement.id_v"), nullable=True)
    id_v4_2 = Column(Integer, ForeignKey("ntpv4_measurement.id_v"), nullable=True)
    id_v4_3 = Column(Integer, ForeignKey("ntpv4_measurement.id_v"), nullable=True)
    id_v4_4 = Column(Integer, ForeignKey("ntpv4_measurement.id_v"), nullable=True)
    id_v5 = Column(Integer, ForeignKey("ntpv5_measurement.id_v5"), nullable=True)

    ntpv1_supported_conf = Column(SmallInteger, nullable=True)
    ntpv2_supported_conf = Column(SmallInteger, nullable=True)
    ntpv3_supported_conf = Column(SmallInteger, nullable=True)
    ntpv4_supported_conf = Column(SmallInteger, nullable=True)
    ntpv5_supported_conf = Column(SmallInteger, nullable=True)

    analysis_v1 = Column(Text, nullable=True)
    analysis_v2 = Column(Text, nullable=True)
    analysis_v3 = Column(Text, nullable=True)
    analysis_v4 = Column(Text, nullable=True)
    analysis_v5 = Column(Text, nullable=True)


class FullMeasurementIP(Base):
    __tablename__ = "full_ntp_measurement_ip"
    id_m_ip = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="pending", index=True)
    server_ip = Column(Text, nullable=False)
    created_at_time = Column(DateTime(timezone=True), server_default=func.now())
    id_nts = Column(Integer, nullable=True)
    id_vs = Column(Integer, ForeignKey("ntp_versions.id_vs"), nullable=True)
    id_ripe = Column(Integer, nullable=True)
    measurement_type = Column(String, CheckConstraint("measurement_type IN ('ntpv4','ntpv5')"))
    id_v_measurement = Column(Integer, nullable=True)
    settings = Column(JSON, nullable=True)


class FullMeasurementDN(Base):
    __tablename__ = "full_ntp_measurement_dn"
    id_m_dn = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="pending", index=True)
    server = Column(Text, nullable=False)
    created_at_time = Column(DateTime(timezone=True), server_default=func.now())
    id_nts = Column(Integer, nullable=True)
    id_vs = Column(Integer, ForeignKey("ntp_versions.id_vs"), nullable=True)
    id_ripe = Column(Integer, nullable=True)
    settings = Column(JSON, nullable=True)

    ip_measurements = relationship("FullMeasurementIP",
                                   secondary="dn_ip_link",
                                   backref="domains")


class DNIPLink(Base):
    __tablename__ = "dn_ip_link"
    id_dn = Column(Integer, ForeignKey("full_ntp_measurement_dn.id_m_dn"), primary_key=True)
    id_ip = Column(Integer, ForeignKey("full_ntp_measurement_ip.id_m_ip"), primary_key=True)
