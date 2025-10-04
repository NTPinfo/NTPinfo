from typing import Optional
from sqlalchemy.orm import Session

from server.app.dtos.full_ntp_measurement import FullMeasurementIP, NTSMeasurement, NTPVersions, NTPv5Measurement, \
    FullMeasurementDN, NTPv4Measurement


# methods to convert to JSON (dict)
def ntpv4_or_v5_measurement_to_dict(db: Session, m_id: Optional[int], m_version: Optional[str]) -> Optional[dict]:
    """
    This method converts an NTPVersions object to a dict/JSON. We need to choose in which format is the measurement.
    NTPv1, NTPv2, NTPv3, NTPv4 are in NTPv4 format, but NTPv5 has its own format.
    Args:
        db (Session): A connection to the database (we need to query some IDs)
        m_id (Optional[int]): The ID of the NTP measurement
        m_version (Optional[str]): The version of the NTP measurement
    Returns:
        Optional[dict]: The dict/JSON version or None
    """
    if m_id is None or m_version is None:
        return None
    if m_version == "ntpv5":
        m_v: Optional[NTPv5Measurement] = db.query(NTPv5Measurement).filter_by(id=m_id).first()
        return ntpv5_measurement_to_dict(m_v)
    else: # other versions will be saved in NTPv4 format
        m_v5: Optional[NTPv4Measurement] = db.query(NTPv4Measurement).filter_by(id=m_id).first()
        return ntpv4_measurement_to_dict(m_v5)

def ntpv4_measurement_to_dict(m: Optional[NTPv4Measurement]) -> Optional[dict]:
    """
    This method converts an NTPv4Measurement object to a dict/JSON. It is important to note that NTPv1 ... NTPv3 are also
    in this NTPv4Measurement format.
    Args:
        m (Optional[NTPv4Measurement]): The measurement object to convert.
    Returns:
        Optional[dict]: The dict/JSON version or None
    """
    if m is None:
        return None
    return {
        "id": m.id,
        "ntp_data": m.ntpv_data,
    }

def ntpv5_measurement_to_dict(m: Optional[NTPv5Measurement]) -> Optional[dict]:
    """
    This method converts an NTPv5Measurement object to a dict/JSON (only for NTPv5).
    Args:
        m (Optional[NTPv5Measurement]): The measurement object to convert.
    Returns:
        Optional[dict]: The dict/JSON version or None
    """
    if m is None:
        return None
    return {
        "id": m.id,
        "draft_name": m.draft_name,
        "ntpv5_analysis": m.analysis,
        "ntpv5_data": m.ntpv5_data,
    }

def nts_measurement_to_dict(m: Optional[NTSMeasurement]) -> Optional[dict]:
    """
    This method converts an NTSMeasurement object to a dict/JSON.
    Args:
        m (Optional[NTSMeasurement]): The measurement object to convert.
    Returns:
        Optional[dict]: The dict/JSON version or None
    """
    if m is None:
        return None
    return {
        "nts_id": m.id_nts,
        "nts_succeeded": m.succeeded,
        "nts_analysis": m.analysis,
        "nts_data": m.nts_data,
        "nts_measurement_version": m.measurement_type,
    }

def ntp_versions_to_dict(db: Session, m: Optional[NTPVersions]) -> Optional[dict]:
    """
    This method converts an NTPVersions object to a dict/JSON.
    Args:
        db (Session): A connection to the database (we need to query some IDs)
        m (Optional[NTPVersions]): The measurement object to convert.
    Returns:
        Optional[dict]: The dict/JSON version or None
    """
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

def full_measurement_ip_to_dict(db: Session, m: FullMeasurementIP, part_of_dn_measurement: bool=False) -> dict:
    """
    This method converts a FullMeasurementIP object to a dict/JSON. It fully takes the whole object.
    The response may be large. "part_of_dn_measurement" is used to not send again the settings, because they are the
    same as in the settings for the overall domain name. So they are redundant.
    Args:
        db (Session): A connection to the database (we need to query some IDs)
        m (FullMeasurementIP): The measurement object to convert.
        part_of_dn_measurement (bool): Whether the measurement is part of the domain name measurement or not.
    Returns:
        dict: The full dict/JSON version of the measurement.
    """
    m_nts: Optional[NTSMeasurement] = db.query(NTSMeasurement).filter_by(id_nts=m.id_nts).first()
    m_vs: Optional[NTPVersions] = db.query(NTPVersions).filter_by(id_vs=m.id_vs).first()
    ans: dict= {
        "search_id": "ip"+str(m.id_m_ip),
        "status": m.status,
        "server": m.server_ip,
        "created_at_time": m.created_at_time.isoformat() if m.created_at_time else None,
        "main_measurement": ntpv4_or_v5_measurement_to_dict(db, m.id_main_measurement, m.response_version),
        "nts": nts_measurement_to_dict(m_nts),
        "ntp_versions": ntp_versions_to_dict(db, m_vs),
        # "id_ripe": m.id_ripe, # this ID does not exist (it is null) if it was part of a domain name measurement
        "response_version": m.response_version,
        "response_error": m.response_error,
    }
    if not part_of_dn_measurement:
        ans["id_ripe"] = m.id_ripe
        ans["settings"] = m.settings if isinstance(m.settings, dict) else getattr(m.settings, "dict", lambda: m.settings)(),
    return ans

def full_measurement_dn_to_dict(db: Session, m: FullMeasurementDN) -> dict:
    """
    This method converts a FullMeasurementDN object to a dict/JSON. It fully takes the whole object.
    If this measurement has 4 full measurements on IP, then it will take all of them and return in a single large dict/JSON.
    The response may be very large (10Kb).
    It best to use after the measurement was finished (for example, when someone access this measurement through a link)
    Args:
        db (Session): A connection to the database (we need to query some IDs)
        m (FullMeasurementDN): The measurement object to convert.
    Returns:
        dict: The full dict/JSON version of the measurement.
    """
    m_nts: Optional[NTSMeasurement] = db.query(NTSMeasurement).filter_by(id_nts=m.id_nts).first()
    m_vs: Optional[NTPVersions] = db.query(NTPVersions).filter_by(id_vs=m.id_vs).first()

    return {
        "search_id": "dn" + str(m.id_m_dn),
        "status": m.status,
        "server": m.server,
        "created_at_time": m.created_at_time.isoformat() if m.created_at_time else None,
        "nts": nts_measurement_to_dict(m_nts),
        "ntp_versions": ntp_versions_to_dict(db, m_vs),
        "id_ripe": m.id_ripe,
        "response_error": m.response_error,
        "settings": m.settings if isinstance(m.settings, dict) else getattr(m.settings, "dict", lambda: m.settings)(),
        "ip_measurements": [
            full_measurement_ip_to_dict(db, m_ip, True) for m_ip in m.ip_measurements
        ]
    }

# here are the methods that get partial results. It does not search deeper to translate IDs. You will need to query them separately.
# This is in order to improve the performance.

def partial_measurement_ip_to_dict(db: Session, m: FullMeasurementIP, part_of_dn_measurement: bool=False) -> dict:
    """
    This method converts a FullMeasurementIP object to a dict/JSON, but it does not fully take the whole object.
    It just takes the main results and then for the other parts, it provides the IDs to you.
    This method is efficient, because there would not be so much redundant data sent over the network.
    Args:
        db (Session): A connection to the database (we need to query some IDs)
        m (FullMeasurementIP): The measurement object to convert.
        part_of_dn_measurement (bool): Whether the measurement is part of the domain name measurement or not.
    Returns:
        dict: The partial dict/JSON version of the measurement.
    """
    m_nts: Optional[NTSMeasurement] = db.query(NTSMeasurement).filter_by(id_nts=m.id_nts).first()
    ans: dict = {
        "search_id": "ip"+str(m.id_m_ip),
        "status": m.status,
        "server": m.server_ip,
        "created_at_time": m.created_at_time.isoformat() if m.created_at_time else None,
        "main_measurement": ntpv4_or_v5_measurement_to_dict(db, m.id_main_measurement, m.response_version),
        "nts": nts_measurement_to_dict(m_nts),
        "ntp_versions_id": m.id_vs,   # here it is just the ID
        "response_version": m.response_version,
        "response_error": m.response_error,
    }
    if not part_of_dn_measurement:
        ans["id_ripe"] = m.id_ripe
        ans["settings"] = m.settings if isinstance(m.settings, dict) else getattr(m.settings, "dict", lambda: m.settings)(),
    return ans

def partial_measurement_dn_to_dict(db: Session, m: FullMeasurementDN) -> dict:
    """
    This method converts a FullMeasurementDN object to a dict/JSON, but it does not fully take the whole object.
    It just takes the main results and then for the other parts, it provides the IDs to you.
    This method is efficient, because there would not be so much redundant data sent over the network.
    Args:
        db (Session): A connection to the database (we need to query some IDs)
        m (FullMeasurementDN): The measurement object to convert.
    Returns:
        dict: The partial dict/JSON version of the measurement.
    """
    m_nts: Optional[NTSMeasurement] = db.query(NTSMeasurement).filter_by(id_nts=m.id_nts).first()

    return {
        "search_id": "dn" + str(m.id_m_dn),
        "status": m.status,
        "server": m.server,
        "created_at_time": m.created_at_time.isoformat() if m.created_at_time else None,
        "nts": nts_measurement_to_dict(m_nts), # this is too small to only send the id.
        "ntp_versions_id": m.id_vs,   # here it is just the ID
        "id_ripe": m.id_ripe,
        "response_error": m.response_error,
        "settings": m.settings if isinstance(m.settings, dict) else getattr(m.settings, "dict", lambda: m.settings)(),
        "ip_measurements_ids": [
            "ip"+str(m_ip.id_m_ip) for m_ip in m.ip_measurements  # a list with the measurements_ip IDs that have been finished!
        ]
    }