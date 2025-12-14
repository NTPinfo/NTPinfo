from server.app.models.CustomError import DNSError
from server.app.dtos.NtpExtraDetails import NtpExtraDetails
from server.app.dtos.NtpMainDetails import NtpMainDetails
from server.app.dtos.NtpServerInfo import NtpServerInfo
from server.app.dtos.NtpTimestamps import NtpTimestamps
from server.app.dtos.PreciseTime import PreciseTime
from server.app.dtos.ProbeData import ProbeData
from ipaddress import ip_address, IPv4Address, IPv6Address

from server.app.services.api_services import *
from unittest.mock import patch, MagicMock
from server.app.dtos.NtpMeasurement import NtpMeasurement
from datetime import datetime
import pytest


def mock_precise(seconds=1234567890, fraction=0) -> PreciseTime:
    return PreciseTime(seconds=seconds, fraction=fraction)


MOCK_NTP_MEASUREMENT = NtpMeasurement(
    vantage_point_ip=ip_address('127.0.0.1'),
    server_info=NtpServerInfo(
        ntp_version=4,
        ntp_server_ip=IPv4Address("192.168.0.1"),
        ntp_server_name="pool.ntp.org",
        ntp_server_ref_parent_ip=None,
        ref_name=None,
        ntp_server_location=ServerLocation(country_code="RO", coordinates=(25.0, -71.0))
    ),
    timestamps=NtpTimestamps(
        client_sent_time=mock_precise(1),
        server_recv_time=mock_precise(2),
        server_sent_time=mock_precise(3),
        client_recv_time=mock_precise(4),
    ),
    main_details=NtpMainDetails(
        offset=0.123,
        rtt=0.456,
        stratum=2,
        precision=-20.0,
        reachability=""
    ),
    extra_details=NtpExtraDetails(
        root_delay=mock_precise(5),
        ntp_last_sync_time=mock_precise(6),
        root_dispersion=mock_precise(7),
        poll=5,
        leap=0
    )
)


def test_get_format():
    measurement = MOCK_NTP_MEASUREMENT

    formatted_measurement = get_format(measurement, 0.75)

    assert formatted_measurement["ntp_version"] == 4
    assert formatted_measurement["ntp_server_ip"] == "192.168.0.1"
    assert formatted_measurement["ntp_server_name"] == "pool.ntp.org"
    assert formatted_measurement["ntp_server_ref_parent_ip"] is None
    assert formatted_measurement["ref_name"] is None
    assert formatted_measurement["offset"] == 0.123
    assert formatted_measurement["rtt"] == 0.456
    assert formatted_measurement["stratum"] == 2
    assert formatted_measurement["precision"] == -20.0
    assert formatted_measurement["reachability"] == ""
    assert formatted_measurement["leap"] == 0
    assert formatted_measurement["jitter"] == 0.75


@patch("server.app.services.api_services.calculate_jitter_from_measurements")
@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.perform_ntp_measurement_domain_name_list")
@patch("server.app.services.api_services.perform_ntp_measurement_ip")
def test_measure_with_ip(mock_measure_ip, mock_measure_domain, mock_insert, mock_jitter):
    fake_measurement = MagicMock(spec=NtpMeasurement)
    mock_measure_ip.return_value = fake_measurement
    fake_session = MagicMock(spec=Session)
    mock_jitter.return_value = (0.5, 1)
    result = measure("192.168.1.1", 4, fake_session)

    assert result == [(fake_measurement, 0.5, 1)]
    mock_measure_ip.assert_called_once_with("192.168.1.1")
    mock_insert.assert_called_once_with(fake_measurement, mock_insert.call_args[0][1])  # pool
    mock_measure_domain.assert_not_called()


@patch("server.app.services.api_services.calculate_jitter_from_measurements")
@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.perform_ntp_measurement_domain_name_list")
@patch("server.app.services.api_services.perform_ntp_measurement_ip")
def test_measure_with_domain(mock_measure_ip, mock_measure_domain, mock_insert, mock_jitter):
    fake_measurement = MagicMock(spec=NtpMeasurement)
    fake_measurement.server_info = MagicMock()
    fake_measurement.server_info.ntp_server_ref_parent_ip = ip_address("1.2.3.4")
    mock_measure_domain.return_value = [fake_measurement]
    mock_measure_ip.return_value = None
    mock_jitter.return_value = (0, 1)
    fake_session = MagicMock(spec=Session)
    result = measure("pool.ntp.org", 4, fake_session)

    assert result == [(fake_measurement, 0, 1)]
    mock_measure_domain.assert_called_once_with("pool.ntp.org", None, 4)
    mock_insert.assert_called_once_with(fake_measurement, mock_insert.call_args[0][1])  # pool
    mock_measure_ip.assert_not_called()


@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.perform_ntp_measurement_domain_name_list")
@patch("server.app.services.api_services.perform_ntp_measurement_ip")
def test_measure_with_invalid_ip(mock_measure_ip, mock_measure_domain, mock_insert):
    fake_measurement = MagicMock(spec=NtpMeasurement)
    mock_measure_ip.return_value = None
    mock_measure_domain.return_value = [fake_measurement]
    fake_session = MagicMock(spec=Session)
    result = measure("not.an.ip", 4, fake_session)

    assert result is None
    mock_measure_ip.assert_not_called()
    mock_measure_domain.assert_called_once_with("not.an.ip", None, 4)
    mock_insert.assert_not_called()


@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.perform_ntp_measurement_domain_name_list")
@patch("server.app.services.api_services.perform_ntp_measurement_ip")
def test_measure_with_unresolvable_input(mock_measure_ip, mock_measure_domain, mock_insert):
    mock_measure_ip.return_value = None
    mock_measure_domain.return_value = None
    fake_session = MagicMock(spec=Session)
    result = measure("not.an.ip", 4, fake_session)

    assert result is None
    mock_measure_ip.assert_not_called()
    mock_measure_domain.assert_called_once_with("not.an.ip", None, 4)
    mock_insert.assert_not_called()


@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.perform_ntp_measurement_domain_name_list")
@patch("server.app.services.api_services.perform_ntp_measurement_ip")
@patch("server.app.services.api_services.calculate_jitter_from_measurements")
def test_measure_with_jitter(mock_jitter, mock_measure_ip, mock_measure_domain, mock_insert):
    fake_measurement = MagicMock(spec=NtpMeasurement)
    fake_measurement.timestamps = NtpTimestamps(
        PreciseTime(0, 0),
        PreciseTime(0, 0),
        PreciseTime(0, 0),
        PreciseTime(0, 0)
    )
    fake_server_info = MagicMock()
    fake_server_info.ntp_server_ip = IPv4Address("192.168.1.1")
    fake_server_info.ntp_version = 4
    fake_measurement.server_info = fake_server_info
    mock_measure_ip.return_value = fake_measurement
    mock_jitter.return_value = 0.75, 4
    fake_session = MagicMock(spec=Session)
    result = measure("192.168.1.1", 4, session=fake_session, measurement_no=7)

    assert result == [(fake_measurement, 0.75, 4)]
    mock_measure_ip.assert_called_once_with("192.168.1.1")
    mock_insert.assert_called_once_with(fake_measurement, mock_insert.call_args[0][1])  # pool
    mock_jitter.assert_called_once_with(fake_session, fake_measurement, 7)
    mock_measure_domain.assert_not_called()


@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.perform_ntp_measurement_domain_name_list")
@patch("server.app.services.api_services.perform_ntp_measurement_ip")
def test_measure_with_exception(mock_measure_ip, mock_measure_domain, mock_insert):
    mock_measure_ip.return_value = None
    mock_measure_domain.side_effect = DNSError("DNS failure")
    fake_session = MagicMock(spec=Session)

    with pytest.raises(DNSError):
        measure("invalid.server", 4, fake_session)
    mock_measure_ip.assert_not_called()
    mock_measure_domain.assert_called_once_with("invalid.server", None, 4)
    mock_insert.assert_not_called()


@patch("server.app.services.api_services.get_measurements_timestamps_ip")
@patch("server.app.services.api_services.parse_ip")
def test_fetch_historic_data_empty_result(mock_parse_ip, mock_get_ip):
    mock_parse_ip.return_value = "10.0.0.5"
    mock_get_ip.return_value = []
    fake_session = MagicMock(spec=Session)
    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 2)

    results = fetch_historic_data_with_timestamps("10.0.0.5", start, end, fake_session)
    assert results == []


@patch("server.app.services.api_services.get_measurements_timestamps_ip")
@patch("server.app.services.api_services.get_measurements_timestamps_dn")
@patch("server.app.services.api_services.parse_ip")
def test_fetch_historic_data_ip(mock_parse_ip, mock_get_dn, mock_get_ip):
    mock_parse_ip.return_value = "192.168.1.1"
    mock_get_ip.return_value = [
        MOCK_NTP_MEASUREMENT
    ]
    mock_get_dn.return_value = []
    fake_session = MagicMock(spec=Session)
    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 2)

    results = fetch_historic_data_with_timestamps("192.168.1.1", start, end, fake_session)

    assert isinstance(results, list)
    assert len(results) == 1
    print(results[0])
    assert isinstance(results[0], NtpMeasurement)
    mock_parse_ip.assert_called_once()
    mock_get_ip.assert_called_once()
    mock_get_dn.assert_not_called()


@patch("server.app.services.api_services.get_measurements_timestamps_ip")
@patch("server.app.services.api_services.get_measurements_timestamps_dn")
def test_fetch_historic_data_domain_name(mock_get_dn, mock_get_ip):
    mock_get_ip.return_value = []
    mock_get_dn.return_value = [
        MOCK_NTP_MEASUREMENT
    ]
    fake_session = MagicMock(spec=Session)
    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 2)

    results = fetch_historic_data_with_timestamps("time.google.com", start, end, fake_session)

    assert isinstance(results, list)
    assert len(results) == 1
    print(results[0])
    assert isinstance(results[0], NtpMeasurement)
    mock_get_ip.assert_not_called()
    mock_get_dn.assert_called_once()


def mock_ripe_parse_result():
    return RipeMeasurement(
        measurement_id=123456,
        ntp_measurement=NtpMeasurement(
            vantage_point_ip=IPv4Address('83.231.3.54'),
            server_info=NtpServerInfo(
                ntp_version=4,
                ntp_server_ip=IPv4Address('18.252.12.124'),
                ntp_server_name='time.some_server.com',
                ntp_server_ref_parent_ip=None,
                ref_name=None,
                ntp_server_location=ServerLocation(country_code="GL", coordinates=(25.2132, -71.4343))
            ),
            timestamps=NtpTimestamps(
                client_sent_time=mock_precise(3957337543, 1845620736),
                server_recv_time=mock_precise(3957337543, 1623990272),
                server_sent_time=mock_precise(3957337543, 1623990272),
                client_recv_time=mock_precise(3957337543, 1963061248)
            ),
            main_details=NtpMainDetails(
                offset=0.065274,
                rtt=0.027344,
                stratum=1,
                precision=9.53674e-07,
                reachability=""
            ),
            extra_details=NtpExtraDetails(
                root_delay=mock_precise(0, 0),
                ntp_last_sync_time=mock_precise(-1, 0),
                poll=1,
                root_dispersion=mock_precise(seconds=0, fraction=327679),
                leap=0
            )
        ),
        probe_data=ProbeData(
            probe_id="9999",
            probe_addr=(IPv4Address('83.231.3.54'), None),
            probe_location=ServerLocation(
                country_code='CZ',
                coordinates=(16.5995, 49.1605)
            )
        ),
        time_to_result=5014.4233,
        ref_id='GPSs'
    )


@patch("server.app.services.api_services.parse_data_from_ripe_measurement")
@patch("server.app.services.api_services.get_data_from_ripe_measurement")
def test_fetch_ripe_data(mock_get_data_from_ripe, mock_parse_data_from_ripe):
    mock_get_data_from_ripe.return_value = []
    mock_parse_data_from_ripe.return_value = [mock_ripe_parse_result()], "Complete"

    result, status = fetch_ripe_data("123456")

    assert isinstance(result, list)
    assert len(result) == 1

    data = result[0]

    assert data["ntp_version"] == 4
    assert data["ripe_measurement_id"] == 123456
    assert data["ntp_server_ip"] == "18.252.12.124"
    assert data["ntp_server_name"] == "time.some_server.com"
    assert data["probe_addr"]["ipv4"] == "83.231.3.54"
    assert data["probe_addr"]["ipv6"] is None
    assert data["probe_id"] == "9999"
    assert data["probe_location"]["country_code"] == "CZ"
    assert data["probe_location"]["coordinates"] == (16.5995, 49.1605)
    assert data["time_to_result"] == 5014.4233
    assert data["stratum"] == 1
    assert data["poll"] == 1
    assert data["precision"] == 9.53674e-07
    assert data["root_dispersion"] == NtpCalculator.calculate_float_time(PreciseTime(seconds=0, fraction=327679))
    assert data["ref_id"] == "GPSs"

    result_data = data["result"][0]
    assert result_data["client_sent_time"].get("seconds") == 3957337543
    assert result_data["rtt"] == 0.027344
    assert result_data["offset"] == 0.065274


def test_get_ripe_format():
    data = get_ripe_format(mock_ripe_parse_result())
    assert isinstance(data, dict)

    assert data["ntp_version"] == 4
    assert data["ripe_measurement_id"] == 123456
    assert data["ntp_server_ip"] == "18.252.12.124"
    assert data["ntp_server_name"] == "time.some_server.com"
    assert data["probe_addr"]["ipv4"] == "83.231.3.54"
    assert data["probe_addr"]["ipv6"] is None
    assert data["probe_id"] == "9999"
    assert data["probe_location"]["country_code"] == "CZ"
    assert data["probe_location"]["coordinates"] == (16.5995, 49.1605)
    assert data["time_to_result"] == 5014.4233
    assert data["stratum"] == 1
    assert data["poll"] == 1
    assert data["precision"] == 9.53674e-07
    assert data["root_dispersion"] == NtpCalculator.calculate_float_time(PreciseTime(seconds=0, fraction=327679))
    assert data["ref_id"] == "GPSs"

    result_data = data["result"][0]
    assert result_data["client_sent_time"].get("seconds") == 3957337543
    assert result_data["rtt"] == 0.027344
    assert result_data["offset"] == 0.065274


@patch("server.app.services.api_services.perform_ripe_measurement_domain_name")
@patch("server.app.services.api_services.perform_ripe_measurement_ip")
def test_perform_ripe_measurement_with_dn_with_client_ip(mock_m_ip, mock_m_dn):
    mock_m_ip.return_value = 0
    mock_m_dn.return_value = 123456
    settings = AdvancedSettings()
    settings.custom_client_ip = "82.211.23.56"
    settings.wanted_ip_type = 4
    m_id = perform_ripe_measurement("time.some_server.com", settings)

    mock_m_ip.assert_not_called()
    mock_m_dn.assert_called_once()

    assert m_id == "123456"


@patch("server.app.services.api_services.perform_ripe_measurement_domain_name")
@patch("server.app.services.api_services.perform_ripe_measurement_ip")
def test_perform_ripe_measurement_with_dn_without_client_ip(mock_m_ip, mock_m_dn):
    mock_m_ip.return_value = 0
    mock_m_dn.return_value = 123456
    settings = AdvancedSettings()
    settings.custom_client_ip = "82.211.23.56"
    settings.wanted_ip_type = 4

    m_id = perform_ripe_measurement("time.some_server.com", settings)

    mock_m_ip.assert_not_called()
    mock_m_dn.assert_called_once()

    assert m_id == "123456"


@patch("server.app.services.api_services.perform_ripe_measurement_domain_name")
@patch("server.app.services.api_services.perform_ripe_measurement_ip")
def test_perform_ripe_measurement_with_ip(mock_m_ip, mock_m_dn):
    mock_m_ip.return_value = 123456
    mock_m_dn.return_value = 0

    settings = AdvancedSettings()
    settings.custom_client_ip = "82.211.23.56"
    settings.wanted_ip_type = 4

    m_id = perform_ripe_measurement("18.252.12.124", settings)

    mock_m_ip.assert_called_once()
    mock_m_dn.assert_not_called()

    assert m_id == "123456"


@patch("server.app.services.api_services.check_all_measurements_scheduled")
def test_check_ripe_measurement_complete_true(mock_check_scheduled):
    mock_check_scheduled.return_value = True

    result = check_ripe_measurement_scheduled("123456")
    mock_check_scheduled.assert_called_once()
    assert result is True


@patch("server.app.services.api_services.check_all_measurements_scheduled")
def test_check_ripe_measurement_complete_false(mock_check_scheduled):
    mock_check_scheduled.return_value = False

    result = check_ripe_measurement_scheduled("123456")
    mock_check_scheduled.assert_called_once()
    assert result is False


@patch("server.app.services.api_services.check_all_measurements_scheduled")
def test_check_ripe_measurement_complete_raises_value_error(mock_check_scheduled):
    mock_check_scheduled.side_effect = ValueError("RIPE API error: Something went wrong")

    with pytest.raises(ValueError, match="RIPE API error: Something went wrong"):
        check_ripe_measurement_scheduled("123456")
    mock_check_scheduled.assert_called_once_with(measurement_id="123456")


@patch("server.app.services.api_services.check_all_measurements_scheduled")
def test_check_ripe_measurement_complete_raises_generic_exception(mock_check_scheduled):
    mock_check_scheduled.side_effect = ValueError("RIPE API error: The number of scheduled probes is negative")

    with pytest.raises(ValueError, match="RIPE API error: The number of scheduled probes is negative"):
        check_ripe_measurement_scheduled("123456")
    mock_check_scheduled.assert_called_once_with(measurement_id="123456")
