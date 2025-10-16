import pprint
import time

from sqlalchemy.orm import Session

from server.app.utils.location_resolver import get_country_for_ip, get_coordinates_for_ip
from server.app.utils.validate import sanitize_string
from server.app.dtos.MeasurementRequest import MeasurementRequest
from server.app.utils.analyze_ntp_versions import run_tool_on_ntp_version
from server.app.dtos.full_ntp_measurement import NTSMeasurement, FullMeasurementDN, NTPv4Measurement, NTPv5Measurement, \
    put_fields_ntpv4, put_fields_ntpv5, put_fields_4_or_5, NTPv4ServerInfo, NTPv5ServerInfo
from server.app.dtos.AdvancedSettings import AdvancedSettings
from server.app.utils.nts_check import perform_nts_measurement_ip, perform_nts_measurement_domain_name
from server.app.dtos.full_ntp_measurement import FullMeasurementIP, NTPVersions
from server.app.utils.ip_utils import get_ip_family, ref_id_to_ip_or_name
from server.app.utils.location_resolver import get_asn_for_ip
from server.app.utils.ip_utils import is_this_ip_anycast
from server.app.utils.perform_measurements import perform_ntp_measurement_domain_name_list, \
    analyze_supported_ntp_versions
from server.app.utils.ip_utils import get_server_ip
from server.app.models.CustomError import InputError, RipeMeasurementError, DNSError
from server.app.utils.load_config_data import get_nr_of_measurements_for_jitter, \
    get_right_ntp_nts_binary_tool_for_your_os
from server.app.utils.calculations import calculate_jitter_from_measurements, human_date_to_ntp_precise_time
from server.app.utils.ip_utils import ip_to_str
from typing import Any, Optional, Tuple

from server.app.utils.ripe_fetch_data import check_all_measurements_scheduled
from server.app.utils.perform_measurements import perform_ripe_measurement_domain_name
from server.app.utils.validate import ensure_utc, is_ip_address, parse_ip
from server.app.services.NtpCalculator import NtpCalculator
from server.app.utils.perform_measurements import perform_ntp_measurement_ip, \
    perform_ripe_measurement_ip
from datetime import datetime
from server.app.dtos.ProbeData import ServerLocation
from server.app.dtos.RipeMeasurement import RipeMeasurement
from server.app.utils.ripe_fetch_data import parse_data_from_ripe_measurement, get_data_from_ripe_measurement
from server.app.db.db_interaction import insert_measurement
from server.app.db.db_interaction import get_measurements_timestamps_ip, get_measurements_timestamps_dn
from server.app.dtos.NtpMeasurement import NtpMeasurement


def get_format(measurement: NtpMeasurement, jitter: Optional[float] = None,
               nr_jitter_measurements: int = get_nr_of_measurements_for_jitter()) -> dict[str, Any]:
    """
    Format an NTP measurement object into a dictionary suitable for JSON serialization.

    Args:
        measurement (NtpMeasurement): An object representing the NTP measurement result
        jitter (Optional[float]): Optional jitter value if multiple measurements are performed
        nr_jitter_measurements (int): The number of measurements used in the jitter calculation

    Returns:
        dict: A dictionary containing key measurement details like this:
            - Server info (ntp version, IP, name, reference IP, reference)
            - Timestamps (client sent time, server receive time, server sent time, client receive time)
            - Measurement metrics (offset, delay, stratum, precision, reachability)
            - Extra details (root delay, last sync time, leap indicator)
    """
    return {
        "ntp_version": measurement.server_info.ntp_version,
        "vantage_point_ip": ip_to_str(measurement.vantage_point_ip),
        "ntp_server_ip": ip_to_str(measurement.server_info.ntp_server_ip),
        "ntp_server_name": measurement.server_info.ntp_server_name,
        "ntp_server_location": {
            "ip_is_anycast": is_this_ip_anycast(ip_to_str(measurement.server_info.ntp_server_ip)),
            "country_code": measurement.server_info.ntp_server_location.country_code,
            "coordinates": measurement.server_info.ntp_server_location.coordinates
        },
        "ntp_server_ref_parent_ip": ip_to_str(measurement.server_info.ntp_server_ref_parent_ip),
        "ref_name": measurement.server_info.ref_name,

        "client_sent_time": {
            "seconds": measurement.timestamps.client_sent_time.seconds,
            "fraction": measurement.timestamps.client_sent_time.fraction
        },
        "server_recv_time": {
            "seconds": measurement.timestamps.server_recv_time.seconds,
            "fraction": measurement.timestamps.server_recv_time.fraction
        },
        "server_sent_time": {
            "seconds": measurement.timestamps.server_sent_time.seconds,
            "fraction": measurement.timestamps.server_sent_time.fraction
        },
        "client_recv_time": {
            "seconds": measurement.timestamps.client_recv_time.seconds,
            "fraction": measurement.timestamps.client_recv_time.fraction
        },

        "offset": measurement.main_details.offset,
        "rtt": measurement.main_details.rtt,
        "stratum": measurement.main_details.stratum,
        "precision": measurement.main_details.precision,
        "reachability": measurement.main_details.reachability,

        "root_delay": NtpCalculator.calculate_float_time(measurement.extra_details.root_delay),
        "poll": measurement.extra_details.poll,
        "root_dispersion": NtpCalculator.calculate_float_time(measurement.extra_details.root_dispersion),
        "asn_ntp_server": get_asn_for_ip(str(measurement.server_info.ntp_server_ip)),
        "ntp_last_sync_time": {
            "seconds": measurement.extra_details.ntp_last_sync_time.seconds,
            "fraction": measurement.extra_details.ntp_last_sync_time.fraction
        },
        # if it has value = 3 => invalid
        "leap": measurement.extra_details.leap,
        # if the server has multiple IPs addresses we should show them to the client
        "jitter": jitter,
        "nr_measurements_jitter": nr_jitter_measurements
    }


def get_ripe_format(measurement: RipeMeasurement) -> dict[str, Any]:
    """
        Converts a RipeMeasurement object into a standardized dictionary format.

        This function extracts relevant information from the provided RipeMeasurement
        instance—including NTP server info, probe data, timing details, and measurement
        results—and formats it as a plain dictionary.

        Args:
            measurement (RipeMeasurement): The parsed measurement object containing NTP and probe data

        Returns:
            dict[str, Any]:
                A dictionary containing structured measurement data. Keys include:
                - NTP Server info (ntp version, ripe measurement id, IP, name, ref id)
                - Probe data (probe address, probe id in RIPE Atlas, probe location, time to result)
                - Measurement metrics (stratum, poll, precision, root delay, root dispersion, reachability)
                - NTP measurement data (rtt, offset, timestamps)
    """
    probe_location: Optional[ServerLocation] = measurement.probe_data.probe_location
    # this code regarding ref_id is because we need to consider IPv6 cases (M5 hashes involved)
    ref_id_str: str | None = "NO REFERENCE"
    try:
        ref_ip, ref_text = ref_id_to_ip_or_name(int(measurement.ref_id), measurement.ntp_measurement.main_details.stratum,
                                          get_ip_family(ip_to_str(measurement.ntp_measurement.server_info.ntp_server_ip)))
        if ref_ip is not None:
            ref_id_str = ip_to_str(ref_ip)
        elif ref_text is not None:
            ref_id_str = ref_text
    except Exception as e: #if ref_id could not be converted to an integer (ex: it was already a str)
        ref_id_str = measurement.ref_id
    return {
        "ntp_version": measurement.ntp_measurement.server_info.ntp_version,
        "vantage_point_ip": ip_to_str(measurement.ntp_measurement.vantage_point_ip),
        "ripe_measurement_id": measurement.measurement_id,
        "ntp_server_ip": ip_to_str(measurement.ntp_measurement.server_info.ntp_server_ip),
        "ntp_server_name": measurement.ntp_measurement.server_info.ntp_server_name,
        "ntp_server_location": {
            "ip_is_anycast": is_this_ip_anycast(ip_to_str(measurement.ntp_measurement.server_info.ntp_server_ip)),
            "country_code": measurement.ntp_measurement.server_info.ntp_server_location.country_code,
            "coordinates": measurement.ntp_measurement.server_info.ntp_server_location.coordinates
        },
        "probe_addr": {
            "ipv4": ip_to_str(measurement.probe_data.probe_addr[0]),
            "ipv6": ip_to_str(measurement.probe_data.probe_addr[1])
        },
        "probe_id": str(measurement.probe_data.probe_id),
        "probe_location": {
            "country_code": probe_location.country_code if probe_location else "UNKNOWN",
            "coordinates": probe_location.coordinates if probe_location else (0.0, 0.0)
        },
        "time_to_result": measurement.time_to_result,
        "stratum": measurement.ntp_measurement.main_details.stratum,
        "poll": measurement.ntp_measurement.extra_details.poll,
        "precision": measurement.ntp_measurement.main_details.precision,
        "root_delay": NtpCalculator.calculate_float_time(measurement.ntp_measurement.extra_details.root_delay),
        "root_dispersion": NtpCalculator.calculate_float_time(
            measurement.ntp_measurement.extra_details.root_dispersion),
        "asn_ntp_server": get_asn_for_ip(str(measurement.ntp_measurement.server_info.ntp_server_ip)),
        "ref_id": ref_id_str,
        "result": [
            {
                "client_sent_time": {
                    "seconds": measurement.ntp_measurement.timestamps.client_sent_time.seconds,
                    "fraction": measurement.ntp_measurement.timestamps.client_sent_time.fraction
                },
                "server_recv_time": {
                    "seconds": measurement.ntp_measurement.timestamps.server_recv_time.seconds,
                    "fraction": measurement.ntp_measurement.timestamps.server_recv_time.fraction
                },
                "server_sent_time": {
                    "seconds": measurement.ntp_measurement.timestamps.server_sent_time.seconds,
                    "fraction": measurement.ntp_measurement.timestamps.server_sent_time.fraction
                },
                "client_recv_time": {
                    "seconds": measurement.ntp_measurement.timestamps.client_recv_time.seconds,
                    "fraction": measurement.ntp_measurement.timestamps.client_recv_time.fraction
                },
                "rtt": measurement.ntp_measurement.main_details.rtt,
                "offset": measurement.ntp_measurement.main_details.offset
            }
        ]
    }


def override_desired_ip_type_if_input_is_ip(target_server: str, wanted_ip_type: int) -> int:
    """
    If the target server input is IP, then we want to perform its IP type measurements.
    Only for domain names, "wanted_ip_type" is considered. Otherwise, it is ignored.

    Args:
        target_server (str): The server we want to measure (domain name or IP address)
        wanted_ip_type (int): The IP type the user said they wanted to measure.

    Returns:
        int: The IP type of the server in case the server input is IP, otherwise the wanted_ip_type unmodified.
    """
    if is_ip_address(target_server) == "ipv4":
        return 4
    elif is_ip_address(target_server) == "ipv6":
        return 6
    return wanted_ip_type

def measure(server: str, wanted_ip_type: int, session: Session, client_ip: Optional[str] = None,
            measurement_no: int = get_nr_of_measurements_for_jitter()) -> list[tuple[
    NtpMeasurement, float, int]] | None:
    """
    Performs an NTP measurement for a given server (IP or domain name) and stores the result in the database.

    This function determines whether the input is an IP address or a domain name,
    then performs an NTP measurement using the appropriate method. The result is inserted
    into the database and returned.

    Args:
        server (str): A string representing either an IPv4/IPv6 address or a domain name.
        wanted_ip_type (int): The IP type that we want to measure. Used for domain names.
        session (Session): The currently active database session.
        client_ip (Optional[str]): The client IP or None if it was not provided.
        measurement_no (int): How many extra measurements to perform if the jitter_flag is True.

    Returns:
        list[tuple[NtpMeasurement, float, int]] | None:
            - A list of pairs with a populated `NtpMeasurement` object if the measurement is successful, and the jitter.
            - `None` if an exception occurs during the measurement process.

    Raises:
        DNSError: If the domain name is invalid, or it could not be resolved.

    Notes:
        - If the server string is empty or improperly formatted, this may raise exceptions internally,
          which are caught and logged to stdout.
        - This function modifies persistent state by inserting a measurement into the database.
    """
    try:
        if is_ip_address(server) is not None:
            m = perform_ntp_measurement_ip(server)
            if m is not None:
                jitter = 0.0
                nr_jitter_measurements = 0
                insert_measurement(m, session)
                result = calculate_jitter_from_measurements(session, m, measurement_no)
                # if result is not None:
                jitter, nr_jitter_measurements = result
                return [(m, jitter, nr_jitter_measurements)]
            # the measurement failed
            print("The ntp server " + server + " is not responding.")
            return None
        else:
            measurements: Optional[list[NtpMeasurement]] = perform_ntp_measurement_domain_name_list(server,
                                                                                                    client_ip, wanted_ip_type)
            if measurements is not None:
                m_results = []
                for m in measurements:
                    if str(m.server_info.ntp_server_ref_parent_ip) == "0.0.0.0":
                        m_results.append((m, 0.0, 1))
                        continue
                    jitter = 0.0
                    nr_jitter_measurements = 0
                    insert_measurement(m, session)
                    result = calculate_jitter_from_measurements(session, m, measurement_no)
                    # if result is not None:
                    jitter, nr_jitter_measurements = result
                    m_results.append((m, jitter, nr_jitter_measurements))
                return m_results
            print("The ntp server " + server + " is not responding.")
            return None
    except DNSError as e:
        print("Performing measurement error message:", e)
        raise e
    except Exception as e:
        print("Performing measurement error message:", e)
        return None

def check_and_get_settings(input_settings: MeasurementRequest) -> AdvancedSettings:
    """
    This method takes the parameters that the client inputted. It checks them and it returns the settings.
    Args:
        input_settings (MeasurementRequest): The parameters that the client inputted.
    Returns:
        AdvancedSettings: The settings to be used internally in the server. (valid settings)
    Raises:
        InputError: If some settings are invalid.
    """
    wanted_ip_type = 6 if input_settings.ipv6_measurement else 4
    # Override it if we received an IP, not a domain name:
    # In case the input is an IP and not a domain name, then "wanted_ip_type" will be ignored and the IP type of the IP will be used.
    input_settings.wanted_ip_type = override_desired_ip_type_if_input_is_ip(input_settings.server, wanted_ip_type)
    # create the settings (get rid of None-s)

    settings = AdvancedSettings()

    if input_settings.measurement_type is not None:
        settings.measurement_type = input_settings.measurement_type

    if input_settings.ntp_versions_to_analyze is not None:
        settings.ntp_versions_to_analyze = input_settings.ntp_versions_to_analyze
    if input_settings.analyse_all_ntp_versions is not None:
        settings.analyse_all_ntp_versions = input_settings.analyse_all_ntp_versions
    if input_settings.ntp_versions_analysis_on_each_ip is not None:
        settings.ntp_versions_analysis_on_each_ip = input_settings.ntp_versions_analysis_on_each_ip
    if input_settings.nts_analysis_on_each_ip is not None:
        settings.nts_analysis_on_each_ip = input_settings.nts_analysis_on_each_ip

    if input_settings.ntpv5_draft is not None:
        settings.ntpv5_draft = input_settings.ntpv5_draft

    if input_settings.custom_probes_asn is not None:
        settings.custom_probes_asn = input_settings.custom_probes_asn
    if input_settings.custom_probes_country is not None:
        settings.custom_probes_country = input_settings.custom_probes_country
    if input_settings.custom_client_ip is not None:
        settings.custom_client_ip = input_settings.custom_client_ip

    return check_settings(settings)

def check_settings(settings: AdvancedSettings) -> AdvancedSettings:
    """
    This method checks the values in the settings.
    Args:
        settings (AdvancedSettings): The parameters that the client inputted.
    Returns:
        AdvancedSettings: The settings to be used internally in the server. (valid settings)
    Raises:
        InputError: If some settings are invalid.
    """
    # checks
    # main measurement settings
    if settings.wanted_ip_type != 4 and settings.wanted_ip_type != 6:
        raise InputError("wanted_ip_type must be 4 or 6")
    if not settings.measurement_type in ["ntpv1", "ntpv2", "ntpv3", "ntpv4", "ntpv5"]:
        raise InputError("measurement_type must be ntpv1 or ntpv2 or ntpv3 or ntpv4 or ntpv5")
    # ntp versions settings
    if not settings.measurement_type in ["ntpv1", "ntpv2", "ntpv3", "ntpv4", "ntpv5"]:
        raise InputError("measurement_type must be either ntpv1 or ntpv2 or ntpv3 or ntpv4 or ntpv5")
    settings.ntp_versions_to_analyze = list(set(settings.ntp_versions_to_analyze))
    for v in settings.ntp_versions_to_analyze:
        if not settings.measurement_type in ["ntpv1", "ntpv2", "ntpv3", "ntpv4", "ntpv5"]:
            raise InputError(f"the version {v} must be either ntpv1 or ntpv2 or ntpv3 or ntpv4 or ntpv5")
    if settings.analyse_all_ntp_versions: # if they want to measure everything, override the list
        settings.ntp_versions_to_analyze = ["ntpv1", "ntpv2", "ntpv3", "ntpv4", "ntpv5"]

    # RIPE part
    if settings.custom_client_ip != "" and is_ip_address(settings.custom_client_ip) is None:
        raise InputError("custom_client_ip must be either null/empty or a valid IP address")
    return settings

def complete_this_measurement_dn(measurement_id: int, dn_ips: list[str], settings: AdvancedSettings) -> None:
    """
    if the measurement_id is not in the database, then this method does nothing.
    """

    # very important: keep this "import" here (Because it needs to be imported after SQLAlchemy has been initialized)
    from server.app.db_config import _SessionLocal
    print(f"starting dn...{measurement_id}")


    if _SessionLocal is None: # this will never be the case. This code is to solve a mypy type error
        print("_SessionLocal is None. No connection to the database")
        return
    db = _SessionLocal()
    status = ""
    try:
        m: FullMeasurementDN | None = db.query(FullMeasurementDN).filter_by(id_m_dn=measurement_id).first()
        if not m:
            return
        server = str(m.server)

        # RIPE PART
        m.status = "starting RIPE measurement"
        status = m.status
        db.commit()
        add_ripe_measurement_id_to_db_measurement(db, server, settings, m)
        # delete the custom client ip
        settings.custom_client_ip = ""

        # MAIN NTP measurement PART
        i = 0
        for ip in dn_ips:
            # print(f"ip:{ip}")
            m.status = f"adding ntp measurements {i + 1}/{len(dn_ips)}"
            status = m.status
            i = i + 1
            db.commit()
            measurement_ip = FullMeasurementIP(
                status="pending",
                server_ip=ip,
                settings=settings.model_dump()
            )
            db.add(measurement_ip)
            db.commit()
            db.refresh(measurement_ip)
            time.sleep(1.2)
            complete_this_measurement_ip(measurement_ip.id_m_ip, settings, True, server)
            m.ip_measurements.append(measurement_ip)
            # NTP servers may refuse to respond if you poll them very often
            db.commit()
        # NTS PART
        # no check because it is done by default
        m.status = "adding nts"
        status = m.status
        db.commit()
        time.sleep(1)
        nts_ans = perform_nts_measurement_domain_name(server, settings)

        nts = NTSMeasurement.from_dict(nts_ans, server) # currently we only support NTS with ntpv4
        db.add(nts)
        db.flush()
        m.id_nts = nts.id_nts
        db.commit()
        db.refresh(nts)

        # NTP Versions PART
        # check the settings -> to see if the client wants NTP version analysis:
        if settings.analyse_all_ntp_versions or len(settings.ntp_versions_to_analyze) > 0:
            # adding NTP versions analysis
            m.status = "adding NTP versions analysis"
            status = m.status
            db.commit()
            time.sleep(1)
            add_ntp_versions_to_db_measurement(db, server, settings, m)


        # add settings
        m.settings = settings.model_dump()
        # Update with results
        m.status = "finished"
        status = m.status
        db.commit()
    except Exception as e:
        print("Completing measurement error message:\n", e)
        try:
            db.rollback()
            m = db.query(FullMeasurementDN).filter_by(id_m_dn=measurement_id).first()
            if m and m.status != "finished":
                m.status = "failed"
                m.response_error = f"(surprising) error when completing the measurement: {e.__class__.__name__}"
                db.commit()
        except Exception as inner:
            print("Error while marking failed:", inner)
    finally:
        db.close()



def complete_this_measurement_ip(measurement_id: int, settings: AdvancedSettings, part_of_dn_measurement: bool=False,
                                 from_dn: Optional[str] = None) -> None:
    """
    if the measurement_id is not in the database, then this method does nothing.
    """

    # very important: keep this "import" here (Because it needs to be imported after SQLAlchemy has been initialized)
    from server.app.db_config import _SessionLocal
    print(f"starting ip...{measurement_id}")
    if _SessionLocal is None: # this will never be the case. This code is to solve a mypy type error
        print("_SessionLocal is None. No connection to the database")
        return
    db = _SessionLocal()
    status = ""
    try:
        m: FullMeasurementIP | None = db.query(FullMeasurementIP).filter_by(id_m_ip=measurement_id).first()
        if not m:
            return
        server_ip = str(m.server_ip)
        # m.status = "starting"
        # status = m.status
        # db.commit()

        # RIPE PART (only if it is not part of the domain name. In that case you can see it at domain name)
        if not part_of_dn_measurement:
            m.status = "starting RIPE measurement"
            status = m.status
            db.commit()
            add_ripe_measurement_id_to_db_measurement(db, server_ip, settings, m)
            # delete the custom client ip
            settings.custom_client_ip = ""
        # MAIN NTP measurement PART
        # if it fails, you will see the error message in the m.response_error
        add_custom_ntp_measurement_ip_to_db_measurement(db, server_ip, settings, m, from_dn)

        # NTS PART
        # if it is part of a dn measurement, you need to check if the client really wants on each IP address.
        if part_of_dn_measurement == False or settings.nts_analysis_on_each_ip:
            m.status = "adding nts"
            status = m.status
            db.commit()
            time.sleep(1)
            nts_ans = perform_nts_measurement_ip(server_ip)
            nts_ans["warning_ip"] = "NTS measurements on IPs cannot check TLS certificate."
            # do not add from_dn here because NTS is special and KE of NTS may change the IP
            nts = NTSMeasurement.from_dict(nts_ans, server_ip) # currently we only support NTS with ntpv4
            db.add(nts)
            db.flush()
            m.id_nts = nts.id_nts
            db.commit()
            db.refresh(nts)

        # NTP Versions PART
        # check the settings -> to see if the client wants NTP version analysis:
        # if is not part of a dn measurement, then check as usual. But if it is, then "analyse_all_ntp_versions" and "ntp_versions_to_analyze"
        # are settings for the domain name. We need to look at "nts_analysis_on_each_ip" to see if the client also wants to apply the
        # settings on the IP addresses
        if part_of_dn_measurement == False or settings.ntp_versions_analysis_on_each_ip:
            if settings.analyse_all_ntp_versions or len(settings.ntp_versions_to_analyze) > 0:
                # adding NTP versions analysis
                m.status = "adding NTP versions analysis"
                status = m.status
                db.commit()
                time.sleep(1) #to make sure the server would not blacklist us
                add_ntp_versions_to_db_measurement(db, server_ip, settings, m, from_dn)
        # add settings
        m.settings = settings.model_dump()
        # Update with results
        m.status = "finished"
        status = m.status
        db.commit()
    except Exception as e:
        take_care_of_exception(db, e, measurement_id, True)
    finally:
        db.close()

def take_care_of_exception(db: Session, e: Exception, measurement_id: int, ip_measurement: bool) -> None:
    """
    This method takes care of marking the measurement as failed, if something happened.
    Args:
        db (Session): A connection to the database (we need to query some IDs).
        e (Exception): An exception instance.
        measurement_id (int): The measurement id.
        ip_measurement (bool): Whether the measurement was on an IP address.
    """
    print("Completing measurement error message:", e)
    try:
        db.rollback()
        m = db.query(FullMeasurementIP).filter_by(id_m_ip=measurement_id).first()
        if m and m.status != "finished":
            m.status = "failed"
            m.response_error = f"(surprising) error when completing the measurement: {e.__class__.__name__}"
            db.commit()
    except Exception as inner:
        print("Error while marking failed:", inner)

def add_custom_ntp_measurement_ip_to_db_measurement(db: Session, server_ip: str, settings: AdvancedSettings,
                                            full_m: FullMeasurementIP, from_dn: Optional[str] = None) -> None:
    """
    This method is used when you performed a full measurement on an IP address.
    If the measurement fails, you will not see why in the full_m.response_error
    Args:
        db (Session): A connection to the database (we need to query some IDs)
        server_ip (str): The IP address of the server.
        settings (AdvancedSettings): The settings to use.
        full_m (FullMeasurementIP): Full measurement IP object.
        from_dn (Optional[str]): The domain name of this IP address, if available. (it will simplify the
                process of searching in the db)
    Returns:
        None: nothing
    """
    try:
        binary_nts_tool = get_right_ntp_nts_binary_tool_for_your_os()
    except Exception as e:
        # This is the case when the tool fails, because python was not able to find it or run it.
        full_m.response_error = "Measurement could not be performed (binary tool not available)."
        db.commit()
        return
    try:
        conf, analysis, data = run_tool_on_ntp_version(server_ip, str(binary_nts_tool),
                                settings.measurement_type, settings.ntpv5_draft)

        # 3 cases:
        # 1 we received a real wanted ntp version
        # 2 we received a fake wanted ntp version
        # 3 we received a real different ntp version
        # the client will see the results
        # as what class do we save it? ->
        # save as what the response version says
        host = server_ip
        if from_dn is not None:
            host = from_dn
        # the decision was based on these statements:
        # it is ok if in NTPv5 class we have fake measurements that says their version is NTPv5
        #  which is the ntp server's problem, not ours-> we can easily detect them
        # it is not ok if in NTPv5 class we have correct NTPv4 measurements
        response_version = str(data.get("version"))
        # in case the measurement failed (you can also see that the conf is "0")
        if data.get("version") is None or data.get("error") is not None:
            full_m.response_error = analysis
            db.commit()
            return

        if response_version != "5" and response_version != "ntpv5": # I think this may help if someone is confused about notations.
            # then it is either NTPv1,v2,v3 or v4. But all of them are saved in the database in the NTPv4 format.
            # add the "from_dn" in case it exists.
            measurement_v = NTPv4Measurement(host=host, measured_server_ip=server_ip)
            put_fields_ntpv4(measurement_v, data, analysis)

            db.add(measurement_v)
            db.flush()
            # add the server info
            get_server_info_objectv4(db, measurement_v.id, server_ip)
            full_m.id_main_measurement = measurement_v.id
        else:

            measurement_v5 = NTPv5Measurement(host=host, measured_server_ip=server_ip)
            put_fields_ntpv5(measurement_v5, data, analysis, settings.ntpv5_draft)
            db.add(measurement_v5)
            db.flush()
            # add the server info
            get_server_info_objectv5(db, measurement_v5.id, server_ip)
            full_m.id_main_measurement = measurement_v5.id
        full_m.response_version = "ntpv" + response_version
        db.commit()
    except Exception as e: # we arrive here iff run_tool_on_ntp_version throws an error
        print("error in adding custom ntp measurement:", e)

def get_server_info_objectv4(db: Session, m_id: int, server_ip: str) -> None:
    """
    Creates the server info object fot this measurement.
    Args:
        db (Session): A connection to the database (we need to query some IDs).
        m_id (int): The measurement (NTPv4 class) id.
        server_ip (Optional[str]): The IP address of the server.
    Returns:
         None: nothing
    """
    msi = NTPv4ServerInfo(m_id=m_id, ip_is_anycast=is_this_ip_anycast(server_ip),
                        asn_ntp_server=get_asn_for_ip(server_ip), country_code=get_country_for_ip(server_ip))
    msi.vantage_point_ip = ip_to_str(get_server_ip(4))
    c: Optional[Tuple[float, float]] = get_coordinates_for_ip(server_ip)
    if c is not None:
        msi.coordinates_x = c[0]
        msi.coordinates_y = c[1]
    db.add(msi)
    db.flush()

def get_server_info_objectv5(db: Session, m_id: int, server_ip: str) -> None:
    """
    Creates the server info object fot this measurement.
    Args:
        db (Session): A connection to the database (we need to query some IDs).
        m_id (int): The measurement (NTPv5 class) id.
        server_ip (Optional[str]): The IP address of the server.
    Returns:
         None: nothing
    """
    msi = NTPv5ServerInfo(m_id=m_id, ip_is_anycast=is_this_ip_anycast(server_ip),
                        asn_ntp_server=get_asn_for_ip(server_ip), country_code=get_country_for_ip(server_ip))
    msi.vantage_point_ip = ip_to_str(get_server_ip(4))
    c: Optional[Tuple[float, float]] = get_coordinates_for_ip(server_ip)
    if c is not None:
        msi.coordinates_x = c[0]
        msi.coordinates_y = c[1]
    db.add(msi)
    db.flush()

def get_host_and_server_ip(server: str, from_dn: Optional[str] = None) -> Tuple[str, Optional[str]]:
    """
    This method gets the host and server IP. It is useful because it can work with both cases: domain name and IP address
    Args:
        server (str): The server name. (ip or dn)
        from_dn (Optional[str]): The domain name of this IP address.
    Returns:
        Tuple[str, Optional[str]]: The host and server IP.
    """
    host = server
    server_ip = None
    if is_ip_address(server):
        server_ip = server
    if from_dn is not None:
        host = from_dn
    return host, server_ip

def add_ntp_versions_to_db_measurement(db: Session, server: str, settings: AdvancedSettings,
                                m: FullMeasurementDN | FullMeasurementIP, from_dn: Optional[str] = None) -> None:
    """
    This method adds the ntp versions analysis to the database and to the measurement.
    If this fails, then the ID for this measurement will be None/Null when the status of the overall
    measurement will be "finished".
    Args:
        db (Session): A connection to the database (we need to query some IDs)
        server (str): The server (IP address or domain name)
        settings (AdvancedSettings): The settings to use.
        m (FullMeasurementDN | FullMeasurementIP): Full measurement IP object.
        from_dn (Optional[str]): The domain name of this IP address, if available.
    Returns:
        None: nothing
    """
    host, server_ip = get_host_and_server_ip(server, from_dn=from_dn)
    # print(f"ntpv: host: {host}, ip: {server_ip}")
    try:
        ntpv_ans = analyze_supported_ntp_versions(server, settings)
        #if there is an error with our tool (not the results from our tool! Important difference)
        if ntpv_ans.get("error") is not None:
            return
        # !!! IMPORTANT !!!
        # if for example you wanted an NTPv5 measurement, but you received an NTPv4 response, then it will be saved
        # as NTPv4 in our databases, and the whole situation will be highlighted in the NTPVersions. This is because we
        # want to avoid having versions in the wrong place.
        # On the other hand, we may end with "fake" NTPv5 measurements if a server replies with NTPv4 response, but has set
        # the version to NTPv4. But this is exactly the scope of this tool! To spot mistakes in the NTP servers behaviours.
        ntp_vs = NTPVersions(ntpv1_supported_conf=ntpv_ans.get("ntpv1_supported_confidence"),
                             ntpv2_supported_conf=ntpv_ans.get("ntpv2_supported_confidence"),
                             ntpv3_supported_conf=ntpv_ans.get("ntpv3_supported_confidence"),
                             ntpv4_supported_conf=ntpv_ans.get("ntpv4_supported_confidence"),
                             ntpv5_supported_conf=ntpv_ans.get("ntpv5_supported_confidence"),
                             ntpv1_analysis=ntpv_ans.get("ntpv1_analysis"),
                             ntpv2_analysis=ntpv_ans.get("ntpv2_analysis"),
                             ntpv3_analysis=ntpv_ans.get("ntpv3_analysis"),
                             ntpv4_analysis=ntpv_ans.get("ntpv4_analysis"),
                             ntpv5_analysis=ntpv_ans.get("ntpv5_analysis"),
                             # we will add the results immediately (and their response versions)
                             )
        db.add(ntp_vs)
        db.flush()  # assign ID without commit yet

        # insert measurements
        ntpv1, resp1_vs = add_ntp_measurement(db, ntpv_ans.get("ntpv1_m_result"), settings, host, server_ip)
        ntpv2, resp2_vs = add_ntp_measurement(db, ntpv_ans.get("ntpv2_m_result"), settings, host, server_ip)
        ntpv3, resp3_vs = add_ntp_measurement(db, ntpv_ans.get("ntpv3_m_result"), settings, host, server_ip)
        ntpv4, resp4_vs = add_ntp_measurement(db, ntpv_ans.get("ntpv4_m_result"), settings, host, server_ip)
        ntpv5, resp5_vs = add_ntp_measurement(db, ntpv_ans.get("ntpv5_m_result"), settings, host, server_ip)

        # link them if they exist
        if ntpv1:
            ntp_vs.id_v4_1 = ntpv1.id
            ntp_vs.ntpv1_response_version = resp1_vs
            put_fields_4_or_5(ntpv1, resp1_vs, ntpv_ans.get("ntpv1_m_result"))#, ntpv_ans.get("ntpv1_analysis") # redundant dat
        if ntpv2:
            ntp_vs.id_v4_2 = ntpv2.id
            ntp_vs.ntpv2_response_version = resp2_vs
            put_fields_4_or_5(ntpv2, resp2_vs, ntpv_ans.get("ntpv2_m_result"))
        if ntpv3:
            ntp_vs.id_v4_3 = ntpv3.id
            ntp_vs.ntpv3_response_version = resp3_vs
            put_fields_4_or_5(ntpv3, resp3_vs, ntpv_ans.get("ntpv3_m_result"))
        if ntpv4:
            ntp_vs.id_v4_4 = ntpv4.id
            ntp_vs.ntpv4_response_version = resp4_vs
            put_fields_4_or_5(ntpv4, resp4_vs, ntpv_ans.get("ntpv4_m_result"))
        if ntpv5:
            ntp_vs.id_v5 = ntpv5.id
            ntp_vs.ntpv5_response_version = resp5_vs
            put_fields_4_or_5(ntpv5, resp5_vs, ntpv_ans.get("ntpv5_m_result"), ntpv_ans.get("ntpv5_analysis"), settings.ntpv5_draft)

        db.flush()
        m.id_vs = ntp_vs.id_vs
        db.commit()
        db.refresh(ntp_vs)
    except Exception as e:
        print(f"error in adding ntp versions: {e}")

def add_ntp_measurement(db: Session, result: Optional[dict], settings: AdvancedSettings, host: str, server_ip: Optional[str]) \
        -> Tuple[Optional[NTPv4Measurement | NTPv5Measurement], Optional[str]]:
    """
    This method adds the result (NTP measurement) into the database.
    Args:
        db (Session): A connection to the database.
        result (Optional[dict]): the result of the adding NTP measurement
        settings (AdvancedSettings): the settings to use
        host (Optional[str]): the host to use (IP or domain name)
        server_ip (Optional[str]): the IP
    Returns:
        Tuple[Optional[NTPv4Measurement | NTPv5Measurement], Optional[str]]: A pair of the measurement and its version.
    """
    #result = ntpv_ans.get(result_key)
    if result and not result.get("error") and result.get("version"):
        vs = "ntpv4"
        measurement_vs: NTPv5Measurement | NTPv4Measurement
        if str(result.get("version")) == "5" or str(result.get("version")) == "ntpv5":
            measurement_vs = NTPv5Measurement(host=host, measured_server_ip=server_ip)
            vs = "ntpv5"
        else:
            measurement_vs = NTPv4Measurement(host=host, measured_server_ip=server_ip)
            vs = "ntpv" + str(result.get("version"))
        db.add(measurement_vs)
        db.flush()
        return measurement_vs, vs
    # if we did not receive a valid measurement, then we do not save it
    return None, None

def add_ripe_measurement_id_to_db_measurement(db: Session, server: str, settings: AdvancedSettings,
                                              m: FullMeasurementDN | FullMeasurementIP) -> None:
    """
    This method perform the RIPE measurement.
    It marked the ripe_error field if there are any errors.
    Args:
        db (Session): A connection to the database (we need to query some IDs)
        server (str): The server (IP address or domain name)
        settings (AdvancedSettings): The settings to use.
        m (FullMeasurementDN | FullMeasurementIP): Full measurement IP object.
    Returns:
        None: nothing
    """
    try:
        ripe_measurement_id = perform_ripe_measurement(server, settings.custom_client_ip, settings.wanted_ip_type)
        m.id_ripe = int(ripe_measurement_id)
        db.commit()
    except RipeMeasurementError as e:
        print("RIPE measurement initiated, but it failed. RIPE has a problem: ", e)
        m.ripe_error = f"RIPE measurement initiated, but it failed: {sanitize_string(str(e))}"
        db.commit()
    except Exception as e:
        print("Failed to initiate RIPE measurement: ", e)
        m.ripe_error = "Failed to initiate RIPE measurement"
        db.commit()

def fetch_historic_data_with_timestamps(server: str, start: datetime, end: datetime, session: Session) -> list[
    NtpMeasurement]:
    """
    Fetches and reconstructs NTP measurements from the database within a specific time range.

    Converts the provided human-readable datetime range into NTP-compatible timestamps,
    queries the database based on whether the server is an IP address or domain name,
    and reconstructs each result as an `NtpMeasurement` object.

    Args:
        server (str): An IPv4/IPv6 address or domain name string for which measurements should be fetched.
        start (datetime): The start of the time range (in local or UTC timezone).
        end (datetime): The end of the time range (in local or UTC timezone).
        session (Session): The currently active database session.

    Returns:
        list[NtpMeasurement]: A list of `NtpMeasurement` objects representing the historical data
        for the given server within the time window.

    Notes:
        - The input datetimes are converted to UTC before processing.
        - IP addresses are validated using the `is_ip_address()` utility function.
        - Data is fetched using `get_measurements_timestamps_ip` or `get_measurements_timestamps_dn`
          depending on the server type.
        - The `PreciseTime` wrapper is used to reconstruct accurate timestamps from database fields.
    """
    start_pt = human_date_to_ntp_precise_time(ensure_utc(start))
    end_pt = human_date_to_ntp_precise_time(ensure_utc(end))
    # print(start_pt)
    # print(end_pt)
    # start_pt = PreciseTime(450, 20)
    # end_pt = PreciseTime(1200, 100)
    measurements = []
    if is_ip_address(server) is not None:
        measurements = get_measurements_timestamps_ip(session, parse_ip(server), start_pt, end_pt)
    else:
        measurements = get_measurements_timestamps_dn(session, server, start_pt, end_pt)

    return measurements


def fetch_ripe_data(measurement_id: str) -> tuple[list[dict], str]:
    """
    Fetches and formats NTP measurement data from RIPE Atlas.

    This function retrieves raw measurement data from the RIPE Atlas API using the given
    measurement ID, parses it into internal data structures, and formats it into a
    standardized dictionary format.

    Args:
        measurement_id (str): The unique ID of the RIPE Atlas measurement to fetch.

    Returns:
        list[dict]: A list of dictionaries, each representing a formatted NTP measurement.
    """
    measurements, status = parse_data_from_ripe_measurement(get_data_from_ripe_measurement(measurement_id))
    measurements_formated = []
    for m in measurements:
        measurements_formated.append(get_ripe_format(m))
    return measurements_formated, status



def perform_ripe_measurement(ntp_server: str, client_ip: Optional[str], wanted_ip_type: int) -> str:
    """
    Initiate a RIPE Atlas measurement for a given server (IP address or domain name).

    This function determines whether the provided server is an IP address or a domain name,
    and triggers the appropriate RIPE measurement.

    Args:
        ntp_server (str): The IP address or domain name of the target NTP server.
        client_ip (Optional[str]): The IP address of the client requesting the measurement.
        wanted_ip_type (int): The IP type that we want to measure. (4 or 6)

    Returns:
        str: The RIPE measurement ID. (as a string)

    Raises:
        Exception: If the server string is invalid or the measurement failed.
    """
    # use our server as the client if the client IP is not provided
    if client_ip is None:
        client_ip = ip_to_str(get_server_ip(wanted_ip_type))
        if client_ip is None:
            raise InputError("Could not determine IP address of neither server nor client")
    try:
        if is_ip_address(ntp_server) is not None:
            measurement_id = perform_ripe_measurement_ip(ntp_server, client_ip)
            return str(measurement_id)
        else:
            measurement_id = perform_ripe_measurement_domain_name(ntp_server, client_ip, wanted_ip_type)
            return str(measurement_id)
    except InputError as e:
        raise e
    except RipeMeasurementError as e:
        raise e
    except Exception as e:
        raise ValueError(e)


def check_ripe_measurement_scheduled(measurement_id: str) -> bool:
    """
    Check if a RIPE Atlas measurement has been fully scheduled.

    This function delegates to `check_all_measurements_scheduled()` to verify that
    all requested probes have been scheduled for the given RIPE measurement ID.

    Args:
        measurement_id (str): The ID of the RIPE measurement to check.

    Returns:
        bool: True if all requested probes are scheduled, False otherwise.

    Raises:
        ValueError: If the RIPE API returns an error or unexpected data.
    """
    return check_all_measurements_scheduled(measurement_id=measurement_id)
