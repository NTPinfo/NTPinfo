import time
from datetime import datetime, timezone, timedelta

from server.app.utils.load_config_data import get_rate_limit_per_client_ip
from server.tests.integration_tests.db_fixture import *


def test_perform_measurement(client):
    headers = {"X-Forwarded-For": "83.25.24.11"}
    end = datetime.now(timezone.utc)

    resp_get_before = client.get("/measurements/history/", params={
        "server": "216.239.35.4",
        "start": (end - timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    }, headers=headers)

    assert len(resp_get_before.json()["measurements"]) == 0
    cnt = 0
    headers = {"X-Forwarded-For": "83.35.24.20"}
    client.app.state.limiter.reset()  # reset the rate limit
    response = client.post("/measurements/", json={"server": "216.239.35.4"},
                           headers=headers)
    assert response.status_code == 200 or response.status_code == 400
    if response.status_code == 200:
        assert "measurement" in response.json()
    assert len(response.json()) == 1
    client.app.state.limiter.reset()  # reset the rate limit
    end = datetime.now(timezone.utc)
    headers = {"X-Forwarded-For": "83.45.24.30"}
    resp_get_after = client.get("/measurements/history/", params={
        "server": "216.239.35.4",
        "start": (end - timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    }, headers=headers)
    assert len(resp_get_after.json()["measurements"]) == cnt


def test_perform_measurement_dn(client):
    headers = {"X-Forwarded-For": "83.25.24.10"}
    end = datetime.now(timezone.utc)

    resp_get_before = client.get("/measurements/history/", params={
        "server": "time.apple.com",
        "start": (end - timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    })
    assert len(resp_get_before.json()["measurements"]) == 0

    client.app.state.limiter.reset()  # reset the rate limit
    response = client.post("/measurements/", json={"server": "time.apple.com"},
                           headers=headers)
    assert response.status_code == 200 or response.status_code == 400
    assert len(response.json()) == 1
    if response.status_code == 200:
        assert "measurement" in response.json()
        assert len(response.json()["measurement"]) >= 1


def test_perform_multiple_measurements(client):
    headers = {"X-Forwarded-For": "83.25.24.10"}
    end = datetime.now(timezone.utc)

    resp_get_before = client.get("/measurements/history/", params={
        "server": "216.239.35.4",
        "start": (end - timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    })
    assert len(resp_get_before.json()["measurements"]) == 0
    cnt = 0
    for _ in range(3):
        client.app.state.limiter.reset()  # reset the rate limit
        response = client.post("/measurements/", json={"server": "216.239.35.4"},
                               headers=headers)
        assert response.status_code == 200 or response.status_code == 400
        if response.status_code == 200:
            cnt += 1
            assert "measurement" in response.json()
        assert len(response.json()) == 1
        time.sleep(1)

    end = datetime.now(timezone.utc)
    resp_get_after = client.get("/measurements/history/", params={
        "server": "216.239.35.4",
        "start": (end - timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    })
    assert resp_get_after.status_code == 200

    assert len(resp_get_after.json()["measurements"]) == 0


def test_perform_multiple_measurement_rate_limiting(client):
    # try with IP, a different API
    headers = {"X-Forwarded-For": "83.25.24.10"}
    end = datetime.now(timezone.utc)

    resp_get_before = client.get("/measurements/history/", params={
        "server": "216.239.35.4",
        "start": (end - timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    })
    limit_reached = 0
    assert len(resp_get_before.json()["measurements"]) == 0
    n = int(get_rate_limit_per_client_ip().split("/")[0])
    # we can only test the rate limit for small n. Otherwise, the measurements could take too much time and the test
    # could be flaky
    if n <= 10:
        for _ in range(n + 10):
            response = client.post("/measurements/", json={"server": ""},
                                   headers=headers)
            assert response.status_code == 400 or response.status_code == 429
            if response.status_code == 429:
                limit_reached = 1
                break
        assert limit_reached == 1


def test_perform_multiple_measurement_rate_limiting_historical_data(client):
    # test rate limit for historical data
    end = datetime.now(timezone.utc)
    n = int(get_rate_limit_per_client_ip().split("/")[0])
    limit_reached = 0
    # we can only test the rate limit for small n. Otherwise, the measurements could take too much time and the test
    # could be flaky
    if n <= 10:
        for _ in range(n + 10):
            response = client.get("/measurements/history/", params={
                "server": "",
                "start": (end - timedelta(minutes=10)).isoformat(),
                "end": end.isoformat()
            })
            assert response.status_code == 400 or response.status_code == 429
            if response.status_code == 429:
                limit_reached = 1
                break
        assert limit_reached == 1


def test_perform_measurement_empty_server(client):
    headers = {"X-Forwarded-For": "83.25.24.10"}

    response = client.post("/measurements/", json={"server": ""},
                           headers=headers)
    assert response.status_code == 400
    assert response.json() == {'detail': "Either 'ip' or 'dn' must be provided."}

    end = datetime.now(timezone.utc)
    resp_get_after = client.get("/measurements/history/", params={
        "server": "216.239.35.4",
        "start": (end - timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    })
    assert len(resp_get_after.json()["measurements"]) == 0


def test_perform_measurement_wrong_server(client):
    headers = {"X-Forwarded-For": "83.25.24.10"}
    response = client.post("/measurements/", json={"server": "random-server"},
                           headers=headers)
    assert response.status_code == 422
    assert "measurement" not in response.json()

    end = datetime.now(timezone.utc)
    client.app.state.limiter.reset()  # reset the rate limit
    resp_get_after = client.get("/measurements/history/", params={
        "server": "random-server",
        "start": (end - timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    })
    assert len(resp_get_after.json()["measurements"]) == 0


def test_read_historic_data_empty(client):
    end = datetime.now(timezone.utc)
    response = client.get("/measurements/history/", params={
        "server": "",
        "start": (end - timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    })
    assert response.status_code == 400
    assert "measurement" not in response.json()
    assert response.json() == {'detail': "Either 'ip' or 'domain name' must be provided"}


def test_read_historic_data_wrong_start(client):
    end = datetime.now(timezone.utc)
    response = client.get("/measurements/history/", params={
        "server": "91.210.128.220",
        "start": (end + timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    })
    assert response.status_code == 400
    assert "measurement" not in response.json()
    assert response.json() == {'detail': "'start' must be earlier than 'end'"}


def test_read_historic_data_wrong_end(client):
    end = datetime.now(timezone.utc) + timedelta(minutes=10)
    response = client.get("/measurements/history/", params={
        "server": "91.210.128.220",
        "start": (end - timedelta(minutes=10)).isoformat(),
        "end": end.isoformat()
    })
    assert response.status_code == 400
    assert "measurement" not in response.json()
    assert response.json() == {'detail': "'end' cannot be in the future"}
