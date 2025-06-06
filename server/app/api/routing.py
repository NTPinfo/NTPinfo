from fastapi import HTTPException, APIRouter, Request, Depends

from datetime import datetime, timezone
from typing import Any, Optional, Generator

from sqlalchemy.orm import Session

from server.app.utils.ip_utils import ip_to_str
from server.app.models.CustomError import InputError, RipeMeasurementError
from server.app.utils.ip_utils import get_server_ip
from server.app.db_config import get_db

from server.app.services.api_services import fetch_ripe_data
from server.app.services.api_services import perform_ripe_measurement
from server.app.rate_limiter import limiter
from server.app.dtos.MeasurementRequest import MeasurementRequest
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
@limiter.limit("5/second")
async def read_data_measurement(payload: MeasurementRequest, request: Request,
                                session: Session = Depends(get_db)) -> dict[str, Any]:
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
        session (Session): The currently active database session.

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
    response = measure(server, session, client_ip)
    # print(response)
    if response is not None:
        new_format = []
        for r in response:
            result, jitter, nr_jitter_measurements = r
            new_format.append(get_format(result, jitter, nr_jitter_measurements))
        return {
            "measurement": new_format
        }
    else:
        raise HTTPException(status_code=404, detail="Your search does not seem to match any server")


@router.get("/measurements/history/")
@limiter.limit("5/second")
async def read_historic_data_time(server: str,
                                  start: datetime, end: datetime, request: Request,
                                  session: Session = Depends(get_db)) -> dict[str, list[dict[str, Any]]]:
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
        session (Session): The currently active database session.

    Returns:
        dict: A dictionary containing a list of formatted measurements under "measurements".

    Raises:
        HTTPException: 400 error if `server` parameter is empty.
        HTTPException: 404 error if `server` parameter is not found.
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
    result = fetch_historic_data_with_timestamps(server, start, end, session)
    formatted_results = [get_format(entry, nr_jitter_measurements=0) for entry in result]
    return {
        "measurements": formatted_results
    }


@router.post("/measurements/ripe/trigger/")
@limiter.limit("5/second")
async def trigger_ripe_measurement(payload: MeasurementRequest, request: Request) -> dict[str, Any]:
    """
    Trigger a RIPE Atlas NTP measurement for a specified server.

    This endpoint initiates a RIPE Atlas measurement for the given NTP server
    (IP address or domain name) provided in the payload. Once the measurement
    is triggered, it returns a measurement ID which can later be used to fetch
    the result using the `/measurements/ripe/{measurement_id}` endpoint.

    This endpoint is also limited to 5 requests per minute to prevent abuse and reduce server load.

    Args:
        payload (MeasurementRequest): A Pydantic model that includes:
            - server (str): The IP address or domain name of the target server
            - jitter_flag (bool, optional): Whether to calculate jitter
            - measurements_no (int, optional): Number of measurements
        request (Request): The FastAPI request object, used to extract the client IP address

    Returns:
        dict[str, Any]: A dictionary containing:
            - measurement_id (str): The ID of the triggered RIPE measurement
            - status (str): Status message ("started")
            - message (str): Instructions on how to retrieve the result
            - ip_list (list[str]): List of ips for ntp server

    Raises:
        HTTPException:
            - 400: If the `server` field is empty
            - 500: If the RIPE measurement could not be initiated
            - 503: If we could not get client IP address or our server's IP address
    """
    server = payload.server
    if len(server) == 0:
        raise HTTPException(status_code=400, detail="Either 'ip' or 'dn' must be provided")

    client_ip: Optional[str]
    if request.client is None:
        client_ip = None
    else:
        client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    # we need an IP. If this is None, just use our server IP.
    if client_ip is None:
        try:
            client_ip = ip_to_str(get_server_ip())
        except Exception as e:
            raise HTTPException(status_code=503,
                                detail="failed to get client IP address or a default IP address to use")
    try:
        measurement_id = perform_ripe_measurement(server, client_ip=client_ip)
        return {
            "measurement_id": measurement_id,
            "status": "started",
            "message": "You can fetch the result at /measurements/ripe/{measurement_id}",
        }
    except InputError as e:
        print(e)
        raise HTTPException(status_code=400,
                            detail=f"Input parameter is invalid. Failed to initiate measurement: {str(e)}")
    except RipeMeasurementError as e:
        print(e)
        raise HTTPException(status_code=400, detail=f"Ripe measurement initiated, but it failed: {str(e)}")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Failed to initiate measurement: {str(e)}")


@router.get("/measurements/ripe/{measurement_id}")
@limiter.limit("5/second")
async def get_ripe_measurement_result(measurement_id: str, request: Request) -> dict[str, Any]:
    """
    Retrieve the results of a previously triggered RIPE Atlas measurement.

    This endpoint checks the RIPE Atlas API for a given measurement ID. It determines
    if the measurement is complete (all probes have been scheduled) and returns
    the data accordingly. If the results are not yet ready, it informs the client
    that the measurement is still pending.

    This endpoint is also limited to 5 requests per minute to prevent abuse and reduce server load.

    Args:
        measurement_id (str): The ID of the RIPE measurement to fetch
        request (Request): The FastAPI Request object (used for rate limiting)

    Returns:
        dict[str, Any]: A dictionary with the status and measurement results:
            - If complete: {"status": "complete", "results": <ripe_data>}
            - If pending: {"status": "pending", "message": "..."}
            - If partial results received: {"status": "partial_results", "results": <ripe_data>}
    Raises:
        HTTPException: - 500: If fetching the measurement did not work.
    Notes:
        - A result is only marked "complete" when all requested probes have been scheduled
    """
    try:
        ripe_measurement_result, status = fetch_ripe_data(measurement_id=measurement_id)
        if not ripe_measurement_result:
            return {
                "status": "pending",
                "message": "Measurement not ready yet. Please try again later."
            }

        if status == "Complete":
            return {
                "status": "complete",
                "results": ripe_measurement_result
            }

        if status == "Ongoing":
            return {
                "status": "partial_results",
                "results": ripe_measurement_result
            }

        return {
            "status": "timeout",
            "message": "RIPE data likely completed but incomplete probe responses."
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to fetch result: {str(e)}. Try again later!"
        }
