Conversion from data tables to NtpMeasurement class
---------------------------------------------------

.. autofunction::  server.app.db.db_interaction.row_to_dict

.. autofunction::  server.app.db.db_interaction.rows_to_dicts

.. autofunction::  server.app.db.db_interaction.dict_to_measurement

.. autofunction::  server.app.db.db_interaction.rows_to_measurements


Methods used for interaction with the database
----------------------------------------------

Insertion
^^^^^^^^^

.. autofunction:: server.app.db.db_interaction.insert_measurement

Fetching data based on IP
^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: server.app.db.db_interaction.get_measurements_timestamps_ip


Fetching data based on domain name
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: server.app.db.db_interaction.get_measurements_timestamps_dn

Fetching measurements for jitter calculation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: server.app.db.db_interaction.get_measurements_for_jitter_ip

