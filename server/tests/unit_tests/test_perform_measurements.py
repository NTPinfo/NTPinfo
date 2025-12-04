from ipaddress import IPv4Address
import pytest
from server.app.utils.perform_measurements import *
from unittest.mock import patch, MagicMock
from server.app.dtos.PreciseTime import PreciseTime


@patch("server.app.utils.perform_measurements.domain_name_to_ip_list")
@patch("server.app.utils.perform_measurements.get_timeout_measurement_s")
@patch("server.app.utils.perform_measurements.ntplib.NTPClient")
@patch("server.app.utils.perform_measurements.convert_ntp_response_to_measurement")
def test_perform_ntp_measurement_domain_name_list(mock_convert, mock_ntpclient_class,
                                                  mock_timeout, mock_domain_names):
    mock_domain_names.return_value = ["3.4.5.6", "12.34.123.90", "102.34.123.90"]
    mock_timeout.return_value = 3.5
    mock_measurement1 = MagicMock(spec=NtpMeasurement)
    mock_measurement2 = None
    mock_measurement3 = MagicMock(spec=NtpMeasurement)
    mock_convert.side_effect  = [mock_measurement1, mock_measurement2, mock_measurement3]
    # mock responses from ntplib
    mock_client = MagicMock()
    mock_ntpclient_class.return_value = mock_client
    mock_ntp_response = MagicMock()
    mock_client.request.return_value = mock_ntp_response

    result = perform_ntp_measurement_domain_name_list("time.server.nl", "123.45.67.89", 4, 4)
    assert result == [mock_measurement1, mock_measurement3]
    assert mock_convert.call_count == 3
    assert mock_client.request.call_count == 3


@patch("server.app.utils.perform_measurements.domain_name_to_ip_list")
@patch("server.app.utils.perform_measurements.get_timeout_measurement_s")
@patch("server.app.utils.perform_measurements.ntplib.NTPClient")
@patch("server.app.utils.perform_measurements.convert_ntp_response_to_measurement")
def test_perform_ntp_measurement_domain_name_list_want_ipv6(mock_convert, mock_ntpclient_class,
                                                  mock_timeout, mock_domain_names):
    mock_domain_names.return_value = ["2a06:93c0::24", "3a06:93c0::24", "2a06:90c0::24"]
    mock_timeout.return_value = 3.5
    mock_measurement1 = MagicMock(spec=NtpMeasurement)
    mock_measurement2 = None
    mock_measurement3 = MagicMock(spec=NtpMeasurement)
    mock_convert.side_effect  = [mock_measurement1, mock_measurement2, mock_measurement3]
    # mock responses from ntplib
    mock_client = MagicMock()
    mock_ntpclient_class.return_value = mock_client
    mock_ntp_response = MagicMock()
    mock_client.request.return_value = mock_ntp_response

    result = perform_ntp_measurement_domain_name_list("time.server.nl", "123.45.67.89", 6, 4)
    assert result == [mock_measurement1, mock_measurement3]
    assert mock_convert.call_count == 3
    assert mock_client.request.call_count == 3


@patch("server.app.utils.perform_measurements.domain_name_to_ip_list")
@patch("server.app.utils.perform_measurements.get_timeout_measurement_s")
@patch("server.app.utils.perform_measurements.ntplib.NTPClient")
@patch("server.app.utils.perform_measurements.convert_ntp_response_to_measurement")
def test_perform_ntp_measurement_domain_name_list_none(mock_convert, mock_ntpclient_class,
                                                       mock_timeout, mock_domain_names):
    mock_domain_names.return_value = ["3.4.5.6", "12.34.123.90", "102.34.123.90"]
    mock_timeout.return_value = 3.5
    mock_convert.side_effect  = [None, None, None]
    # mock responses from ntplib
    mock_client = MagicMock()
    mock_ntpclient_class.return_value = mock_client
    mock_ntp_response = MagicMock()
    mock_client.request.return_value = mock_ntp_response

    result = perform_ntp_measurement_domain_name_list("time.server.nl", "123.45.67.89", 4, 4)
    assert result is None
    assert mock_convert.call_count == 3
    assert mock_client.request.call_count == 3

@patch("server.app.utils.perform_measurements.domain_name_to_ip_list")
@patch("server.app.utils.perform_measurements.get_timeout_measurement_s")
@patch("server.app.utils.perform_measurements.ntplib.NTPClient")
@patch("server.app.utils.perform_measurements.convert_ntp_response_to_measurement")
def test_perform_ntp_measurement_domain_name_list_exception(mock_convert, mock_ntpclient_class,
                                                            mock_timeout, mock_domain_names):
    mock_domain_names.return_value = ["3.4.5.6", "12.34.123.90", "102.34.123.90"]
    mock_timeout.return_value = 3.5
    mock_measurement3 = MagicMock(spec=NtpMeasurement)
    mock_convert.side_effect  = [Exception("some message"), mock_measurement3] # 2 instead of 3 because the first time it
    # won't be called as we will throw an error in client.request()

    # mock responses from ntplib
    mock_client = MagicMock()
    mock_ntpclient_class.return_value = mock_client
    mock_ntp_response = MagicMock()
    mock_client.request.side_effect = [Exception("other message"), mock_ntp_response, mock_ntp_response]

    result = perform_ntp_measurement_domain_name_list("time.server.nl", "123.45.67.89", 4, 4)
    assert result == [get_non_responding_ntp_measurement("3.4.5.6", "time.server.nl", 4),
                      get_non_responding_ntp_measurement("12.34.123.90", "time.server.nl", 4), mock_measurement3]
    assert mock_convert.call_count == 2
    assert mock_client.request.call_count == 3

@patch("server.app.utils.perform_measurements.get_timeout_measurement_s")
@patch("server.app.utils.perform_measurements.ntplib.NTPClient")
@patch("server.app.utils.perform_measurements.convert_ntp_response_to_measurement")
def test_perform_ntp_measurement_ip(mock_convert, mock_ntpclient_class, mock_timeout):
    mock_timeout.return_value = 3.5
    mock_measurement = MagicMock(spec=NtpMeasurement)
    mock_convert.return_value = mock_measurement
    # mock responses from ntplib
    mock_client = MagicMock()
    mock_ntpclient_class.return_value = mock_client
    mock_ntp_response = MagicMock()
    mock_client.request.return_value = mock_ntp_response

    result = perform_ntp_measurement_ip("123.45.67.89", 4)
    assert result == mock_measurement

    mock_client.request.assert_called_once_with("123.45.67.89", 4, timeout=3.5)
    mock_convert.assert_called_once_with(response=mock_ntp_response,
                                         server_ip_str="123.45.67.89",
                                         server_name=None,
                                         ntp_version=4)

@patch("server.app.utils.perform_measurements.get_timeout_measurement_s")
@patch("server.app.utils.perform_measurements.ntplib.NTPClient")
@patch("server.app.utils.perform_measurements.convert_ntp_response_to_measurement")
def test_perform_ntp_measurement_ip_exception(mock_convert, mock_ntpclient_class, mock_timeout):

    assert perform_ntp_measurement_ip("something67.89", 4) is None
    mock_timeout.return_value = 3.5
    mock_measurement = MagicMock(spec=NtpMeasurement)
    mock_convert.return_value = mock_measurement
    # mock responses from ntplib
    mock_client = MagicMock()
    mock_ntpclient_class.return_value = mock_client
    mock_client.request.side_effect = Exception("invalid")

    result = perform_ntp_measurement_ip("123.45.67.89", 4)
    assert result is None


@patch("server.app.utils.perform_measurements.get_server_ip")
def test_convert_ntp_response_to_measurement(mock_server_ip):
    mock_server_ip.return_value = IPv4Address("2.4.5.6")
    mock_response = MagicMock()
    mock_response.ref_id = 23467
    mock_response.stratum = 1
    mock_response.orig_timestamp = 3000.23
    mock_response.recv_timestamp = 3001.56
    mock_response.tx_timestamp = 3002.78
    mock_response.dest_timestamp = 3003.97
    mock_response.ref_timestamp = 2999.123
    mock_response.offset = 0.001
    mock_response.delay = 0.002
    mock_response.stratum = 2
    mock_response.precision = -20

    mock_response.root_delay = 0.025
    mock_response.leap = 0
    mock_response.poll = 0.02
    mock_response.root_dispersion = 4000

    result = convert_ntp_response_to_measurement(mock_response, "32.34.35.36", "ntp server", 4)

    assert result is not None

    assert result.server_info.ntp_version == 4
    assert result.server_info.ntp_server_ip == IPv4Address("32.34.35.36")
    assert result.server_info.ntp_server_name == "ntp server"
    assert result.server_info.ntp_server_ref_parent_ip == IPv4Address('0.0.91.171')
    assert result.server_info.ref_name is None

    assert result.timestamps.client_sent_time == PreciseTime(seconds=3000, fraction=987842478)
    assert result.timestamps.server_recv_time == PreciseTime(seconds=3001, fraction=2405181685)
    assert result.timestamps.server_sent_time == PreciseTime(seconds=3002, fraction=3350074490)
    assert result.timestamps.client_recv_time == PreciseTime(seconds=3003, fraction=4166118277)

    assert result.main_details.offset == 0.001
    assert result.main_details.rtt == 0.002
    assert result.main_details.stratum == 2
    assert result.main_details.precision == -20
    assert result.main_details.reachability == ""

    assert result.extra_details.root_delay == PreciseTime(seconds=0, fraction=107374182)
    assert result.extra_details.ntp_last_sync_time == PreciseTime(seconds=2999, fraction=528280977)
    assert result.extra_details.leap == 0
    assert result.extra_details.poll == 0.02
    assert result.extra_details.root_dispersion == PreciseTime(seconds=4000, fraction=0)

    assert result.vantage_point_ip == IPv4Address("2.4.5.6")
    assert print_ntp_measurement(result) == True
    assert print_ntp_measurement(23) == False

@patch("server.app.utils.perform_measurements.get_server_ip")
def test_convert_ntp_response_to_measurement_exception(mock_server_ip):
    mock_server_ip.return_value = None
    mock_response = MagicMock()
    mock_response.ref_id = 23467
    mock_response.stratum = 1
    mock_response.orig_timestamp = 3000.23
    mock_response.recv_timestamp = 3001.56
    mock_response.tx_timestamp = 3002.78
    mock_response.dest_timestamp = 3003.97
    mock_response.ref_timestamp = 2999.123
    mock_response.offset = 0.001
    mock_response.delay = 0.002
    mock_response.stratum = 2
    mock_response.precision = -20

    mock_response.root_delay = 0.025
    mock_response.leap = 0
    mock_response.poll = 0.02
    mock_response.root_dispersion = 4000

    result = convert_ntp_response_to_measurement(mock_response, "32.34.35.36", "ntp server", 4)

    assert result is not None
    assert result.server_info.ntp_version == 4
    assert result.vantage_point_ip is None

    assert convert_ntp_response_to_measurement(mock_response, "something else", "ntp server", 4) is None


@patch("server.app.utils.perform_measurements.requests.post")
@patch("server.app.utils.perform_measurements.get_request_settings")
def test_perform_ripe_measurement_domain_name_normal(mock_settings, mock_post):
    mock_settings.return_value = ({"Authorization": "Key"}, {"some": 36, "other": "other"})
    mock_response = MagicMock()
    mock_response.json.return_value = {"measurements": [85439]}
    mock_post.return_value = mock_response

    settings = AdvancedSettings()
    settings.custom_client_ip = "2.3.4.5"
    settings.wanted_ip_type = 4

    result = perform_ripe_measurement_domain_name("time.apple.com", settings, 10)

    assert result == 85439


@patch("server.app.utils.perform_measurements.requests.post")
@patch("server.app.utils.perform_measurements.get_request_settings")
def test_perform_ripe_measurement_domain_name_normal_want_ipv6(mock_settings, mock_post):
    mock_settings.return_value = ({"Authorization": "Key"}, {"some": 36, "other": "other"})
    mock_response = MagicMock()
    mock_response.json.return_value = {"measurements": [85439]}
    mock_post.return_value = mock_response

    settings = AdvancedSettings()
    settings.custom_client_ip = "2.3.4.5"
    settings.wanted_ip_type = 6

    result = perform_ripe_measurement_domain_name("time.apple.com", settings, 10)

    assert result == 85439

@patch("server.app.utils.perform_measurements.requests.post")
@patch("server.app.utils.perform_measurements.get_request_settings")
def test_perform_ripe_measurement_domain_name_try_catch(mock_settings, mock_post):
    mock_settings.return_value = ({"Authorization": "Key"}, {"somefield": 3, "other": "no"})
    mock_response = MagicMock()
    mock_response.json.return_value = {"error": "not found"}
    mock_post.return_value = mock_response

    settings = AdvancedSettings()
    settings.custom_client_ip = "2.3.4.5"
    settings.wanted_ip_type = 4

    with pytest.raises(RipeMeasurementError, match="not found"):
        perform_ripe_measurement_domain_name("time.apple.com", settings, 10)

    mock_response2 = MagicMock()
    mock_response2.json.return_value = {"something": "error, not found"}
    mock_post.return_value = mock_response2
    with pytest.raises(RipeMeasurementError, match=r"Ripe measurement failed:.*"):
        perform_ripe_measurement_domain_name("time.apple.com", settings, 10)

@patch("server.app.utils.perform_measurements.requests.post")
@patch("server.app.utils.perform_measurements.get_request_settings")
def test_perform_ripe_measurement_domain_name_exceptions(mock_settings, mock_post):
    settings = AdvancedSettings()
    settings.custom_client_ip = "2.3.4.5"
    settings.wanted_ip_type = 4
    # invalid "probes requested"
    with pytest.raises(InputError):
        perform_ripe_measurement_domain_name("ntp.pool.org", settings, -1)
    with pytest.raises(InputError):
        perform_ripe_measurement_domain_name("ntp.pool.org", settings, 0)

    settings.custom_client_ip = "blabla"
    with pytest.raises(InputError):
        perform_ripe_measurement_domain_name("ntp.pool.org", settings, 3)

    settings.custom_client_ip = "2.3.4.5"
    settings.wanted_ip_type = 6
    with pytest.raises(InputError):
        perform_ripe_measurement_domain_name("ntp.pool.org", settings, 0)
    # invalid client ip


@patch("server.app.utils.perform_measurements.requests.post")
@patch("server.app.utils.perform_measurements.get_request_settings")
def test_perform_ripe_measurement_ip_normal(mock_settings, mock_post):
    mock_settings.return_value = ({"Authorization": "Key"}, {"somefield": 3, "other": "no"})
    mock_response = MagicMock()
    mock_response.json.return_value = {"measurements": [12412]}
    mock_post.return_value = mock_response

    settings = AdvancedSettings()
    settings.custom_client_ip = "2.3.4.5"
    settings.wanted_ip_type = 4

    result = perform_ripe_measurement_ip("123.45.67.89", settings, 10)

    assert result == 12412

@patch("server.app.utils.perform_measurements.requests.post")
@patch("server.app.utils.perform_measurements.get_request_settings")
def test_perform_ripe_measurement_ip_try_catch(mock_settings, mock_post):
    mock_settings.return_value = ({"Authorization": "Key"}, {"somefield": 3, "other": "no"})
    mock_response = MagicMock()
    mock_response.json.return_value = {"error": "not found"}
    mock_post.return_value = mock_response

    settings = AdvancedSettings()
    settings.custom_client_ip = "2.3.4.5"
    settings.wanted_ip_type = 4

    with pytest.raises(RipeMeasurementError, match="not found"):
        perform_ripe_measurement_ip("123.45.67.89", settings, 10)

    mock_response2 = MagicMock()
    mock_response2.json.return_value = {"something": "error, not found"}
    mock_post.return_value = mock_response2
    with pytest.raises(RipeMeasurementError, match=r"Ripe measurement failed:.*"):
        perform_ripe_measurement_ip("123.45.67.89", settings, 10)


@patch("server.app.utils.perform_measurements.requests.post")
@patch("server.app.utils.perform_measurements.get_request_settings")
def test_perform_ripe_measurement_ip_exceptions(mock_settings, mock_post):
    settings = AdvancedSettings()
    settings.custom_client_ip = "2.3.4.5"
    settings.wanted_ip_type = 4
    # invalid "probes requested"
    with pytest.raises(InputError):
        perform_ripe_measurement_ip("123.45.67.89", settings, -1)
    with pytest.raises(InputError):
        perform_ripe_measurement_ip("123.45.67.89", settings, 0)
    # invalid client ip
    settings.custom_client_ip = "blabla"
    with pytest.raises(InputError):
        perform_ripe_measurement_ip("123.45.67.89", settings, 3)
    # invalid ntp server IP
    settings.custom_client_ip = "2.3.4.5"
    with pytest.raises(InputError):
        perform_ripe_measurement_ip("123.45aso.67.89", settings, 0)


@patch("server.app.utils.perform_measurements.get_probes")
@patch("server.app.utils.perform_measurements.get_ripe_account_email")
@patch("server.app.utils.perform_measurements.get_ripe_timeout_per_probe_ms")
@patch("server.app.utils.perform_measurements.get_ripe_packets_per_probe")
@patch("server.app.utils.perform_measurements.get_ripe_api_token")
def test_get_request_settings_ok(mock_ripe_api_token, mock_packets, mock_timeout, mock_email, mock_probes):
    mock_ripe_api_token.return_value = "token"
    mock_packets.return_value = 4
    mock_timeout.return_value = 3400
    mock_email.return_value = "email@email.com"
    mock_probes.return_value = [{
        "type": "probes",
        "value": "234,12,865",
        "requested": 3
    },
    {
        "type": "asn",
        "value": "9009",
        "requested": 4
    }]

    (h, c) = get_request_settings(4, "ntp.server.com", "74.22.34.47",28)
    assert h == {
        "Authorization": "Key token",
        "Content-Type": "application/json"
    }
    assert c == {"definitions": [
        {
            "type": "ntp",
            "af": 4,
            "resolve_on_probe": True,
            "description": "NTP measurement to ntp.server.com",
            "packets": 4,
            "timeout": 3400,
            "skip_dns_check": False,
            "target": "ntp.server.com"
        }
    ],
        "is_oneoff": True,
        "bill_to": "email@email.com",
        "probes": [{
            "type": "probes",
            "value": "234,12,865",
            "requested": 3
        },
            {
                "type": "asn",
                "value": "9009",
                "requested": 4
            }]
    }
@patch("server.app.utils.perform_measurements.get_probes")
@patch("server.app.utils.perform_measurements.get_ripe_account_email")
@patch("server.app.utils.perform_measurements.get_ripe_timeout_per_probe_ms")
@patch("server.app.utils.perform_measurements.get_ripe_packets_per_probe")
@patch("server.app.utils.perform_measurements.get_ripe_api_token")
def test_get_request_settings_exception(mock_ripe_api_token, mock_packets, mock_timeout, mock_email, mock_probes):
    mock_ripe_api_token.return_value = "token"
    mock_packets.return_value = 4
    mock_timeout.return_value = 3400
    mock_email.return_value = "email@email.com"
    mock_probes.side_effect = InputError("exc")
    with pytest.raises(Exception):
        get_request_settings(4, "ntp.server.com", "74.22.34.47", 28)

    mock_timeout.reset_mock()
    mock_timeout.side_effect = ValueError("env problem")
    with pytest.raises(ValueError):
        get_request_settings(4, "ntp.server.com", "74.22.34.47", 28)
