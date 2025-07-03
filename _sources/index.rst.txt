NTPinfo documentation
=====================

Welcome to the documentation of NTPinfo app, created for the course CSE2000 Software Project at TU Delft.

The product is split into 2 parts. The first one is the server side, that handles the
measurements and API calls to `ntplib` and the Ripe Atlas API, stores measurements
in the database and interacts with it to retrieve historical data, and has classes and
an API to send data to the front end and client side. The second part is the client,
which contains all of the front-end of the application. It uses `React` with `Vite`, base
`CSS` for styling, `ChartJS` for data visualization, and `axios` for API interaction.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules.backend
   modules.frontend
