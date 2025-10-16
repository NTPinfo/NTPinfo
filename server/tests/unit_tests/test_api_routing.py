from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from ipaddress import IPv4Address, ip_address

from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from server.app.utils.load_config_data import get_rate_limit_per_client_ip
from server.app.dtos.ProbeData import ServerLocation
from server.app.models.CustomError import RipeMeasurementError, DNSError, MeasurementQueryError
from server.app.models.Base import Base
from server.app.main import create_app
from server.app.dtos.NtpExtraDetails import NtpExtraDetails
from server.app.dtos.NtpMainDetails import NtpMainDetails
from server.app.dtos.NtpMeasurement import NtpMeasurement
from server.app.dtos.NtpServerInfo import NtpServerInfo
from server.app.dtos.NtpTimestamps import NtpTimestamps
from server.app.dtos.PreciseTime import PreciseTime
from datetime import datetime, timezone, timedelta
from server.app.api.routing import get_db

engine = MagicMock(spec=Engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# @patch("server.app.main.load_config_data.verify_if_config_is_set")
# @patch("server.app.db_config.init_engine")
@pytest.fixture(scope="function", autouse=True)
def test_client():  # mock_init_engine, mock_verify_config):
    # mock_init_engine.return_value = True
    # mock_verify_config.return_value = True
    with patch("server.app.db_config.init_engine") as mocked_init_engine:
        mocked_init_engine.return_value = None

        test_app = create_app(dev=False)
        test_app.dependency_overrides[get_db] = override_get_db

        Base.metadata.create_all(bind=engine)

        client = TestClient(test_app)
        yield client

        client.close()
        Base.metadata.drop_all(bind=engine)
        test_app.state.limiter.reset()


def mock_precise(seconds=1234567890, fraction=0) -> PreciseTime:
    return PreciseTime(seconds=seconds, fraction=fraction)


def mock_measurement() -> NtpMeasurement:
    return NtpMeasurement(
        vantage_point_ip=ip_address('127.0.0.1'),
        server_info=NtpServerInfo(
            ntp_version=4,
            ntp_server_ip=IPv4Address("192.168.0.1"),
            ntp_server_name="pool.ntp.org",
            ntp_server_ref_parent_ip=None,
            ref_name=None,
            ntp_server_location=ServerLocation(country_code="RO", coordinates=(25.0, -71.0))
        ),
        timestamps=NtpTimestamps(
            client_sent_time=mock_precise(1),
            server_recv_time=mock_precise(2),
            server_sent_time=mock_precise(3),
            client_recv_time=mock_precise(4),
        ),
        main_details=NtpMainDetails(
            offset=0.123,
            rtt=0.456,
            stratum=2,
            precision=-20.0,
            reachability=""
        ),
        extra_details=NtpExtraDetails(
            root_delay=mock_precise(5),
            ntp_last_sync_time=mock_precise(6),
            root_dispersion=mock_precise(7),
            poll=5,
            leap=0
        )
    )


def get_mock_data():
    return [
        NtpMeasurement(
            vantage_point_ip=ip_address('127.0.0.1'),
            server_info=NtpServerInfo(
                ntp_version=4,
                ntp_server_ip=IPv4Address("192.168.1.1"),
                ntp_server_name="pool.ntp.org",
                ntp_server_ref_parent_ip=IPv4Address("192.168.1.2"),
                ref_name="pool.ntp.org",
                ntp_server_location=ServerLocation(country_code="RO", coordinates=(25.0, -71.0))
            ),
            timestamps=NtpTimestamps(
                client_sent_time=mock_precise(1609459200),
                server_recv_time=mock_precise(1609459205),
                server_sent_time=mock_precise(1609459206),
                client_recv_time=mock_precise(1609459210),
            ),
            main_details=NtpMainDetails(
                offset=0.002,
                rtt=0.005,
                stratum=2,
                precision=0.0001,
                reachability="1111"
            ),
            extra_details=NtpExtraDetails(
                root_delay=mock_precise(100),
                ntp_last_sync_time=mock_precise(200),
                root_dispersion=mock_precise(400),
                poll=60,
                leap=0
            )
        ),
        NtpMeasurement(
            vantage_point_ip=ip_address('127.0.0.1'),
            server_info=NtpServerInfo(
                ntp_version=4,
                ntp_server_ip=IPv4Address("192.168.1.2"),
                ntp_server_name="pool.ntp.org",
                ntp_server_ref_parent_ip=IPv4Address("192.168.1.3"),
                ref_name="pool.ntp.org",
                ntp_server_location=ServerLocation(country_code="GL", coordinates=(25.2132, -71.4343))
            ),
            timestamps=NtpTimestamps(
                client_sent_time=mock_precise(1609459201),
                server_recv_time=mock_precise(1609459206),
                server_sent_time=mock_precise(1609459207),
                client_recv_time=mock_precise(1609459211),
            ),
            main_details=NtpMainDetails(
                offset=0.004,
                rtt=0.008,
                stratum=1,
                precision=0.0002,
                reachability="1010"
            ),
            extra_details=NtpExtraDetails(
                root_delay=mock_precise(200),
                ntp_last_sync_time=mock_precise(300),
                root_dispersion=mock_precise(500),
                poll=5,
                leap=0
            )
        ),
    ]


def mock_fetch_ripe_data_result():
    return {
        "ntp_version": 4,
        "ripe_measurement_id": 123456,
        "ntp_server_ip": "some_ip_ntp",
        "ntp_server_name": "time.google.com",

        "probe_addr": {
            "ipv4": "some_ip_probe",
            "ipv6": None
        },

        "probe_id": 123,

        "probe_location": {
            "country_code": "RO",
            "coordinates": [12.23, 13.20]
        },

        "time_to_result": 5014.4233,
        "stratum": 1,
        "poll": 1,
        "precision": 9.53674e-07,

        "root-delay": {
            "seconds": 3957511627,
            "fraction": 3696222208
        },

        "root-dispersion": 7.62939e-05,
        "ref-id": "GOOG",

        "probe_count_per_type": {
            "asn": 9,
            "prefix": 1,
            "country": 26,
            "area": 4,
            "random": 0
        },

        "result": [
            {
                "client_sent_time": {
                    "seconds": 3957511627,
                    "fraction": 3696222208
                },
                "server_recv_time": {
                    "seconds": 3957511627,
                    "fraction": 3723411456
                },
                "server_sent_time": {
                    "seconds": 3957511627,
                    "fraction": 3696222208
                },
                "client_recv_time": {
                    "seconds": 3957511627,
                    "fraction": 3696222208
                },
                "rtt": 0.027478,
                "offset": 0.065277
            }
        ]
    }


def test_read_root(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    assert "<title>NTPInfo API</title>" in response.text
    assert "Welcome to the NTPInfo API" in response.text
    assert "interactive docs" in response.text


# @patch("server.app.api.routing.Depends")
@patch("server.app.api.routing.get_server_ip")
@patch("server.app.services.api_services.perform_ntp_measurement_domain_name_list")
@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.is_ip_address")
def test_read_data_measurement_success(mock_is_ip, mock_insert, mock_perform_measurement, mock_get_server_ip,
                                       test_client):
    mock_db = MagicMock()

    # Override FastAPI dependency
    app = create_app(dev=False)
    app.dependency_overrides[get_db] = mock_db
    client = TestClient(app)
    mock_is_ip.return_value = None
    measurement = mock_measurement()
    # mock_depends.return_value = MagicMock()
    mock_get_server_ip.return_value = "234.22.41.9"

    mock_perform_measurement.return_value = [measurement]

    headers = {"X-Forwarded-For": "83.25.24.10"}
    response = test_client.post("/measurements/", json={"server": "pool.ntp.org", "ipv6_measurement": False},
                                headers=headers)
    assert response.status_code == 200
    assert "measurement" in response.json()
    assert response.json()["measurement"][0]["ntp_server_name"] == "pool.ntp.org"
    assert response.json()["measurement"][0]["jitter"] == 0
    mock_perform_measurement.assert_called_with("pool.ntp.org", "83.25.24.10", 4)
    mock_insert.assert_called_once_with(measurement, mock_insert.call_args[0][1])
    client.close()


@patch("server.app.api.routing.get_server_ip")
@patch("server.app.services.api_services.perform_ntp_measurement_domain_name_list")
@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.is_ip_address")
def test_read_data_measurement_missing_measurement_no(mock_is_ip, mock_insert, mock_perform_measurement,
                                                      mock_get_server_ip, test_client):
    mock_is_ip.return_value = None
    measurement = mock_measurement()
    mock_get_server_ip.return_value = "234.22.41.9"
    mock_perform_measurement.return_value = measurement
    headers = {"X-Forwarded-For": "83.25.24.10"}
    response = test_client.post("/measurements/", json={"server": "pool.ntp.org", "ipv6_measurement": False},
                                headers=headers)
    assert response.status_code == 400
    assert '{"detail":"Server is not reachable."}' in response.text


@patch("server.app.api.routing.get_server_ip")
@patch("server.app.services.api_services.perform_ntp_measurement_domain_name_list")
@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.is_ip_address")
@patch("server.app.services.api_services.calculate_jitter_from_measurements")
def test_read_data_measurement_with_jitter(mock_jitter, mock_is_ip, mock_insert, mock_perform_measurement,
                                           mock_get_server_ip, test_client):
    mock_is_ip.return_value = None
    measurement = mock_measurement()
    mock_get_server_ip.return_value = "234.22.41.9"
    mock_perform_measurement.return_value = [measurement]
    mock_jitter.return_value = 0.75, 4

    headers = {"X-Forwarded-For": "83.25.24.10"}
    response = test_client.post("/measurements/",
                                json={"server": "pool.ntp.org", "ipv6_measurement": False},
                                headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert "measurement" in json_data
    assert response.json()["measurement"][0]["jitter"] == 0.75
    assert response.json()["measurement"][0]["nr_measurements_jitter"] == 4
    mock_insert.assert_called_once()


def test_read_data_measurement_missing_server(test_client):
    headers = {"X-Forwarded-For": "83.25.24.10"}

    response = test_client.post("/measurements/", json={"server": ""}, headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "Either 'ip' or 'dn' must be provided."}


@patch("server.app.api.routing.get_server_ip")
def test_read_data_measurement_wrong_server(mock_get_server_ip, test_client):
    mock_get_server_ip.return_value = "234.22.41.9"
    headers = {"X-Forwarded-For": "83.25.24.10"}

    response = test_client.post("/measurements/", json={"server": "random-server-name.org", "ipv6_measurement": False},
                                headers=headers)
    assert response.status_code == 422
    assert response.json() == {"detail": "Domain name is invalid or cannot be resolved."}


def create_mock_measurement(measurement_id, host, ip, client_sent_time):
    mock = MagicMock()
    mock.id = measurement_id
    mock.host = host
    mock.measured_server_ip = ip
    mock.client_sent_time = client_sent_time
    return mock


def get_mock_dict_data(ntp_server_ip=None, ntp_server_name=None, poll=60):
    return {
        "id": 1,
        "host": ntp_server_name,
        "measured_server_ip": ntp_server_ip,
        "offset": 0.011264801025390625,
        "rtt": 0.011186599731445312,
        "stratum": 1,
        "poll": poll,
        "client_sent_time": 17047961655855346000,
        "server_recv_time": 17047961655927750000,
        "server_sent_time": 17047961655927750000,
        "client_recv_time": 17047961655903392000,
        "ref_time": 17047961655927750000,
        "leap": 0,
        "mode": 4,
        "version": 4,
        "precision": -20,
        "root_delay": 0,
        "root_disp": 0.0000762939453125,
        "ref_id": "some ref",
        "extensions": None,
        "analysis": "It supports NTPv4."
    }


@patch("server.app.api.routing.get_ntp_v4_historical_measurements")
def test_read_historic_data_ip(mock_get_measurements, test_client):
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=10)

    mock_get_measurements.return_value = [
        get_mock_dict_data(ntp_server_ip="192.168.1.1", poll=60),
        get_mock_dict_data(ntp_server_ip="192.168.1.1", poll=5)
    ]

    response = test_client.get("/measurements/history/", params={
        "server": "192.168.1.1",
        "start": start.isoformat(),
        "end": end.isoformat()
    })

    assert response.status_code == 200
    data = response.json()["measurements"]
    assert len(data) == 2
    assert data[0]["measured_server_ip"] == "192.168.1.1"
    assert data[0]["poll"] == 60
    assert data[1]["poll"] == 5
    mock_get_measurements.assert_called_once()


@patch("server.app.api.routing.get_ntp_v4_historical_measurements")
def test_read_historic_data_dn(mock_get_measurements, test_client):
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=10)

    mock_get_measurements.return_value = [
        get_mock_dict_data(ntp_server_name="pool.ntp.org", poll=60),
        get_mock_dict_data(ntp_server_name="pool.ntp.org", poll=5)
    ]

    response = test_client.get("/measurements/history/", params={
        "server": "pool.ntp.org",
        "start": start.isoformat(),
        "end": end.isoformat()
    })

    assert response.status_code == 200
    data = response.json()["measurements"]
    assert len(data) == 2
    assert data[0]["host"] == "pool.ntp.org"
    assert data[0]["poll"] == 60
    assert data[1]["poll"] == 5
    mock_get_measurements.assert_called_once()


def test_read_historic_data_missing_server(test_client):
    end = datetime.now(timezone.utc)

    response = test_client.get("/measurements/history/", params={
        "server": None,
        "start": (end - timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    })
    assert response.status_code == 400
    assert response.json() == {"detail": "Either 'ip' or 'domain name' must be provided"}


def test_read_historic_data_wrong_start(test_client):
    end = datetime.now(timezone.utc)

    response = test_client.get("/measurements/history/", params={
        "server": "pool.ntp.org",
        "start": (end + timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    })
    assert response.status_code == 400
    assert response.json() == {"detail": "'start' must be earlier than 'end'"}


def test_read_historic_data_wrong_end(test_client):
    end = datetime.now(timezone.utc)

    response = test_client.get("/measurements/history/", params={
        "server": "pool.ntp.org",
        "start": (end - timedelta(minutes=10)).isoformat(),
        "end": (end + timedelta(minutes=10)).isoformat()
    })
    assert response.status_code == 400
    assert response.json() == {"detail": "'end' cannot be in the future"}


@patch("server.app.api.routing.get_server_ip")
@patch("server.app.services.api_services.perform_ntp_measurement_domain_name_list")
@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.is_ip_address")
def test_perform_measurement_with_rate_limiting(mock_is_ip, mock_insert, mock_perform_measurement,
                                                mock_get_server_ip, test_client):
    mock_is_ip.return_value = None
    measurement = mock_measurement()
    mock_get_server_ip.return_value = "234.22.41.9"

    mock_perform_measurement.return_value = [measurement]

    n = int(get_rate_limit_per_client_ip().split("/")[0])
    test_client.app.state.limiter.reset()  # reset the rate limit
    for _ in range(n):
        headers = {"X-Forwarded-For": "83.25.24.10"}
        response = test_client.post("/measurements/", json={"server": "pool.ntp.org", "ipv6_measurement": False},
                                    headers=headers)
        assert response.status_code == 200
        assert "measurement" in response.json()
        assert response.json()["measurement"][0]["ntp_server_name"] == "pool.ntp.org"
        assert response.json()["measurement"][0]["jitter"] == 0.0
        mock_perform_measurement.assert_called_with("pool.ntp.org", "83.25.24.10", 4)

    assert mock_perform_measurement.call_count == n
    calls_before_6th = mock_perform_measurement.call_count
    response = test_client.post("/measurements/", json={"server": "pool.ntp.org", "ipv6_measurement": False},
                                headers=headers)
    assert response.status_code == 429
    assert ("error" in response.json())

    assert mock_perform_measurement.call_count == calls_before_6th


@patch("server.app.api.routing.get_ntp_v4_historical_measurements")
def test_historic_data_ip_rate_limiting(mock_get_measurements, test_client):
    end = datetime.now(timezone.utc)

    mock_get_measurements.return_value = [
        get_mock_dict_data(ntp_server_ip="192.168.1.1", poll=60),
        get_mock_dict_data(ntp_server_ip="192.168.1.1", poll=5)
    ]

    n = int(get_rate_limit_per_client_ip().split("/")[0])
    test_client.app.state.limiter.reset()  # reset the rate limit

    for _ in range(n):
        response = test_client.get("/measurements/history/", params={
            "server": "192.168.1.1",
            "start": (end - timedelta(minutes=10)).isoformat(),
            "end": end.isoformat()
        })

        assert response.status_code == 200
        data = response.json()["measurements"]
        assert len(data) == 2
        assert data[0]["measured_server_ip"] == "192.168.1.1"
        assert data[0]["poll"] == 60
        assert data[1]["poll"] == 5

    assert mock_get_measurements.call_count == n

    response = test_client.get("/measurements/history/", params={
        "server": "192.168.1.1",
        "start": (end - timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    })

    assert response.status_code == 429
    assert "error" in response.json()
    assert mock_get_measurements.call_count == n


@patch("server.app.api.routing.get_ntp_v4_historical_measurements")
def test_historic_data_dn_rate_limiting(mock_get_measurements, test_client):
    end = datetime.now(timezone.utc)

    mock_get_measurements.return_value = [
        get_mock_dict_data(ntp_server_name="pool.ntp.org", poll=60),
        get_mock_dict_data(ntp_server_name="pool.ntp.org", poll=5)
    ]

    n = int(get_rate_limit_per_client_ip().split("/")[0])
    test_client.app.state.limiter.reset()  # reset the rate limit

    for _ in range(n):
        response = test_client.get("/measurements/history/", params={
            "server": "pool.ntp.org",
            "start": (end - timedelta(minutes=10)).isoformat(),
            "end": end.isoformat()
        })

        assert response.status_code == 200
        data = response.json()["measurements"]
        assert len(data) == 2
        assert data[0]["host"] == "pool.ntp.org"
        assert data[0]["poll"] == 60
        assert data[1]["poll"] == 5

    assert mock_get_measurements.call_count == n

    response = test_client.get("/measurements/history/", params={
        "server": "pool.ntp.org",
        "start": (end - timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    })

    assert response.status_code == 429
    assert "error" in response.json()
    assert mock_get_measurements.call_count == n


def test_trigger_ripe_measurement_server_not_present(test_client):
    headers = {"X-Forwarded-For": "83.25.24.10"}
    response = test_client.post("/measurements/ripe/trigger/",
                                json={"server": "", "ipv6_measurement": False},
                                headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "Either 'ip' or 'dn' must be provided"}


@patch("server.app.api.routing.perform_ripe_measurement")
def test_trigger_ripe_measurement_server_ip(mock_perform_ripe_measurement, test_client):
    mock_perform_ripe_measurement.return_value = "123456"
    headers = {"X-Forwarded-For": "83.25.24.10"}
    response = test_client.post("/measurements/ripe/trigger/",
                                json={"server": "83.25.24.10", "ipv6_measurement": False},
                                headers=headers)
    assert response.status_code == 200
    assert response.json()["measurement_id"] == "123456"
    assert response.json()["status"] == "started"
    assert response.json()["message"] == "You can fetch the result at /measurements/ripe/{measurement_id}"


@patch("server.app.api.routing.perform_ripe_measurement")
def test_trigger_ripe_measurement_server_dn(mock_perform_ripe_measurement, test_client):
    mock_perform_ripe_measurement.return_value = "123456"
    headers = {"X-Forwarded-For": "83.25.24.10"}
    response = test_client.post("/measurements/ripe/trigger/",
                                json={"server": "time.server_some.com", "ipv6_measurement": False},
                                headers=headers)
    assert response.status_code == 200
    assert response.json()["measurement_id"] == "123456"
    assert response.json()["status"] == "started"
    assert response.json()["message"] == "You can fetch the result at /measurements/ripe/{measurement_id}"


@patch("server.app.api.routing.perform_ripe_measurement")
def test_trigger_ripe_measurement_server_error(mock_perform_ripe_measurement, test_client):
    mock_perform_ripe_measurement.side_effect = Exception("Could not find any IP address for time.server_some.com.")

    headers = {"X-Forwarded-For": "83.25.24.10"}
    response = test_client.post("/measurements/ripe/trigger/",
                                json={"server": "time.server_some.com", "ipv6_measurement": False},
                                headers=headers)

    assert response.status_code == 500
    assert response.json()[
               "detail"] == "Failed to initiate measurement: Could not find any IP address for time.server_some.com."


@patch("server.app.api.routing.fetch_ripe_data")
def test_get_ripe_measurement_result_pending(mock_fetch_ripe_data, test_client):
    mock_fetch_ripe_data.return_value = None, "Timeout"
    response = test_client.get("/measurements/ripe/123456")
    assert response.status_code == 202
    print(response.json())
    assert response.json() == "Measurement is still being processed."


@patch("server.app.api.routing.fetch_ripe_data")
def test_get_ripe_measurement_result_partial(mock_fetch_ripe_data, test_client):
    mock_fetch_ripe_data.return_value = mock_fetch_ripe_data_result(), "Ongoing"
    response = test_client.get("/measurements/ripe/123456")
    assert response.status_code == 206
    assert response.json()["status"] == "partial_results"
    assert response.json()["results"] == mock_fetch_ripe_data_result()


@patch("server.app.api.routing.fetch_ripe_data")
def test_get_ripe_measurement_result_complete(mock_fetch_ripe_data, test_client):
    mock_fetch_ripe_data.return_value = mock_fetch_ripe_data_result(), "Complete"
    response = test_client.get("/measurements/ripe/123456")
    assert response.status_code == 200
    assert response.json()["status"] == "complete"
    assert response.json()["results"] == mock_fetch_ripe_data_result()


@patch("server.app.api.routing.fetch_ripe_data")
def test_get_ripe_measurement_result_error(mock_fetch_ripe_data, test_client):
    mock_fetch_ripe_data.side_effect = RipeMeasurementError(
        "RIPE API error: Bad Request - There was a problem with your request")
    response = test_client.get("/measurements/ripe/123456")
    assert response.status_code == 405
    assert response.json()[
               "detail"] == "RIPE call failed: RIPE API error: Bad Request - There was a problem with your request. Try again later!"
