import json
from unittest.mock import patch, MagicMock
import pytest

from server.app.utils.analyze_ntp_versions import parse_ntp_versions_response_to_dict, directly_analyze_all_ntp_versions


def test_parse_nts_response_to_dict():
    ans = {"a": 2, "b": 3}
    assert parse_ntp_versions_response_to_dict("{\"a\": 2, \"b\": 3}") == ans
    with pytest.raises(Exception):
        parse_ntp_versions_response_to_dict("{a 2, ff}")



# simulate errors
@patch("server.app.utils.analyze_ntp_versions.subprocess.run")
def test_directly_analyze_all_ntp_versions_no_tool_fail(mock_run):
    mock_run.side_effect = Exception("tool failed")
    result = directly_analyze_all_ntp_versions("time.cloudflare.com","/tool/ntpnts", "draft-ietf-ntp-ntpv5-05")
    assert result["error"].find("Error") != -1