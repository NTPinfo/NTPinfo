Global Types
============

The global types used across multiple components are stored in ``client/src/utils/types.ts``.

NTPData
-------

This data type is used for storing relevant variables of the measurements displayed on the website and used for data visualization:

- Offset
- Round-trip time
- Stratum of the NTP server
- Jitter
- Precision of the NTP server
- Time at which the measurement was taken (UNIX time)
- IP address of the NTP server
- Name of the NTP server
- Reference ID of the reference of the NTP server
- Root dispersion of the NTP server
- Root delay of the NTP server
- The IP address of the vantage point

RIPEData
--------

Used for storing variables from RIPE Atlas measurements:

- An ``NTPData`` variable with all its data
- Probe ID
- Country of the probe
- Geolocation of the probe
- Whether results were actually received
- Measurement ID

RIPEResp
--------

Response data for triggering a RIPE measurement:

- Measurement ID
- IP of the vantage point that initiated the measurement

Measurement
-----------

Used to determine what measurement is shown on the graphs.
It is a union type: ``"RTT" | "offset"``
