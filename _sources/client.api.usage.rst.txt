API Usage
=========

There are currently **5** different API endpoints used by the front-end of the application.
These can all be found in ``client/src/hooks``.

They all use ``axios`` for the requests, and each implements a different function.
Helper functions for transforming data and the global types used can be found in ``client/utils``.

API Hooks
---------

1. **useFetchIPData**

   This hook provides the user’s query (IP or domain name) as a payload to the backend.

   It performs a **POST** request to the backend to measure the given NTP server.
   If the query is a domain name, the result includes all NTP servers measured from that domain name.
   If it's an IP, only that specific NTP server is measured.

   It parses the JSON received using the method ``transformJSONDataToNTPData``.

   It returns a **5-tuple**:

   +------------------+--------------------------------------------------------------+
   | Return value     | Description                                                  |
   +==================+==============================================================+
   | ``data``         | An array of NTP results                                      |
   +------------------+--------------------------------------------------------------+
   | ``loading``      | ``boolean`` indicating if the measurement is ongoing         |
   +------------------+--------------------------------------------------------------+
   | ``error``        | Error object if one occurred                                 |
   +------------------+--------------------------------------------------------------+
   | ``httpStatus``   | The HTTP status of the request                               |
   +------------------+--------------------------------------------------------------+
   | ``fetchData``    | A function to initiate the POST request                      |
   +------------------+--------------------------------------------------------------+

2. **useFetchHistoricalIPData**

   This hook fetches data over a specific period for a given server.

   It performs a **GET** request to the backend. The server can be either an IP or domain name.
   Start and end times must be in ISO8601 format.

   It also uses ``transformJSONDataToNTPData``.

   It returns a **4-tuple**:

   +------------------+--------------------------------------------------------------+
   | Return value     | Description                                                  |
   +==================+==============================================================+
   | ``data``         | An array of NTP results                                      |
   +------------------+--------------------------------------------------------------+
   | ``loading``      | ``boolean`` indicating if the fetch is ongoing               |
   +------------------+--------------------------------------------------------------+
   | ``error``        | Error object if one occurred                                 |
   +------------------+--------------------------------------------------------------+
   | ``fetchData``    | A function to initiate the GET request                       |
   +------------------+--------------------------------------------------------------+

3. **triggerRipeMeasurement**

   This hook sends a trigger to start a RIPE measurement.

   It performs a **POST** request to the backend with the server as payload.
   The backend responds with the measurement ID and the vantage point's IP.

   It returns a **4-tuple**:

   +------------------+--------------------------------------------------------------+
   | Return value     | Description                                                  |
   +==================+==============================================================+
   | ``data``         | The response as a ``RIPEResp`` object                        |
   +------------------+--------------------------------------------------------------+
   | ``loading``      | ``boolean`` indicating if the trigger is being processed     |
   +------------------+--------------------------------------------------------------+
   | ``error``        | Error object if one occurred                                 |
   +------------------+--------------------------------------------------------------+
   | ``fetchData``    | A function to initiate the POST request                      |
   +------------------+--------------------------------------------------------------+

4. **useFetchRipeData**

   This hook fetches RIPE measurement data via polling.

   RIPE sends results in parts, so polling is used to retrieve updates. If the RIPE measurement isn't ready,
   the hook handles HTTP 405 and retries after a delay. The polling stops if:
   - An error occurs
   - Measurement completes
   - It times out
   - A new measurement begins

   It returns a **3-tuple**:

   +--------------+-----------------------------------------------------------------+
   | Return value | Description                                                     |
   +==============+=================================================================+
   | ``result``   | An array of RIPE results                                        |
   +--------------+-----------------------------------------------------------------+
   | ``status``   | A status string: ``"pending" | "partial_results" | "complete"   |
   |              | | "timeout" | "error"``                                         |
   +--------------+-----------------------------------------------------------------+
   | ``error``    | Error object if one occurred                                    |
   +--------------+-----------------------------------------------------------------+

5. **useIpInfo**

   This hook fetches geolocation data for an IP without contacting the backend.

   It uses ``ip-api`` to retrieve coordinates and country code. Used for NTP servers and the vantage point.

   The result is stored in an ``IpInfoData`` object:

   - ``coordinates``: a tuple ``[number, number]``
   - ``country_code``: a ``string``

   Note: If the IP is private, ``coordinates`` will be ``[undefined, undefined]``.

   It returns a **5-tuple**:

   +------------------+----------------------------------------------------------------+
   | Return value     | Description                                                    |
   +==================+================================================================+
   | ``data``         | Geolocation data as ``IpInfoData``                             |
   +------------------+----------------------------------------------------------------+
   | ``loading``      | ``boolean`` indicating if the fetch is ongoing                 |
   +------------------+----------------------------------------------------------------+
   | ``error``        | Error object if one occurred                                   |
   +------------------+----------------------------------------------------------------+
   | ``fetchData``    | A function to initiate the GET request                         |
   +------------------+----------------------------------------------------------------+
   | ``clearIP``      | A function to reset the internal state of ``data``             |
   +------------------+----------------------------------------------------------------+
