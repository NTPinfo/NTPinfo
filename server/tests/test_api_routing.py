from unittest.mock import patch, Mock, MagicMock
import pytest
from fastapi.testclient import TestClient
from ipaddress import IPv4Address, IPv6Address, ip_address
from server.app.main import app
from server.app.models.NtpExtraDetails import NtpExtraDetails
from server.app.models.NtpMainDetails import NtpMainDetails
from server.app.models.NtpMeasurement import NtpMeasurement
from server.app.models.NtpServerInfo import NtpServerInfo
from server.app.models.NtpTimestamps import NtpTimestamps
from server.app.models.PreciseTime import PreciseTime
from datetime import datetime, timezone, timedelta
from server.app.db.config import pool

client = None


@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown():
    global client
    client = TestClient(app)
    yield client
    app.state.limiter.reset()
    client.close()


@pytest.fixture(scope="session", autouse=True)
def close_pool_after_tests():
    yield
    if pool:
        pool.close()


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
            ref_name=None
        ),
        timestamps=NtpTimestamps(
            client_sent_time=mock_precise(1),
            server_recv_time=mock_precise(2),
            server_sent_time=mock_precise(3),
            client_recv_time=mock_precise(4),
        ),
        main_details=NtpMainDetails(
            offset=0.123,
            delay=0.456,
            stratum=2,
            precision=-20.0,
            reachability=""
        ),
        extra_details=NtpExtraDetails(
            root_delay=mock_precise(5),
            ntp_last_sync_time=mock_precise(6),
            leap=0
        )
    )


def get_mock_data():
    # Return a list of two elements for mock data
    return [
        {
            'vantage_point_ip': '127.0.0.1',
            'ntp_version': 4,
            'ntp_server_ip': '192.168.1.1',
            'ntp_server_name': 'pool.ntp.org',
            'root_delay': 100,
            'root_delay_prec': 500,
            'ntp_last_sync_time': 200,
            'ntp_last_sync_time_prec': 300,
            'offset': 0.002,
            'delay': 0.005,
            'stratum': 2,
            'precision': 0.0001,
            'reachability': '1111',
            'client_sent': 1609459200,
            'client_sent_prec': 250,
            'server_recv': 1609459205,
            'server_recv_prec': 200,
            'server_sent': 1609459206,
            'server_sent_prec': 150,
            'client_recv': 1609459210,
            'client_recv_prec': 100,
            'ntp_server_ref_parent_ip': '192.168.1.2',
            'ref_name': 'pool.ntp.org',
            'timestamp': (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        },
        {
            'vantage_point_ip': '127.0.0.1',
            'ntp_version': 4,
            'ntp_server_ip': '192.168.1.2',
            'ntp_server_name': 'pool.ntp.org',
            'root_delay': 200,
            'root_delay_prec': 400,
            'ntp_last_sync_time': 300,
            'ntp_last_sync_time_prec': 400,
            'offset': 0.004,
            'delay': 0.008,
            'stratum': 1,
            'precision': 0.0002,
            'reachability': '1010',
            'client_sent': 1609459201,
            'client_sent_prec': 150,
            'server_recv': 1609459206,
            'server_recv_prec': 120,
            'server_sent': 1609459207,
            'server_sent_prec': 90,
            'client_recv': 1609459211,
            'client_recv_prec': 60,
            'ntp_server_ref_parent_ip': '192.168.1.3',
            'ref_name': 'pool.ntp.org',
            'timestamp': (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        }
    ]


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


@patch("server.app.services.api_services.perform_ntp_measurement_domain_name")
@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.is_ip_address")
def test_read_data_measurement_success(mock_is_ip, mock_insert, mock_perform_measurement):
    mock_is_ip.return_value = None
    measurement = mock_measurement()
    mock_perform_measurement.return_value = (measurement, ["83.25.24.10"])

    headers = {"X-Forwarded-For": "83.25.24.10"}
    response = client.post("/measurements/", json={"server": "pool.ntp.org", "jitter_flag": False}, headers=headers)
    assert response.status_code == 200
    assert "measurement" in response.json()
    assert response.json()["measurement"]["ntp_server_name"] == "pool.ntp.org"
    assert response.json()["measurement"]["jitter"] is None
    mock_perform_measurement.assert_called_with("pool.ntp.org", "83.25.24.10")
    mock_insert.assert_called_once_with(measurement, mock_insert.call_args[0][1])


@patch("server.app.services.api_services.perform_ntp_measurement_domain_name")
@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.is_ip_address")
def test_read_data_measurement_missing_measurement_no(mock_is_ip, mock_insert, mock_perform_measurement):
    mock_is_ip.return_value = None
    measurement = mock_measurement()
    mock_perform_measurement.return_value = (measurement, ["83.25.24.10"])

    headers = {"X-Forwarded-For": "83.25.24.10"}
    response = client.post("/measurements/", json={"server": "pool.ntp.org", "jitter_flag": True}, headers=headers)
    assert response.status_code == 422
    assert "measurements_no is required when jitter_flag is True." in response.text


@patch("server.app.services.api_services.perform_ntp_measurement_domain_name")
@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.is_ip_address")
@patch("server.app.services.api_services.calculate_jitter_from_measurements")
def test_read_data_measurement_with_jitter(mock_jitter, mock_is_ip, mock_insert, mock_perform_measurement):
    mock_is_ip.return_value = None
    measurement = mock_measurement()
    mock_perform_measurement.return_value = (measurement, ["83.25.24.10"])
    mock_jitter.return_value = 0.75

    headers = {"X-Forwarded-For": "83.25.24.10"}
    response = client.post("/measurements/", json={"server": "pool.ntp.org", "jitter_flag": True, "measurements_no": 3},
                           headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert "measurement" in json_data
    assert response.json()["measurement"]["jitter"] == 0.75


def test_read_data_measurement_missing_server():
    headers = {"X-Forwarded-For": "83.25.24.10"}
    response = client.post("/measurements/", json={"server": "", "jitter_flag": False}, headers=headers)
    assert response.status_code == 400
    assert response.json() == {"error": "Either 'ip' or 'dn' must be provided"}


def test_read_data_measurement_wrong_server():
    headers = {"X-Forwarded-For": "83.25.24.10"}
    response = client.post("/measurements/", json={"server": "random-server-name.org", "jitter_flag": False},
                           headers=headers)
    assert response.status_code == 200
    assert response.json() == {"error": "Could not perform measurement, dns or ip not reachable."}


@patch("server.app.services.api_services.get_measurements_timestamps_dn")
@patch("server.app.services.api_services.get_measurements_timestamps_ip")
@patch("server.app.services.api_services.is_ip_address")
@patch("server.app.services.api_services.human_date_to_ntp_precise_time")
def test_read_historic_data_ip(mock_human_date_to_ntp, mock_is_ip, mock_get_ip, mock_get_dn):
    end = datetime.now(timezone.utc)
    mock_is_ip.return_value = IPv4Address("192.168.1.1")
    mock_human_date_to_ntp.return_value = PreciseTime(1000, 500)
    mock_data = get_mock_data()

    mock_get_ip.return_value = mock_data  # Mock for IP address fetch
    mock_get_dn.return_value = mock_data  # Mock for Domain Name fetch
    response = client.get("/measurements/history/", params={
        "server": "192.168.1.1",
        "start": (end - timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    })

    assert response.status_code == 200
    data = response.json()["measurements"]
    assert len(data) == 2
    assert data[0]["ntp_server_ip"] == "192.168.1.1"
    mock_get_ip.assert_called_once()
    mock_get_dn.assert_not_called()


@patch("server.app.services.api_services.get_measurements_timestamps_dn")
@patch("server.app.services.api_services.get_measurements_timestamps_ip")
@patch("server.app.services.api_services.is_ip_address")
@patch("server.app.services.api_services.human_date_to_ntp_precise_time")
def test_read_historic_data_dn(mock_human_date_to_ntp, mock_is_ip, mock_get_ip, mock_get_dn):
    end = datetime.now(timezone.utc)
    mock_is_ip.return_value = None
    mock_human_date_to_ntp.return_value = PreciseTime(1000, 500)
    mock_data = get_mock_data()

    mock_get_ip.return_value = mock_data  # Mock for IP address fetch
    mock_get_dn.return_value = mock_data  # Mock for Domain Name fetch
    response = client.get("/measurements/history/", params={
        "server": "pool.ntp.org",
        "start": (end - timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    })

    assert response.status_code == 200
    data = response.json()["measurements"]
    assert len(data) == 2
    assert data[0]["ntp_server_name"] == "pool.ntp.org"
    mock_get_ip.assert_not_called()
    mock_get_dn.assert_called_once()


def test_read_historic_data_missing_server():
    end = datetime.now(timezone.utc)
    response = client.get("/measurements/history/", params={
        "server": None,
        "start": (end - timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    })
    assert response.status_code == 400
    assert response.json() == {'error': "Either 'ip' or 'domain name' must be provided"}


def test_read_historic_data_wrong_start():
    end = datetime.now(timezone.utc)
    response = client.get("/measurements/history/", params={
        "server": "pool.ntp.org",
        "start": (end + timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    })
    assert response.status_code == 400
    assert response.json() == {"error": "'start' must be earlier than 'end'"}


def test_read_historic_data_wrong_end():
    end = datetime.now(timezone.utc)
    response = client.get("/measurements/history/", params={
        "server": "pool.ntp.org",
        "start": (end - timedelta(minutes=10)).isoformat(),
        "end": (end + timedelta(minutes=10)).isoformat()
    })
    assert response.status_code == 400
    assert response.json() == {"error": "'end' cannot be in the future"}


@patch("server.app.services.api_services.perform_ntp_measurement_domain_name")
@patch("server.app.services.api_services.insert_measurement")
@patch("server.app.services.api_services.is_ip_address")
def test_perform_measurement_with_rate_limiting(mock_is_ip, mock_insert, mock_perform_measurement):
    mock_is_ip.return_value = None
    measurement = mock_measurement()
    mock_perform_measurement.return_value = (measurement, ["83.25.24.10"])

    for _ in range(5):
        headers = {"X-Forwarded-For": "83.25.24.10"}
        response = client.post("/measurements/", json={"server": "pool.ntp.org", "jitter_flag": False}, headers=headers)
        assert response.status_code == 200
        assert "measurement" in response.json()
        assert response.json()["measurement"]["ntp_server_name"] == "pool.ntp.org"
        assert response.json()["measurement"]["jitter"] is None
        mock_perform_measurement.assert_called_with("pool.ntp.org", "83.25.24.10")

    assert mock_perform_measurement.call_count == 5
    calls_before_6th = mock_perform_measurement.call_count
    response = client.post("/measurements/", json={"server": "pool.ntp.org", "jitter_flag": False}, headers=headers)
    assert response.status_code == 429
    assert response.json() == {"error": "Rate limit exceeded: 5 per 1 minute"}

    assert mock_perform_measurement.call_count == calls_before_6th


@patch("server.app.services.api_services.get_measurements_timestamps_dn")
@patch("server.app.services.api_services.get_measurements_timestamps_ip")
@patch("server.app.services.api_services.is_ip_address")
@patch("server.app.services.api_services.human_date_to_ntp_precise_time")
def test_historic_data_ip_rate_limiting(mock_human_date_to_ntp, mock_is_ip, mock_get_ip, mock_get_dn):
    end = datetime.now(timezone.utc)
    mock_is_ip.return_value = IPv4Address("192.168.0.1")
    mock_human_date_to_ntp.return_value = PreciseTime(1000, 500)
    mock_data = get_mock_data()

    mock_get_ip.return_value = mock_data  # Mock for IP address fetch
    mock_get_dn.return_value = mock_data  # Mock for Domain Name fetch
    for _ in range(5):
        response = client.get("/measurements/history/", params={
            "server": "192.168.1.1",
            "start": (end - timedelta(minutes=10)).isoformat(),
            "end": end.isoformat()
        })

        assert response.status_code == 200
        data = response.json()["measurements"]
        assert len(data) == 2
        assert data[0]["ntp_server_ip"] == "192.168.1.1"

    assert mock_get_ip.call_count == 5

    calls_before_6th = mock_get_ip.call_count
    response = client.get("/measurements/history/", params={
        "server": "192.168.1.1",
        "start": (end - timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    })
    assert response.status_code == 429
    assert response.json() == {"error": "Rate limit exceeded: 5 per 1 minute"}

    assert mock_get_ip.call_count == calls_before_6th
    mock_get_dn.assert_not_called()


@patch("server.app.services.api_services.get_measurements_timestamps_dn")
@patch("server.app.services.api_services.get_measurements_timestamps_ip")
@patch("server.app.services.api_services.is_ip_address")
@patch("server.app.services.api_services.human_date_to_ntp_precise_time")
def test_historic_data_dn_rate_limiting(mock_human_date_to_ntp, mock_is_ip, mock_get_ip, mock_get_dn):
    end = datetime.now(timezone.utc)
    mock_is_ip.return_value = None
    mock_human_date_to_ntp.return_value = PreciseTime(1000, 500)
    mock_data = get_mock_data()

    mock_get_ip.return_value = mock_data  # Mock for IP address fetch
    mock_get_dn.return_value = mock_data  # Mock for Domain Name fetch

    for _ in range(5):
        response = client.get("/measurements/history/", params={
            "server": "pool.ntp.org",
            "start": (end - timedelta(minutes=10)).isoformat(),
            "end": end.isoformat()
        })

        assert response.status_code == 200
        data = response.json()["measurements"]
        assert len(data) == 2
        assert data[0]["ntp_server_name"] == "pool.ntp.org"

    assert mock_get_dn.call_count == 5

    calls_before_6th = mock_get_dn.call_count
    response = client.get("/measurements/history/", params={
        "server": "pool.ntp.org",
        "start": (end - timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    })
    assert response.status_code == 429
    assert response.json() == {"error": "Rate limit exceeded: 5 per 1 minute"}

    assert mock_get_dn.call_count == calls_before_6th
    mock_get_ip.assert_not_called()
