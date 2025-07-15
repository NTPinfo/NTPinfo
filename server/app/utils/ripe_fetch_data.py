import time
from ipaddress import ip_address, IPv4Address, IPv6Address
import requests

from server.app.services.NtpCalculator import NtpCalculator
from server.app.utils.location_resolver import get_country_for_ip, get_coordinates_for_ip
from server.app.models.CustomError import RipeMeasurementError
from server.app.utils.load_config_data import get_ripe_api_token, get_ripe_server_timeout
from server.app.dtos.PreciseTime import PreciseTime
from server.app.dtos.NtpExtraDetails import NtpExtraDetails
from server.app.dtos.NtpMainDetails import NtpMainDetails
from server.app.dtos.NtpMeasurement import NtpMeasurement
from server.app.dtos.NtpServerInfo import NtpServerInfo
from server.app.dtos.NtpTimestamps import NtpTimestamps
from server.app.dtos.ProbeData import ServerLocation, ProbeData
from server.app.dtos.RipeMeasurement import RipeMeasurement
from server.app.utils.perform_measurements import convert_float_to_precise_time
from typing import Any, cast


def check_all_measurements_scheduled(measurement_id: str) -> bool:
    """
    Check if all RIPE Atlas probes for a given measurement have been scheduled.

    This function compares the number of probes requested with the number of probes successfully
    scheduled. If all requested probes are scheduled, it returns True. Otherwise,
    it returns False

    Args:
        measurement_id (str): The ID of the RIPE Atlas measurement to check.

    Returns:
        bool: True if all requested probes have been scheduled, False otherwise.

    Raises:
        ValueError: If the RIPE API returns an error or if the probe count data
                    is missing or invalid.
    """
    url = f"https://atlas.ripe.net/api/v2/measurements/{measurement_id}/"

    headers = {
        "Authorization": f"Key {get_ripe_api_token()}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    json_data = response.json()
    if isinstance(json_data, dict) and 'error' in json_data:
        raise ValueError(
            f"RIPE API error: {json_data['error']['title']} - {json_data['error']['detail']}")
    probes_requested: int = json_data.get("probes_requested", -1)
    probes_scheduled: int = json_data.get("probes_scheduled", -1)
    # status = json_data["status"].get("name", "No status")
    if probes_requested == -1:
        raise ValueError(
            f"RIPE API error: The number of scheduled probes is negative")
    return probes_requested == probes_scheduled  # and status == "Stopped"


def check_all_measurements_done(measurement_id: str, measurement_req: int) -> str:
    """
    Check the status of a RIPE Atlas measurement.

    This function queries the RIPE Atlas API for a given measurement ID and determines
    whether the measurement is complete, ongoing, or should be considered timed out. The status is based
    on the number of probes requested, the measurement status provided by RIPE, and
    how much time has passed since the measurement started.

    Parameters:
        measurement_id (str): RIPE Atlas measurement ID.
        measurement_req (int): The number of probes expected for the measurement to be considered complete.

    Returns:
        str:
            - "Complete": All expected probes have responded or the measurement is stopped.
            - "Ongoing": The measurement is still in progress and has not exceeded the timeout threshold.
            - "Timeout": The measurement did not complete within the allowed time window.

    Raises:
        RipeMeasurementError: If there are errors with the response from ripe, either not received or malformed.

    Notes:
        - If the difference between the current time and the measurement's start time exceeds the configured time in seconds,
          and the measurement is not yet complete, it is considered "Timeout".
        - This function assumes a successful HTTP response from the RIPE API; if not, it will raise an exception.
    """
    url = f"https://atlas.ripe.net/api/v2/measurements/{measurement_id}/"

    headers = {
        "Authorization": f"Key {get_ripe_api_token()}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        json_data = response.json()
    except requests.RequestException as e:
        raise RipeMeasurementError(f"Network error while checking measurement status: {str(e)}")
    except ValueError:
        raise RipeMeasurementError("Invalid JSON response from RIPE API.")

    if isinstance(json_data, dict) and 'error' in json_data:
        raise RipeMeasurementError(
            f"RIPE API error: {json_data['error']['title']} - {json_data['error']['detail']}")

    probes_requested: int = json_data.get("probes_requested", -1)
    status_ripe: str = json_data["status"].get("name", "NO RESPONSE")
    start_time = int(json_data.get("start_time", 0))

    if probes_requested == measurement_req:
        return "Complete"
    elif status_ripe == "Stopped":
        return "Complete"
    elif status_ripe == "NO RESPONSE":
        return "Timeout"
    else:
        current_time = int(time.time())
        if (current_time - start_time) > get_ripe_server_timeout():
            return "Timeout"
        else:
            return "Ongoing"


def get_data_from_ripe_measurement(measurement_id: str) -> list[dict[str, Any]]:
    """
    Fetches raw measurement results from the RIPE Atlas API.

    This function queries the RIPE Atlas v2 API using the provided measurement ID,
    authenticates with an API key stored in the RIPE_KEY environment variable, and
    returns the parsed JSON response as a list of dictionaries.

    Args:
        measurement_id (str): The RIPE Atlas measurement ID to fetch results for.

    Returns:
        list[dict[str, Any]]: A list of measurement result entries as dictionaries.

    Raises:
        RipeMeasurementError: If the HTTP request fails or the response cannot be parsed as JSON or the answer is not a list of dicts.

    Notes:
        - Requires the `RIPE_KEY` environment variable to be set with a valid API key.
    """
    url = f"https://atlas.ripe.net/api/v2/measurements/{measurement_id}/results/"

    headers = {
        "Authorization": f"Key {get_ripe_api_token()}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        json_data = response.json()
    except requests.RequestException as e:
        raise RipeMeasurementError(f"Network error while fetching measurement data: {str(e)}")
    except ValueError:
        raise RipeMeasurementError("Invalid JSON response from RIPE API.")

    if isinstance(json_data, dict) and 'error' in json_data:
        raise RipeMeasurementError(
            f"RIPE API error: {json_data['error'].get('title')} - {json_data['error'].get('detail')}")

    if not isinstance(json_data, list):
        raise RipeMeasurementError("Unexpected format: Expected list of results from RIPE API.")
    return cast(list[dict[str, Any]], response.json())


def get_probe_data_from_ripe_by_id(probe_id: str) -> dict[str, Any]:
    """
    Retrieves detailed information about a specific RIPE Atlas probe by its ID.

    This function sends a GET request to the RIPE Atlas API to fetch metadata
    about the specified probe. The request is authenticated using the RIPE API key
    stored in the RIPE_KEY environment variable.

    Args:
        probe_id (str): The ID of the RIPE Atlas probe to fetch information for.

    Returns:
        dict[str, Any]: A dictionary containing metadata about the probe

    Raises:
        RipeMeasurementError: If the HTTP request fails or the response is not valid JSON.

    Notes:
        - Requires the `RIPE_KEY` environment variable to be set with a valid API key.
    """
    url = f"https://atlas.ripe.net/api/v2/probes/{probe_id}/"

    headers = {
        "Authorization": f"Key {get_ripe_api_token()}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        json_data = response.json()
    except requests.RequestException as e:
        raise RipeMeasurementError(f"Network error while fetching probe data for {probe_id}: {str(e)}")
    except ValueError:
        raise RipeMeasurementError("Invalid JSON response from RIPE API.")
    return cast(dict[str, Any], json_data)


def parse_probe_data(probe_response: dict) -> ProbeData:
    """
    Parses probe metadata received from the RIPE Atlas API into a ProbeData object.

    This function extracts relevant information such as the probe ID, IP addresses,
    country code, and coordinates from the API response.

    Args:
        probe_response (dict): The raw dictionary response from the RIPE Atlas probe lookup API.

    Returns:
        ProbeData: Parsed information including the probe's ID, IP addresses, country code, and location.

    Notes:
        - If an error is present in the response, a default `ProbeData` with dummy values is returned.
        - Coordinates default to `[0.0, 0.0]` if not provided.
        - Country code defaults to `"NO COUNTRY CODE"` if not found.
    """
    if probe_response.get('error'):
        return ProbeData(probe_id="-1", probe_addr=(None, None), probe_location=None)

    probe_id = probe_response.get('id', '-1')
    v4 = probe_response.get('address_v4')
    v6 = probe_response.get('address_v6')
    try:
        ipv4 = ip_address(v4) if v4 is not None else None
        if ipv4 is not None and not isinstance(ipv4, IPv4Address):
            ipv4 = None
    except Exception as e:
        ipv4 = None
    try:
        ipv6 = ip_address(v6) if v6 is not None else None
        if ipv6 is not None and not isinstance(ipv6, IPv6Address):
            ipv6 = None
    except Exception as e:
        ipv6 = None
    probe_addr: tuple[IPv4Address | None, IPv6Address | None] = (ipv4, ipv6)

    country_code = probe_response.get('country_code', "NO COUNTRY CODE")

    geometry = probe_response.get('geometry')
    coordinates = geometry.get('coordinates', [0.0, 0.0]) if geometry else [0.0, 0.0]

    probe_location = ServerLocation(country_code=country_code,
                                    coordinates=coordinates)
    return ProbeData(probe_id=probe_id, probe_addr=probe_addr, probe_location=probe_location)


def is_failed_measurement(entry: dict[str, Any]) -> bool:
    """
    Determines if a RIPE measurement entry has failed.

    A measurement is considered failed if all result entries contain the key "x" with value "*",
    which typically indicates a failed probe response.

    Args:
        entry (dict[str, Any]): A dictionary representing a single measurement entry from the RIPE API.

    Returns:
        bool: True if all entries in the result indicate failure, False otherwise.
    """
    result = entry.get("result", [])
    return all(r.get("x") == "*" for r in result)


def successful_measurement(entry: dict[str, Any]) -> int | None:
    """
    Identifies the index of the successful measurement with the lowest offset.

    A successful measurement is one that contains the "origin-ts" field,
    indicating a valid timestamp. Among all such entries, the one with the
    lowest absolute offset value is considered the most successful.

    Args:
        entry (dict[str, Any]): A dictionary representing a single measurement entry from the RIPE API.

    Returns:
        int | None: The index of the result entry with the lowest absolute offset (closest to 0), or None if no valid entries exist.
    """
    result = entry.get("result", [])
    min_abs_offset = float("inf")
    min_index = None

    for i, r in enumerate(result):
        if "origin-ts" in r and "offset" in r:
            try:
                # we want the closest offset to 0 from the packets sent from this probe. (this is why we use abs)
                abs_offset = abs(NtpCalculator.calculate_offset_from_dict(r))
                if abs_offset < min_abs_offset:
                    min_abs_offset = abs_offset
                    min_index = i
            except (ValueError, TypeError):
                continue

    return min_index


def parse_data_from_ripe_measurement(data_measurement: list[dict]) -> tuple[list[RipeMeasurement], str]:
    """
    Parses raw RIPE Atlas measurement data into a list of RipeMeasurement objects.

    This function:
      - Determines whether each measurement entry failed or succeeded.
      - Extracts NTP-related server and timing information.
      - Converts timestamps and metrics into structured internal representations.
      - Adds probe-specific metadata fetched from the RIPE API.
      - Returns a status string indicating whether all measurements have been processed.

    Args:
        data_measurement (list[dict]): A list of dictionaries representing raw measurement entries from the RIPE Atlas API.

    Returns:
        tuple[list[RipeMeasurement], str]:
            - A list of parsed and structured `RipeMeasurement` objects.
            - A status string returned by `check_all_measurements_done`, indicating
              whether all expected measurements are present and complete.

    Notes:
        - Measurements that are marked as failed are still processed, but filled with default values.
        - Probe metadata is fetched using the probe ID (`prb_id`) in each measurement.
        - Timestamps are converted using `convert_float_to_precise_time`.
    """
    msm_id = -1
    ripe_measurements = []
    for measurement in data_measurement:
        # check for result if ok
        failed = is_failed_measurement(measurement)
        idx = successful_measurement(measurement) if not failed else None

        from_ip = measurement.get('from')
        try:
            vantage_point_ip = ip_address(from_ip) if from_ip is not None else None
        except Exception as e:
            vantage_point_ip = None
        version = measurement.get('version', -1)
        dst_addr = measurement.get('dst_addr')
        try:
            dst_addr_ip = ip_address(dst_addr) if dst_addr is not None else None
        except Exception as e:
            dst_addr_ip = None
        dst_name = measurement.get('dst_name')

        server_info = NtpServerInfo(
            ntp_version=version,
            ntp_server_ip=dst_addr_ip,
            ntp_server_name=dst_name,
            ntp_server_ref_parent_ip=None,
            ref_name=None,
            ntp_server_location=ServerLocation(country_code=get_country_for_ip(str(dst_addr_ip)),
                                               coordinates=get_coordinates_for_ip(str(dst_addr_ip)))
        )

        if not failed and idx is not None:
            result = measurement['result'][idx]
            timestamps = NtpTimestamps(
                client_sent_time=convert_float_to_precise_time(result.get('origin-ts', -1.0)),
                server_recv_time=convert_float_to_precise_time(result.get('receive-ts', -1.0)),
                server_sent_time=convert_float_to_precise_time(result.get('transmit-ts', -1.0)),
                client_recv_time=convert_float_to_precise_time(result.get('final-ts', -1.0))
            )
            offset = NtpCalculator.calculate_offset(timestamps)
            # print(offset, NtpCalculator.calculate_offset_from_dict(result)) # they have exactly the same values
            # print(offset, result.get('offset', -1.0)) # the RIPE offset had inverted sign

            rtt = result.get('rtt', -1.0)
            #rtt = NtpCalculator.calculate_rtt(timestamps) # or we can use our formula which is the same
            # print(rtt, result.get('rtt', -1.0))
        else:
            timestamps = NtpTimestamps(*(PreciseTime(-1, 0) for _ in range(4)))
            offset = rtt = -1

        stratum = measurement.get('stratum', -1)
        precision = measurement.get('precision', -1)

        main_details = NtpMainDetails(offset=offset,
                                      rtt=rtt,
                                      stratum=stratum,
                                      precision=precision,
                                      reachability="")

        root_delay = measurement.get('root-delay', -1.0)

        poll = measurement.get('poll', -1)

        root_dispersion = measurement.get('root-dispersion', -1.0)

        extra_details = NtpExtraDetails(root_delay=convert_float_to_precise_time(root_delay),
                                        poll=poll, root_dispersion=convert_float_to_precise_time(root_dispersion),
                                        ntp_last_sync_time=convert_float_to_precise_time(-1.0),
                                        leap=0)
        ntp_measurement = NtpMeasurement(vantage_point_ip=vantage_point_ip, server_info=server_info,
                                         timestamps=timestamps, main_details=main_details,
                                         extra_details=extra_details)

        time_to_result = measurement.get('ttr', -1.0)
        ref_id = measurement.get('ref-id', 'NO REFERENCE')
        measurement_id = measurement.get('msm_id', -1)
        msm_id = measurement_id

        ripe_measurement = RipeMeasurement(
            measurement_id=measurement_id,
            ntp_measurement=ntp_measurement,
            probe_data=parse_probe_data(get_probe_data_from_ripe_by_id(measurement['prb_id'])),
            time_to_result=time_to_result,
            ref_id=ref_id
        )
        ripe_measurements.append(ripe_measurement)
    return ripe_measurements, check_all_measurements_done(str(msm_id), len(ripe_measurements))

# example how to use the methods:
# print(parse_data_from_ripe_measurement(get_data_from_ripe_measurement("106323686")))
# print(parse_probe_data(get_probe_data_from_ripe_by_id("7304")))
