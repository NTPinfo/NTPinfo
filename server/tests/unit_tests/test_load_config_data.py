import pytest
from unittest.mock import patch, MagicMock, call
from server.app.utils.load_config_data import *


@patch("server.app.utils.load_config_data.os.path.exists")
def test_load_config(mock):
    mock.return_value = False
    with pytest.raises(FileNotFoundError):
        load_config()


@patch("server.app.utils.load_config_data.Path.exists")
@patch("server.app.utils.load_config_data.get_right_ntp_nts_binary_tool_for_your_os")
@patch("server.app.utils.load_config_data.check_geolite_account_id_and_key")
@patch("server.app.utils.load_config_data.get_max_mind_path_asn")
@patch("server.app.utils.load_config_data.get_max_mind_path_country")
@patch("server.app.utils.load_config_data.get_max_mind_path_city")
@patch("server.app.utils.load_config_data.get_anycast_prefixes_v6_url")
@patch("server.app.utils.load_config_data.get_anycast_prefixes_v4_url")
@patch("server.app.utils.load_config_data.get_ripe_server_timeout")
@patch("server.app.utils.load_config_data.get_ripe_number_of_probes_per_measurement")
@patch("server.app.utils.load_config_data.get_ripe_packets_per_probe")
@patch("server.app.utils.load_config_data.get_ripe_timeout_per_probe_ms")
@patch("server.app.utils.load_config_data.get_edns_timeout_s")
@patch("server.app.utils.load_config_data.get_edns_default_servers")
@patch("server.app.utils.load_config_data.get_mask_ipv6")
@patch("server.app.utils.load_config_data.get_mask_ipv4")
@patch("server.app.utils.load_config_data.get_nr_of_measurements_for_jitter")
@patch("server.app.utils.load_config_data.get_timeout_measurement_s")
@patch("server.app.utils.load_config_data.get_ntp_version")
@patch("server.app.utils.load_config_data.get_ripe_api_token")
@patch("server.app.utils.load_config_data.get_ripe_account_email")
def test_verify_if_config_is_set(mock_ripe_account_email, mock_ripe_api_token, mock_ntp_version,
                                 mock_timeout_measurement_s, mock_nr_of_measurements_for_jitter, mock_mask_ipv4,
                                 mock_mask_ipv6,
                                 mock_edns_default_servers, mock_timeout_s, mock_ripe_timeout_per_probe_ms,
                                 mock_ripe_packets_per_probe,
                                 mock_ripe_number_of_probes_per_measurement, mock_ripe_server_timeout, mock_anycast_4,
                                 mock_anycast_6, mock_city, mock_country,
                                 mock_asn, mock_geolite_account, mock_get_binary, mock_path_exists):
    mock_ripe_account_email.return_value = "e@email.com"
    mock_ripe_api_token.return_value = "e"
    mock_ntp_version.return_value = 4
    mock_timeout_measurement_s.return_value = 3
    mock_nr_of_measurements_for_jitter.return_value = 1
    mock_mask_ipv4.return_value = 21
    mock_mask_ipv6.return_value = 45
    mock_edns_default_servers.return_value = ["9.9.9.9"]
    mock_timeout_s.return_value = 2
    mock_ripe_timeout_per_probe_ms.return_value = 2
    mock_ripe_packets_per_probe.return_value = 2
    mock_ripe_number_of_probes_per_measurement.return_value = 1
    mock_ripe_server_timeout.return_value = 20
    mock_anycast_4.return_value = "link"
    mock_anycast_6.return_value = "link"
    mock_city.return_value = "link"
    mock_country.return_value = "link"
    mock_asn.return_value = "link"
    mock_geolite_account.return_value = True
    mock_get_binary.return_value = Path("tools/")
    mock_path_exists.return_value = True

    verify_if_config_is_set()
    mock_ripe_account_email.assert_called_once()
    mock_ripe_api_token.assert_called_once()
    mock_ntp_version.assert_called_once()
    mock_timeout_measurement_s.assert_called_once()
    mock_nr_of_measurements_for_jitter.assert_called_once()
    mock_mask_ipv4.assert_called_once()
    mock_mask_ipv6.assert_called_once()
    mock_edns_default_servers.assert_called_once()
    mock_timeout_s.assert_called_once()
    mock_ripe_timeout_per_probe_ms.assert_called_once()
    mock_ripe_packets_per_probe.assert_called_once()
    mock_ripe_number_of_probes_per_measurement.assert_called_once()
    mock_ripe_server_timeout.assert_called_once()


@patch("server.app.utils.load_config_data.os.getenv")
def test_get_ripe_account_email(mock):
    mock.return_value = "email"
    assert get_ripe_account_email() == "email"
    mock.assert_called_with("ripe_account_email")

    # None -> Exception
    mock.return_value = None
    with pytest.raises(ValueError):
        get_ripe_account_email()
    mock.assert_called_with("ripe_account_email")


@patch("server.app.utils.load_config_data.os.getenv")
def test_get_ripe_api_token(mock):
    mock.return_value = "ripe token"
    assert get_ripe_api_token() == "ripe token"
    mock.assert_called_with("ripe_api_token")

    # None -> Exception
    mock.return_value = None
    with pytest.raises(ValueError):
        get_ripe_api_token()
    mock.assert_called_with("ripe_api_token")


# ntp version
@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ntp_version_ok(mock_config):
    mock_config["ntp"] = {"version": 5}
    assert get_ntp_version() == 5


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ntp_version_missing_section(mock_config):
    with pytest.raises(ValueError, match="ntp section is missing"):
        get_ntp_version()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ntp_version_missing_var(mock_config):
    mock_config["ntp"] = {"blabla": 5}
    with pytest.raises(ValueError, match="ntp 'version' is missing"):
        get_ntp_version()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ntp_version_different_type(mock_config):
    mock_config["ntp"] = {"version": "no"}
    with pytest.raises(ValueError, match="ntp 'version' must be an 'int'"):
        get_ntp_version()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ntp_version_boundaries(mock_config):
    mock_config["ntp"] = {"version": -1}
    with pytest.raises(ValueError, match="ntp 'version' must be > 0"):
        get_ntp_version()
    mock_config["ntp"] = {"version": 0}
    with pytest.raises(ValueError, match="ntp 'version' must be > 0"):
        get_ntp_version()
    mock_config["ntp"] = {"version": 1}
    assert get_ntp_version() == 1


# ntp timeout_measurement_s
@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_timeout_measurement_s_ok(mock_config):
    mock_config["ntp"] = {"timeout_measurement_s": 5}
    assert get_timeout_measurement_s() == 5
    mock_config["ntp"] = {"timeout_measurement_s": 5.2}
    assert get_timeout_measurement_s() == 5.2


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_timeout_measurement_s_missing_section(mock_config):
    with pytest.raises(ValueError, match="ntp section is missing"):
        get_timeout_measurement_s()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_timeout_measurement_s_missing_var(mock_config):
    mock_config["ntp"] = {"blabla": 5.3}
    with pytest.raises(ValueError, match="ntp 'timeout_measurement_s' is missing"):
        get_timeout_measurement_s()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_timeout_measurement_s_different_type(mock_config):
    mock_config["ntp"] = {"timeout_measurement_s": "no"}
    with pytest.raises(ValueError, match="ntp 'timeout_measurement_s' must be a 'float' or an 'int'"):
        get_timeout_measurement_s()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_timeout_measurement_s_boundaries(mock_config):
    mock_config["ntp"] = {"timeout_measurement_s": -0.1}
    with pytest.raises(ValueError, match="ntp 'timeout_measurement_s' cannot be negative"):
        get_timeout_measurement_s()
    mock_config["ntp"] = {"timeout_measurement_s": 0}
    assert get_timeout_measurement_s() == 0


# ntp number_of_measurements_for_calculating_jitter
@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_nr_of_measurements_for_jitter_ok(mock_config):
    mock_config["ntp"] = {"number_of_measurements_for_calculating_jitter": 6}
    assert get_nr_of_measurements_for_jitter() == 6


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_nr_of_measurements_for_jitter_missing_section(mock_config):
    with pytest.raises(ValueError, match="ntp section is missing"):
        get_nr_of_measurements_for_jitter()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_nr_of_measurements_for_jitter_missing_var(mock_config):
    mock_config["ntp"] = {"blabla": 5}
    with pytest.raises(ValueError, match="ntp 'number_of_measurements_for_calculating_jitter' is missing"):
        get_nr_of_measurements_for_jitter()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_nr_of_measurements_for_jitter_different_type(mock_config):
    mock_config["ntp"] = {"number_of_measurements_for_calculating_jitter": 9.8}
    with pytest.raises(ValueError, match="ntp 'number_of_measurements_for_calculating_jitter' must be an 'int'"):
        get_nr_of_measurements_for_jitter()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_nr_of_measurements_for_jitter_boundaries(mock_config):
    mock_config["ntp"] = {"number_of_measurements_for_calculating_jitter": -1}
    with pytest.raises(ValueError, match="ntp 'number_of_measurements_for_calculating_jitter' must be > 0"):
        get_nr_of_measurements_for_jitter()
    mock_config["ntp"] = {"number_of_measurements_for_calculating_jitter": 0}
    with pytest.raises(ValueError, match="ntp 'number_of_measurements_for_calculating_jitter' must be > 0"):
        get_nr_of_measurements_for_jitter()
    mock_config["ntp"] = {"number_of_measurements_for_calculating_jitter": 1}
    assert get_nr_of_measurements_for_jitter() == 1


# ntp rate_limit
@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_rate_limit_per_client_ip(mock_config):
    mock_config["something"] = {"blabla": 5}
    with pytest.raises(ValueError, match="ntp section is missing"):
        get_rate_limit_per_client_ip()
    mock_config["ntp"] = {"blabla": 5}
    with pytest.raises(ValueError, match="ntp 'rate_limit_per_client_ip' is missing"):
        get_rate_limit_per_client_ip()
    mock_config["ntp"] = {"rate_limit_per_client_ip": 5}
    with pytest.raises(ValueError, match="ntp 'rate_limit_per_client_ip' must be a 'str'"):
        get_rate_limit_per_client_ip()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_rate_limit_per_client_ip_content_invalid(mock_config):
    mock_config["ntp"] = {"rate_limit_per_client_ip": "5 second"}
    with pytest.raises(ValueError, match="ntp 'rate_limit_per_client_ip' must contain 2 parts, separated by a '/'"):
        get_rate_limit_per_client_ip()
    mock_config["ntp"] = {"rate_limit_per_client_ip": "/second"}
    with pytest.raises(ValueError, match="ntp 'rate_limit_per_client_ip' must have first part an integer"):
        get_rate_limit_per_client_ip()
    mock_config["ntp"] = {"rate_limit_per_client_ip": "7/seconds"}
    with pytest.raises(ValueError, match="ntp 'rate_limit_per_client_ip' unit must be either 'second' or 'minute'"):
        get_rate_limit_per_client_ip()
    mock_config["ntp"] = {"rate_limit_per_client_ip": "4/second/"}
    with pytest.raises(ValueError, match="ntp 'rate_limit_per_client_ip' is in invalid format"):
        get_rate_limit_per_client_ip()
    mock_config["ntp"] = {"rate_limit_per_client_ip": "5/hour"}
    with pytest.raises(ValueError, match="ntp 'rate_limit_per_client_ip' unit must be either 'second' or 'minute'"):
        get_rate_limit_per_client_ip()
    mock_config["ntp"] = {"rate_limit_per_client_ip": "4/"}
    with pytest.raises(ValueError, match="ntp 'rate_limit_per_client_ip' unit must be either 'second' or 'minute'"):
        get_rate_limit_per_client_ip()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_rate_limit_per_client_ip_content_ok(mock_config):
    mock_config["ntp"] = {"rate_limit_per_client_ip": "5/second"}
    assert get_rate_limit_per_client_ip() == "5/second"

    mock_config["ntp"] = {"rate_limit_per_client_ip": "40/second"}
    assert get_rate_limit_per_client_ip() == "40/second"

    mock_config["ntp"] = {"rate_limit_per_client_ip": "11/mInute"}
    assert get_rate_limit_per_client_ip() == "11/mInute"


# edns mask_ipv4
@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_mask_ipv4_ok(mock_config):
    mock_config["edns"] = {"mask_ipv4": 6}
    assert get_mask_ipv4() == 6


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_mask_ipv4_missing_section(mock_config):
    with pytest.raises(ValueError, match="edns section is missing"):
        get_mask_ipv4()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_mask_ipv4_missing_var(mock_config):
    mock_config["edns"] = {"blabla": 5}
    with pytest.raises(ValueError, match="edns 'mask_ipv4' is missing"):
        get_mask_ipv4()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_mask_ipv4_different_type(mock_config):
    mock_config["edns"] = {"mask_ipv4": "no"}
    with pytest.raises(ValueError, match="edns 'mask_ipv4' must be an 'int'"):
        get_mask_ipv4()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_mask_ipv4_boundaries(mock_config):
    mock_config["edns"] = {"mask_ipv4": -1}
    with pytest.raises(ValueError, match="edns 'mask_ipv4' must be between 0 and 32 inclusive"):
        get_mask_ipv4()
    mock_config["edns"] = {"mask_ipv4": 33}
    with pytest.raises(ValueError, match="edns 'mask_ipv4' must be between 0 and 32 inclusive"):
        get_mask_ipv4()
    mock_config["edns"] = {"mask_ipv4": 0}
    assert get_mask_ipv4() == 0
    mock_config["edns"] = {"mask_ipv4": 32}
    assert get_mask_ipv4() == 32


# edns mask_ipv6
@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_mask_ipv6_ok(mock_config):
    mock_config["edns"] = {"mask_ipv6": 40}
    assert get_mask_ipv6() == 40


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_mask_ipv6_missing_section(mock_config):
    with pytest.raises(ValueError, match="edns section is missing"):
        get_mask_ipv6()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_mask_ipv6_missing_var(mock_config):
    mock_config["edns"] = {"blabla": 5}
    with pytest.raises(ValueError, match="edns 'mask_ipv6' is missing"):
        get_mask_ipv6()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_mask_ipv6_different_type(mock_config):
    mock_config["edns"] = {"mask_ipv6": "no"}
    with pytest.raises(ValueError, match="edns 'mask_ipv6' must be an 'int'"):
        get_mask_ipv6()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_mask_ipv6_boundaries(mock_config):
    mock_config["edns"] = {"mask_ipv6": -1}
    with pytest.raises(ValueError, match="edns 'mask_ipv6' must be between 0 and 64 inclusive"):
        get_mask_ipv6()
    mock_config["edns"] = {"mask_ipv6": 65}
    with pytest.raises(ValueError, match="edns 'mask_ipv6' must be between 0 and 64 inclusive"):
        get_mask_ipv6()
    mock_config["edns"] = {"mask_ipv6": 0}
    assert get_mask_ipv6() == 0
    mock_config["edns"] = {"mask_ipv6": 64}
    assert get_mask_ipv6() == 64


# edns edns_default_servers
@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_edns_default_servers_ok(mock_config):
    mock_config["edns"] = {"default_order_of_edns_servers": ["2.2.2.2", "8.3.5.3"]}
    assert get_edns_default_servers() == ["2.2.2.2", "8.3.5.3"]


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_edns_default_servers_missing_section(mock_config):
    with pytest.raises(ValueError, match="edns section is missing"):
        get_edns_default_servers()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_edns_default_servers_missing_var(mock_config):
    mock_config["edns"] = {"blabla": 5}
    with pytest.raises(ValueError, match="edns 'default_order_of_edns_servers' is missing"):
        get_edns_default_servers()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_edns_default_servers_different_type(mock_config):
    mock_config["edns"] = {"default_order_of_edns_servers": "3.2.4.5"}
    with pytest.raises(ValueError, match="edns 'default_order_of_edns_servers' must be a 'list'"):
        get_edns_default_servers()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_edns_default_servers_empty(mock_config):
    mock_config["edns"] = {"default_order_of_edns_servers": []}
    with pytest.raises(ValueError, match="edns 'default_order_of_edns_servers' cannot be empty"):
        get_edns_default_servers()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_edns_default_ipv4(mock_config):
    mock_config["edns"] = {"default_order_of_edns_servers": ["2501:4860:4806:8::", "3.2.4.5", "2001:4860:4806:7::"]}
    assert get_ipv4_edns_server() == "3.2.4.5"
    mock_config["edns"] = {"default_order_of_edns_servers": ["2501:4860:4806:8::", Exception("not found")]}
    assert get_ipv4_edns_server() is None


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_edns_default_ipv6(mock_config):
    mock_config["edns"] = {
        "default_order_of_edns_servers": ["55.2.4.5", "2501:4860:4806:8::", "3.2.4.5", "2001:4860:4806:7::"]}
    assert get_ipv6_edns_server() == "2501:4860:4806:8::"
    mock_config["edns"] = {"default_order_of_edns_servers": ["55.2.4.5", Exception("not found"), "55.2.43.5"]}
    assert get_ipv6_edns_server() is None


# edns edns_timeout_s
@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_edns_timeout_s_ok(mock_config):
    mock_config["edns"] = {"edns_timeout_s": 3}
    assert get_edns_timeout_s() == 3
    mock_config["edns"] = {"edns_timeout_s": 3.09}
    assert get_edns_timeout_s() == 3.09


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_edns_timeout_s_missing_section(mock_config):
    with pytest.raises(ValueError, match="edns section is missing"):
        get_edns_timeout_s()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_edns_timeout_s_missing_var(mock_config):
    mock_config["edns"] = {"blabla": 5}
    with pytest.raises(ValueError, match="edns 'edns_timeout_s' is missing"):
        get_edns_timeout_s()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_edns_timeout_s_different_type(mock_config):
    mock_config["edns"] = {"edns_timeout_s": "yes"}
    with pytest.raises(ValueError, match="edns 'edns_timeout_s' must be a 'float' or an 'int' in s"):
        get_edns_timeout_s()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_edns_timeout_s_boundaries(mock_config):
    mock_config["edns"] = {"edns_timeout_s": -2}
    with pytest.raises(ValueError, match="edns 'edns_timeout_s' cannot be negative"):
        get_edns_timeout_s()
    mock_config["edns"] = {"edns_timeout_s": 0}
    assert get_edns_timeout_s() == 0


# ripe_atlas timeout_per_probe_ms
@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ripe_timeout_per_probe_ms_ok(mock_config):
    mock_config["ripe_atlas"] = {"timeout_per_probe_ms": 300}
    assert get_ripe_timeout_per_probe_ms() == 300
    mock_config["ripe_atlas"] = {"timeout_per_probe_ms": 30.09}
    assert get_ripe_timeout_per_probe_ms() == 30.09


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ripe_timeout_per_probe_ms_missing_section(mock_config):
    with pytest.raises(ValueError, match="ripe_atlas section is missing"):
        get_ripe_timeout_per_probe_ms()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ripe_timeout_per_probe_ms_missing_var(mock_config):
    mock_config["ripe_atlas"] = {"blabla": 5}
    with pytest.raises(ValueError, match="ripe_atlas 'timeout_per_probe_ms' is missing"):
        get_ripe_timeout_per_probe_ms()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ripe_timeout_per_probe_ms_different_type(mock_config):
    mock_config["ripe_atlas"] = {"timeout_per_probe_ms": "yes"}
    with pytest.raises(ValueError, match="ripe_atlas 'timeout_per_probe_ms' must be a 'float' or an 'int' in ms"):
        get_ripe_timeout_per_probe_ms()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ripe_timeout_per_probe_ms_boundaries(mock_config):
    mock_config["ripe_atlas"] = {"timeout_per_probe_ms": -0.1}
    with pytest.raises(ValueError, match="ripe_atlas 'timeout_per_probe_ms' must be > 0"):
        get_ripe_timeout_per_probe_ms()
    mock_config["ripe_atlas"] = {"timeout_per_probe_ms": 0}
    with pytest.raises(ValueError, match="ripe_atlas 'timeout_per_probe_ms' must be > 0"):
        get_ripe_timeout_per_probe_ms()
    mock_config["ripe_atlas"] = {"timeout_per_probe_ms": 0.2}
    assert get_ripe_timeout_per_probe_ms() == 0.2


# ripe_atlas packets_per_probe
@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ripe_packets_per_probe_ok(mock_config):
    mock_config["ripe_atlas"] = {"packets_per_probe": 30}
    assert get_ripe_packets_per_probe() == 30


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ripe_packets_per_probe_missing_section(mock_config):
    with pytest.raises(ValueError, match="ripe_atlas section is missing"):
        get_ripe_packets_per_probe()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ripe_packets_per_probe_missing_var(mock_config):
    mock_config["ripe_atlas"] = {"blabla": 5}
    with pytest.raises(ValueError, match="ripe_atlas 'packets_per_probe' is missing"):
        get_ripe_packets_per_probe()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ripe_packets_per_probe_different_type(mock_config):
    mock_config["ripe_atlas"] = {"packets_per_probe": 0.5}
    with pytest.raises(ValueError, match="ripe_atlas 'packets_per_probe' must be an 'int'"):
        get_ripe_packets_per_probe()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ripe_packets_per_probe_boundaries(mock_config):
    mock_config["ripe_atlas"] = {"packets_per_probe": -1}
    with pytest.raises(ValueError, match="ripe_atlas 'packets_per_probe' must be > 0"):
        get_ripe_packets_per_probe()
    mock_config["ripe_atlas"] = {"packets_per_probe": 0}
    with pytest.raises(ValueError, match="ripe_atlas 'packets_per_probe' must be > 0"):
        get_ripe_packets_per_probe()
    mock_config["ripe_atlas"] = {"packets_per_probe": 1}
    assert get_ripe_packets_per_probe() == 1


# ripe_atlas number_of_probes_per_measurement
@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ripe_number_of_probes_per_measurement_ok(mock_config):
    mock_config["ripe_atlas"] = {"number_of_probes_per_measurement": 30}
    assert get_ripe_number_of_probes_per_measurement() == 30


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ripe_number_of_probes_per_measurement_missing_section(mock_config):
    with pytest.raises(ValueError, match="ripe_atlas section is missing"):
        get_ripe_number_of_probes_per_measurement()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ripe_number_of_probes_per_measurement_missing_var(mock_config):
    mock_config["ripe_atlas"] = {"blabla": 5}
    with pytest.raises(ValueError, match="ripe_atlas 'number_of_probes_per_measurement' is missing"):
        get_ripe_number_of_probes_per_measurement()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ripe_number_of_probes_per_measurement_different_type(mock_config):
    mock_config["ripe_atlas"] = {"number_of_probes_per_measurement": 0.5}
    with pytest.raises(ValueError, match="ripe_atlas 'number_of_probes_per_measurement' must be an 'int'"):
        get_ripe_number_of_probes_per_measurement()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ripe_number_of_probes_per_measurement_boundaries(mock_config):
    mock_config["ripe_atlas"] = {"number_of_probes_per_measurement": -1}
    with pytest.raises(ValueError, match="ripe_atlas 'number_of_probes_per_measurement' must be > 0"):
        get_ripe_number_of_probes_per_measurement()
    mock_config["ripe_atlas"] = {"number_of_probes_per_measurement": 0}
    with pytest.raises(ValueError, match="ripe_atlas 'number_of_probes_per_measurement' must be > 0"):
        get_ripe_number_of_probes_per_measurement()
    mock_config["ripe_atlas"] = {"number_of_probes_per_measurement": 1}
    assert get_ripe_number_of_probes_per_measurement() == 1


# ripe_atlas server_timeout
@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ripe_server_timeout_ok(mock_config):
    mock_config["ripe_atlas"] = {"server_timeout": 30}
    assert get_ripe_server_timeout() == 30


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ripe_server_timeout_missing_section(mock_config):
    with pytest.raises(ValueError, match="ripe_atlas section is missing"):
        get_ripe_server_timeout()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ripe_server_timeout_missing_var(mock_config):
    mock_config["ripe_atlas"] = {"blabla": 5}
    with pytest.raises(ValueError, match="ripe_atlas 'server_timeout' is missing"):
        get_ripe_server_timeout()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ripe_server_timeout_different_type(mock_config):
    mock_config["ripe_atlas"] = {"server_timeout": 0.5}
    with pytest.raises(ValueError, match="ripe_atlas 'server_timeout' must be an 'int'"):
        get_ripe_server_timeout()


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_ripe_server_timeout_boundaries(mock_config):
    mock_config["ripe_atlas"] = {"server_timeout": -1}
    with pytest.raises(ValueError, match="ripe_atlas 'server_timeout' must be > 0"):
        get_ripe_server_timeout()
    mock_config["ripe_atlas"] = {"server_timeout": 0}
    with pytest.raises(ValueError, match="ripe_atlas 'server_timeout' must be > 0"):
        get_ripe_server_timeout()
    mock_config["ripe_atlas"] = {"server_timeout": 60}
    assert get_ripe_server_timeout() == 60


# bgp tools
@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_anycast_prefixes_v4_url(mock_config):
    mock_config["ripe_atlas"] = {"number_of_probes_per_measurement": -1}
    with pytest.raises(ValueError, match="bgp_tools section is missing"):
        get_anycast_prefixes_v4_url()
    mock_config["bgp_tools"] = {"blabla": -1}
    with pytest.raises(ValueError, match="bgp_tools 'anycast_prefixes_v4_url' is missing"):
        get_anycast_prefixes_v4_url()
    mock_config["bgp_tools"] = {"anycast_prefixes_v4_url": -1}
    with pytest.raises(ValueError, match="bgp_tools 'anycast_prefixes_v4_url' must be a 'str'"):
        get_anycast_prefixes_v4_url()
    mock_config["bgp_tools"] = {"anycast_prefixes_v4_url": "link"}
    assert get_anycast_prefixes_v4_url() == "link"


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_anycast_prefixes_v6_url(mock_config):
    mock_config["ripe_atlas"] = {"bla": -1}
    with pytest.raises(ValueError, match="bgp_tools section is missing"):
        get_anycast_prefixes_v6_url()
    mock_config["bgp_tools"] = {"blabla": -1}
    with pytest.raises(ValueError, match="bgp_tools 'anycast_prefixes_v6_url' is missing"):
        get_anycast_prefixes_v6_url()
    mock_config["bgp_tools"] = {"anycast_prefixes_v6_url": -1}
    with pytest.raises(ValueError, match="bgp_tools 'anycast_prefixes_v6_url' must be a 'str'"):
        get_anycast_prefixes_v6_url()
    mock_config["bgp_tools"] = {"anycast_prefixes_v6_url": "link"}
    assert get_anycast_prefixes_v6_url() == "link"


# max mind
@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_max_mind_path_city(mock_config):
    mock_config["ripe_atlas"] = {"bla": -1}
    with pytest.raises(ValueError, match="max_mind section is missing"):
        get_max_mind_path_city()
    mock_config["max_mind"] = {"bla": -1}
    with pytest.raises(ValueError, match="max_mind 'path_city' is missing"):
        get_max_mind_path_city()
    mock_config["max_mind"] = {"path_city": "link"}
    assert isinstance(get_max_mind_path_city(), str)


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_max_mind_path_country(mock_config):
    mock_config["ripe_atlas"] = {"bla": -1}
    with pytest.raises(ValueError, match="max_mind section is missing"):
        get_max_mind_path_country()
    mock_config["max_mind"] = {"bla": -1}
    with pytest.raises(ValueError, match="max_mind 'path_country' is missing"):
        get_max_mind_path_country()
    mock_config["max_mind"] = {"path_country": "link"}
    assert isinstance(get_max_mind_path_country(), str)


@patch("server.app.utils.load_config_data.config", new_callable=dict)
def test_get_max_mind_path_asn(mock_config):
    mock_config["ripe_atlas"] = {"bla": -1}
    with pytest.raises(ValueError, match="max_mind section is missing"):
        get_max_mind_path_asn()
    mock_config["max_mind"] = {"bla": -1}
    with pytest.raises(ValueError, match="max_mind 'path_asn' is missing"):
        get_max_mind_path_asn()
    mock_config["max_mind"] = {"path_asn": "link"}
    assert isinstance(get_max_mind_path_asn(), str)


@patch("server.app.utils.load_config_data.os.getenv")
def test_check_geolite_account_id_and_key(mock):
    mock.side_effect = [None, "something"]
    assert check_geolite_account_id_and_key() == False
    mock.assert_called_with("ACCOUNT_ID")

    mock.reset_mock()
    mock.side_effect = ["something", None]
    assert check_geolite_account_id_and_key() == False
    assert mock.call_args_list == [call("ACCOUNT_ID"), call("LICENSE_KEY")]

    mock.reset_mock()
    mock.side_effect = ["something", "else"]
    assert check_geolite_account_id_and_key() == True
    assert mock.call_args_list == [call("ACCOUNT_ID"), call("LICENSE_KEY")]
    # None -> Exception
    # mock.return_value = None
    # with pytest.raises(ValueError):
    #     get_ripe_account_email()
    # mock.assert_called_with("ripe_account_email")
