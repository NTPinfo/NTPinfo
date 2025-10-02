import pprint
import time

from sqlalchemy.orm import Session

from server.app.dtos.full_ntp_measurement import NTSMeasurement, FullMeasurementDN, NTPv4Measurement, NTPv5Measurement
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
from server.app.utils.load_config_data import get_nr_of_measurements_for_jitter
from server.app.utils.calculations import calculate_jitter_from_measurements, human_date_to_ntp_precise_time
from server.app.utils.ip_utils import ip_to_str
from typing import Any, Optional

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

def complete_this_measurement_dn(measurement_id, settings: AdvancedSettings) -> None:

    # very important: keep this "import" here (Because it needs to be imported after SQLAlchemy has been initialized)
    from server.app.db_config import _SessionLocal
    # if the measurement_id is not in the database, then this method does nothing.
    print(f"starting...{measurement_id}")


    db = _SessionLocal()
    status = ""
    try:
        m: FullMeasurementDN | None = db.query(FullMeasurementDN).filter_by(id_m_dn=measurement_id).first()
        if not m:
            return
        server = str(m.server)
        # m.status = "starting"
        # status = m.status
        # db.commit()

        # NTS PART
        # no check because it is done by default
        m.status = "adding nts"
        status = m.status
        db.commit()
        settings.wanted_ip_type = -1
        nts_ans = perform_nts_measurement_domain_name(server, settings)
        nts = NTSMeasurement(succeeded=bool(nts_ans["NTS succeeded"]), analysis=nts_ans["NTS analysis"],
                             nts_data=nts_ans, measurement_type="ntpv4") # currently we only support NTS with ntpv4
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
            ntp_vs = add_ntp_versions_to_db_measurement(db, server, settings, m)


        # Update with results
        m.status = "finished"
        status = m.status
        db.commit()
    except Exception as e:
        print("Completing measurement error message:", e)
        try:
            db.rollback()
            m = db.query(FullMeasurementDN).filter_by(id_m_dn=measurement_id).first()
            if m and m.status != "finished":
                m.status = "failed"
                db.commit()
        except Exception as inner:
            print("Error while marking failed:", inner)
    finally:
        db.close()



def complete_this_measurement_ip(measurement_id, settings: AdvancedSettings, part_of_dn_measurement=False) -> None:

    # very important: keep this "import" here (Because it needs to be imported after SQLAlchemy has been initialized)
    from server.app.db_config import _SessionLocal
    # if the measurement_id is not in the database, then this method does nothing.
    print(f"starting...{measurement_id}")

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

        # NTS PART
        # if it is part of a dn measurement, you need to check if the client really wants on each IP address.
        if part_of_dn_measurement == False or settings.nts_analysis_on_each_ip:
            m.status = "adding nts"
            status = m.status
            db.commit()
            nts_ans = perform_nts_measurement_ip(server_ip)
            nts = NTSMeasurement(succeeded=bool(nts_ans["NTS succeeded"]), analysis=nts_ans["NTS analysis"],
                                 nts_data=nts_ans, measurement_type="ntpv4")  # currently we only support NTS with ntpv4
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
        if part_of_dn_measurement == False or settings.ntp_analysis_on_each_ip:
            if settings.analyse_all_ntp_versions or len(settings.ntp_versions_to_analyze) > 0:
                # adding NTP versions analysis
                m.status = "adding NTP versions analysis"
                status = m.status
                db.commit()
                ntp_vs = add_ntp_versions_to_db_measurement(db, server_ip, settings, m)

        # Update with results
        m.status = "finished"
        status = m.status
        db.commit()
    except Exception as e:
        print("Completing measurement error message:", e)
        try:
            db.rollback()
            m = db.query(FullMeasurementIP).filter_by(id_m_ip=measurement_id).first()
            if m and m.status != "finished":
                m.status = "failed"
                db.commit()
        except Exception as inner:
            print("Error while marking failed:", inner)
    finally:
        db.close()

def add_ntp_versions_to_db_measurement(db, server: str, settings: AdvancedSettings, m: FullMeasurementDN | FullMeasurementIP):
    # it is ok if this method will throw an error
    # if m is None:
    #     return None
    ntpv_ans = analyze_supported_ntp_versions(server, settings)
    #if there is an error with our tool (not the results from our tool! Important difference)
    if ntpv_ans.get("error") is not None:
        return None
    pprint.pprint(ntpv_ans)
    ntp_vs = NTPVersions(ntpv1_supported_conf=ntpv_ans.get("ntpv1_supported_confidence"),
                         ntpv2_supported_conf=ntpv_ans.get("ntpv2_supported_confidence"),
                         ntpv3_supported_conf=ntpv_ans.get("ntpv3_supported_confidence"),
                         ntpv4_supported_conf=ntpv_ans.get("ntpv4_supported_confidence"),
                         ntpv5_supported_conf=ntpv_ans.get("ntpv5_supported_confidence"),
                         analysis_v1=ntpv_ans.get("ntpv1_analysis"),
                         analysis_v2=ntpv_ans.get("ntpv2_analysis"),
                         analysis_v3=ntpv_ans.get("ntpv3_analysis"),
                         analysis_v4=ntpv_ans.get("ntpv4_analysis"),
                         analysis_v5=ntpv_ans.get("ntpv5_analysis"),
                         # we will add the results immediately
                         )
    db.add(ntp_vs)
    db.flush()  # assign ID without commit yet

    # a local method
    def add_ntp_measurement(result_key, model_class):
        result = ntpv_ans.get(result_key)
        if result and not result.get("error"):
            measurement = model_class(ntpv_data=result) if model_class == NTPv4Measurement else model_class(
                ntpv5_data=result)
            db.add(measurement)
            db.flush()
            return measurement
        return None

    # insert measurements
    ntpv1 = add_ntp_measurement("ntpv1_m_result", NTPv4Measurement)
    ntpv2 = add_ntp_measurement("ntpv2_m_result", NTPv4Measurement)
    ntpv3 = add_ntp_measurement("ntpv3_m_result", NTPv4Measurement)
    ntpv4 = add_ntp_measurement("ntpv4_m_result", NTPv4Measurement)
    ntpv5 = add_ntp_measurement("ntpv5_m_result", NTPv5Measurement)

    # link them if they exist
    if ntpv1: ntp_vs.id_v4_1 = ntpv1.id_v
    if ntpv2: ntp_vs.id_v4_2 = ntpv2.id_v
    if ntpv3: ntp_vs.id_v4_3 = ntpv3.id_v
    if ntpv4: ntp_vs.id_v4_4 = ntpv4.id_v
    if ntpv5: ntp_vs.id_v5 = ntpv5.id_v5

    m.id_vs = ntp_vs.id_vs
    db.commit()
    db.refresh(ntp_vs)
    return ntp_vs


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
