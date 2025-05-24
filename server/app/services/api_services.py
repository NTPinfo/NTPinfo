from ipaddress import IPv4Address, IPv6Address
from typing import Any, Optional, Coroutine
from server.app.utils.validate import ensure_utc, is_ip_address, parse_ip
from server.app.utils.perform_measurements import perform_ntp_measurement_ip, perform_ntp_measurement_domain_name
from server.app.utils.perform_measurements import human_date_to_ntp_precise_time, ntp_precise_time_to_human_date, calculate_jitter_from_measurements
from datetime import datetime
from server.app.db.connection import insert_measurement
from server.app.db.connection import get_measurements_timestamps_ip, get_measurements_timestamps_dn
from server.app.db.config import pool
from server.app.models.NtpMainDetails import NtpMainDetails
from server.app.models.NtpMeasurement import NtpMeasurement
from server.app.models.NtpServerInfo import NtpServerInfo
from server.app.models.NtpTimestamps import NtpTimestamps
from server.app.models.PreciseTime import PreciseTime
from server.app.models.NtpExtraDetails import NtpExtraDetails


def ip_to_str(ip: Optional[IPv4Address | IPv6Address]) -> Optional[str]:
    """
    Converts an IP address (either IPv4 or IPv6) to its string representation.

    This function takes an `IPv4Address` or `IPv6Address` object and converts it to
    a string. If the input IP is `None`, it returns `None`.

    Args:
        ip (Optional[IPv4Address | IPv6Address]): The IP address to be converted.
            It can be either an `IPv4Address` or `IPv6Address` object, or `None`.

    Returns:
        Optional[str]: The string representation of the IP address, or `None` if the input is `None`.
    """
    return str(ip) if ip is not None else None


def get_format(measurement: NtpMeasurement, jitter: float|None=None, other_server_ips: list[str]|None=None) -> dict[str, Any]:
    """
    Format an NTP measurement object into a dictionary suitable for JSON serialization.

    Args:
        measurement (NtpMeasurement): An object representing the NTP measurement result.
        jitter (float|None): Optional jitter value if multiple measurements are performed.
        other_server_ips (list[str]|None): An optional list of IP addresses if the measurement is performed on a domain name.

    Returns:
        dict: A dictionary containing key measurement details like this:
            - Server info (ntp version, IP, name, reference IP, reference)
            - Timestamps (client sent time, server receive time, server sent time, client receive time)
            - Measurement metrics (offset, delay, stratum, precision, reachability)
            - Extra details (root delay, last sync time, leap indicator)
    """
    return {
        # "vantage": ip_to_str(measurement.vantage_point_ip),
        "ntp_version": measurement.server_info.ntp_version,
        "ntp_server_ip": ip_to_str(measurement.server_info.ntp_server_ip),
        "ntp_server_name": measurement.server_info.ntp_server_name,
        "ntp_server_ref_parent_ip": ip_to_str(measurement.server_info.ntp_server_ref_parent_ip),
        "ref_name": measurement.server_info.ref_name,

        "client_sent_time": measurement.timestamps.server_sent_time,
        "server_recv_time": measurement.timestamps.server_recv_time,
        "server_sent_time": measurement.timestamps.server_sent_time,
        "client_recv_time": measurement.timestamps.client_recv_time,

        "offset": measurement.main_details.offset,
        "delay": measurement.main_details.delay,
        "stratum": measurement.main_details.stratum,
        "precision": measurement.main_details.precision,
        "reachability": measurement.main_details.reachability,

        "root_delay": measurement.extra_details.root_delay,
        "ntp_last_sync_time": measurement.extra_details.ntp_last_sync_time,
        # if it has value = 3 => invalid
        "leap": measurement.extra_details.leap,
        # if the server has multiple IPs addresses we should show them to the client
        "other_server_ips": other_server_ips,
        "jitter": jitter
    }

def measure(server: str, client_ip: Optional[str]=None, jitter_flag: bool=False, measurement_no: int=0) -> tuple[NtpMeasurement, float | None, list[str]|None] | None:
    """
    Performs an NTP measurement for a given server (IP or domain name) and stores the result in the database.

    This function determines whether the input is an IP address or a domain name,
    then performs an NTP measurement using the appropriate method. The result is inserted
    into the database and returned.

    Args:
        server (str): A string representing either an IPv4/IPv6 address or a domain name.
        client_ip (Optional[str]): The client IP or None if it was not provided.
        jitter_flag (bool): Boolean representing whether the client wants to perform multiple measurements to get the jitter.
        measurement_no (int) : How many extra measurements to perform if the jitter_flag is True.

    Returns:
        tuple[NtpMeasurement, float | None, list[str]] | None:
            - A pair with a populated `NtpMeasurement` object if the measurement is successful, the jitter is the jitter_flag is True, and a list of other server ip near the client ip.
            - `None` if an exception occurs during the measurement process.

    Notes:
        - If the server string is empty or improperly formatted, this may raise exceptions internally,
          which are caught and logged to stdout.
        - This function modifies persistent state by inserting a measurement into the database.
    """
    try:
        if is_ip_address(server) is not None:
            m = perform_ntp_measurement_ip(server)
            if m is not None:
                insert_measurement(m, pool)
                jitter = calculate_jitter_from_measurements(m, measurement_no) if jitter_flag else None
                return m, jitter, None  #we have only one server ip so "other_server_ips" is None
            #the measurement failed
            print("The ntp server " + server + " is not responding.")
            return None
        else:
            ans = perform_ntp_measurement_domain_name(server, client_ip)
            if ans is not None:
                m, server_ips = ans
                insert_measurement(m, pool)

                jitter = calculate_jitter_from_measurements(m, measurement_no) if jitter_flag else None
                return m, jitter, server_ips
            print("The ntp server " + server + " is not responding.")
            return None
    except Exception as e:
        print("Performing measurement error message:", e)
        return None


def fetch_historic_data_with_timestamps(server: str, start: datetime, end: datetime) -> list[NtpMeasurement]:
    """
    Fetches and reconstructs NTP measurements from the database within a specific time range.

    Converts the provided human-readable datetime range into NTP-compatible timestamps,
    queries the database based on whether the server is an IP address or domain name,
    and reconstructs each result as an `NtpMeasurement` object.

    Args:
        server (str): An IPv4/IPv6 address or domain name string for which measurements should be fetched.
        start (datetime): The start of the time range (in local or UTC timezone).
        end (datetime): The end of the time range (in local or UTC timezone).

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
    print(start_pt)
    print(end_pt)
    # start_pt = PreciseTime(450, 20)
    # end_pt = PreciseTime(1200, 100)
    # raw_data = get_measurements_timestamps_ip(pool, ip, start_pt, end_pt)
    raw_data = None
    if is_ip_address(server) is not None:
        raw_data = get_measurements_timestamps_ip(pool, parse_ip(server), start_pt, end_pt)
    else:
        raw_data = get_measurements_timestamps_dn(pool, server, start_pt, end_pt)

    measurements = []
    for entry in raw_data:
        vantage_point_ip = entry['vantage_point_ip']
        server_info = NtpServerInfo(entry['ntp_version'], entry['ntp_server_ip'], entry['ntp_server_name'],
                                    entry['ntp_server_ref_parent_ip'], entry['ref_name'])
        extra_details = NtpExtraDetails(PreciseTime(entry['root_delay'], entry['root_delay_prec']),
                                        PreciseTime(entry['ntp_last_sync_time'], entry['ntp_last_sync_time_prec']),
                                        0)
        main_details = NtpMainDetails(entry['offset'], entry['delay'], entry['stratum'],
                                      entry['precision'], entry['reachability'])
        time_stamps = NtpTimestamps(PreciseTime(entry['client_sent'], entry['client_sent_prec']),
                                    PreciseTime(entry['server_recv'], entry['server_recv_prec']),
                                    PreciseTime(entry['server_sent'], entry['server_sent_prec']),
                                    PreciseTime(entry['client_recv'], entry['client_recv_prec']),
                                    )
        measurement = NtpMeasurement(vantage_point_ip, server_info, time_stamps, main_details, extra_details)
        measurements.append(measurement)
    return measurements
