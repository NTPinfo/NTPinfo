import pytest

from server.app.dtos.AdvancedSettings import AdvancedSettings
from server.app.models.CustomError import InputError
from server.app.utils.ripe_probes import get_random_probes, get_area_probes, get_asn_probes, get_prefix_probes, \
    get_country_probes, get_best_probes_with_multiple_attributes, get_probes, get_available_probes_asn, \
    get_available_probes_prefix, \
    get_available_probes_country, get_best_probes_matched_by_single_attribute, get_available_probes_asn_and_prefix, \
    get_available_probes_asn_and_country, get_probes_by_ids, consume_probes
from unittest.mock import patch, MagicMock


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.get_probes_by_ids")
@patch("server.app.utils.ripe_probes.get_best_probes_with_multiple_attributes")
@patch("server.app.utils.ripe_probes.get_best_probes_matched_by_single_attribute")
@patch("server.app.utils.ripe_probes.get_ip_network_details")
@patch("server.app.utils.ripe_probes.get_prefix_from_ip")
def test_get_probes_all_good(mock_get_prefix_from_ip, mock_get_network_details, mock_get_best_single,
                             mock_get_multiple_attributes, mock_get_probes_by_ids, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_get_multiple_attributes.return_value = (9, {345})
    mock_get_best_single.return_value = (0, {345, 11, 22, 33, 45, 55, 66, 77, 88, 99})
    mock_get_probes_by_ids.return_value = {
        'requested': 10,
        'type': 'probes',
        'value': '345,11,22,33,45,55,66,77,88,99'
    }

    mock_get_prefix_from_ip.return_value = "80.211.224.0/20"
    mock_get_network_details.return_value = ("AS15169", "IT", "West")

    settings = AdvancedSettings()
    settings.custom_client_ip = "80.211.238.247"
    settings.wanted_ip_type = 4

    probes_result = get_probes(settings,10)

    answer = [{'requested': 10, 'type': 'probes', 'value': '345,11,22,33,45,55,66,77,88,99'}
              ]
    assert probes_result == answer


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.get_probes_by_ids")
@patch("server.app.utils.ripe_probes.get_best_probes_with_multiple_attributes")
@patch("server.app.utils.ripe_probes.get_best_probes_matched_by_single_attribute")
@patch("server.app.utils.ripe_probes.get_ip_network_details")
@patch("server.app.utils.ripe_probes.get_prefix_from_ip")
def test_get_probes_some_found_from_first_try(mock_get_prefix_from_ip, mock_get_network_details, mock_get_best_single,
                                              mock_get_multiple_attributes, mock_get_probes_by_ids, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_get_multiple_attributes.return_value = (0, {11, 22, 33, 45, 55})
    mock_get_best_single.return_value = (2, {345, 11, 22, 33, 45, 55, 66, 77, 88, 99})
    mock_get_probes_by_ids.return_value = {
        'requested': 5,
        'type': 'probes',
        'value': '11,22,33,45,55'
    }
    mock_get_prefix_from_ip.return_value = None
    mock_get_network_details.return_value = ("AS15169", "IT", None)

    settings = AdvancedSettings()
    settings.custom_client_ip = "80.211.238.247"
    settings.wanted_ip_type = 4

    probes_result = get_probes(settings, 5)
    mock_get_multiple_attributes.assert_called_with(client_ip="80.211.238.247", current_probes_set=set(), ip_asn="AS15169",
                                            ip_prefix=None, ip_country="IT", ip_family=4,
                                            probes_requested=5, strict_this_country=False)

    assert mock_get_multiple_attributes.call_count == 1
    assert mock_get_best_single.call_count == 0
    answer = [{'requested': 5, 'type': 'probes', 'value': '11,22,33,45,55'}]
    assert probes_result == answer


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.get_probes_by_ids")
@patch("server.app.utils.ripe_probes.get_best_probes_with_multiple_attributes")
@patch("server.app.utils.ripe_probes.get_best_probes_matched_by_single_attribute")
@patch("server.app.utils.ripe_probes.get_ip_network_details")
@patch("server.app.utils.ripe_probes.get_prefix_from_ip")
def test_get_probes_some_found_from_first_try_ipv4_ask_ipv6(mock_get_prefix_from_ip, mock_get_network_details, mock_get_best_single,
                                              mock_get_multiple_attributes, mock_get_probes_by_ids, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_get_multiple_attributes.return_value = (0, {11, 22, 33, 45, 55})
    mock_get_best_single.return_value = (2, {345, 11, 22, 33, 45, 55, 66, 77, 88, 99})
    mock_get_probes_by_ids.return_value = {
        'requested': 5,
        'type': 'probes',
        'value': '11,22,33,45,55'
    }
    mock_get_prefix_from_ip.return_value = "80.211.224.0/20"
    mock_get_network_details.return_value = ("AS15169", "IT", None)

    settings = AdvancedSettings()
    settings.custom_client_ip = "80.211.238.247"
    settings.wanted_ip_type = 6

    probes_result = get_probes(settings, 5)
    mock_get_multiple_attributes.assert_called_with(client_ip="80.211.238.247", current_probes_set=set(), ip_asn="AS15169",
                                            ip_prefix=None, ip_country="IT", ip_family=6,
                                            probes_requested=5, strict_this_country=False)

    assert mock_get_multiple_attributes.call_count == 1
    assert mock_get_best_single.call_count == 0
    answer = [{'requested': 5, 'type': 'probes', 'value': '11,22,33,45,55'}]
    assert probes_result == answer


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.get_probes_by_ids")
@patch("server.app.utils.ripe_probes.get_best_probes_with_multiple_attributes")
@patch("server.app.utils.ripe_probes.get_best_probes_matched_by_single_attribute")
@patch("server.app.utils.ripe_probes.get_ip_network_details")
@patch("server.app.utils.ripe_probes.get_prefix_from_ip")
def test_get_probes_area(mock_get_prefix_from_ip, mock_get_network_details, mock_get_best_single,
                         mock_get_multiple_attributes, mock_get_probes_by_ids, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_get_multiple_attributes.return_value = (9, {345})
    mock_get_best_single.return_value = (2, {345, 11, 22, 33, 45, 55, 66, 77})
    mock_get_probes_by_ids.return_value = {
        'requested': 8,
        'type': 'probes',
        'value': '345,11,22,33,45,55,66,77'
    }

    mock_get_prefix_from_ip.return_value = "80.211.224.0/20"
    mock_get_network_details.return_value = ("AS15169", "IT", "West")

    settings = AdvancedSettings()
    settings.custom_client_ip = "80.211.238.247"
    settings.wanted_ip_type = 4

    probes_result = get_probes(settings, 10)
    mock_get_best_single.assert_called_with(client_ip="80.211.238.247", current_probes_set={345}, ip_asn="AS15169",
                                            ip_prefix="80.211.224.0/20", ip_country="IT", ip_family=4,
                                            probes_requested=9,
                                            strict_this_asn=False, strict_this_country=False)

    answer = [{'requested': 8, 'type': 'probes', 'value': '345,11,22,33,45,55,66,77'},
              {'requested': 2, 'type': 'area', 'value': 'West'}]
    assert probes_result == answer


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.get_probes_by_ids")
@patch("server.app.utils.ripe_probes.get_best_probes_with_multiple_attributes")
@patch("server.app.utils.ripe_probes.get_best_probes_matched_by_single_attribute")
@patch("server.app.utils.ripe_probes.get_ip_network_details")
@patch("server.app.utils.ripe_probes.get_prefix_from_ip")
def test_get_probes_area_ipv4_ask_ipv6(mock_get_prefix_from_ip, mock_get_network_details, mock_get_best_single,
                         mock_get_multiple_attributes, mock_get_probes_by_ids, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_get_multiple_attributes.return_value = (9, {345})
    mock_get_best_single.return_value = (2, {345, 11, 22, 33, 45, 55, 66, 77})
    mock_get_probes_by_ids.return_value = {
        'requested': 8,
        'type': 'probes',
        'value': '345,11,22,33,45,55,66,77'
    }

    mock_get_prefix_from_ip.return_value = "80.211.224.0/20"
    mock_get_network_details.return_value = ("AS15169", "IT", "West")

    settings = AdvancedSettings()
    settings.custom_client_ip = "80.211.238.247"
    settings.wanted_ip_type = 6

    probes_result = get_probes(settings, 10)
    mock_get_best_single.assert_called_with(client_ip="80.211.238.247", current_probes_set={345}, ip_asn="AS15169",
                                            ip_prefix=None, ip_country="IT", ip_family=6,
                                            probes_requested=9,
                                            strict_this_asn=False, strict_this_country=False)

    answer = [{'requested': 8, 'type': 'probes', 'value': '345,11,22,33,45,55,66,77'},
              {'requested': 2, 'type': 'area', 'value': 'West'}]
    assert probes_result == answer


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.get_probes_by_ids")
@patch("server.app.utils.ripe_probes.get_best_probes_with_multiple_attributes")
@patch("server.app.utils.ripe_probes.get_best_probes_matched_by_single_attribute")
@patch("server.app.utils.ripe_probes.get_ip_network_details")
@patch("server.app.utils.ripe_probes.get_prefix_from_ip")
def test_get_probes_area_ipv6_ask_ipv4(mock_get_prefix_from_ip, mock_get_network_details, mock_get_best_single,
                         mock_get_multiple_attributes, mock_get_probes_by_ids, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_get_multiple_attributes.return_value = (9, {345})
    mock_get_best_single.return_value = (2, {345, 11, 22, 33, 45, 55, 66, 77})
    mock_get_probes_by_ids.return_value = {
        'requested': 8,
        'type': 'probes',
        'value': '345,11,22,33,45,55,66,77'
    }

    mock_get_prefix_from_ip.return_value = "2a06:93c0::/48"
    mock_get_network_details.return_value = ("AS15169", "IT", "West")

    settings = AdvancedSettings()
    settings.custom_client_ip = "2a06:93c0::24"
    settings.wanted_ip_type = 4

    probes_result = get_probes(settings, 10)

    mock_get_multiple_attributes.assert_called_with(client_ip="2a06:93c0::24", current_probes_set=set(),
                                                    ip_asn="AS15169",
                                                    ip_prefix=None, ip_country="IT", ip_family=4,
                                                    probes_requested=10,
                                                    strict_this_country=False)
    mock_get_best_single.assert_called_with(client_ip="2a06:93c0::24", current_probes_set={345}, ip_asn="AS15169",
                                            ip_prefix=None, ip_country="IT", ip_family=4,
                                            probes_requested=9,
                                            strict_this_asn=False, strict_this_country=False)

    answer = [{'requested': 8, 'type': 'probes', 'value': '345,11,22,33,45,55,66,77'},
              {'requested': 2, 'type': 'area', 'value': 'West'}]
    assert probes_result == answer


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.get_probes_by_ids")
@patch("server.app.utils.ripe_probes.get_best_probes_with_multiple_attributes")
@patch("server.app.utils.ripe_probes.get_best_probes_matched_by_single_attribute")
@patch("server.app.utils.ripe_probes.get_ip_network_details")
@patch("server.app.utils.ripe_probes.get_prefix_from_ip")
def test_get_probes_random(mock_get_prefix_from_ip, mock_get_network_details, mock_get_best_single,
                           mock_get_multiple_attributes, mock_get_probes_by_ids, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_get_multiple_attributes.return_value = (9, {345})
    mock_get_best_single.return_value = (2, {345, 11, 22, 33, 45, 55, 66, 77})
    mock_get_probes_by_ids.return_value = {
        'requested': 8,
        'type': 'probes',
        'value': '345,11,22,33,45,55,66,77'
    }

    mock_get_prefix_from_ip.return_value = "80.211.224.0/20"
    mock_get_network_details.return_value = ("AS15169", "IT", None)

    settings = AdvancedSettings()
    settings.custom_client_ip = "80.211.238.247"
    settings.wanted_ip_type = 4

    probes_result = get_probes(settings, 10)
    mock_get_best_single.assert_called_with(client_ip="80.211.238.247", current_probes_set={345}, ip_asn="AS15169",
                                            ip_prefix="80.211.224.0/20", ip_country="IT", ip_family=4,
                                            probes_requested=9,
                                            strict_this_asn=False, strict_this_country=False)

    answer = [{'requested': 8, 'type': 'probes', 'value': '345,11,22,33,45,55,66,77'},
              {'requested': 2, 'type': 'area', 'value': 'WW'}]
    assert probes_result == answer


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.get_probes_by_ids")
@patch("server.app.utils.ripe_probes.get_best_probes_with_multiple_attributes")
@patch("server.app.utils.ripe_probes.get_best_probes_matched_by_single_attribute")
@patch("server.app.utils.ripe_probes.get_ip_network_details")
@patch("server.app.utils.ripe_probes.get_prefix_probes")
def test_get_probes_only_area(mock_get_prefix_from_ip, mock_get_network_details, mock_get_best_single,
                              mock_get_multiple_attributes, mock_get_probes_by_ids, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_get_multiple_attributes.return_value = (11, {})
    mock_get_best_single.return_value = (11, {})  # nothing new

    mock_get_prefix_from_ip.return_value = "80.211.224.0/20"
    mock_get_network_details.return_value = ("AS15169", "IT", "West")

    settings = AdvancedSettings()
    settings.custom_client_ip = "80.211.238.247"
    settings.wanted_ip_type = 4

    probes_result = get_probes(settings, 11)
    mock_get_multiple_attributes.assert_called_once()
    mock_get_best_single.assert_called_once()
    mock_get_probes_by_ids.assert_not_called()

    answer = [{'requested': 11, 'type': 'area', 'value': 'West'}]
    assert probes_result == answer


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.get_available_probes_asn_and_prefix")
@patch("server.app.utils.ripe_probes.get_available_probes_asn_and_country")
def test_get_best_probes_with_multiple_attributes(mock_asn_country, mock_asn_prefix, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_asn_prefix.return_value = [23, 1, 73, 7429, 15]
    mock_asn_country.return_value = [23, 45, 78, 90000]
    # some values are in both lists
    assert get_best_probes_with_multiple_attributes("80.211.238.247", {3}, "AS15169", "80.211.224.0/20",
                                                    "IT", 4, 7) == (0, {3, 23, 1, 73, 7429, 15, 45, 78})
    assert get_best_probes_with_multiple_attributes("80.211.238.247", {3}, "AS15169", "80.211.224.0/20",
                                                    "IT", 4, 70) == (62, {3, 23, 1, 73, 7429, 15, 45, 78, 90000})
    assert get_best_probes_with_multiple_attributes("80.211.238.247", {3, 7888}, "AS15169", "80.211.224.0/20",
                                                    "IT", 4, 2) == (0, {3, 7888, 23, 1})
    # country None
    assert get_best_probes_with_multiple_attributes("80.211.238.247", {3, 7888}, "AS15169", "80.211.224.0/20",
                                                    None, 4, 10) == (5, {3, 7888, 23, 1, 73, 7429, 15})
    with pytest.raises(InputError):
        get_best_probes_with_multiple_attributes("80.211.238.247", {3}, "AS15169", "80.211.224.0/20", "IT", 4, -7)
    mock_asn_prefix.return_value = []
    # not enough in total, but first category is empty
    assert get_best_probes_with_multiple_attributes("80.211.238.247", {3, 7888}, "AS15169", None,
                                                    "IT", 4, 20) == (16, {3, 7888, 23, 45, 78, 90000})

    assert get_best_probes_with_multiple_attributes("80.211.238.247", {3, 7888}, "AS15169", "80.211.224.0/20",
                                                    "IT", 4, 20) == (16, {3, 7888, 23, 45, 78, 90000})
    # ASN is none
    assert get_best_probes_with_multiple_attributes("80.211.238.247", {3, 7888}, None, "80.211.224.0/20",
                                                    "IT", 4, 20) == (20, {3, 7888})


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.get_available_probes_country")
@patch("server.app.utils.ripe_probes.get_available_probes_prefix")
@patch("server.app.utils.ripe_probes.get_available_probes_asn")
def test_get_best_probe_types_bad_cases(mock_av_asn, mock_av_prefix, mock_av_country, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_av_asn.return_value = {12, 5}
    mock_av_prefix.return_value = {34, 13, 14}
    mock_av_country.return_value = {60}

    c, ids = get_best_probes_matched_by_single_attribute("80.211.238.247", {23}, None, None, None, 4, 3)
    mock_av_asn.assert_not_called()
    mock_av_prefix.assert_not_called()
    mock_av_country.assert_not_called()
    assert c == 3
    assert ids == {23}

    # some fields are missing
    c, ids = get_best_probes_matched_by_single_attribute("80.211.238.247", {23}, "AS15169", None, "IT", 4, 20)
    assert c == 17
    assert ids == {23, 12, 5, 60}
    # some fields are missing
    c, ids = get_best_probes_matched_by_single_attribute("80.211.238.247", {23}, None, "80.211.224.0/20", "IT", 4, 20)
    assert c == 16
    assert ids == {23, 34, 13, 14, 60}
    # negative nr of probes requested
    with pytest.raises(Exception):
        get_best_probes_matched_by_single_attribute("80.211.238.247", {23}, "AS15169", "80.211.224.0/20", "NL", 4, -5)
    with pytest.raises(Exception):
        get_best_probes_matched_by_single_attribute("2a06:93c0::24", {23}, "AS15169", "2a06:93c0::/29", "NL", 6, -1)


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.get_available_probes_country")
@patch("server.app.utils.ripe_probes.get_available_probes_prefix")
@patch("server.app.utils.ripe_probes.get_available_probes_asn")
def test_get_best_probe_types_return_early(mock_av_asn, mock_av_prefix, mock_av_country, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_av_asn.return_value = {12, 5, 16}
    mock_av_prefix.return_value = {34, 13, 14}
    mock_av_country.return_value = {60, 61, 63, 76}

    c, ids = get_best_probes_matched_by_single_attribute("80.211.238.247", {23, 45}, "AS15169", "80.211.224.0/20", "NL",
                                                         4, 3)
    assert c == 0
    assert ids == {23, 45, 12, 5, 16}

    # some fields are missing
    c, ids = get_best_probes_matched_by_single_attribute("80.211.238.247", {23, 45}, "AS15169", "80.211.224.0/20", "IT",
                                                         4, 6)
    assert c == 0
    assert ids == {34, 5, 12, 45, 13, 14, 16, 23}
    # some fields are missing
    c, ids = get_best_probes_matched_by_single_attribute("80.211.238.247", {23, 45}, "AS15169", "80.211.224.0/20", "IT",
                                                         4, 10)
    assert c == 0
    assert ids == {34, 5, 12, 45, 13, 14, 16, 76, 23, 60, 61, 63}


def test_get_probes_by_ids_probes():
    answer = {
        "type": "probes",
        "value": "2",
        "requested": 1
    }
    assert get_probes_by_ids([2]) == answer
    answer = {
        "type": "probes",
        "value": "2,40,1",
        "requested": 3
    }
    assert get_probes_by_ids([2, 40, 1]) == answer

    with pytest.raises(InputError):
        get_probes_by_ids([])


def test_get_asn_probes():
    answer = {
        "type": "asn",
        "value": "AS15169",
        "requested": 7
    }
    assert get_asn_probes("AS15169", 7) == answer
    answer = {
        "type": "asn",
        "value": "AS13335",
        "requested": 20
    }
    assert get_asn_probes("AS13335", 20) == answer

    with pytest.raises(InputError):
        get_asn_probes(None, 23)


def test_get_prefix_probes():
    answer = {
        "type": "prefix",
        "value": "162.159.200.0/24",
        "requested": 7
    }
    assert get_prefix_probes("162.159.200.0/24", 7) == answer
    answer = {
        "type": "prefix",
        "value": "192.2.3.0/8",
        "requested": 20
    }
    assert get_prefix_probes("192.2.3.0/8", 20) == answer

    with pytest.raises(InputError):
        get_prefix_probes(None, 23)


def test_get_country_probes():
    answer = {
        "type": "country",
        "value": "NL",
        "requested": 7
    }
    assert get_country_probes("NL", 7) == answer
    answer = {
        "type": "country",
        "value": "RO",
        "requested": 20
    }
    assert get_country_probes("RO", 20) == answer

    with pytest.raises(InputError):
        get_country_probes(None, 23)


def test_get_area_probes():
    answer = {
        "type": "area",
        "value": "West",
        "requested": 7
    }
    assert get_area_probes("West", 7) == answer
    answer = {
        "type": "area",
        "value": "North-East",
        "requested": 70
    }
    assert get_area_probes("North-East", 70) == answer

    with pytest.raises(InputError):
        get_area_probes(None, 23)


def test_get_random_probes():
    answer = {
        "type": "area",
        "value": "WW",
        "requested": 7
    }
    assert get_random_probes(7) == answer


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.ProbeRequest")
def test_get_available_probes_asn_and_prefix(mock_probe_request, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_probe1 = MagicMock()
    mock_probe1.id = 2
    mock_probe1.geometry = {"coordinates": [1.5, 17]}
    mock_probe1_duplicate = MagicMock()
    mock_probe1_duplicate.id = 2
    mock_probe1_duplicate.geometry = {"coordinates": [1.5, 17]}
    mock_probe2 = MagicMock()
    mock_probe2.id = 12000
    mock_probe2.geometry = {"coordinates": [16.5, -1.7]}
    mock_probe3 = MagicMock()
    mock_probe3.id = 43
    mock_probe3.geometry = {"coordinates": [-45, 0.07]}
    mock_probe4 = MagicMock()
    mock_probe4.id = 878
    mock_probe4.geometry = {"coordinates": [23, -41]}
    mock_probe_request.return_value = [mock_probe1, mock_probe2, mock_probe3, mock_probe4]

    # test ipv4
    result = get_available_probes_asn_and_prefix("80.211.238.247", "AS12345", "80.211.224.0/20", "ipv4")
    assert result == [12000, 2, 43, 878]
    assert mock_probe_request.call_count == 1
    args, kwargs = mock_probe_request.call_args
    assert kwargs["prefix_v4"] == "80.211.224.0/20"
    assert kwargs["tags"] == "system-ipv4-works"
    assert kwargs["status"] == 1

    # test ipv6
    mock_probe_request.reset_mock()
    result = get_available_probes_asn_and_prefix("2001:db8:3333:4444:5555:6666:7777:8888", "AS12345", "2a06:93c0::/29",
                                                 "ipv6")
    assert result == [12000, 2, 43, 878]
    assert mock_probe_request.call_count == 1
    args, kwargs = mock_probe_request.call_args
    assert kwargs["prefix_v6"] == "2a06:93c0::/29"
    assert kwargs["tags"] == "system-ipv6-works"
    assert kwargs["status"] == 1


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.ProbeRequest")
def test_get_available_probes_asn_and_prefix_stop_iteration(mock_probe_request, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_probe1 = MagicMock()
    mock_probe1.id = 2
    mock_probe1.geometry = {"coordinates": [1.5, 17]}
    mock_probe1_duplicate = MagicMock()
    mock_probe1_duplicate.id = 2
    mock_probe1_duplicate.geometry = {"coordinates": [1.5, 17]}
    mock_probe2 = MagicMock()
    mock_probe2.id = 234
    mock_probe2.geometry = {"coordinates": [16.5, -1.5]}
    mock_probe3 = MagicMock()
    mock_probe3.id = 43
    mock_probe3.geometry = {"coordinates": [-45, 0.07]}
    mock_probe4 = MagicMock()
    mock_probe4.id = 878
    mock_probe4.geometry = {"coordinates": None}
    mock_probe_request.return_value = [mock_probe1, mock_probe1_duplicate, mock_probe2, 5, mock_probe4]

    # test ipv4
    result = get_available_probes_asn_and_prefix("80.211.238.247", "AS12345", "80.211.224.0/20", "ipv4")
    assert result == [234, 2, 878]
    assert mock_probe_request.call_count == 1
    args, kwargs = mock_probe_request.call_args
    assert kwargs["prefix_v4"] == "80.211.224.0/20"
    assert kwargs["tags"] == "system-ipv4-works"
    assert kwargs["status"] == 1
    with pytest.raises(Exception):
        get_available_probes_asn_and_prefix("80.211.238.247", "ASab", "80.211.224.0/20", "ipv4")

    # test ipv6
    mock_probe_request.reset_mock()
    result = get_available_probes_asn_and_prefix("2001:db8:3333:4444:5555:6666:7777:8888", "AS12345", "2a06:93c0::/29",
                                                 "ipv6")
    assert result == [234, 2, 878]
    assert mock_probe_request.call_count == 1
    args, kwargs = mock_probe_request.call_args
    assert kwargs["prefix_v6"] == "2a06:93c0::/29"
    assert kwargs["tags"] == "system-ipv6-works"
    assert kwargs["status"] == 1


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.ProbeRequest")
def test_get_available_probes_asn_and_country(mock_probe_request, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_probe1 = MagicMock()
    mock_probe1.id = 2
    mock_probe1.geometry = {"coordinates": [1.5, 17]}
    mock_probe1_duplicate = MagicMock()
    mock_probe1_duplicate.id = 2
    mock_probe1_duplicate.geometry = {"coordinates": [1.5, 17]}
    mock_probe2 = MagicMock()
    mock_probe2.id = 234
    mock_probe2.geometry = {"coordinates": [16.5, -1.5]}
    mock_probe3 = MagicMock()
    mock_probe3.id = 43
    mock_probe3.geometry = {"coordinates": [-45, 0.07]}
    mock_probe4 = MagicMock()
    mock_probe4.id = 8784
    mock_probe4.geometry = {"coordinates": [23, -41]}
    mock_probe_request.return_value = [mock_probe1, mock_probe1_duplicate, mock_probe2, mock_probe3, mock_probe4]

    # test ipv4
    result = get_available_probes_asn_and_country("80.211.238.247", "AS12345", "NL", "ipv4")
    assert result == [234, 2, 43, 8784]
    assert mock_probe_request.call_count == 1
    args, kwargs = mock_probe_request.call_args
    assert kwargs["country_code"] == "NL"
    assert kwargs["tags"] == "system-ipv4-works"
    assert kwargs["status"] == 1

    # test ipv6
    mock_probe_request.reset_mock()
    result = get_available_probes_asn_and_country("2001:db8:3333:4444:5555:6666:7777:8888", "AS12345", "RO", "ipv6")
    assert result == [234, 2, 43, 8784]
    assert mock_probe_request.call_count == 1
    args, kwargs = mock_probe_request.call_args
    assert kwargs["country_code"] == "RO"
    assert kwargs["tags"] == "system-ipv6-works"
    assert kwargs["status"] == 1


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.ProbeRequest")
def test_get_available_probes_asn_and_country_stop_iteration(mock_probe_request, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_probe1 = MagicMock()
    mock_probe1.id = 2
    mock_probe1.geometry = {"coordinates": [1.5, 17]}
    mock_probe1_duplicate = MagicMock()
    mock_probe1_duplicate.id = 2
    mock_probe1_duplicate.geometry = {"coordinates": [1.5, 17]}
    mock_probe2 = MagicMock()
    # missing geometry for probe 2
    mock_probe2.id = 234
    mock_probe3 = MagicMock()
    mock_probe3.id = 43
    mock_probe3.geometry = {"coordinates": [-45, 0.07]}
    mock_probe4 = MagicMock()
    mock_probe4.id = 8784
    mock_probe4.geometry = {"coordinates": None}
    mock_probe_request.return_value = [mock_probe1, mock_probe1_duplicate, mock_probe2, "n", mock_probe4]

    # test ipv4
    result = get_available_probes_asn_and_country("80.211.238.247", "AS12345", "NL", "ipv4")
    assert result == [2, 8784]
    assert mock_probe_request.call_count == 1
    args, kwargs = mock_probe_request.call_args
    assert kwargs["country_code"] == "NL"
    assert kwargs["tags"] == "system-ipv4-works"
    assert kwargs["status"] == 1
    with pytest.raises(Exception):
        get_available_probes_asn_and_country("80.211.238.247", "ASab", "NL", "ipv4")

    # test ipv6
    mock_probe_request.reset_mock()
    result = get_available_probes_asn_and_country("2001:db8:3333:4444:5555:6666:7777:8888", "AS12345", "NL", "ipv6")
    assert result == [2, 8784]
    assert mock_probe_request.call_count == 1
    args, kwargs = mock_probe_request.call_args
    assert kwargs["country_code"] == "NL"
    assert kwargs["tags"] == "system-ipv6-works"
    assert kwargs["status"] == 1


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.ProbeRequest")
def test_get_available_probes_asn(mock_probe_request, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_probe1 = MagicMock()
    mock_probe1.id = 2
    mock_probe1.geometry = {"coordinates": [1.5, 17]}
    mock_probe1_duplicate = MagicMock()
    mock_probe1_duplicate.id = 2
    mock_probe1_duplicate.geometry = {"coordinates": [1.5, 17]}
    mock_probe2 = MagicMock()
    mock_probe2.id = 234
    mock_probe2.geometry = {"coordinates": [16.5, -1.5]}
    mock_probe3 = MagicMock()
    mock_probe3.id = 43
    mock_probe3.geometry = {"coordinates": [-45, 0.07]}
    mock_probe4 = MagicMock()
    mock_probe4.id = 878
    mock_probe4.geometry = {"coordinates": [23, -41]}
    mock_probe_request.return_value = [mock_probe1, mock_probe1_duplicate, mock_probe2, mock_probe3, mock_probe4]

    # test ipv4
    result = get_available_probes_asn("80.211.238.247", "AS12345", "ipv4")
    assert result == [234, 2, 43, 878]
    assert mock_probe_request.call_count == 1
    args, kwargs = mock_probe_request.call_args
    assert kwargs["asn"] == 12345
    assert kwargs["tags"] == "system-ipv4-works"
    assert kwargs["status"] == 1

    # test ipv6
    mock_probe_request.reset_mock()
    result = get_available_probes_asn("2001:db8:3333:4444:5555:6666:7777:8888", "AS67890", "ipv6")
    assert result == [234, 2, 43, 878]
    assert mock_probe_request.call_count == 1
    args, kwargs = mock_probe_request.call_args
    assert kwargs["asn"] == 67890
    assert kwargs["tags"] == "system-ipv6-works"
    assert kwargs["status"] == 1


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.ProbeRequest")
def test_get_available_probes_asn_stop_iteration(mock_probe_request, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_probe1 = MagicMock()
    mock_probe1.id = 2
    mock_probe1.geometry = {"coordinates": [1.5, 17]}
    mock_probe1_duplicate = MagicMock()
    mock_probe1_duplicate.id = 2
    mock_probe1_duplicate.geometry = {"coordinates": [1.5, 17]}
    mock_probe2 = MagicMock()
    mock_probe2.id = 234
    mock_probe2.geometry = {"coordinates": [16.5, -1.5]}
    mock_probe3 = MagicMock()
    mock_probe3.id = 43
    mock_probe3.geometry = {"coordinates": [-45, 0.07]}
    mock_probe4 = MagicMock()
    mock_probe4.id = 878
    mock_probe4.geometry = {"coordinates": None}
    mock_probe_request.return_value = [mock_probe1, mock_probe1_duplicate, mock_probe2, 3, mock_probe4]

    # test ipv4
    result = get_available_probes_asn("80.211.238.247", "12347", "ipv4")
    assert result == [234, 2, 878]
    assert mock_probe_request.call_count == 1
    args, kwargs = mock_probe_request.call_args
    assert kwargs["asn"] == 12347
    assert kwargs["tags"] == "system-ipv4-works"
    assert kwargs["status"] == 1
    with pytest.raises(InputError):
        get_available_probes_asn("80.211.238.247", "AS_invalid", "ipv4")

    # test ipv6
    mock_probe_request.reset_mock()
    result = get_available_probes_asn("2001:db8:3333:4444:5555:6666:7777:8888", "AS12340", "ipv6")
    assert result == [234, 2, 878]
    assert mock_probe_request.call_count == 1
    args, kwargs = mock_probe_request.call_args
    assert kwargs["asn"] == 12340
    assert kwargs["tags"] == "system-ipv6-works"
    assert kwargs["status"] == 1
    with pytest.raises(InputError):
        get_available_probes_asn("2001:db8:3333:4444:5555:6666:7777:8888", "AS_invalid", "ipv6")


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.ProbeRequest")
def test_get_available_probes_prefix(mock_probe_request, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_probe1 = MagicMock()
    mock_probe1.id = 2
    mock_probe1.geometry = {"coordinates": [1.5, 17]}
    mock_probe1_duplicate = MagicMock()
    mock_probe1_duplicate.id = 2
    mock_probe1_duplicate.geometry = {"coordinates": [1.5, 17]}
    mock_probe2 = MagicMock()
    mock_probe2.id = 234
    mock_probe2.geometry = {"coordinates": [16.5, -1.5]}
    mock_probe3 = MagicMock()
    mock_probe3.id = 43
    mock_probe3.geometry = {"coordinates": [-45, 0.07]}
    mock_probe4 = MagicMock()
    mock_probe4.id = 878
    mock_probe4.geometry = {"coordinates": [23, -41]}
    mock_probe_request.return_value = [mock_probe1, mock_probe1_duplicate, mock_probe2, mock_probe3, mock_probe4]

    # test ipv4
    result = get_available_probes_prefix("80.211.238.247", "80.211.224.0/20", "ipv4")
    assert result == [234, 2, 43, 878]
    assert mock_probe_request.call_count == 1
    args, kwargs = mock_probe_request.call_args
    assert kwargs["prefix_v4"] == "80.211.224.0/20"
    assert kwargs["tags"] == "system-ipv4-works"
    assert kwargs["status"] == 1

    # test ipv6
    mock_probe_request.reset_mock()
    result = get_available_probes_prefix("2001:db8:3333:4444:5555:6666:7777:8888", "2a06:93c0::/29", "ipv6")
    assert result == [234, 2, 43, 878]
    assert mock_probe_request.call_count == 1
    args, kwargs = mock_probe_request.call_args
    assert kwargs["prefix_v6"] == "2a06:93c0::/29"
    assert kwargs["tags"] == "system-ipv6-works"
    assert kwargs["status"] == 1


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.ProbeRequest")
def test_get_available_probes_prefix_stop_iteration(mock_probe_request, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_probe1 = MagicMock()
    mock_probe1.id = 2
    mock_probe1.geometry = {"coordinates": [1.5, 17]}
    mock_probe1_duplicate = MagicMock()
    mock_probe1_duplicate.id = 2
    mock_probe1_duplicate.geometry = {"coordinates": [1.5, 17]}
    mock_probe2 = MagicMock()
    mock_probe2.id = 234
    mock_probe2.geometry = {"coordinates": [16.5, -1.5]}
    mock_probe3 = MagicMock()
    mock_probe3.id = 43
    mock_probe3.geometry = {"coordinates": [-45, 0.07]}
    mock_probe4 = MagicMock()
    mock_probe4.id = 878
    mock_probe4.geometry = {"coordinates": None}
    mock_probe_request.return_value = [mock_probe1, mock_probe1_duplicate, mock_probe2, 5, mock_probe4]

    # test ipv4
    result = get_available_probes_prefix("80.211.238.247", "80.211.224.0/20", "ipv4")
    assert result == [234, 2, 878]
    assert mock_probe_request.call_count == 1
    args, kwargs = mock_probe_request.call_args
    assert kwargs["prefix_v4"] == "80.211.224.0/20"
    assert kwargs["tags"] == "system-ipv4-works"
    assert kwargs["status"] == 1

    # test ipv6
    mock_probe_request.reset_mock()
    result = get_available_probes_prefix("2001:db8:3333:4444:5555:6666:7777:8888", "2a06:93c0::/29", "ipv6")
    assert result == [234, 2, 878]
    assert mock_probe_request.call_count == 1
    args, kwargs = mock_probe_request.call_args
    assert kwargs["prefix_v6"] == "2a06:93c0::/29"
    assert kwargs["tags"] == "system-ipv6-works"
    assert kwargs["status"] == 1


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.ProbeRequest")
def test_get_available_probes_country(mock_probe_request, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_probe1 = MagicMock()
    mock_probe1.id = 2
    mock_probe1.geometry = {"coordinates": [1.5, 17]}
    mock_probe1_duplicate = MagicMock()
    mock_probe1_duplicate.id = 2
    mock_probe1_duplicate.geometry = {"coordinates": [1.5, 17]}
    mock_probe2 = MagicMock()
    mock_probe2.id = 234
    mock_probe2.geometry = {"coordinates": [16.5, -1.5]}
    mock_probe3 = MagicMock()
    mock_probe3.id = 43
    mock_probe3.geometry = {"coordinates": [-45, 0.07]}
    mock_probe4 = MagicMock()
    mock_probe4.id = 8784
    mock_probe4.geometry = {"coordinates": [23, -41]}
    mock_probe_request.return_value = [mock_probe1, mock_probe1_duplicate, mock_probe2, mock_probe3, mock_probe4]

    # test ipv4
    result = get_available_probes_country("80.211.238.247", "NL", "ipv4")
    assert result == [234, 2, 43, 8784]
    assert mock_probe_request.call_count == 1
    args, kwargs = mock_probe_request.call_args
    assert kwargs["country_code"] == "NL"
    assert kwargs["tags"] == "system-ipv4-works"
    assert kwargs["status"] == 1
    #{2: 1779.9601472512863, 234: 1745.6443045128183, 43: 5115.719370019957, 8784: 5171.937818291266}
    # test ipv6
    mock_probe_request.reset_mock()
    result = get_available_probes_country("2001:db8:3333:4444:5555:6666:7777:8888", "RO", "ipv6")
    assert result == [234, 2, 43, 8784]
    assert mock_probe_request.call_count == 1
    args, kwargs = mock_probe_request.call_args
    assert kwargs["country_code"] == "RO"
    assert kwargs["tags"] == "system-ipv6-works"
    assert kwargs["status"] == 1


@patch("server.app.utils.ripe_probes.get_coordinates_for_ip")
@patch("server.app.utils.ripe_probes.ProbeRequest")
def test_get_available_probes_country_stop_iteration(mock_probe_request, mock_geolocation):
    mock_geolocation.return_value = (1.0, 1.0)
    mock_probe1 = MagicMock()
    mock_probe1.id = 2
    mock_probe1.geometry = {"coordinates": [1.5, 17]}
    mock_probe2 = MagicMock()
    mock_probe2.id = 234
    mock_probe3 = MagicMock()
    mock_probe3.id = 43
    mock_probe3.geometry = {"coordinates": [-45, 0.07]}
    mock_probe4 = MagicMock()
    mock_probe4.id = 8784
    mock_probe4.geometry = {"coordinates": None}
    mock_probe_request.return_value = [mock_probe1, mock_probe2, "n", mock_probe4]

    # test ipv4
    result = get_available_probes_country("80.211.238.247", "NL", "ipv4")
    assert result == [2, 8784]
    assert mock_probe_request.call_count == 1
    args, kwargs = mock_probe_request.call_args
    assert kwargs["country_code"] == "NL"
    assert kwargs["tags"] == "system-ipv4-works"
    assert kwargs["status"] == 1

    # test ipv6
    mock_probe_request.reset_mock()
    result = get_available_probes_country("2001:db8:3333:4444:5555:6666:7777:8888", "NL", "ipv6")
    assert result == [2, 8784]
    assert mock_probe_request.call_count == 1
    args, kwargs = mock_probe_request.call_args
    assert kwargs["country_code"] == "NL"
    assert kwargs["tags"] == "system-ipv6-works"
    assert kwargs["status"] == 1


def test_consume_probes():
    assert (5, {34, 67, 900}) == consume_probes(7, {34}, [67, 67, 900])
    assert (0, {1, 34, 12, 23}) == consume_probes(2, {34, 1}, [12, 23, 67, 67, 900])
    with pytest.raises(InputError):
        consume_probes(-7, {34}, [67, 900])
