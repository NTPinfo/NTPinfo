from typing import Optional

from server.app.dtos.full_ntp_measurement import FullMeasurementIP, NTSMeasurement, NTPVersions, NTPv5Measurement, \
    FullMeasurementDN, NTPv4Measurement


# methods to convert to JSON (dict)
def ntpv4_or_v5_measurement_to_dict(db, m_id: Optional[int], m_version: Optional[str]):
    if m_id is None or m_version is None:
        return None
    if m_version == "ntpv5":
        m: Optional[NTPv5Measurement] = db.query(NTPv5Measurement).filter_by(id_v5=m_id).first()
        return ntpv5_measurement_to_dict(m)
    else:
        m: Optional[NTPv4Measurement] = db.query(NTPv4Measurement).filter_by(id_v=m_id).first()
        return ntpv4_measurement_to_dict(m)

def ntpv4_measurement_to_dict(m: Optional[NTPv4Measurement]):
    if m is None:
        return None
    return {
        "id": m.id_v,
        "ntp_data": m.ntpv_data,
    }

def ntpv5_measurement_to_dict(m: Optional[NTPv5Measurement]):
    if m is None:
        return None
    return {
        "id": m.id_v5,
        "draft_name": m.draft_name,
        "ntpv5_analysis": m.analysis,
        "ntpv5_data": m.ntpv5_data,
    }

def nts_measurement_to_dict(m: Optional[NTSMeasurement]):
    if m is None:
        return None
    return {
        "nts_id": m.id_nts,
        "nts_succeeded": m.succeeded,
        "nts_analysis": m.analysis,
        "nts_data": m.nts_data,
        "nts_measurement_version": m.measurement_type,
    }

def ntp_versions_to_dict(db, m: Optional[NTPVersions]):
    if m is None:
        return None
    ans: dict = {
        "ntpv1_supported_conf": m.ntpv1_supported_conf,
        "ntpv1_analysis": m.analysis_v1,
        "ntpv1_response_version": m.ntpv1_response_version,
        "ntpv1_data": ntpv4_or_v5_measurement_to_dict(db, m.id_v4_1, m.ntpv1_response_version),

        "ntpv2_supported_conf": m.ntpv2_supported_conf,
        "ntpv2_analysis": m.analysis_v2,
        "ntpv2_response_version": m.ntpv2_response_version,
        "ntpv2_data": ntpv4_or_v5_measurement_to_dict(db, m.id_v4_2, m.ntpv2_response_version),

        "ntpv3_supported_conf": m.ntpv3_supported_conf,
        "ntpv3_analysis": m.analysis_v3,
        "ntpv3_response_version": m.ntpv3_response_version,
        "ntpv3_data": ntpv4_or_v5_measurement_to_dict(db, m.id_v4_3, m.ntpv3_response_version),

        "ntpv4_supported_conf": m.ntpv4_supported_conf,
        "ntpv4_analysis": m.analysis_v4,
        "ntpv4_response_version": m.ntpv4_response_version,
        "ntpv4_data": ntpv4_or_v5_measurement_to_dict(db, m.id_v4_4, m.ntpv4_response_version),

        "ntpv5_supported_conf": m.ntpv5_supported_conf,
        "ntpv5_analysis": m.analysis_v5,
        "ntpv5_response_version": m.ntpv5_response_version,
        "ntpv5_data": ntpv4_or_v5_measurement_to_dict(db, m.id_v5, m.ntpv5_response_version),
    }
    return ans

def full_measurement_ip_to_dict(db, m: FullMeasurementIP) -> dict:
    m_nts: Optional[NTSMeasurement] = db.query(NTSMeasurement).filter_by(id_nts=m.id_nts).first()
    m_vs: Optional[NTPVersions] = db.query(NTPVersions).filter_by(id_vs=m.id_vs).first()
    return {
        "search_id": "ip"+str(m.id_m_ip),
        "status": m.status,
        "server": m.server_ip,
        "created_at_time": m.created_at_time.isoformat() if m.created_at_time else None,
        "main_measurement": ntpv4_or_v5_measurement_to_dict(db, m.id_v_measurement, m.response_version),
        "nts": nts_measurement_to_dict(m_nts),
        "ntp_versions": ntp_versions_to_dict(db, m_vs),
        "id_ripe": m.id_ripe,
        "response_version": m.response_version,
        "response_error": m.response_error,
        "settings": m.settings if isinstance(m.settings, dict) else getattr(m.settings, "dict", lambda: m.settings)(),
    }
def full_measurement_dn_to_dict(db, m: FullMeasurementDN) -> dict:
    m_nts: Optional[NTSMeasurement] = db.query(NTSMeasurement).filter_by(id_nts=m.id_nts).first()
    m_vs: Optional[NTPVersions] = db.query(NTPVersions).filter_by(id_vs=m.id_vs).first()

    return {
        "search_id": "ip" + str(m.id_m_dn),
        "status": m.status,
        "server": m.server,
        "created_at_time": m.created_at_time.isoformat() if m.created_at_time else None,
        "nts": nts_measurement_to_dict(m_nts),
        "ntp_versions": ntp_versions_to_dict(db, m_vs),
        "id_ripe": m.id_ripe,
        "response_error": m.response_error,
        "settings": m.settings if isinstance(m.settings, dict) else getattr(m.settings, "dict", lambda: m.settings)(),
        "ip_measurements": [
            full_measurement_ip_to_dict(db, m_ip) for m_ip in m.ip_measurements
        ]
    }

# def get_full_measurement_ip_ids_for_dn(db, dn_id: int):
#     dn = db.query(FullMeasurementDN).filter(FullMeasurementDN.id_m_dn == dn_id).first()
#     if not dn:
#         return []
#     return dn.ip_measurements