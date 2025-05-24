from ipaddress import ip_address

from server.app.services.api_services import *
from unittest.mock import patch, MagicMock
from server.app.models.NtpMeasurement import NtpMeasurement
from datetime import datetime


def mock_precise(seconds=1234567890, fraction=0) -> PreciseTime:
    return PreciseTime(seconds=seconds, fraction=fraction)


def test_ip_to_str():
    assert ip_to_str(IPv4Address("123.45.67.89")) == "123.45.67.89"
    assert ip_to_str(IPv6Address("2001:db8:3333:4444:5555:6666:7777:8888")) == "2001:db8:3333:4444:5555:6666:7777:8888"
    assert ip_to_str(None) is None


def test_get_format():
    measurement = NtpMeasurement(
        vantage_point_ip=ip_address('127.0.0.1'),
        server_info=NtpServerInfo(
            ntp_version=4,
            ntp_server_ip=IPv4Address("192.168.0.1"),
            ntp_server_name="pool.ntp.org",
            ntp_server_ref_parent_ip=None,
            ref_name=None
        ),
        timestamps=NtpTimestamps(
            client_sent_time=mock_precise(1),
            server_recv_time=mock_precise(2),
            server_sent_time=mock_precise(3),
            client_recv_time=mock_precise(4),
        ),
        main_details=NtpMainDetails(
            offset=0.123,
            delay=0.456,
            stratum=2,
            precision=-20.0,
            reachability=""
        ),
        extra_details=NtpExtraDetails(
            root_delay=mock_precise(5),
            ntp_last_sync_time=mock_precise(6),
            leap=0
        )
    )

    formatted_measurement = get_format(measurement, 0.75,["192.168.10.1"])

    assert formatted_measurement["ntp_version"] == 4
    assert formatted_measurement["ntp_server_ip"] == "192.168.0.1"
    assert formatted_measurement["ntp_server_name"] == "pool.ntp.org"
    assert formatted_measurement["ntp_server_ref_parent_ip"] is None
    assert formatted_measurement["ref_name"] is None
    assert formatted_measurement["offset"] == 0.123
    assert formatted_measurement["delay"] == 0.456
    assert formatted_measurement["stratum"] == 2
    assert formatted_measurement["precision"] == -20.0
    assert formatted_measurement["reachability"] == ""
    assert formatted_measurement["leap"] == 0
    assert formatted_measurement["jitter"] == 0.75
    assert formatted_measurement["other_server_ips"] == ["192.168.10.1"]


@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.perform_ntp_measurement_domain_name")
@patch("server.app.services.api_services.perform_ntp_measurement_ip")
def test_measure_with_ip(mock_measure_ip, mock_measure_domain, mock_insert):
    fake_measurement = MagicMock(spec=NtpMeasurement)
    mock_measure_ip.return_value = fake_measurement

    result = measure("192.168.1.1")

    assert result == (fake_measurement,None,None)
    mock_measure_ip.assert_called_once_with("192.168.1.1")
    mock_insert.assert_called_once_with(fake_measurement, mock_insert.call_args[0][1])  # pool
    mock_measure_domain.assert_not_called()


@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.perform_ntp_measurement_domain_name")
@patch("server.app.services.api_services.perform_ntp_measurement_ip")
def test_measure_with_domain(mock_measure_ip, mock_measure_domain, mock_insert):
    fake_measurement = MagicMock(spec=NtpMeasurement)
    mock_measure_domain.return_value = (fake_measurement, ["1.2.3.4"])
    mock_measure_ip.return_value = None

    result = measure("pool.ntp.org")

    assert result == (fake_measurement, None, ["1.2.3.4"])
    mock_measure_domain.assert_called_once_with("pool.ntp.org",None)
    mock_insert.assert_called_once_with(fake_measurement, mock_insert.call_args[0][1])  # pool
    mock_measure_ip.assert_not_called()


@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.perform_ntp_measurement_domain_name")
@patch("server.app.services.api_services.perform_ntp_measurement_ip")
def test_measure_with_invalid_ip(mock_measure_ip, mock_measure_domain, mock_insert):
    fake_measurement = MagicMock(spec=NtpMeasurement)
    fake_ips = ["4.3.2.1"]
    mock_measure_ip.return_value = None
    mock_measure_domain.return_value = (fake_measurement, fake_ips)

    result = measure("not.an.ip")

    assert result == (fake_measurement, None, fake_ips)
    mock_measure_ip.assert_not_called()
    mock_measure_domain.assert_called_once_with("not.an.ip",None)
    mock_insert.assert_called_once_with(fake_measurement, mock_insert.call_args[0][1])


@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.perform_ntp_measurement_domain_name")
@patch("server.app.services.api_services.perform_ntp_measurement_ip")
def test_measure_with_unresolvable_input(mock_measure_ip, mock_measure_domain, mock_insert):
    mock_measure_ip.return_value = None
    mock_measure_domain.return_value = None

    result = measure("not.an.ip")

    assert result is None
    mock_measure_ip.assert_not_called()
    mock_measure_domain.assert_called_once_with("not.an.ip",None)
    mock_insert.assert_not_called()

@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.perform_ntp_measurement_domain_name")
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
    mock_jitter.return_value = 0.75
    result = measure("192.168.1.1", jitter_flag = True, measurement_no = 3)

    assert result == (fake_measurement,0.75,None)
    mock_measure_ip.assert_called_once_with("192.168.1.1")
    mock_insert.assert_called_once_with(fake_measurement, mock_insert.call_args[0][1])  # pool
    mock_jitter.assert_called_once_with(fake_measurement, 3)
    mock_measure_domain.assert_not_called()

@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.perform_ntp_measurement_domain_name")
@patch("server.app.services.api_services.perform_ntp_measurement_ip")
@patch("server.app.services.api_services.calculate_jitter_from_measurements")
def test_measure_no_jitter(mock_jitter, mock_measure_ip, mock_measure_domain, mock_insert):
    fake_measurement = MagicMock(spec=NtpMeasurement)

    mock_measure_ip.return_value = fake_measurement
    mock_jitter.return_value = 0.75
    result = measure("192.168.1.1", None,False, 3)

    assert result == (fake_measurement,None,None)
    mock_measure_ip.assert_called_once_with("192.168.1.1")
    mock_insert.assert_called_once_with(fake_measurement, mock_insert.call_args[0][1])  # pool
    mock_jitter.assert_not_called()
    mock_measure_domain.assert_not_called()

@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.perform_ntp_measurement_domain_name")
@patch("server.app.services.api_services.perform_ntp_measurement_ip")
def test_measure_with_exception(mock_measure_ip, mock_measure_domain, mock_insert):
    mock_measure_ip.return_value = None
    mock_measure_domain.side_effect = Exception("DNS failure")

    result = measure("invalid.server")

    assert result is None
    mock_measure_ip.assert_not_called()
    mock_measure_domain.assert_called_once_with("invalid.server",None)
    mock_insert.assert_not_called()


@patch("server.app.services.api_services.get_measurements_timestamps_ip")
@patch("server.app.services.api_services.parse_ip")
def test_fetch_historic_data_empty_result(mock_parse_ip, mock_get_ip):
    mock_parse_ip.return_value = "10.0.0.5"
    mock_get_ip.return_value = []

    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 2)

    results = fetch_historic_data_with_timestamps("10.0.0.5", start, end)
    assert results == []


@patch("server.app.services.api_services.get_measurements_timestamps_ip")
@patch("server.app.services.api_services.get_measurements_timestamps_dn")
@patch("server.app.services.api_services.parse_ip")
def test_fetch_historic_data_ip(mock_parse_ip, mock_get_dn, mock_get_ip):
    mock_parse_ip.return_value = "192.168.1.1"
    mock_get_ip.return_value = [
        {
            "id": 1,
            'vantage_point_ip': '127.0.0.1',
            "ntp_server_ip": "192.168.1.1",
            "ntp_server_name": "test",
            "ntp_version": 3,
            "ntp_server_ref_parent_ip": "10.0.0.1",
            "ref_name": "parent.ref",

            "offset": 0.1,
            "delay": 0.2,
            "stratum": 2,
            "precision": -20,
            "reachability": 255,

            "root_delay": 10,
            "root_delay_prec": 100,
            "ntp_last_sync_time": 20,
            "ntp_last_sync_time_prec": 200,

            "client_sent": 1, "client_sent_prec": 10,
            "server_recv": 2, "server_recv_prec": 20,
            "server_sent": 3, "server_sent_prec": 30,
            "client_recv": 4, "client_recv_prec": 40,

        }
    ]
    mock_get_dn.return_value = []

    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 2)

    results = fetch_historic_data_with_timestamps("192.168.1.1", start, end)

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
        {
            "id": 1,
            'vantage_point_ip': '127.0.0.1',
            "ntp_server_ip": "192.168.1.1",
            "ntp_server_name": "time.google.com",
            "ntp_version": 3,
            "ntp_server_ref_parent_ip": "10.0.0.1",
            "ref_name": "parent.ref",

            "offset": 0.1,
            "delay": 0.2,
            "stratum": 2,
            "precision": -20,
            "reachability": 255,

            "root_delay": 10,
            "root_delay_prec": 100,
            "ntp_last_sync_time": 20,
            "ntp_last_sync_time_prec": 200,

            "client_sent": 1, "client_sent_prec": 10,
            "server_recv": 2, "server_recv_prec": 20,
            "server_sent": 3, "server_sent_prec": 30,
            "client_recv": 4, "client_recv_prec": 40,

        }
    ]

    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 2)

    results = fetch_historic_data_with_timestamps("time.google.com", start, end)

    assert isinstance(results, list)
    assert len(results) == 1
    print(results[0])
    assert isinstance(results[0], NtpMeasurement)
    mock_get_ip.assert_not_called()
    mock_get_dn.assert_called_once()
