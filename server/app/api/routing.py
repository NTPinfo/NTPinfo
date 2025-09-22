from fastapi import HTTPException, APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from datetime import datetime, timezone
from typing import Optional
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse

from server.app.utils.validate import is_ip_address
from server.app.dtos.AdvancedSettings import AdvancedSettings
from server.app.utils.nts_check import perform_nts_measurement_domain_name, perform_nts_measurement_ip
from server.app.utils.load_config_data import get_rate_limit_per_client_ip
from server.app.dtos.RipeMeasurementResponse import RipeResult
from server.app.dtos.NtpMeasurementResponse import MeasurementResponse
from server.app.dtos.RipeMeasurementTriggerResponse import RipeMeasurementTriggerResponse
from server.app.utils.location_resolver import get_country_for_ip, get_coordinates_for_ip
from server.app.utils.ip_utils import client_ip_fetch, get_server_ip_if_possible, get_server_ip
from server.app.models.CustomError import DNSError, MeasurementQueryError
from server.app.utils.ip_utils import ip_to_str
from server.app.models.CustomError import InputError, RipeMeasurementError
from server.app.db_config import get_db

from server.app.services.api_services import fetch_ripe_data, override_desired_ip_type_if_input_is_ip
from server.app.services.api_services import perform_ripe_measurement
from server.app.rate_limiter import limiter
from server.app.dtos.MeasurementRequest import MeasurementRequest
from server.app.services.api_services import get_format, measure, fetch_historic_data_with_timestamps

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def read_root() -> str:
    """
    Root endpoint for basic service health check.

    Returns:
        dict: A simple HTML welcome message.
    """
    return """
    <html>
        <head>
            <title>NTPInfo API</title>
        </head>
        <body>
            <h1>Welcome to the NTPInfo API</h1>
            <p>This API powers the NTPInfo platform, offering real-time metrics collection related to Network Time Protocol (NTP) analysis.</p>
            <p>See the <a href='/api/docs'>interactive docs</a> or <a href='/api/redoc'>ReDoc</a> for more info.</p>
        </body>
    </html>
    """


@router.post(
    "/measurements/",
    summary="Perform a live NTP measurement",
    description="""
Compute a live NTP synchronization measurement for a specified server.

- Accepts an IP or domain name.
- Returns data about the measurement
- Limited to 5 requests per second.
""",
    response_model=MeasurementResponse,
    responses={
        200: {"description": "Measurement successfully initiated"},
        400: {"description": "Invalid server address"},
        422: {"description": "Domain resolution failed"},
        500: {"description": "Internal server error"}
    }
)
@limiter.limit(get_rate_limit_per_client_ip())
async def read_data_measurement(payload: MeasurementRequest, request: Request,
                                session: Session = Depends(get_db)) -> JSONResponse:
    """
    Compute a live NTP measurement for a given server (IP or domain).

    This endpoint receives a JSON payload containing the server to be measured.
    It uses the `measure()` function to perform the NTP synchronization measurement,
    and formats the result using `get_format()`. User can choose whether they want to measure IPv4 of IPv6,
    but this will take effect only for domain names. If user inputs an IP, we will measure the type of that IP.

    Args:
        payload (MeasurementRequest):
            A Pydantic model containing:
                - server (str): IP address (IPv4/IPv6) or domain name of the NTP server.
                - ipv6_measurement (bool): True if the type of IPs that we want to measure is IPv6. False otherwise.
        request (Request): The Request object that gives you the IP of the client.
        session (Session): The currently active database session.

    Returns:
        JSONResponse: A json response containing a list of formatted measurements under "measurements".

    Raises:
        HTTPException: 400 - If the `server` field is empty or no response.
        HTTPException: 422 - If the server cannot perform the desired IP type (IPv4 or IPv6) measurements,
              or if the domain name could not be resolved.
        HTTPException: 503 - If we could not get client IP address or our server's IP address.
        HTTPException: 500 - If an unexpected server error occurs.

    Notes:
        - This endpoint is also limited to <`see config file`> to prevent abuse and reduce server load.
    """
    server = payload.server
    if len(server) == 0:
        raise HTTPException(status_code=400, detail="Either 'ip' or 'dn' must be provided.")

    wanted_ip_type = 6 if payload.ipv6_measurement else 4
    # Override it if we received an IP, not a domain name:
    # In case the input is an IP and not a domain name, then "wanted_ip_type" will be ignored and the IP type of the IP will be used.
    wanted_ip_type = override_desired_ip_type_if_input_is_ip(server, wanted_ip_type)

    # for IPv6 measurements, we need to communicate using IPv6. (we need to have the same protocol as the target)
    this_server_ip_strict = get_server_ip(wanted_ip_type)  # strict means we want exactly this type
    if this_server_ip_strict is None:  # which means we cannot perform this type of NTP measurements from our server
        raise HTTPException(status_code=422,
                            detail=f"Our server cannot perform IPv{wanted_ip_type} measurements currently. Try the other IP type.")

    # get the client IP (the same type as wanted_ip_type)
    client_ip: Optional[str] = client_ip_fetch(request=request, wanted_ip_type=wanted_ip_type)
    try:
        response = measure(server, wanted_ip_type, session, client_ip)
        if response is not None:
            new_format = []
            for r in response:
                result, jitter, nr_jitter_measurements = r
                new_format.append(get_format(result, jitter, nr_jitter_measurements))
            return JSONResponse(
                status_code=200,
                content={
                    "measurement": new_format
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Server is not reachable.")
    except HTTPException as e:
        print(e)
        raise e
    except DNSError as e:
        print(e)
        raise HTTPException(status_code=422, detail="Domain name is invalid or cannot be resolved.")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}.")


@router.get(
    "/measurements/history/",
    summary="Retrieve historic NTP measurements",
    description="""
Fetch historic NTP measurement data for a given server over a specified time range.

- Accepts a server IP or domain name.
- Filters data between `start` and `end` timestamps (UTC).
- Rejects queries with invalid or future timestamps.
- Limited to 5 requests per second.
""",
    response_model=MeasurementResponse,
    responses={
        200: {"description": "Successful retrieval of historic measurements"},
        400: {"description": "Invalid parameters or malformed datetime values"},
        500: {"description": "Server error or database access issue"}
    }
)
@limiter.limit(get_rate_limit_per_client_ip())
async def read_historic_data_time(server: str,
                                  start: datetime, end: datetime, request: Request,
                                  session: Session = Depends(get_db)) -> JSONResponse:
    """
    Retrieve historic NTP measurements for a given server and optional time range.

    This endpoint fetches past measurement data for the specified server using the
    `fetch_historic_data_with_timestamps()` function. It can optionally filter results
    based on a time range (start and end datetime).

    Args:
        server (str): IP address or domain name of the NTP server.
        start (datetime, optional): Start timestamp for data filtering.
        end (datetime, optional): End timestamp for data filtering.
        request (Request): Request object for making the limiter work.
        session (Session): The currently active database session.

    Returns:
        JSONResponse: A json response containing a list of formatted measurements under "measurements".

    Raises:
        HTTPException: 400 - If `server` parameter is empty, or the start and end dates are badly formatted (e.g., `start >= end`, `end` in future).
        HTTPException: 500 - If there's an internal server error, such as a database access issue (`MeasurementQueryError`) or any other unexpected server-side exception.

    Notes:
        - This endpoint is also limited to <`see config file`> to prevent abuse and reduce server load.
    """
    if len(server) == 0:
        raise HTTPException(status_code=400, detail="Either 'ip' or 'domain name' must be provided")

    if start >= end:
        raise HTTPException(status_code=400, detail="'start' must be earlier than 'end'")

    if end > datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="'end' cannot be in the future")

    try:
        result = fetch_historic_data_with_timestamps(server, start, end, session)
        formatted_results = [get_format(entry, nr_jitter_measurements=0) for entry in result]
        return JSONResponse(
            status_code=200,
            content={
                "measurements": formatted_results
            }
        )
    except MeasurementQueryError as e:
        raise HTTPException(status_code=500, detail=f"There was an error with accessing the database: {str(e)}.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sever error: {str(e)}.")


# NTS API
@router.post(
    "/measurements/nts/",
    summary="Perform a live NTS measurement",
    description="""
Compute a live NTS synchronization measurement for a specified server.

- Accepts an IP or domain name.
- Returns data about the measurement
- It would NOT be used on the main page. Currently it is experimental.
""",
    response_model=MeasurementResponse,
    responses={
        200: {"description": "Measurement successfully initiated"},
        400: {"description": "Invalid server address"},
    }
)
@limiter.limit(get_rate_limit_per_client_ip())
async def perform_and_read_nts_measurement(payload: MeasurementRequest, request: Request,
                                    session: Session = Depends(get_db)) -> JSONResponse:
    """
    This API will perform an NTS measurement on the specified server.
    Args:
        payload (MeasurementRequest):
            A Pydantic model from which we need:
                - server (str): IP address (IPv4/IPv6) or domain name of the NTP server.
                - ipv6_measurement (bool): True if the type of IPs that we want to measure is IPv6. False otherwise.
        request (Request): The Request object that gives you the IP of the client.
        session (Session): The currently active database session.
    Returns:
        JSONResponse: A json response containing an analysis of the NTS measurement.
    Raises:
        HTTPException: 400 - If the `server` field is empty or no response.
    """
    server = payload.server
    if len(payload.server) == 0:
        raise HTTPException(status_code=400, detail="Either 'ip' or 'dn' must be provided.")
    wanted_ip_type = 6 if payload.ipv6_measurement else 4
    wanted_ip_type = override_desired_ip_type_if_input_is_ip(server, wanted_ip_type)
    # build the settings
    settings = AdvancedSettings()
    settings.wanted_ip_type = wanted_ip_type

    ans: dict = {}
    if is_ip_address(server) is None: # domain name case
        ans = perform_nts_measurement_domain_name(server, settings)
    else:
        ans = perform_nts_measurement_ip(server)
        # add this warning to make things clear (It is hard to try to find the right domain name of an IP address)
        ans["warning_ip"] = "NTS measurements on IPs cannot check TLS certificate."
    return JSONResponse(
        status_code=200,
        content=ans)

# RIPE APIs

@router.post(
    "/measurements/ripe/trigger/",
    summary="Trigger a RIPE Atlas NTP measurement",
    description="""
Initiate a RIPE Atlas NTP measurement for the specified server.

- Accepts an IP address or domain name via the request payload.
- Returns a measurement ID and vantage point metadata.
- Limited to 5 requests per second.
""",
    response_model=RipeMeasurementTriggerResponse,
    responses={
        200: {"description": "Measurement successfully initiated"},
        400: {"description": "Invalid input parameters"},
        502: {"description": "RIPE Atlas measurement failed after initiation"},
        503: {"description": "Failed to retrieve client or server IP"},
        500: {"description": "Internal server error"}
    }
)
@limiter.limit(get_rate_limit_per_client_ip())
async def trigger_ripe_measurement(payload: MeasurementRequest, request: Request) -> JSONResponse:
    """
    Trigger a RIPE Atlas NTP measurement for a specified server.

    This endpoint initiates a RIPE Atlas measurement for the given NTP server
    (IP address or domain name) provided in the payload. Once the measurement
    is triggered, it returns a measurement ID which can later be used to fetch
    the result using the `/measurements/ripe/{measurement_id}` endpoint.

    Args:
        payload (MeasurementRequest):
            A Pydantic model that includes:
                - server (str): The IP address or domain name of the target server.
                - ipv6_measurement (bool): True if the type of IPs that we want to measure is IPv6. False otherwise.
        request (Request): The FastAPI request object, used to extract the client IP address.

    Returns:
        JSONResponse: A json response containing:
            - measurement_id (str): The ID of the triggered RIPE measurement.
            - status (str): Status message ("started").
            - message (str): Instructions on how to retrieve the result.
            - ip_list (list[str]): List of ips for ntp server.

    Raises:
        HTTPException: 400 - If the `server` field is invalid.
        HTTPException: 500 - If the RIPE measurement could not be initiated.
        HTTPException: 502 - If the RIPE measurement was initiated but failed.
        HTTPException: 503 - If we could not get client IP address or our server's IP address.

    Notes:
        - This endpoint is also limited to <`see config file`> to prevent abuse and reduce server load.
    """
    server = payload.server
    wanted_ip_type = 6 if payload.ipv6_measurement else 4
    if len(server) == 0:
        raise HTTPException(status_code=400, detail="Either 'ip' or 'dn' must be provided")

    client_ip: Optional[str] = client_ip_fetch(request=request, wanted_ip_type=wanted_ip_type)
    print("client IP is: ", client_ip)
    try:
        measurement_id = perform_ripe_measurement(server, client_ip=client_ip, wanted_ip_type=wanted_ip_type)
        this_server_ip = get_server_ip_if_possible(wanted_ip_type)  # this does not affect the measurement
        return JSONResponse(
            status_code=200,
            content={
                "measurement_id": measurement_id,
                "vantage_point_ip": ip_to_str(this_server_ip),
                "vantage_point_location": {
                    "country_code": get_country_for_ip(ip_to_str(this_server_ip)),
                    "coordinates": get_coordinates_for_ip(ip_to_str(this_server_ip))
                },
                "status": "started",
                "message": "You can fetch the result at /measurements/ripe/{measurement_id}",
            }
        )
    except InputError as e:
        print(e)
        raise HTTPException(status_code=400,
                            detail=f"Input parameter is invalid. Failed to initiate measurement: {str(e)}")
    except RipeMeasurementError as e:
        print(e)
        raise HTTPException(status_code=502, detail=f"Ripe measurement initiated, but it failed: {str(e)}")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Failed to initiate measurement: {str(e)}")


@router.get(
    "/measurements/ripe/{measurement_id}",
    summary="Fetch RIPE Atlas measurement results",
    description="""
Retrieve the result of a previously triggered RIPE Atlas NTP measurement.

- Accepts a RIPE Atlas `measurement_id` as a path parameter.
- Returns full results if the measurement is complete.
- Returns partial results if some probes are still pending.
- Informs the client if results are not ready yet.
- Limited to 5 requests per second.
""",
    response_model=RipeResult,
    responses={
        200: {"description": "Measurement complete"},
        202: {"description": "Measurement still being processed"},
        206: {"description": "Partial results available"},
        405: {"description": "RIPE API error"},
        504: {"description": "Timeout or incomplete probe data"},
        500: {"description": "Internal server error"}
    }
)
@limiter.limit(get_rate_limit_per_client_ip())
async def get_ripe_measurement_result(measurement_id: str, request: Request) -> JSONResponse:
    """
    Retrieve the results of a previously triggered RIPE Atlas measurement.

    This endpoint checks the RIPE Atlas API for a given measurement ID. It determines
    if the measurement is complete (all probes responded, or measurement was stopped by RIPE Atlas) and returns
    the data accordingly. If the results are not yet ready, it informs the client
    that the measurement is still pending, or that partial results have been returned.

    Args:
        measurement_id (str): The ID of the RIPE measurement to fetch.
        request (Request): The FastAPI Request object (used for rate limiting).

    Returns:
        JSONResponse: A JSON-formatted HTTP response containing the measurement status and results:

            - If the measurement is complete (HTTP 200):

              .. code-block:: json

                 {
                     "status": "complete",
                     "message": "Measurement has been completed.",
                     "results": "<ripe_data>"
                 }

            - If the measurement is still in progress with partial data (HTTP 206):

              .. code-block:: json

                 {
                     "status": "partial_results",
                     "message": "Measurement is still in progress. These are partial results.",
                     "results": "<ripe_data>"
                 }

            - If the measurement has not produced results yet (HTTP 202):

              .. code-block:: text

                 "Measurement is still being processed."

            - If the probe responses are incomplete and likely timed out (HTTP 504):

              .. code-block:: json

                 {
                     "status": "timeout",
                     "message": "RIPE data likely completed but incomplete probe responses."
                 }

    Raises:
        HTTPException: 405 - If the RIPE API request fails (e.g., network or service error).
        HTTPException: 500 - If an unexpected internal error occurs during processing.

    Notes:
        - A measurement is considered "complete" only when all requested probes have responded.
        - The endpoint is rate-limited to <`see config file`> to prevent abuse and manage system load.
    """
    try:
        ripe_measurement_result, status = fetch_ripe_data(measurement_id=measurement_id)
        if not ripe_measurement_result:
            return JSONResponse(status_code=202, content="Measurement is still being processed.")
        if status == "Complete":
            return JSONResponse(
                status_code=200,
                content={
                    "status": "complete",
                    "message": "Measurement has been completed.",
                    "results": ripe_measurement_result
                }
            )

        if status == "Ongoing":
            return JSONResponse(
                status_code=206,
                content={
                    "status": "partial_results",
                    "message": "Measurement is still in progress. These are partial results.",
                    "results": ripe_measurement_result
                }
            )
        return JSONResponse(
            status_code=504,
            content={
                "status": "timeout",
                "message": "RIPE data likely completed but incomplete probe responses."
            }
        )
    except RipeMeasurementError as e:
        print(e)
        raise HTTPException(status_code=405, detail=f"RIPE call failed: {str(e)}. Try again later!")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Sever error: {str(e)}.")
