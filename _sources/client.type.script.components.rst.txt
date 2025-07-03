TypeScript Components
=====================

For better structure, understanding, and modularity of the front-end code, several sections have been split into reusable components.

Component List
--------------

- **DownloadButton**

- **Hero**

- **InputSection**

- **LineGraph**

  - This component uses ChartJS to create a line graph from the provided data.
  - It uses the ``Measurement`` type to determine whether to show *delay* or *offset* on the y-axis.
  - The values for the y-axis are taken from an array of ``NTPData``.
  - The ``Measurement`` type consists of either ``"delay"`` or ``"offset"``.
  - The x-axis shows the measurement time as a string representation of a Python ``Date`` object, taken from the ``time`` field of ``NTPData``.

- **LoadingSpinner**

- **ResultSummary**

- **TimeInput**

- **Visualization**

  - This is the popup shown when the "View Historical Data" button is pressed.
  - It includes all options for selecting which data to visualize.
  - Includes **dropdowns** to choose the desired time period.
  - A **Custom** button allows users to manually input a time period using additional fields.
  - **Radio buttons** allow selection between *Delay* and *Offset* as the measurement to be shown.
  - Includes **DownloadButtons** to download data for the selected time period.

- **WorldMap**

  - This component renders a map to visualize all geolocation data.
  - It uses the ``Leaflet`` library for rendering the map.
  - The map tiles are based on the **Dark Matter** theme provided by `CARTO <https://carto.com/>`_.
  - Displays the location of:
    - RIPE probes
    - NTP server(s)
    - Vantage point
  - Icons used are located in ``src/assets``.
  - Each point on the map shows detailed information such as:
    - **RIPE probes**: RTT, offset, and probe ID
    - **NTP servers**: IP address and name
    - **Vantage point**: IP address and location
