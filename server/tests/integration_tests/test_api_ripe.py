import pytest
from fastapi.testclient import TestClient

from server.app.dtos.AdvancedSettings import AdvancedSettings
from server.app.utils.load_config_data import get_ripe_api_token
from server.app.main import create_app
from server.app.utils.ripe_fetch_data import check_all_measurements_scheduled, check_all_measurements_done, \
    get_data_from_ripe_measurement, get_probe_data_from_ripe_by_id
from server.app.utils.ripe_probes import get_available_probes_asn_and_prefix, get_available_probes_asn_and_country, \
    get_available_probes_country, get_available_probes_asn, get_available_probes_prefix, get_probes

@pytest.fixture(scope="function")
def client():
    app = create_app(dev=False)
    app.state.limiter.reset()
    client = TestClient(app)
    yield client
    app.state.limiter.reset()
# test integration with creating a RIPE measurement.

def test_creating_ripe_measurement_unsuccessful(client):
    headers = {"X-Forwarded-For": "83.25.24.10"}
    response = client.post("/measurements/ripe/trigger/", json={"server": "", "ipv6_measurement": False})
    assert response.status_code == 400
    client.app.state.limiter.reset() # reset the rate limit
    response = client.post("/measurements/ripe/trigger/", json={"server": "4536.35.pool.bla", "ipv6_measurement": False},
                           headers=headers)

    # failed RIPE measurement because that domain name is an invalid NTP server
    assert response.status_code == 502

def test_creating_ripe_measurement_successful(client):
    # try:
    #     get_ripe_api_token()
    # except Exception:
    #     print("could not perform this test: creating_ripe_measurement_successful")
    #     return
    headers = {"X-Forwarded-For": "83.25.24.10"}
    response = client.post("/measurements/ripe/trigger/", json={"server": "pool.ntp.org", "ipv6_measurement": False},
                           headers=headers)
    assert response.status_code == 200
    assert "measurement_id" in response.json()
    # response = client.post("/measurements/ripe/trigger/", json={"server": "216.239.35.4", "ipv6_measurement": False},
    #                        headers=headers)
    # assert response.status_code == 200
    # assert "measurement_id" in response.json()


def test_creating_ripe_measurement_successful_ipv6(client):
    headers = {"X-Forwarded-For": "2a06:93c0::24"}
    response = client.post("/measurements/ripe/trigger/", json={"server": "time.google.com", "ipv6_measurement": True},
                           headers=headers)
    assert response.status_code == 200
    assert "measurement_id" in response.json()

    client.app.state.limiter.reset() # reset the rate limit
    # now test that the IP type of our client does not matter:
    headers = {"X-Forwarded-For": "83.25.24.10"}
    response = client.post("/measurements/ripe/trigger/", json={"server": "2001:4860:4806:8::", "ipv6_measurement": True},
                           headers=headers)
    assert response.status_code == 200
    assert "measurement_id" in response.json() # check if the measurement was successful

# test integration with getting the data from a measurement ID (fetching)
def test_get_ripe_measurement_result_unsuccessful(client):
    response = client.get("/measurements/ripe/-107704481")
    assert response.status_code == 405 or response.status_code == 500

def test_get_ripe_measurement_result_successful(client):
    # try:
    #     get_ripe_api_token()
    # except Exception:
    #     print("could not perform this test: get_ripe_measurement_result_successful")
    #     return
    response = client.get("/measurements/ripe/107704481")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "complete"

def test_fetching_details_about_measurement():
    # try:
    #     get_ripe_api_token()
    # except Exception:
    #     print("could not perform this test: fetching details")
    #     return
    # this m_id needs to be a measurement that is available on RIPE Atlas
    m_id = "107704481" # a measurement done on 2025-06-04 to 216.239.35.4 with 35 probes
    assert check_all_measurements_scheduled(m_id) is True
    assert check_all_measurements_done(m_id,35) == "Complete"
    data = get_data_from_ripe_measurement(m_id)
    # verify we got information from probes
    for pb in data:
        # verify the measurement was done for the correct IP address
        assert pb["dst_addr"] == "216.239.35.4"
        # verify if the measurement was correctly get
        assert "result" in pb



# test integration with getting the available probes
# there we test whether our requests to the RIPE API (to see how many probes of a type
# are available) are successful

def test_get_available_probes_asn_and_prefix():
    # these are details for some probes in Germany
    result = get_available_probes_asn_and_prefix("95.223.228.43", "AS3209", "95.223.0.0/16", "ipv4")

    # no duplicates
    assert len(result) == len(set(result))
    # data about the probes (max 3 probes)
    max_count = 0
    for p_id in result:
        if max_count >= 3:
            break
        max_count += 1
        try:
            data = get_probe_data_from_ripe_by_id(str(p_id))
            ans = str(data.get("asn_v4")) == "AS3209" or str(data.get("asn_v4") == "3209")
            # if it responds, verify it is true (otherwise the lines above will throw an exception)
            assert ans is True
        except Exception as e:
            # some probes may not respond
            continue

def test_get_available_probes_asn_and_country():
    # these are details for some probes in Germany
    result = get_available_probes_asn_and_country("95.223.228.43", "AS3209", "DE", "ipv4")

    # no duplicates
    assert len(result) == len(set(result))
    # there is at least a probe in this country
    assert len(result) > 0

def test_get_available_probes_asn():
    result = get_available_probes_asn("95.223.228.43", "AS3209", "ipv4")
    # no duplicates
    assert len(result) == len(set(result))
    # data about the probes (max 3 probes)
    max_count = 0
    for p_id in result:
        if max_count >= 3:
            break
        max_count += 1
        try:
            data = get_probe_data_from_ripe_by_id(str(p_id))
            ans = str(data.get("asn_v4")) == "AS3209" or str(data.get("asn_v4") == "3209")
            # if it responds, verify it is true (otherwise the lines above will throw an exception)
            assert ans is True
        except Exception as e:
            # some probes may not respond
            continue

def test_get_available_probes_prefix():
    result = get_available_probes_prefix("95.223.228.43", "95.223.0.0/16", "ipv4")
    # no duplicates
    assert len(result) == len(set(result))

def test_get_available_probes_country():
    # these are details for some probes in Germany
    result = get_available_probes_country("95.223.228.43",  "DE", "ipv4")
    # data about the probes (max 5 probes)
    max_count = 0
    for p_id in result:
        if max_count >= 5:
            break
        max_count += 1
        try:
            data = get_probe_data_from_ripe_by_id(str(p_id))
            ans = (data.get("country_code") == "DE" )
            # if it responds, verify it is true (otherwise the lines above will throw an exception)
            assert ans is True
        except Exception as e:
            # some probes may not respond
            continue

    # no duplicates
    assert len(result) == len(set(result))
    # there is at least a probe in this country
    assert len(result) > 0

def test_get_probes():
    # Germany
    settings = AdvancedSettings()
    settings.custom_client_ip = "95.223.228.43"
    settings.wanted_ip_type = 4
    result = get_probes(settings,15)
    counter = 0
    for r in result:
        counter += r["requested"]
    assert counter == 15
    # Germany but IPv6
    settings = AdvancedSettings()
    settings.custom_client_ip = "95.223.228.43"
    settings.wanted_ip_type = 6
    result = get_probes(settings, 3)
    counter = 0
    for r in result:
        counter += r["requested"]
    assert counter == 3
    # Romania
    settings = AdvancedSettings()
    settings.custom_client_ip = "46.97.170.106"
    settings.wanted_ip_type = 4
    result = get_probes(settings, 1)
    counter = 0
    for r in result:
        counter += r["requested"]
    assert counter == 1
    # Cambodia
    settings = AdvancedSettings()
    settings.custom_client_ip = "202.79.26.65"
    settings.wanted_ip_type = 4
    result = get_probes(settings, 10)
    counter = 0
    for r in result:
        counter += r["requested"]
    assert counter == 10
    # Netherlands
    settings = AdvancedSettings()
    settings.custom_client_ip = "145.92.210.165"
    settings.wanted_ip_type = 4
    result = get_probes(settings, 20)
    counter = 0
    for r in result:
        counter += r["requested"]
    assert counter == 20