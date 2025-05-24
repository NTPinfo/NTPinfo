from ipaddress import IPv6Address, IPv4Address, ip_address

from server.app.utils.perform_measurements import *
#import unittest
from unittest.mock import patch, MagicMock
from server.app.models.PreciseTime import PreciseTime

def make_mock_measurement(seconds_offset: int) -> NtpMeasurement:
    fake_measurement = MagicMock(spec=NtpMeasurement)

    timestamps = NtpTimestamps(
        PreciseTime(0, 0),
        PreciseTime(seconds_offset // 4, 0),
        PreciseTime(seconds_offset // 2, 0),
        PreciseTime(seconds_offset, 0)
    )
    fake_server_info = MagicMock()
    fake_server_info.ntp_server_ip = IPv4Address("1.2.3.4")
    fake_server_info.ntp_version = 4
    fake_measurement.timestamps = timestamps
    fake_measurement.server_info = fake_server_info

    return fake_measurement


def test_ntp_precise_time_to_human_date():
    t=PreciseTime(None,12345)
    assert ntp_precise_time_to_human_date(t)==""
    t2=PreciseTime(3955513183,623996928)
    assert ntp_precise_time_to_human_date(t2)=="2025-05-06 09:39:43.145286 UTC"

def test_ref_id_to_ip_or_name():
    ip,name=ref_id_to_ip_or_name(1590075150,2)
    assert ip==IPv4Address('94.198.159.14')
    assert name is None

    ip,name=ref_id_to_ip_or_name(1590075150,2000)
    assert ip is None
    assert name is None

@patch("server.app.utils.perform_measurements.socket.getaddrinfo")
@patch("server.app.utils.perform_measurements.ntplib.NTPClient.request")
def test_perform_ntp_measurement_domain_name(mock_request, mock_getaddrinfo):
    # Mock socket.getaddrinfo
    mock_getaddrinfo.return_value = [(None, None, None, None, ("123.45.67.89", 0))]

    # Create a fake ntplib response
    mock_response = MagicMock()
    mock_response.ref_id = 1590075150

    mock_response.ref_timestamp = 3948758383.2
    mock_response.orig_timestamp = 3948758384.0
    mock_response.recv_timestamp = 3948758385.0
    mock_response.tx_timestamp = 3948758386.0
    mock_response.dest_timestamp = 3948758389.2

    mock_response.offset = 0.001
    mock_response.delay = 0.002
    mock_response.stratum = 2
    mock_response.precision = -20

    mock_response.root_delay = 0.025
    mock_response.leap = 0
    mock_request.return_value = mock_response

    result_tuple = perform_ntp_measurement_domain_name("mock.ntp.server",None)

    assert result_tuple is not None
    result,l = result_tuple
    assert l == ["123.45.67.89"]

    assert result.server_info.ntp_version == 3
    assert result.server_info.ntp_server_ip == IPv4Address("123.45.67.89")
    assert result.server_info.ntp_server_name == "mock.ntp.server"
    assert result.server_info.ntp_server_ref_parent_ip == IPv4Address("94.198.159.14")
    assert result.server_info.ref_name is None

    assert result.timestamps.client_sent_time == PreciseTime(seconds=3948758389, fraction=858992640)
    assert result.timestamps.server_recv_time == PreciseTime(seconds=3948758384, fraction=0)
    assert result.timestamps.server_sent_time == PreciseTime(seconds=3948758385, fraction=0)
    assert result.timestamps.client_recv_time == PreciseTime(seconds=3948758386, fraction=0)

    assert result.main_details.offset == 0.001
    assert result.main_details.delay == 0.002
    assert result.main_details.stratum == 2
    assert result.main_details.precision == -20
    assert result.main_details.reachability == ""

    assert result.extra_details.root_delay == PreciseTime(seconds=0, fraction=107374182)
    assert result.extra_details.ntp_last_sync_time == PreciseTime(seconds=3948758383, fraction=858992640)
    assert result.extra_details.leap == 0


@patch("server.app.utils.perform_measurements.ntplib.NTPClient.request")
def test_perform_ntp_measurement_ip(mock_request):

    # Create a fake ntplib response
    mock_response = MagicMock()
    mock_response.ref_id = 1590075150

    mock_response.ref_timestamp = 3948758383.2
    mock_response.orig_timestamp = 3948758384.0
    mock_response.recv_timestamp = 3948758385.0
    mock_response.tx_timestamp = 3948758386.0
    mock_response.dest_timestamp = 3948758389.2

    mock_response.offset = 0.001
    mock_response.delay = 0.002
    mock_response.stratum = 2
    mock_response.precision = -20

    mock_response.root_delay = 0.025
    mock_response.leap = 0
    mock_request.return_value = mock_response

    result = perform_ntp_measurement_ip("123.45.67.89",3)

    assert result is not None

    assert result.server_info.ntp_version == 3
    assert result.server_info.ntp_server_ip == IPv4Address("123.45.67.89")
    assert result.server_info.ntp_server_name is None
    assert result.server_info.ntp_server_ref_parent_ip == IPv4Address("94.198.159.14")
    assert result.server_info.ref_name is None

    assert result.timestamps.client_sent_time == PreciseTime(seconds=3948758389, fraction=858992640)
    assert result.timestamps.server_recv_time == PreciseTime(seconds=3948758384, fraction=0)
    assert result.timestamps.server_sent_time == PreciseTime(seconds=3948758385, fraction=0)
    assert result.timestamps.client_recv_time == PreciseTime(seconds=3948758386, fraction=0)

    assert result.main_details.offset == 0.001
    assert result.main_details.delay == 0.002
    assert result.main_details.stratum == 2
    assert result.main_details.precision == -20
    assert result.main_details.reachability == ""

    assert result.extra_details.root_delay == PreciseTime(seconds=0, fraction=107374182)
    assert result.extra_details.ntp_last_sync_time == PreciseTime(seconds=3948758383, fraction=858992640)
    assert result.extra_details.leap == 0

    assert  print_ntp_measurement(result) == True
    assert  print_ntp_measurement(23) == False

@patch("server.app.utils.perform_measurements.perform_ntp_measurement_ip")
def test_calculate_jitter_from_measurements(mock_perform):
    fake_initial_measurement = make_mock_measurement(1)

    other_measurements = [
        make_mock_measurement(5),
        make_mock_measurement(3),
        make_mock_measurement(4),
        make_mock_measurement(6)
    ]
    mock_perform.side_effect = other_measurements
    times = 4
    res = calculate_jitter_from_measurements(fake_initial_measurement, times)

    offsets = [NtpCalculator.calculate_offset(fake_initial_measurement.timestamps)] + [NtpCalculator.calculate_offset(m.timestamps) for m in other_measurements]

    expected = NtpCalculator.calculate_jitter(offsets)

    assert res == expected
    assert mock_perform.call_count == times

@patch("server.app.utils.perform_measurements.perform_ntp_measurement_ip")

def test_calculate_jitter_from_measurements_with_none(mock_perform):
    fake_initial_measurement = make_mock_measurement(1)

    other_measurements = [
        make_mock_measurement(5),
        make_mock_measurement(3),
        None,
        None,
        make_mock_measurement(6)
    ]
    mock_perform.side_effect = other_measurements
    times = 5
    res = calculate_jitter_from_measurements(fake_initial_measurement, times)

    offsets = [NtpCalculator.calculate_offset(fake_initial_measurement.timestamps)]
    for m in other_measurements[:1]:
        offsets.append(NtpCalculator.calculate_offset(m.timestamps))

    expected = NtpCalculator.calculate_jitter(offsets)

    assert res == expected
    assert mock_perform.call_count == 3
