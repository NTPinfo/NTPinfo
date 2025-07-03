Root /
--------------

Root endpoint for basic service health check
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: server.app.api.routing.read_root


/measurements
--------------

Compute a live NTP measurement for a given server (IP or domain)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: server.app.api.routing.read_data_measurement


/measurements/history
---------------------

Fetch historic NTP measurement data for a given server over a specified time range
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: server.app.api.routing.read_historic_data_time


/measurements/ripe/trigger
--------------------------

Initiate a RIPE Atlas NTP measurement for the specified server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: server.app.api.routing.trigger_ripe_measurement


/measurements/ripe/{measurement_id}
-----------------------------------

Retrieve the results of a previously triggered RIPE Atlas measurement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: server.app.api.routing.get_ripe_measurement_result