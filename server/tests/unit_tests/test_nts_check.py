import json
from unittest.mock import patch, MagicMock
import pytest

from server.app.dtos.AdvancedSettings import AdvancedSettings
from server.app.models.CustomError import InputError
from server.app.utils.nts_check import parse_nts_response_to_dict, did_ke_performed_on_different_ip, \
    perform_nts_measurement_domain_name, perform_nts_measurement_ip

nts_example = {
      "Host": "time.cloudflare.com",
      "Measured server IP": "162.159.200.123",
      "Measured server port": "123",
      "client_recv_time": 17040536884840854228,
      "client_sent_time": 17040536884552151449,
      "kissCode": "",
      "leap": 0,
      "minError": 0.470486668,
      "mode": 4,
      "offset": -0.503975,
      "poll": 1,
      "precision": 2.9e-8,
      "ref_id": "10.204.8.35",
      "ref_id_raw": "0x0acc0823",
      "ref_time": 17040536627566057007,
      "root_delay": 0.039367676,
      "root_disp": 0.000259399,
      "root_dist": 0.053431569,
      "rtt": 0.066976664,
      "server_recv_time": 17040536877914520677,
      "server_sent_time": 17040536882532335742,
      "stratum": 3,
      "version": 4
    }
nts_error = "NTS session could not be established: key exchange failure key exchange failure: dial tcp: lookup time.cloudflare.comfe: i/o timeout"

def test_parse_nts_response_to_dict():
    ans = {"a": 2, "b": 3}
    assert parse_nts_response_to_dict("{\"a\": 2, \"b\": 3}") == ans
    with pytest.raises(Exception):
        parse_nts_response_to_dict("{a 2, ff}")

@patch("server.app.utils.nts_check.get_right_ntp_nts_binary_tool_for_your_os")
@patch("server.app.utils.nts_check.subprocess.run")
def test_perform_nts_measurement_domain_name_success(mock_run, mock_binary_tool):
    settings = AdvancedSettings()
    settings.wanted_ip_type = -1
    mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(nts_example))
    mock_binary_tool.return_value = "/tool/path/nts_binary"
    result = perform_nts_measurement_domain_name("time.cloudflare.com", settings)
    assert result["NTS succeeded"] is True
    assert str(result["NTS analysis"]).find("It is NTS") != -1
    assert str(result["Measured server IP"]) == "162.159.200.123"
    assert result["Host"] == "time.cloudflare.com"

@patch("server.app.utils.nts_check.get_right_ntp_nts_binary_tool_for_your_os")
@patch("server.app.utils.nts_check.subprocess.run")
def test_perform_nts_measurement_domain_name_success6(mock_run, mock_binary_tool):
    settings = AdvancedSettings()
    settings.wanted_ip_type = 6
    mock_run.return_value = MagicMock(returncode=6, stdout=json.dumps(nts_example))
    mock_binary_tool.return_value = "/tool/path/nts_binary"
    result = perform_nts_measurement_domain_name("time.cloudflare.com", settings)
    assert result["NTS succeeded"] is True
    assert str(result["NTS analysis"]).find("It is NTS, but failed on ipv6") != -1
    assert str(result["NTS analysis"]).find("working NTS IP") != -1
    assert str(result["Measured server IP"]) == "162.159.200.123"
    assert result["Host"] == "time.cloudflare.com"

# simulate errors
@patch("server.app.utils.nts_check.get_right_ntp_nts_binary_tool_for_your_os")
@patch("server.app.utils.nts_check.subprocess.run")
def test_perform_nts_measurement_domain_name_no_tool_fail(mock_run, mock_binary_tool):
    settings = AdvancedSettings()
    settings.wanted_ip_type = -1
    mock_run.return_value = MagicMock(returncode=1, stdout=json.dumps(nts_error))
    mock_binary_tool.side_effect = Exception("not found")
    result = perform_nts_measurement_domain_name("time.cloudflare.com", settings)
    assert result["NTS succeeded"] is False
    assert str(result["NTS analysis"]).find("NTS test could not be performed (binary tool not available)") != -1

@patch("server.app.utils.nts_check.get_right_ntp_nts_binary_tool_for_your_os")
@patch("server.app.utils.nts_check.subprocess.run")
def test_perform_nts_measurement_domain_name_KEfails(mock_run, mock_binary_tool):
    settings = AdvancedSettings()
    settings.wanted_ip_type = -1
    mock_run.return_value = MagicMock(returncode=1, stdout=json.dumps(nts_error))
    mock_binary_tool.return_value = "/tool/path/nts_binary"
    result = perform_nts_measurement_domain_name("time.cloudflare.com", settings)
    assert result["NTS succeeded"] is False
    assert str(result["NTS analysis"]).find(nts_error) != -1

@patch("server.app.utils.nts_check.parse_nts_response_to_dict")
@patch("server.app.utils.nts_check.get_right_ntp_nts_binary_tool_for_your_os")
@patch("server.app.utils.nts_check.subprocess.run")
def test_perform_nts_measurement_domain_name_read_binary_fails_on_retCode0(mock_run, mock_binary_tool, mock_parse):
    settings = AdvancedSettings()
    settings.wanted_ip_type = -1
    mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(nts_example))
    mock_binary_tool.return_value = "/tool/path/nts_binary"
    mock_parse.side_effect = Exception("error parsing")
    result = perform_nts_measurement_domain_name("time.cloudflare.com", settings)
    assert result["NTS succeeded"] is True
    assert str(result["NTS analysis"]).find("NTS measurement succeeded, but could not retrieve data") != -1

@patch("server.app.utils.nts_check.parse_nts_response_to_dict")
@patch("server.app.utils.nts_check.get_right_ntp_nts_binary_tool_for_your_os")
@patch("server.app.utils.nts_check.subprocess.run")
def test_perform_nts_measurement_domain_name_read_binary_fails_on_retCode6(mock_run, mock_binary_tool, mock_parse):
    settings = AdvancedSettings()
    settings.wanted_ip_type = 6
    mock_run.return_value = MagicMock(returncode=6, stdout=json.dumps(nts_example))
    mock_binary_tool.return_value = "/tool/path/nts_binary"
    mock_parse.side_effect = Exception("error parsing")
    result = perform_nts_measurement_domain_name("time.cloudflare.com", settings)
    assert result["NTS succeeded"] is True
    assert str(result["NTS analysis"]).find("Measurement failed on ipv6") != -1
    assert str(result["NTS analysis"]).find("succeeded on the other type. Could not retrieve more data") != -1

@patch("server.app.utils.nts_check.sanitize_string")
@patch("server.app.utils.nts_check.get_right_ntp_nts_binary_tool_for_your_os")
@patch("server.app.utils.nts_check.subprocess.run")
def test_perform_nts_measurement_domain_name_read_binary_fails_on_retCode2(mock_run, mock_binary_tool, mock_sanitize):
    settings = AdvancedSettings()
    settings.wanted_ip_type = 6
    mock_run.return_value = MagicMock(returncode=2, stdout=json.dumps(nts_example))
    mock_binary_tool.return_value = "/tool/path/nts_binary"
    mock_sanitize.side_effect = Exception("error sanitize")
    result = perform_nts_measurement_domain_name("time.cloudflare.com", settings)
    assert result["NTS succeeded"] is False
    assert str(result["NTS analysis"]).find("NTS measurement failed, but could not retrieve more data") != -1

nts_ip_example = {
      "Host": "162.159.200.123",
      "Measured server IP": "162.159.200.123",
      "Measured server port": "123",
      "client_recv_time": 17040545190008101842,
      "client_sent_time": 17040545189824941549,
      "kissCode": "",
      "leap": 0,
      "minError": 0.461195918,
      "mode": 4,
      "offset": -0.482413362,
      "poll": 1,
      "precision": 2.9e-8,
      "ref_id": "10.50.8.163",
      "ref_id_raw": "0x0a3208a3",
      "ref_time": 17040544866557981789,
      "root_delay": 0.039459229,
      "root_disp": 0.000488281,
      "root_dist": 0.041435339,
      "rtt": 0.042434888,
      "server_recv_time": 17040545183517789329,
      "server_sent_time": 17040545187844848848,
      "stratum": 3,
      "version": 4
    }
# nts on specific IP
@patch("server.app.utils.nts_check.get_right_ntp_nts_binary_tool_for_your_os")
@patch("server.app.utils.nts_check.subprocess.run")
def test_perform_nts_measurement_ip_success(mock_run, mock_binary_tool):
    mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(nts_ip_example))
    mock_binary_tool.return_value = "/tool/path/nts_binary"
    result = perform_nts_measurement_ip("162.159.200.123")
    assert result["NTS succeeded"] is True
    assert str(result["NTS analysis"]).find("NTS measurement succeeded on this IP") != -1
    assert str(result["Measured server IP"]) == "162.159.200.123"
    assert result["Host"] == "162.159.200.123"

@patch("server.app.utils.nts_check.did_ke_performed_on_different_ip")
@patch("server.app.utils.nts_check.get_right_ntp_nts_binary_tool_for_your_os")
@patch("server.app.utils.nts_check.subprocess.run")
def test_perform_nts_measurement_ip_successKESwitch(mock_run, mock_binary_tool, mock_did_ke):
    mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(nts_ip_example))
    mock_binary_tool.return_value = "/tool/path/nts_binary"
    mock_did_ke.return_value = (True, "1.2.3.4")
    result = perform_nts_measurement_ip("162.159.200.123")
    assert result["NTS succeeded"] is True
    assert str(result["NTS analysis"]).find("Measurement succeeded, but Key Exchange forced") != -1
    assert str(result["NTS analysis"]).find("1.2.3.4") != -1
    assert result["Host"] == "162.159.200.123" # the original host

@patch("server.app.utils.nts_check.get_right_ntp_nts_binary_tool_for_your_os")
@patch("server.app.utils.nts_check.subprocess.run")
def test_perform_nts_measurement_ip_fail_no_tool(mock_run, mock_binary_tool):
    mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(nts_ip_example))
    mock_binary_tool.side_effect = Exception("not found")
    result = perform_nts_measurement_ip("162.159.200.123")
    assert result["NTS succeeded"] is False
    assert str(result["NTS analysis"]).find("NTS test could not be performed (binary tool not available)") != -1

@patch("server.app.utils.nts_check.get_right_ntp_nts_binary_tool_for_your_os")
@patch("server.app.utils.nts_check.subprocess.run")
def test_perform_nts_measurement_ip_fail_measurement1(mock_run, mock_binary_tool):
    mock_run.return_value = MagicMock(returncode=1, stdout="  KE failed  ")
    mock_binary_tool.return_value = "/tool/path/nts_binary"
    result = perform_nts_measurement_ip("162.159.200.123")
    assert result["NTS succeeded"] is False
    assert str(result["NTS analysis"]) == "KE failed"

@patch("server.app.utils.nts_check.parse_nts_response_to_dict")
@patch("server.app.utils.nts_check.get_right_ntp_nts_binary_tool_for_your_os")
@patch("server.app.utils.nts_check.subprocess.run")
def test_perform_nts_measurement_ip_parsing_tool_response_fail_on_success(mock_run, mock_binary_tool, mock_parse):
    mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(nts_ip_example))
    mock_binary_tool.return_value = "/tool/path/nts_binary"
    mock_parse.side_effect = Exception("error parsing")
    result = perform_nts_measurement_ip("162.159.200.123")
    assert result["NTS succeeded"] is True
    assert str(result["NTS analysis"]) == "NTS measurement succeeded, but could not retrieve data"

@patch("server.app.utils.nts_check.sanitize_string")
@patch("server.app.utils.nts_check.get_right_ntp_nts_binary_tool_for_your_os")
@patch("server.app.utils.nts_check.subprocess.run")
def test_perform_nts_measurement_ip_parsing_tool_response_fail_on_fail2(mock_run, mock_binary_tool, mock_sanitize):
    mock_run.return_value = MagicMock(returncode=2, stdout=json.dumps(nts_ip_example))
    mock_binary_tool.return_value = "/tool/path/nts_binary"
    mock_sanitize.side_effect = Exception("error sanitize")
    result = perform_nts_measurement_ip("162.159.200.123")
    assert result["NTS succeeded"] is False
    assert str(result["NTS analysis"]) == "NTS measurement failed, but could not retrieve more data"

def test_did_ke_performed_on_different_ip():
    d = {"Measured serIP": "223.23.23.23"}
    with pytest.raises(InputError):
        did_ke_performed_on_different_ip("223.23.23.23", d)
    d = {"Measured server IP": "123.23.23.23"}
    assert did_ke_performed_on_different_ip("223.23.23.23", d) == (True, "123.23.23.23")
    assert did_ke_performed_on_different_ip("123.23.23.23", d) == (False, "123.23.23.23")
