# FullMeasurementDN and FullMeasurementIP Models Documentation

## Overview

The `FullMeasurementDN` and `FullMeasurementIP` models are SQLAlchemy database models that store comprehensive NTP (Network Time Protocol) measurement data. These models are part of the NTP measurement platform and store all measurement results, including NTP data, NTS (Network Time Security) data, NTP versions analysis, and RIPE Atlas measurements.

### Key Differences

- **FullMeasurementDN**: Stores measurements for **domain names** (e.g., `pool.ntp.org`). Can contain multiple IP measurements (typically 4 IPv4 addresses).
- **FullMeasurementIP**: Stores measurements for **IP addresses** (e.g., `192.168.1.1`). Can be standalone or part of a domain name measurement.

---

## FullMeasurementDN Model

### Table Name
`full_ntp_measurement_dn`

### Fields

| Field Name | Type | Nullable | Description |
|------------|------|----------|-------------|
| `id_m_dn` | `int` | ❌ Primary Key | Unique identifier for the domain name measurement |
| `status` | `str` | ❌ | Measurement status: `"pending"`, `"finished"`, `"failed"`, etc. |
| `server` | `str` | ❌ | Domain name that was measured (e.g., `"pool.ntp.org"`) |
| `created_at_time` | `DateTime` | ❌ | Timestamp when the measurement was created (auto-set) |
| `id_nts` | `int` | ✅ | Foreign key to `nts_measurement` table (NTS measurement ID) |
| `id_vs` | `int` | ✅ | Foreign key to `ntp_versions` table (NTP versions analysis ID) |
| `id_ripe` | `int` | ✅ | RIPE Atlas measurement ID (if RIPE measurement was performed) |
| `ripe_error` | `str` | ✅ | Error message if RIPE Atlas measurement failed |
| `response_error` | `str` | ✅ | Error message if there was an error with the input/measurement |
| `settings` | `dict` (JSON) | ✅ | Measurement settings (IP type, NTP versions to analyze, etc.) |

### Relationships

- **`ip_measurements`**: Many-to-many relationship with `FullMeasurementIP` through the `dn_ip_link` junction table. Contains all IP measurements associated with this domain name (typically 4 IPv4 addresses).

---

## FullMeasurementIP Model

### Table Name
`full_ntp_measurement_ip`

### Fields

| Field Name | Type | Nullable | Description |
|------------|------|----------|-------------|
| `id_m_ip` | `int` | ❌ Primary Key | Unique identifier for the IP measurement |
| `status` | `str` | ❌ | Measurement status: `"pending"`, `"finished"`, `"failed"`, etc. |
| `server_ip` | `str` | ❌ | IP address that was measured (e.g., `"192.168.1.1"`) |
| `created_at_time` | `DateTime` | ❌ | Timestamp when the measurement was created (auto-set) |
| `id_nts` | `int` | ✅ | Foreign key to `nts_measurement` table (NTS measurement ID) |
| `id_vs` | `int` | ✅ | Foreign key to `ntp_versions` table (NTP versions analysis ID) |
| `id_ripe` | `int` | ✅ | RIPE Atlas measurement ID (null if part of DN measurement) |
| `response_version` | `str` | ✅ | NTP version used in the main measurement (e.g., `"ntpv4"`, `"ntpv5"`) |
| `ripe_error` | `str` | ✅ | Error message if RIPE Atlas measurement failed |
| `response_error` | `str` | ✅ | Error message if main NTP measurement failed (e.g., timeout) |
| `id_main_measurement` | `int` | ✅ | Foreign key to `ntpv4_measurement` or `ntpv5_measurement` table. **Null if measurement failed** |
| `settings` | `dict` (JSON) | ✅ | Measurement settings (only present if standalone, not part of DN measurement) |

### Relationships

- **`domains`**: One-to-many relationship with `FullMeasurementDN` through the `dn_ip_link` junction table. Contains all domain name measurements that include this IP measurement.

---

## JSON Serialization

### Converting to Dictionary/JSON

The models can be converted to dictionaries using utility functions in `server/app/utils/convert_measurement_to_format.py`:

#### FullMeasurementDN to JSON

```python
from server.app.utils.convert_measurement_to_format import full_measurement_dn_to_dict

# Convert to full JSON (includes all nested data)
json_data = full_measurement_dn_to_dict(db, dn_measurement)

# Result structure:
{
    "search_id": "dn223",
    "status": "finished",
    "server": "pool.ntp.org",
    "created_at_time": "2025-12-04T20:18:31.130344+01:00",
    "nts": { ... },  # NTS measurement data or null
    "ntp_versions": { ... },  # NTP versions analysis or null
    "id_ripe": 142199215,  # or null
    "ripe_error": null,  # or error message
    "response_error": null,  # or error message
    "ip_measurements": [
        { ... },  # FullMeasurementIP data (without settings)
        { ... },
        { ... },
        { ... }
    ],
    "settings": { ... }  # Measurement settings
}
```

#### FullMeasurementIP to JSON

```python
from server.app.utils.convert_measurement_to_format import full_measurement_ip_to_dict

# Convert to full JSON (includes all nested data)
json_data = full_measurement_ip_to_dict(db, ip_measurement, part_of_dn_measurement=False)

# Result structure:
{
    "search_id": "ip571",
    "status": "finished",
    "server": "192.168.1.1",
    "created_at_time": "2025-12-04T20:18:32.042998+01:00",
    "response_version": "ntpv4",  # or null if failed
    "main_measurement": { ... },  # NTPv4 or NTPv5 measurement data or null
    "nts": { ... },  # NTS measurement data or null
    "ntp_versions": { ... },  # NTP versions analysis or null
    "id_ripe": 142199216,  # or null (null if part of DN measurement)
    "ripe_error": null,  # or error message
    "response_error": null,  # or error message (e.g., "measurement timeout: ...")
    "settings": { ... }  # Only if part_of_dn_measurement=False
}
```

#### Partial Results (Performance Optimization)

For better performance when polling, use partial conversion methods that return IDs instead of full nested data:

```python
from server.app.utils.convert_measurement_to_format import partial_measurement_ip_to_dict

# Convert to partial JSON (returns IDs instead of full nested objects)
partial_json = partial_measurement_ip_to_dict(db, ip_measurement)

# Result structure:
{
    "search_id": "ip571",
    "status": "finished",
    "server": "192.168.1.1",
    "id_nts": 235,  # ID instead of full object
    "id_vs": 123,   # ID instead of full object
    "id_main_measurement": 456,  # ID instead of full object
    # ... other fields
}
```

---

## Complete JSON Examples

The following examples show the actual JSON structure returned by the conversion functions, as used by the frontend.

### Example 1: FullMeasurementDN JSON Output

This is the complete JSON structure returned by `full_measurement_dn_to_dict()` when accessing a domain name measurement:

```json
{
    "search_id": "dn292",
    "status": "finished",
    "server": "time.cloudflare.com",
    "created_at_time": "2025-12-05T23:46:14.253339+01:00",
    "nts": {
        "nts_id": 305,
        "nts_succeeded": true,
        "nts_analysis": "It is NTS. One NTS IP is 162.159.200.1",
        "host": "time.cloudflare.com",
        "measured_server_ip": "162.159.200.1",
        "measured_server_port": 123,
        "offset": 0.003382527,
        "rtt": 0.026763638,
        "kiss_code": "",
        "stratum": 3,
        "poll": 1,
        "nts_measurement_version": "ntpv4",
        "client_sent_time": 17068043609669883782,
        "server_recv_time": 17068043609655992835,
        "server_sent_time": 17068043609744358549,
        "client_recv_time": 17068043609787305181,
        "ref_time": 17068043379686524398,
        "leap": 0,
        "mode": 4,
        "version": 4,
        "min_error": 0.0,
        "precision": 1.4e-08,
        "root_delay": 0.005249023,
        "root_disp": 0.000152588,
        "root_dist": 0.016158918,
        "ref_id": "10.8.8.33",
        "ref_id_raw": "0x0a080821"
    },
    "ntp_versions": {
        "ntpv1_supported_conf": null,
        "ntpv1_analysis": null,
        "ntpv1_response_version": null,
        "ntpv1_data": null,
        "ntpv2_supported_conf": null,
        "ntpv2_analysis": null,
        "ntpv2_response_version": null,
        "ntpv2_data": null,
        "ntpv3_supported_conf": 100,
        "ntpv3_analysis": "It supports NTPv3.",
        "ntpv3_response_version": "ntpv3",
        "ntpv3_data": {
            "id": 1197,
            "host": "time.cloudflare.com",
            "measured_server_ip": null,
            "offset": 0.0025377273559570312,
            "rtt": 0.024156570434570312,
            "stratum": 3,
            "poll": 0,
            "client_sent_time": 17068043653452894214,
            "server_recv_time": 17068043653515669609,
            "server_sent_time": 17068043653516114708,
            "client_recv_time": 17068043653557090550,
            "ref_time": 17068043453049857570,
            "leap": 0,
            "mode": 4,
            "version": 3,
            "precision": -25.0,
            "root_delay": 0.0052490234375,
            "root_disp": 0.000152587890625,
            "ref_id": "IPv6 MD5 hash: 0x0a080821",
            "extensions": null
        },
        "ntpv4_supported_conf": 100,
        "ntpv4_analysis": "It supports NTPv4.",
        "ntpv4_response_version": "ntpv4",
        "ntpv4_data": {
            "id": 1198,
            "host": "time.cloudflare.com",
            "measured_server_ip": null,
            "offset": 0.0021665096282958984,
            "rtt": 0.025507450103759766,
            "stratum": 3,
            "poll": 0,
            "client_sent_time": 17068043614263753743,
            "server_recv_time": 17068043614327837371,
            "server_sent_time": 17068043614328094350,
            "client_recv_time": 17068043614373566608,
            "ref_time": 17068042685446120702,
            "leap": 0,
            "mode": 4,
            "version": 4,
            "precision": -26.0,
            "root_delay": 0.00555419921875,
            "root_disp": 0.0003509521484375,
            "ref_id": "IPv6 MD5 hash: 0x0ae30804",
            "extensions": null
        },
        "ntpv5_supported_conf": 0,
        "ntpv5_analysis": "measurement timeout: read udp [2001:610:450:41::186]:52917->[2606:4700:f1::123]:123: i/o timeout",
        "ntpv5_response_version": null,
        "ntpv5_data": null
    },
    "id_ripe": 142377156,
    "ripe_error": null,
    "response_error": null,
    "ip_measurements": [
        {
            "search_id": "ip684",
            "status": "finished",
            "server": "162.159.200.1",
            "created_at_time": "2025-12-05T23:46:15.007364+01:00",
            "response_version": "ntpv4",
            "main_measurement": {
                "id": 1195,
                "host": "time.cloudflare.com",
                "measured_server_ip": "162.159.200.1",
                "offset": 0.001462697982788086,
                "rtt": 0.024531841278076172,
                "stratum": 3,
                "poll": 0,
                "client_sent_time": 17068043595515430363,
                "server_recv_time": 17068043595574394661,
                "server_sent_time": 17068043595574677550,
                "client_recv_time": 17068043595621076680,
                "ref_time": 17068043107189326738,
                "leap": 0,
                "mode": 4,
                "version": 4,
                "precision": -26.0,
                "root_delay": 0.0052490234375,
                "root_disp": 0.000244140625,
                "ref_id": "10.20.8.26",
                "extensions": null,
                "ntp_server_location": {
                    "ip_is_anycast": true,
                    "country_code": null,
                    "asn_ntp_server": "13335",
                    "coordinates_x": 25.0,
                    "coordinates_y": -71.0,
                    "vantage_point_ip": "145.126.193.134"
                },
                "analysis": "It supports NTPv4."
            },
            "nts": null,
            "ntp_versions": null,
            "ripe_error": null,
            "response_error": null
        },
        {
            "search_id": "ip685",
            "status": "finished",
            "server": "162.159.200.123",
            "created_at_time": "2025-12-05T23:46:16.313649+01:00",
            "response_version": "ntpv4",
            "main_measurement": {
                "id": 1196,
                "host": "time.cloudflare.com",
                "measured_server_ip": "162.159.200.123",
                "offset": 0.0020210742950439453,
                "rtt": 0.024671077728271484,
                "stratum": 3,
                "poll": 0,
                "client_sent_time": 17068043601115297200,
                "server_recv_time": 17068043601176959675,
                "server_sent_time": 17068043601177262486,
                "client_recv_time": 17068043601221562852,
                "ref_time": 17068043561254587655,
                "leap": 0,
                "mode": 4,
                "version": 4,
                "precision": -26.0,
                "root_delay": 0.0056610107421875,
                "root_disp": 0.0001373291015625,
                "ref_id": "10.227.8.4",
                "extensions": null,
                "ntp_server_location": {
                    "ip_is_anycast": true,
                    "country_code": null,
                    "asn_ntp_server": "13335",
                    "coordinates_x": 25.0,
                    "coordinates_y": -71.0,
                    "vantage_point_ip": "145.126.193.134"
                },
                "analysis": "It supports NTPv4."
            },
            "nts": null,
            "ntp_versions": null,
            "ripe_error": null,
            "response_error": null
        }
    ],
    "settings": {
        "ntpv5_draft": "draft-ietf-ntp-ntpv5-06",
        "wanted_ip_type": 4,
        "custom_client_ip": "",
        "measurement_type": "ntpv4",
        "custom_probes_asn": "",
        "custom_probes_country": "",
        "ntp_versions_to_analyze": [
            "ntpv4",
            "ntpv5",
            "ntpv3"
        ],
        "nts_analysis_on_each_ip": false,
        "analyse_all_ntp_versions": false,
        "ntp_versions_analysis_on_each_ip": false
    }
}
```

### Example 2: FullMeasurementIP JSON Output (Standalone)

This is the complete JSON structure returned by `full_measurement_ip_to_dict()` for a standalone IP measurement:

```json
{
    "search_id": "ip571",
    "status": "finished",
    "server": "192.168.1.1",
    "created_at_time": "2025-12-04T20:18:32.042998+01:00",
    "response_version": "ntpv4",
    "main_measurement": {
        "id": 456,
        "analysis": "Successfully measured NTP server",
        "host": "pool.ntp.org",
        "measured_server_ip": "192.168.1.1",
        "offset": 0.023456,
        "rtt": 0.045678,
        "stratum": 2,
        "poll": 6,
        "client_sent_time": 17067619021864347056,
        "server_recv_time": 17067618969544751435,
        "server_sent_time": 17067619004519621161,
        "client_recv_time": 17067619022004577738,
        "ref_time": 17067616496502057609,
        "leap": 0,
        "mode": 4,
        "version": 4,
        "precision": 2.9e-08,
        "root_delay": 0.008712769,
        "root_disp": 0.000778198,
        "ref_id": "1.149.205.37",
        "extensions": null,
        "ntp_server_location": {
            "ip_is_anycast": false,
            "country_code": "US",
            "asn_ntp_server": "AS12345",
            "coordinates_x": -122.4194,
            "coordinates_y": 37.7749,
            "vantage_point_ip": "203.0.113.1"
        }
    },
    "nts": {
        "nts_id": 235,
        "nts_succeeded": true,
        "nts_analysis": "NTS is supported",
        "host": "pool.ntp.org",
        "measured_server_ip": "192.168.1.1",
        "measured_server_port": 123,
        "offset": -4.055285715,
        "rtt": 0.031495957,
        "kiss_code": null,
        "stratum": 2,
        "poll": 1,
        "nts_measurement_version": "ntpv4",
        "client_sent_time": 17067619021864347056,
        "server_recv_time": 17067618969544751435,
        "server_sent_time": 17067619004519621161,
        "client_recv_time": 17067619022004577738,
        "ref_time": 17067616496502057609,
        "leap": 0,
        "mode": 4,
        "version": 4,
        "min_error": 4.039537737,
        "precision": 2.9e-08,
        "root_delay": 0.008712769,
        "root_disp": 0.000778198,
        "root_dist": 0.020882561,
        "ref_id": "1.149.205.37",
        "ref_id_raw": "0x0195cd25"
    },
    "ntp_versions": {
        "ntpv1_supported_conf": null,
        "ntpv1_analysis": null,
        "ntpv1_response_version": null,
        "ntpv1_data": null,
        "ntpv2_supported_conf": null,
        "ntpv2_analysis": null,
        "ntpv2_response_version": null,
        "ntpv2_data": null,
        "ntpv3_supported_conf": 100,
        "ntpv3_analysis": "NTPv3 is supported",
        "ntpv3_response_version": "ntpv3",
        "ntpv3_data": {
            "id": 789,
            "host": "pool.ntp.org",
            "measured_server_ip": "192.168.1.1",
            "offset": 0.023456,
            "rtt": 0.045678,
            "stratum": 2,
            "poll": 6,
            "client_sent_time": 17067619021864347056,
            "server_recv_time": 17067618969544751435,
            "server_sent_time": 17067619004519621161,
            "client_recv_time": 17067619022004577738,
            "ref_time": 17067616496502057609,
            "leap": 0,
            "mode": 4,
            "version": 3,
            "precision": 2.9e-08,
            "root_delay": 0.008712769,
            "root_disp": 0.000778198,
            "ref_id": "1.149.205.37",
            "extensions": null,
            "ntp_server_location": {
                "ip_is_anycast": false,
                "country_code": "US",
                "asn_ntp_server": "AS12345",
                "coordinates_x": -122.4194,
                "coordinates_y": 37.7749,
                "vantage_point_ip": "203.0.113.1"
            }
        },
        "ntpv4_supported_conf": 100,
        "ntpv4_analysis": "NTPv4 is supported",
        "ntpv4_response_version": "ntpv4",
        "ntpv4_data": {
            "id": 456,
            "host": "pool.ntp.org",
            "measured_server_ip": "192.168.1.1",
            "offset": 0.023456,
            "rtt": 0.045678,
            "stratum": 2,
            "poll": 6,
            "client_sent_time": 17067619021864347056,
            "server_recv_time": 17067618969544751435,
            "server_sent_time": 17067619004519621161,
            "client_recv_time": 17067619022004577738,
            "ref_time": 17067616496502057609,
            "leap": 0,
            "mode": 4,
            "version": 4,
            "precision": 2.9e-08,
            "root_delay": 0.008712769,
            "root_disp": 0.000778198,
            "ref_id": "1.149.205.37",
            "extensions": null,
            "ntp_server_location": {
                "ip_is_anycast": false,
                "country_code": "US",
                "asn_ntp_server": "AS12345",
                "coordinates_x": -122.4194,
                "coordinates_y": 37.7749,
                "vantage_point_ip": "203.0.113.1"
            }
        },
        "ntpv5_supported_conf": 0,
        "ntpv5_analysis": "NTPv5 is not supported",
        "ntpv5_response_version": null,
        "ntpv5_data": null
    },
    "id_ripe": 142199216,
    "ripe_error": null,
    "response_error": null,
    "settings": {
        "ntpv5_draft": "draft-ietf-ntp-ntpv5-06",
        "wanted_ip_type": 4,
        "custom_client_ip": "",
        "measurement_type": "ntpv4",
        "custom_probes_asn": "",
        "custom_probes_country": "",
        "ntp_versions_to_analyze": ["ntpv3", "ntpv4", "ntpv5"],
        "nts_analysis_on_each_ip": false,
        "analyse_all_ntp_versions": false,
        "ntp_versions_analysis_on_each_ip": false
    }
}
```

### Example 3: FullMeasurementIP as Part of DN Measurement

When an IP measurement is part of a domain name measurement, the `settings` field is omitted (since it's redundant with the DN measurement's settings):


### Example 4: NTPv5 Measurement Structure

When the main measurement uses NTPv5, the structure includes NTPv5-specific fields:

```json
{
    "id": 789,
    "draft_name": "draft-ietf-ntp-ntpv5-06",
    "analysis": "Successfully measured NTPv5 server",
    "host": "pool.ntp.org",
    "measured_server_ip": "192.168.1.1",
    "offset": 0.023456,
    "rtt": 0.045678,
    "stratum": 2,
    "poll": 6,
    "client_cookie": 12345678901234567890,
    "server_cookie": 98765432109876543210,
    "client_sent_time": 17067619021864347056,
    "server_recv_time": 17067618969544751435,
    "server_sent_time": 17067619004519621161,
    "client_recv_time": 17067619022004577738,
    "leap": 0,
    "mode": 4,
    "version": 5,
    "precision": 2.9e-08,
    "root_delay": 0.008712769,
    "root_disp": 0.000778198,
    "timescale": 1,
    "era": 0,
    "flags_raw": 12345,
    "flags_decoded": {
        "flag1": true,
        "flag2": false
    },
    "extensions": null,
    "ntp_server_location": {
        "ip_is_anycast": false,
        "country_code": "US",
        "asn_ntp_server": "AS12345",
        "coordinates_x": -122.4194,
        "coordinates_y": 37.7749,
        "vantage_point_ip": "203.0.113.1"
    }
}
```

### Example 5: Failed NTS Measurement

When NTS measurement fails, only minimal fields are returned:

```json
{
    "nts_id": 236,
    "nts_succeeded": false,
    "nts_analysis": "NTS handshake failed: connection timeout"
}
```

### Example 6: Partial Measurement Results

Partial results are used for polling and return IDs instead of full nested objects:

#### Partial IP Measurement

```json
{
    "search_id": "ip571",
    "status": "pending",
    "server": "192.168.1.1",
    "created_at_time": "2025-12-04T20:18:32.042998+01:00",
    "main_measurement": {
        "id": 456,
        "host": "pool.ntp.org",
        "measured_server_ip": "192.168.1.1",
        "offset": 0.023456,
        "rtt": 0.045678,
        "stratum": 2,
        "poll": 6,
        "client_sent_time": 17067619021864347056,
        "server_recv_time": 17067618969544751435,
        "server_sent_time": 17067619004519621161,
        "client_recv_time": 17067619022004577738,
        "ref_time": 17067616496502057609,
        "leap": 0,
        "mode": 4,
        "version": 4,
        "precision": 2.9e-08,
        "root_delay": 0.008712769,
        "root_disp": 0.000778198,
        "ref_id": "1.149.205.37",
        "extensions": null,
        "ntp_server_location": {
            "ip_is_anycast": false,
            "country_code": "US",
            "asn_ntp_server": "AS12345",
            "coordinates_x": -122.4194,
            "coordinates_y": 37.7749,
            "vantage_point_ip": "203.0.113.1"
        }
    },
    "nts": {
        "nts_id": 235,
        "nts_succeeded": true,
        "nts_analysis": "It is NTS. One NTS server is fra1-1.ntspool.nl",
        "host": "ke.experimental.ntspooltest.org",
        "measured_server_ip": "fra1-1.ntspool.nl",
        "measured_server_port": 123,
        "offset": -4.055285715,
        "rtt": 0.031495957,
        "kiss_code": null,
        "stratum": 2,
        "poll": 1,
        "nts_measurement_version": "ntpv4",
        "client_sent_time": 17067619021864347056,
        "server_recv_time": 17067618969544751435,
        "server_sent_time": 17067619004519621161,
        "client_recv_time": 17067619022004577738,
        "ref_time": 17067616496502057609,
        "leap": 0,
        "mode": 4,
        "version": 4,
        "min_error": 4.039537737,
        "precision": 2.9e-08,
        "root_delay": 0.008712769,
        "root_disp": 0.000778198,
        "root_dist": 0.020882561,
        "ref_id": "1.149.205.37",
        "ref_id_raw": "0x0195cd25"
    },
    "ntp_versions_id": 123,
    "response_version": "ntpv4",
    "ripe_error": null,
    "response_error": null,
    "id_ripe": 142199216,
    "settings": {
        "ntpv5_draft": "draft-ietf-ntp-ntpv5-06",
        "wanted_ip_type": 4,
        "custom_client_ip": "",
        "measurement_type": "ntpv4",
        "custom_probes_asn": "",
        "custom_probes_country": "",
        "ntp_versions_to_analyze": ["ntpv3", "ntpv4", "ntpv5"],
        "nts_analysis_on_each_ip": false,
        "analyse_all_ntp_versions": false,
        "ntp_versions_analysis_on_each_ip": false
    }
}
```

**Note**: `ntp_versions_id` is an ID instead of the full `ntp_versions` object. The frontend must fetch it separately if needed.

#### Partial DN Measurement

```json
{
    "search_id": "dn223",
    "status": "pending",
    "server": "ke.experimental.ntspooltest.org",
    "created_at_time": "2025-12-04T20:18:31.130344+01:00",
    "nts": {
        "nts_id": 235,
        "nts_succeeded": true,
        "nts_analysis": "It is NTS. One NTS server is fra1-1.ntspool.nl",
        "host": "ke.experimental.ntspooltest.org",
        "measured_server_ip": "fra1-1.ntspool.nl",
        "measured_server_port": 123,
        "offset": -4.055285715,
        "rtt": 0.031495957,
        "kiss_code": null,
        "stratum": 2,
        "poll": 1,
        "nts_measurement_version": "ntpv4",
        "client_sent_time": 17067619021864347056,
        "server_recv_time": 17067618969544751435,
        "server_sent_time": 17067619004519621161,
        "client_recv_time": 17067619022004577738,
        "ref_time": 17067616496502057609,
        "leap": 0,
        "mode": 4,
        "version": 4,
        "min_error": 4.039537737,
        "precision": 2.9e-08,
        "root_delay": 0.008712769,
        "root_disp": 0.000778198,
        "root_dist": 0.020882561,
        "ref_id": "1.149.205.37",
        "ref_id_raw": "0x0195cd25"
    },
    "ntp_versions_id": 124,
    "id_ripe": 142199215,
    "ip_measurements_ids": ["ip571", "ip572", "ip573", "ip574"],
    "ripe_error": null,
    "response_error": null,
    "settings": {
        "ntpv5_draft": "draft-ietf-ntp-ntpv5-06",
        "wanted_ip_type": 4,
        "custom_client_ip": "",
        "measurement_type": "ntpv4",
        "custom_probes_asn": "",
        "custom_probes_country": "",
        "ntp_versions_to_analyze": ["ntpv5", "ntpv4", "ntpv3"],
        "nts_analysis_on_each_ip": false,
        "analyse_all_ntp_versions": false,
        "ntp_versions_analysis_on_each_ip": false
    }
}
```

**Note**: `ip_measurements_ids` contains a list of search IDs (e.g., `"ip571"`) instead of full IP measurement objects. The frontend must fetch each IP measurement separately if needed.

### Example 7: Measurement with Errors

When a measurement fails, error fields are populated:

```json
{
    "search_id": "ip571",
    "status": "finished",
    "server": "192.168.1.1",
    "created_at_time": "2025-12-04T20:18:32.042998+01:00",
    "response_version": null,
    "main_measurement": null,
    "nts": null,
    "ntp_versions": null,
    "ripe_error": "RIPE Atlas measurement failed: timeout",
    "response_error": "measurement timeout: read udp 145.126.195.1:51662->192.168.1.1:123: i/o timeout",
    "id_ripe": null,
    "settings": {
        "ntpv5_draft": "draft-ietf-ntp-ntpv5-06",
        "wanted_ip_type": 4,
        "custom_client_ip": "",
        "measurement_type": "ntpv4",
        "custom_probes_asn": "",
        "custom_probes_country": "",
        "ntp_versions_to_analyze": ["ntpv3", "ntpv4", "ntpv5"],
        "nts_analysis_on_each_ip": false,
        "analyse_all_ntp_versions": false,
        "ntp_versions_analysis_on_each_ip": false
    }
}
```

**Key Points**:
- `response_error` indicates the main NTP measurement failed
- `main_measurement` is `null` when there's a `response_error`
- `ripe_error` indicates RIPE Atlas measurement failed (if applicable)
- `id_ripe` may still be set even if `ripe_error` is present (if RIPE measurement was initiated)

---

## Status Values

Common status values used in both models:

- **`"pending"`**: Measurement is queued or in progress
- **`"finished"`**: Measurement completed successfully
- **`"failed"`**: Measurement failed (check `response_error` or `ripe_error`)
- **`"partial_results"`**: Some results available but measurement not complete
- **`"timeout"`**: Measurement timed out

---

## Error Handling

### Common Error Scenarios

1. **Main Measurement Failed** (`response_error` is set):
   - `id_main_measurement` will be `null`
   - `response_error` contains the error message (e.g., `"measurement timeout: read udp ..."`)

2. **RIPE Measurement Failed** (`ripe_error` is set):
   - `id_ripe` may still be set (if RIPE measurement was initiated)
   - `ripe_error` contains the error message

3. **NTS Measurement Not Available**:
   - `id_nts` will be `null`
   - No error message (NTS is optional)

4. **NTP Versions Analysis Not Available**:
   - `id_vs` will be `null`
   - No error message (versions analysis is optional)

### Checking for Errors

```python
# Check if main measurement failed
if ip_measurement.response_error:
    print(f"Main measurement error: {ip_measurement.response_error}")
    # id_main_measurement will be null

# Check if RIPE measurement failed
if dn_measurement.ripe_error:
    print(f"RIPE measurement error: {dn_measurement.ripe_error}")

# Check if measurement is in error state
if ip_measurement.status == "failed":
    # Handle failed measurement
    pass
```

---

## Settings JSON Structure

The `settings` field contains a JSON object with measurement configuration:

```python
{
    "wanted_ip_type": 4,  # 4 for IPv4, 6 for IPv6
    "measurement_type": "ntpv4",  # "ntpv4" or "ntpv5"
    "ntpv5_draft": "draft-ietf-ntp-ntpv5-06",  # Only for NTPv5
    "ntp_versions_to_analyze": ["ntpv3", "ntpv4", "ntpv5"],  # Versions to test
    "analyse_all_ntp_versions": false,  # If true, analyze all versions
    "nts_analysis_on_each_ip": false,  # Whether to perform NTS on each IP
    "ntp_versions_analysis_on_each_ip": false,  # Whether to analyze versions on each IP
    "custom_probes_asn": "",  # Custom RIPE probe ASN filter
    "custom_probes_country": "",  # Custom RIPE probe country filter
    "custom_client_ip": ""  # Custom client IP for measurement
}
```

---

## Best Practices

1. **Always check `status` before accessing nested data if you need to directly take the full measurement**: Ensure the measurement is `"finished"` before accessing related measurements.

2. **Handle null values**: Many fields are nullable. Always check for `None` before accessing:
   ```python
   if ip_measurement.id_main_measurement:
       # Safe to access main measurement
       pass
   ```

3. **Use partial results for polling**: When polling for measurement updates, use `partial_measurement_*_to_dict()` for better performance.

4. **Check error fields**: Always check `response_error` and `ripe_error` to understand why a measurement might have failed.
---

## Related Models

- **`NTSMeasurement`**: Stores NTS (Network Time Security) measurement data
- **`NTPVersions`**: Stores NTP versions analysis results
- **`NTPv4Measurement`**: Stores NTPv4 measurement data
- **`NTPv5Measurement`**: Stores NTPv5 measurement data
- **`DNIPLink`**: Junction table linking domain and IP measurements

---

## API Endpoints

These models are typically accessed through the following API endpoints:

- **`GET /measurements/results/{m_id}`**: Get full measurement results (uses `full_measurement_*_to_dict()`)
- **`GET /measurements/partial-results/{m_id}`**: Get partial measurement results (uses `partial_measurement_*_to_dict()`)
- **`GET /measurements/ripe/{ripe_id}`**: Get RIPE Atlas measurement results

Where `m_id` can be:
- `"dn{id}"` for domain name measurements (e.g., `"dn223"`)
- `"ip{id}"` for IP address measurements (e.g., `"ip571"`)

---

## Additional Resources

- **Model Definitions**: `server/app/dtos/full_ntp_measurement.py`
- **Serialization Functions**: `server/app/utils/convert_measurement_to_format.py`
- **Database Schema**: `server/database_tables_sql.txt`

