from typing import Optional
import geoip2.database

from server.app.utils.load_config_data import get_max_mind_path_asn
from server.app.utils.load_config_data import get_max_mind_path_country, get_max_mind_path_city


def get_coordinates_for_ip(client_ip: Optional[str]) -> tuple[float, float]:
    """
    Retrieves the geographical location (latitude and longitude) of a given IP address
    using the MaxMind GeoLite2-City database.

    If the location cannot be determined due to missing data, database issues, or
    the IP not being found, it returns the coordinates of an (almost) randomly chosen location as a fallback.

    Args:
        client_ip (Optional[str]): The IP address of the client to geolocate

    Returns:
        tuple[float, float]: A tuple containing the latitude and longitude. If the location
        cannot be resolved, returns (25.0, -71.0).
    """
    if client_ip is None:
        return 25.0, -71.0
    try:
        with geoip2.database.Reader(f'{get_max_mind_path_city()}') as reader:
            response = reader.city(client_ip)
            lat = response.location.latitude
            long = response.location.longitude
            if lat is None or long is None:
                raise ValueError(f"Location data incomplete for {client_ip}")
            return lat, long
    except Exception as e:
        print(e)
        return 25.0, -71.0


def get_country_for_ip(client_ip: Optional[str]) -> Optional[str]:
    """
    Retrieves the country code of a given IP address using the MaxMind GeoLite2-Country database.
    If the country code cannot be determined due to missing data, database issues, or
    the IP not being found, it returns None.

    Args:
        client_ip (Optional[str]): The IP address of the client to geolocate.

    Returns:
        Optional[str]: The country code for the ip location or None.
    """
    if client_ip is None:
        return None
    try:
        with geoip2.database.Reader(f'{get_max_mind_path_country()}') as reader:
            response = reader.country(client_ip).country.iso_code
            return response
    except Exception as e:
        print(e)
        return None


def get_continent_for_ip(client_ip: Optional[str]) -> Optional[str]:
    """
    Retrieves the continent code of a given IP address using the MaxMind GeoLite2-Country database.
    If the continent code cannot be determined due to missing data, database issues, or
    the IP not being found, it returns None.

    Args:
        client_ip (Optional[str]): The IP address of the client to geolocate.

    Returns:
        Optional[str]: The continent code for the ip location or None.
    """
    if client_ip is None:
        return None
    try:
        with geoip2.database.Reader(f'{get_max_mind_path_country()}') as reader:
            response = reader.country(client_ip).continent.code
            return response
    except Exception as e:
        print(e)
        return None


def get_asn_for_ip(client_ip: str) -> Optional[str]:
    """
    Retrieves the asn of a given IP address using the MaxMind GeoLite2-ASN database.
    If the asn cannot be determined due to missing data, database issues, or
    the IP not being found, it returns None.

    Args:
        client_ip (str): The IP address of the client to geolocate.

    Returns:
        Optional[str]: The ans for the ip location or None.
    """
    try:
        with geoip2.database.Reader(f'{get_max_mind_path_asn()}') as reader:
            response = reader.asn(client_ip).autonomous_system_number
            return str(response)
    except Exception as e:
        print(e)
        return None
