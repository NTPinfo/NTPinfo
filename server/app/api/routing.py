from fastapi import HTTPException, APIRouter, Request

from datetime import datetime, timezone
from typing import Any, Optional

from server.app.rate_limiter import limiter
from server.app.models.MeasurementRequest import MeasurementRequest
from server.app.services.api_services import get_format, measure, fetch_historic_data_with_timestamps

router = APIRouter()


@router.get("/")
def read_root() -> dict[str, str]:
    """
    Root endpoint for basic service health check.

    Returns:
        dict: A simple JSON message {"Hello": "World"}
    """
    return {"Hello": "World"}


@router.post("/measurements/")
@limiter.limit("5/minute")
async def read_data_measurement(payload: MeasurementRequest, request: Request) -> dict[str, Any]:
    """
    Compute a live NTP measurement for a given server (IP or domain).

    This endpoint receives a JSON payload containing the server to be measured.
    It uses the `measure()` function to perform the NTP synchronization measurement,
    and formats the result using `get_format()`.

    This endpoint is also limited to 5 requests per minute to prevent abuse and reduce server load.

    Args:
        payload (MeasurementRequest): A Pydantic model containing:
            - server (str): IP address (IPv4/IPv6) or domain name of the NTP server.
        request (Request): The Request object that gives you the IP of the client.

    Returns:
        dict: On success, returns {"measurement": <formatted_measurement_dict>}.
              On failure, returns {"Error": "Could not perform measurement, DNS or IP not reachable."}

    Raises:
        HTTPException: 400 error if the `server` field is empty.
    """
    server = payload.server
    if len(server) == 0:
        raise HTTPException(status_code=400, detail="Either 'ip' or 'dn' must be provided")

    # get the client IP from the request
    client_ip: Optional[str]
    if request.client is None:
        client_ip = None
    else:
        try:
            client_ip = request.headers.get("X-Forwarded-For", request.client.host)
        except Exception as e:
            client_ip = None
    times = payload.measurements_no if payload.measurements_no else 0
    response = measure(server, client_ip, payload.jitter_flag, times)
    if response is not None:
        result, jitter, other_server_ips = response
        return {
            "measurement": get_format(result, jitter, other_server_ips)
        }
    else:
        return {
            "error": "Could not perform measurement, dns or ip not reachable."
        }


@router.get("/measurements/history/")
@limiter.limit("5/minute")
async def read_historic_data_time(server: str,
                                  start: datetime, end: datetime, request: Request) -> dict[str, list[dict[str, Any]]]:
    """
    Retrieve historic NTP measurements for a given server and optional time range.

    This endpoint fetches past measurement data for the specified server using the
    `fetch_historic_data_with_timestamps()` function. It can optionally filter results
    based on a time range (start and end datetime).

    This endpoint is also limited to 5 requests per minute to prevent abuse and reduce server load.

    Args:
        server (str): IP address or domain name of the NTP server.
        start (datetime, optional): Start timestamp for data filtering.
        end (datetime, optional): End timestamp for data filtering.
        request (Request): Request object for making the limiter work

    Returns:
        dict: A dictionary containing a list of formatted measurements under "measurements".

    Raises:
        HTTPException: 400 error if `server` parameter is empty.
    """
    if len(server) == 0:
        raise HTTPException(status_code=400, detail="Either 'ip' or 'domain name' must be provided")

    if start >= end:
        raise HTTPException(status_code=400, detail="'start' must be earlier than 'end'")

    if end > datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="'end' cannot be in the future")

    # utc_time_from_9am = datetime(2025, 5, 7, 7, 0, tzinfo=timezone.utc)
    # current_utc_time = datetime(2025, 5, 7, 11, 15, tzinfo=timezone.utc)
    #
    # start_test = utc_time_from_9am
    # end_test = current_utc_time
    result = fetch_historic_data_with_timestamps(server, start, end)
    formatted_results = [get_format(entry) for entry in result]
    return {
        "measurements": formatted_results
    }
