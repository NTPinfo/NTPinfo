from ipaddress import IPv4Address, IPv6Address
from unittest.mock import patch, MagicMock, mock_open
import pytest
from fastapi import HTTPException, Request

from server.app.utils.load_config_data import get_mask_ipv4, get_mask_ipv6
from server.app.utils.ip_utils import ref_id_to_ip_or_name, get_ip_family, get_area_of_ip, get_ip_network_details, \
    ip_to_str, is_this_ip_anycast, randomize_ip, get_server_ip_if_possible, is_private_ip, client_ip_fetch


def test_ip_to_str():
    assert ip_to_str(IPv4Address("123.45.67.89")) == "123.45.67.89"
    assert ip_to_str(IPv6Address("2001:db8:3333:4444:5555:6666:7777:8888")) == "2001:db8:3333:4444:5555:6666:7777:8888"
    assert ip_to_str(None) is None

def test_ref_id_to_ip_or_name_stratum01():
    ip, name = ref_id_to_ip_or_name(0x4e54534e, 0, 4)
    assert ip is None
    assert name == "NTSN"

    ip, name = ref_id_to_ip_or_name(0x4e54534e, 1, 6)
    assert ip is None
    assert name == "NTSN"

def test_ref_id_to_ip_or_name():
    ip, name = ref_id_to_ip_or_name(1590075150, 2, 4)
    assert ip == IPv4Address('94.198.159.14')
    assert name is None

    ip, name = ref_id_to_ip_or_name(1590075150, 2000, 4)
    assert ip is None
    assert name is None

def test_ref_id_to_ip_or_name_ipv6():
    ip, name = ref_id_to_ip_or_name(1590075150, 2, 6)
    assert ip is None
    assert name == "IPv6 MD5 hash: 0x5ec69f0e"

    ip, name = ref_id_to_ip_or_name(1590075150, 2000, 6)
    assert ip is None
    assert name is None

def test_get_ip_family():
    assert get_ip_family("189.24.80.23") == 4
    assert get_ip_family("2001:0db8:85a3:0000:0000:8a2e:0370:7334") == 6
    with pytest.raises(Exception):
        get_ip_family("1sfefef23")


def test_get_area_of_ip():
    assert get_area_of_ip("NL", None) == "WW"
    assert get_area_of_ip("NL", "EU") == "North-Central"
    assert get_area_of_ip("US", "NA") == "West"
    assert get_area_of_ip("BR", "SA") == "West"
    assert get_area_of_ip("ZA", "AF") == "South-Central"
    # North-East
    assert get_area_of_ip("RU", "AS") == "North-East"
    assert get_area_of_ip("KZ", "AS") == "North-East"
    assert get_area_of_ip("MN", "AS") == "North-East"
    # South-East
    assert get_area_of_ip("CN", "AS") == "South-East"


@patch("server.app.utils.ip_utils.get_continent_for_ip")
@patch("server.app.utils.ip_utils.get_country_for_ip")
@patch("server.app.utils.ip_utils.get_asn_for_ip")
def test_get_ip_network_details_success(mock_get_asn, mock_get_country, mock_get_continent):
    mock_get_asn.return_value = "12345"
    mock_get_country.return_value = "NL"
    mock_get_continent.return_value = "EU"

    asn, country, area = get_ip_network_details("1.1.1.1")

    assert asn == "12345"
    assert country == "NL"
    assert area == "North-Central"


@patch("server.app.utils.ip_utils.get_continent_for_ip")
@patch("server.app.utils.ip_utils.get_country_for_ip")
@patch("server.app.utils.ip_utils.get_asn_for_ip")
def test_get_ip_network_details_exception(mock_get_asn, mock_get_country, mock_get_continent):
    mock_get_asn.side_effect = Exception("fail")
    mock_get_country.side_effect = Exception("fail")
    mock_get_continent.side_effect = Exception("fail")

    asn, country, area = get_ip_network_details("1.1.1.1")

    assert asn is None
    assert country is None
    assert area is None


@patch("server.app.utils.ip_utils.get_server_ip")
def test_get_server_ip_if_possible_normal(mock_get_server_ip):
    mock_get_server_ip.side_effect = ["3.4.5.6", "2a06:93c0::24"]
    assert get_server_ip_if_possible(4) == "3.4.5.6"

    mock_get_server_ip.reset_mock()
    assert get_server_ip_if_possible(6) == "2a06:93c0::24"

@patch("server.app.utils.ip_utils.get_server_ip")
def test_get_server_ip_if_possible_exception(mock_get_server_ip):
    mock_get_server_ip.side_effect = [None, Exception("fail")]

    assert get_server_ip_if_possible(6) is None

    mock_get_server_ip.reset_mock()
    mock_get_server_ip.side_effect = [None, "3.4.5.6"]

    assert get_server_ip_if_possible(6) == "3.4.5.6"

@patch("server.app.utils.ip_utils.try_converting_ip")
@patch("server.app.utils.ip_utils.get_server_ip")
def test_client_ip_fetch_not_client_ip_found(mock_server_ip, mock_try_converting):
    mock_server_ip.return_value = "3.4.5.6"
    mock_try_converting.return_value = "4.5.6.7"
    mock_request = MagicMock()
    mock_request.headers.get.return_value = None
    mock_request.client = MagicMock()
    mock_request.client.host = "192.168.0.1"  # private IP

    assert client_ip_fetch(mock_request, 4) == "3.4.5.6"

@patch("server.app.utils.ip_utils.try_converting_ip")
@patch("server.app.utils.ip_utils.get_server_ip")
def test_client_ip_fetch_not_ip(mock_server_ip, mock_try_converting):
    mock_server_ip.return_value = "3.4.5.6"
    mock_try_converting.return_value = "4.5.6.7"
    mock_request = MagicMock()
    mock_request.headers.get.return_value = "something"
    mock_request.client = MagicMock()
    mock_request.client.host = "192.168.0.1"

    assert client_ip_fetch(mock_request, 4) == "3.4.5.6"

@patch("server.app.utils.ip_utils.try_converting_ip")
@patch("server.app.utils.ip_utils.get_server_ip")
def test_client_ip_fetch_private(mock_server_ip, mock_try_converting):
    mock_server_ip.return_value = "3.4.5.6"
    mock_try_converting.return_value = "2400:44a0:1::"
    mock_request = MagicMock()
    mock_request.headers.get.return_value = "192.0.0.1"
    mock_request.client = MagicMock()
    mock_request.client.host = "192.0.0.1"

    assert client_ip_fetch(mock_request, 4) == "3.4.5.6"
    assert client_ip_fetch(mock_request, 6) == "2400:44a0:1::"


@patch("server.app.utils.ip_utils.try_converting_ip")
@patch("server.app.utils.ip_utils.get_server_ip")
def test_client_ip_fetch_exception(mock_server_ip, mock_try_converting):
    mock_server_ip.side_effect = Exception("fail")
    mock_try_converting.return_value = "4.5.6.7"
    mock_request = MagicMock()
    mock_request.headers.get.return_value = "192.0.0.1"
    mock_request.client = MagicMock()
    mock_request.client.host = "192.0.0.1"

    with pytest.raises(HTTPException):
        assert client_ip_fetch(mock_request, 4)

def test_is_private():
    assert is_private_ip("blabla") == False
    assert is_private_ip("84.96.120.251") == False
    assert is_private_ip("192.0.0.1") == True

def test_is_this_ip_anycast_input_errors():
    assert is_this_ip_anycast(None) is False
    assert is_this_ip_anycast("blabla") is False


@patch("server.app.utils.ip_utils.open", new_callable=mock_open, read_data="1.0.0.0/24\ninvalid\n1.3.1.0/16\n")
@patch("server.app.utils.ip_utils.os.path.join")
@patch("server.app.utils.ip_utils.os.path.dirname")
@patch("server.app.utils.ip_utils.os.path.abspath")
def test_is_this_ip_anycast_ipv4(mock_abspath, mock_dirname, mock_join, mock_openn):
    mock_dirname.return_value = "/server/app/utils"
    mock_abspath.return_value = "/server/app/utils/data/prefix"
    mock_join.return_value = "/server/app/utils/prefix"
    # true
    result = is_this_ip_anycast("1.3.0.0")
    assert result is True
    mock_join.assert_called_once_with("/server/app/utils", "..", "..", "anycast-v4-prefixes.txt")

    # false
    mock_join.reset_mock()
    result = is_this_ip_anycast("1.7.0.0")
    assert result is False
    mock_join.assert_called_once_with("/server/app/utils", "..", "..", "anycast-v4-prefixes.txt")


@patch("server.app.utils.ip_utils.open", new_callable=mock_open,
       read_data="2001:4998:170::/48\ninvalid\n2400:44a0:1::/48\n")
@patch("server.app.utils.ip_utils.os.path.join")
@patch("server.app.utils.ip_utils.os.path.dirname")
@patch("server.app.utils.ip_utils.os.path.abspath")
def test_is_this_ip_anycast_ipv6(mock_abspath, mock_dirname, mock_join, mock_openn):
    mock_dirname.return_value = "/server/app/utils"
    mock_abspath.return_value = "/server/app/utils/data/prefix"
    mock_join.return_value = "/server/app/utils/prefix"
    # true
    result = is_this_ip_anycast("2400:44a0:1::")
    assert result is True
    mock_join.assert_called_once_with("/server/app/utils", "..", "..", "anycast-v6-prefixes.txt")

    # false
    mock_join.reset_mock()
    result = is_this_ip_anycast("3001:4998::")
    assert result is False
    mock_join.assert_called_once_with("/server/app/utils", "..", "..", "anycast-v6-prefixes.txt")


@patch("server.app.utils.ip_utils.open", new_callable=mock_open,
       read_data="2001:4998:170::/48\ninvalid\n2400:44a0:1::/48\n")
@patch("server.app.utils.ip_utils.os.path.join")
@patch("server.app.utils.ip_utils.os.path.dirname")
@patch("server.app.utils.ip_utils.os.path.abspath")
def test_is_this_ip_anycast_exception(mock_abspath, mock_dirname, mock_join, mock_openn):
    mock_dirname.return_value = "/server/app/utils"
    mock_abspath.return_value = "/server/app/utils/data/prefix"
    mock_join.side_effect = Exception("not found")
    # error loading database
    result = is_this_ip_anycast("2400:44a0:1::")
    assert result is False


def test_randomize_ipv4():
    ipv4 = IPv4Address("123.45.67.89")
    res = randomize_ip(ipv4)
    assert isinstance(res, IPv4Address)

    original_int = int(ipv4)
    randomized_int = int(res)

    network_mask = (2 ** 32 - 1) << (32 - get_mask_ipv4()) & 0xFFFFFFFF

    original_network = original_int & network_mask
    randomized_network = randomized_int & network_mask

    assert original_network == randomized_network


def test_randomize_ipv6():
    ipv6 = IPv6Address("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
    res = randomize_ip(ipv6)
    assert isinstance(res, IPv6Address)

    original_int = int(ipv6)
    randomized_int = int(res)

    network_mask = (2 ** 128 - 1) << (128 - get_mask_ipv6()) & (2 ** 128 - 1)

    original_network = original_int & network_mask
    randomized_network = randomized_int & network_mask

    assert original_network == randomized_network


def test_randomize_ip_not_ip():
    ip = "no ip"
    res = randomize_ip(ip)
    assert res is None
