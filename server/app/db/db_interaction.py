from datetime import datetime, timezone
from ipaddress import IPv4Address, IPv6Address, ip_address

from sqlalchemy import Row
from sqlalchemy.orm import Session

from server.app.dtos.full_ntp_measurement import NTPv4Measurement
from server.app.utils.convert_measurement_to_format import full_measurement_dn_to_dict, full_measurement_ip_to_dict, \
    ntpv4_or_v5_measurement_to_dict, ntpv4_measurement_to_dict
from server.app.dtos.full_ntp_measurement import FullMeasurementDN, FullMeasurementIP
from server.app.utils.validate import sanitize_string
from server.app.dtos.ProbeData import ServerLocation
from server.app.utils.location_resolver import get_country_for_ip, get_coordinates_for_ip
from server.app.dtos.NtpExtraDetails import NtpExtraDetails
from server.app.dtos.NtpMainDetails import NtpMainDetails
from server.app.dtos.NtpServerInfo import NtpServerInfo
from server.app.dtos.NtpTimestamps import NtpTimestamps
from server.app.utils.ip_utils import ip_to_str
from server.app.models.Measurement import Measurement
from server.app.models.Time import Time
from server.app.dtos.PreciseTime import PreciseTime
from server.app.dtos.NtpMeasurement import NtpMeasurement
from server.app.models.CustomError import InvalidMeasurementDataError
from server.app.models.CustomError import DatabaseInsertError
from server.app.models.CustomError import MeasurementQueryError
from typing import Any, List


def row_to_dict(m: Measurement, t: Time) -> dict[str, Any]:
    """
    Converts a Measurement and Time SQLAlchemy row into a dictionary.

    Args:
        m (Measurement): The measurement row containing NTP measurement data.
        t (Time): The time row containing timestamp data for the measurement.

    Returns:
        dict[str, Any]: A dictionary representation of the combined measurement and timestamp data.
    """
    return {
        "id": m.id,
        "vantage_point_ip": m.vantage_point_ip,
        "ntp_server_ip": m.ntp_server_ip,
        "ntp_server_name": m.ntp_server_name,
        "ntp_version": m.ntp_version,
        "ntp_server_ref_parent_ip": m.ntp_server_ref_parent,
        "ref_name": m.ref_name,
        "offset": m.time_offset,
        "RTT": m.rtt,
        "stratum": m.stratum,
        "precision": m.precision,
        "reachability": m.reachability,
        "root_delay": m.root_delay,
        "root_delay_prec": m.root_delay_prec,
        "poll": m.poll,
        "root_dispersion": m.root_dispersion,
        "root_dispersion_prec": m.root_dispersion_prec,
        "ntp_last_sync_time": m.ntp_last_sync_time,
        "ntp_last_sync_time_prec": m.ntp_last_sync_time_prec,
        "client_sent": t.client_sent,
        "client_sent_prec": t.client_sent_prec,
        "server_recv": t.server_recv,
        "server_recv_prec": t.server_recv_prec,
        "server_sent": t.server_sent,
        "server_sent_prec": t.server_sent_prec,
        "client_recv": t.client_recv,
        "client_recv_prec": t.client_recv_prec
    }


def rows_to_dicts(rows: list[Row[tuple[Measurement, Time]]]) -> list[dict[str, Any]]:
    """
    Converts a list of Measurement-Time row tuples into a list of dictionaries.

    Args:
        rows (list[Row[tuple[Measurement, Time]]]): List of database rows containing Measurement and Time.

    Returns:
        list[dict[str, Any]]: A list of dictionaries where each dictionary contains combined data from Measurement and Time.
    """
    return [row_to_dict(row.Measurement, row.Time) for row in rows]


def dict_to_measurement(entry: dict[str, Any]) -> NtpMeasurement:
    """
    Converts a dictionary representation of a measurement into an NtpMeasurement object.

    Args:
        entry (dict[str, Any]): A dictionary containing the keys needed to construct an NtpMeasurement object.

    Returns:
        NtpMeasurement: A fully constructed NtpMeasurement using the provided data.

    Raises:
        InvalidMeasurementDataError: If required keys are missing or construction fails due to invalid types/values.
    """

    required_keys = [
        'vantage_point_ip', 'ntp_server_ip', 'ntp_server_name', 'ntp_version', 'ntp_server_ref_parent_ip',
        'ref_name', 'offset', 'RTT', 'stratum', 'precision', 'reachability',
        'root_delay', 'root_delay_prec', 'poll', 'root_dispersion', 'root_dispersion_prec',
        'ntp_last_sync_time', 'ntp_last_sync_time_prec',
        'client_sent', 'client_sent_prec', 'server_recv', 'server_recv_prec',
        'server_sent', 'server_sent_prec', 'client_recv', 'client_recv_prec'
    ]

    missing = [k for k in required_keys if k not in entry]
    if missing:
        raise InvalidMeasurementDataError(f"Missing required keys: {missing}")

    try:
        vantage_point_ip = ip_address(entry['vantage_point_ip']) if entry['vantage_point_ip'] else None
        ntp_ref_parent_ip = ip_address(entry['ntp_server_ref_parent_ip']) if entry['ntp_server_ref_parent_ip'] else None
        ntp_server_ip = ip_address(entry['ntp_server_ip'])
        ntp_server_country_code = get_country_for_ip(entry['ntp_server_ip'])
        ntp_server_coordinates = get_coordinates_for_ip(entry['ntp_server_ip'])
        server_info = NtpServerInfo(ntp_version=entry['ntp_version'], ntp_server_ip=ntp_server_ip,
                                    ntp_server_name=entry['ntp_server_name'],
                                    ntp_server_location=ServerLocation(ntp_server_country_code, ntp_server_coordinates),
                                    ntp_server_ref_parent_ip=ntp_ref_parent_ip, ref_name=entry['ref_name'])
        extra_details = NtpExtraDetails(PreciseTime(entry['root_delay'], entry['root_delay_prec']),
                                        entry['poll'],
                                        PreciseTime(entry['root_dispersion'], entry['root_dispersion_prec']),
                                        PreciseTime(entry['ntp_last_sync_time'], entry['ntp_last_sync_time_prec']),
                                        0)
        main_details = NtpMainDetails(entry['offset'], entry['RTT'], entry['stratum'],
                                      entry['precision'], entry['reachability'])
        time_stamps = NtpTimestamps(PreciseTime(entry['client_sent'], entry['client_sent_prec']),
                                    PreciseTime(entry['server_recv'], entry['server_recv_prec']),
                                    PreciseTime(entry['server_sent'], entry['server_sent_prec']),
                                    PreciseTime(entry['client_recv'], entry['client_recv_prec']),
                                    )
        return NtpMeasurement(vantage_point_ip, server_info, time_stamps, main_details, extra_details)
    except Exception as e:
        raise InvalidMeasurementDataError(f"Failed to build NtpMeasurement: {e}")


def rows_to_measurements(rows: list[Row[tuple[Measurement, Time]]]) -> list[NtpMeasurement]:
    """
    Converts a list of Measurement-Time row tuples into NtpMeasurement objects.

    Args:
        rows (list[Row[tuple[Measurement, Time]]]): List of database rows containing Measurement and Time data.

    Returns:
        list[NtpMeasurement]: A list of NtpMeasurement objects created from the row data.
    """
    return [dict_to_measurement(d) for d in rows_to_dicts(rows)]


def insert_measurement(measurement: NtpMeasurement, session: Session) -> None:
    """
    Inserts a new NTP measurement into the database. Before inserting, it sanitizes the string fields,
    because some fields may have a null character at the end which should be removed.

    This function stores both the raw timestamps (in the `times` table) and the
    processed measurement data (in the `measurements` table).
    It wraps operations in a single transaction to ensure consistency and atomicity.
    If any insert fails, the transaction is rolled back.

    Args:
        measurement (NtpMeasurement): The measurement data to store.
        session (Session): The currently active database session.

    Raises:
        DatabaseInsertError: If inserting the measurement or timestamps fails.

    Notes:
        - Timestamps are stored with both second and fractional parts.
        - A foreign key (`time_id`) is used to link `measurements` to the `times` table.
        - Any failure within the transaction block results in automatic rollback.

    """
    try:
        time = Time(
            client_sent=measurement.timestamps.client_sent_time.seconds,
            client_sent_prec=measurement.timestamps.client_sent_time.fraction,
            server_recv=measurement.timestamps.server_recv_time.seconds,
            server_recv_prec=measurement.timestamps.server_recv_time.fraction,
            server_sent=measurement.timestamps.server_sent_time.seconds,
            server_sent_prec=measurement.timestamps.server_sent_time.fraction,
            client_recv=measurement.timestamps.client_recv_time.seconds,
            client_recv_prec=measurement.timestamps.client_recv_time.fraction
        )
        session.add(time)
        session.flush()
        measurement_entry = Measurement(
            vantage_point_ip=ip_to_str(measurement.vantage_point_ip),
            ntp_server_ip=ip_to_str(measurement.server_info.ntp_server_ip),
            ntp_server_name=sanitize_string(measurement.server_info.ntp_server_name),
            ntp_version=measurement.server_info.ntp_version,
            ntp_server_ref_parent=sanitize_string(ip_to_str(measurement.server_info.ntp_server_ref_parent_ip)),
            ref_name=sanitize_string(measurement.server_info.ref_name),
            time_id=time.id,
            time_offset=measurement.main_details.offset,
            rtt=measurement.main_details.rtt,
            stratum=measurement.main_details.stratum,
            precision=measurement.main_details.precision,
            reachability=sanitize_string(measurement.main_details.reachability),
            root_delay=measurement.extra_details.root_delay.seconds,
            root_delay_prec=measurement.extra_details.root_delay.fraction,
            poll=measurement.extra_details.poll,
            root_dispersion=measurement.extra_details.root_dispersion.seconds,
            root_dispersion_prec=measurement.extra_details.root_dispersion.fraction,
            ntp_last_sync_time=measurement.extra_details.ntp_last_sync_time.seconds,
            ntp_last_sync_time_prec=measurement.extra_details.ntp_last_sync_time.fraction,
            timestamps=time
        )
        session.add(measurement_entry)
        session.commit()
    except Exception as e:
        session.rollback()
        raise DatabaseInsertError(f"Failed to insert measurement: {e}")


def get_measurements_timestamps_ip(session: Session, ip: IPv4Address | IPv6Address | None, start: PreciseTime,
                                   end: PreciseTime) -> list[NtpMeasurement]:
    """
    Fetch measurements for a specific IP address within a precise time range.

    This function queries the `measurements` table, joined with the `times` table,
    and filters the results by:
    - The NTP server IP (`ntp_server_ip`)
    - The timestamp range (`client_sent` field) between `start` and `end`

    Args:
        session (Session): The currently active database session.
        ip (IPv4Address | IPv6Address | None): The IP address of the NTP server.
        start (PreciseTime): The start of the time range to filter on.
        end (PreciseTime): The end of the time range to filter on.

    Returns:
        list[dict]: A list of measurement records. Each record includes:
            - IP, version, stratum
            - client/server send/receive timestamps with fractional parts
            - other measurement metadata

    Raises:
        MeasurementQueryError: If the database query fails.
    """
    try:
        query = (
            session.query(Measurement, Time)
            .join(Time, Measurement.time_id == Time.id)
            .filter(
                Measurement.ntp_server_ip == str(ip),
                Time.client_sent >= start.seconds,
                Time.client_sent <= end.seconds
            )
        )
        return rows_to_measurements(query.all())
    except Exception as e:
        raise MeasurementQueryError(f"Failed to fetch measurements for IP {ip}: {e}")


def get_measurements_timestamps_dn(session: Session, dn: str, start: PreciseTime, end: PreciseTime) -> list[
    NtpMeasurement]:
    """
    Fetches measurements for a specific domain name within a precise time range.

    Similar to `get_measurements_timestamps_ip`, but filters by `ntp_server_name`.
    instead of `ntp_server_ip`.

    Args:
        session (Session): The currently active database session.
        dn (str): The domain name of the NTP server.
        start (PreciseTime): The start of the time range to filter on.
        end (PreciseTime): The end of the time range to filter on.

    Returns:
        list[dict]: A list of measurement records (as dictionaries), each including:
            - Measurement metadata (domain name, version, etc.)
            - Timing data (client/server send/receive with precision)

    Raises:
        MeasurementQueryError: If the database query fails.
    """
    try:
        query = (
            session.query(Measurement, Time)
            .join(Time, Measurement.time_id == Time.id)
            .filter(
                Measurement.ntp_server_name == dn,
                Time.client_sent >= start.seconds,
                Time.client_sent <= end.seconds
            )
        )
        return rows_to_measurements(query.all())
    except Exception as e:
        raise MeasurementQueryError(f"Failed to fetch measurements for domain name: {dn}: {e}")


def get_measurements_for_jitter_ip(session: Session, ip: IPv4Address | IPv6Address | None, number: int = 7) -> list[
    NtpMeasurement]:
    """
    Fetches the last specified number (default 7) of measurements for specific IP address for calculating the jitter.

    This function queries the `measurements` table, joined with the `times` table,
    and filters the results by: The NTP server IP (`ntp_server_ip`) and limits the result to the number specified.

    Args:
        session (Session): The currently active database session.
        ip (IPv4Address | IPv6Address): The IP address of the NTP server.
        number (int): The number of measurements to get.

    Returns:
        list[dict]: A list of measurement records (as dictionaries), each including
            - Measurement metadata (IP, version, stratum, etc.)
            - Timing data (client/server send/receive with fractions)

    Raises:
        MeasurementQueryError: If the database query fails.
    """
    try:
        query = (
            session.query(Measurement, Time)
            .join(Time, Measurement.time_id == Time.id)
            .filter(
                Measurement.ntp_server_ip == ip_to_str(ip)
            )
            .limit(number)
        )
        return rows_to_measurements(query.all())
    except Exception as e:
        raise MeasurementQueryError(f"Failed to fetch measurements for jitter for IP {ip}: {e}")


def get_full_historical_domain_measurements(
        db: Session,
        domain: str,
        start_time: datetime,
        end_time: datetime
) -> List[dict]:
    """
    Retrieve historical domain-based NTP measurements between two timestamps.
    Returns full JSON representations.
    """
    measurements = (
        db.query(FullMeasurementDN)
        .filter(
            FullMeasurementDN.server == domain,
            FullMeasurementDN.created_at_time >= start_time,
            FullMeasurementDN.created_at_time <= end_time,
        )
        .order_by(FullMeasurementDN.created_at_time.desc())
        .all()
    )

    return [
        full_measurement_dn_to_dict(db, m)
        for m in measurements
    ]


def get_full_historical_ip_measurements(
        db: Session,
        ip: str,
        start_time: datetime,
        end_time: datetime
) -> List[dict]:
    """
    Retrieve historical IP-based NTP measurements between two timestamps.
    Returns full JSON representations.
    """
    measurements = (
        db.query(FullMeasurementIP)
        .filter(
            FullMeasurementIP.server_ip == ip,
            FullMeasurementIP.created_at_time >= start_time,
            FullMeasurementIP.created_at_time <= end_time,
        )
        .order_by(FullMeasurementIP.created_at_time.desc())
        .all()
    )

    return [
        full_measurement_ip_to_dict(db, m, part_of_dn_measurement=False)
        for m in measurements
    ]


def get_full_historical_measurements(
        db: Session,
        host: str,
        start_time: datetime,
        end_time: datetime
) -> List[dict]:
    """
    Automatically determines if host is an IP or domain name.
    """
    import ipaddress
    try:
        ipaddress.ip_address(host)
        return get_full_historical_ip_measurements(db, host, start_time, end_time)
    except ValueError:
        return get_full_historical_domain_measurements(db, host, start_time, end_time)


def datetime_to_ntp_timestamp(dt: datetime) -> int:
    """
    Convert a Python datetime (UTC) to a 64-bit NTP timestamp.
    """
    ntp_epoch = datetime(1900, 1, 1, tzinfo=timezone.utc)
    unix_epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    delta = (dt - unix_epoch).total_seconds()
    ntp_seconds = delta + 2208988800  # NTP epoch offset
    return int(ntp_seconds * (2 ** 32))  # 32 bits fractional seconds


def get_ntp_v4_historical_measurements_ip(
        db: Session,
        host: str,
        start_time: datetime,
        end_time: datetime
) -> List[dict]:
    """
    Retrieve historical NTP measurements between two timestamps.
    Returns only NTPv4 JSON representations for performance.
    """
    measurements = (
        db.query(NTPv4Measurement)
        .filter(
            NTPv4Measurement.measured_server_ip == host,
            NTPv4Measurement.client_sent_time >= datetime_to_ntp_timestamp(start_time),
            NTPv4Measurement.client_sent_time <= datetime_to_ntp_timestamp(end_time),
        )
        .all()
    )

    result = []
    for m in measurements:
        d = ntpv4_measurement_to_dict(m, from_ntp_versions=False)
        if d is not None:
            result.append(d)
    return result


def get_ntp_v4_historical_measurements_dn(
        db: Session,
        host: str,
        start_time: datetime,
        end_time: datetime
) -> List[dict]:
    """
    Retrieve historical NTP measurements between two timestamps.
    Returns only NTPv4 JSON representations for performance.
    """
    measurements = (
        db.query(NTPv4Measurement)
        .filter(
            NTPv4Measurement.host == host,
            NTPv4Measurement.client_sent_time >= datetime_to_ntp_timestamp(start_time),
            NTPv4Measurement.client_sent_time <= datetime_to_ntp_timestamp(end_time),
        )
        .all()
    )

    result = []
    for m in measurements:
        d = ntpv4_measurement_to_dict(m, from_ntp_versions=False)
        if d is not None:
            result.append(d)
    return result


def get_ntp_v4_historical_measurements(
        db: Session,
        host: str,
        start_time: datetime,
        end_time: datetime
) -> List[dict]:
    """
    Automatically determines if host is an IP or domain name.
    """
    import ipaddress
    try:
        ipaddress.ip_address(host)
        return get_ntp_v4_historical_measurements_ip(db, host, start_time, end_time)
    except ValueError:
        return get_ntp_v4_historical_measurements_dn(db, host, start_time, end_time)
