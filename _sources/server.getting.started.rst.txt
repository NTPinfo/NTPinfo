Server Setup and Running
========================

There are two ways to start the server: manually configuring it or using a Docker container.

To set up and run the back-end server manually, follow the steps below.

Locally Configure the Server
----------------------------

1. **Create a virtual environment**

   .. code-block:: bash

      python -m venv venv

   Then activate the virtual environment:

   - On **macOS/Linux**:

     .. code-block:: bash

        source venv/bin/activate

   - On **Windows**:

     .. code-block:: bash

        .\venv\Scripts\activate

2. **Install and prepare PostgreSQL database**

   2.1. Visit: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
   Select and download your preferred version of PostgreSQL.

   2.2. Go to the download location and double-click the `.exe` file.
   Follow the installation steps and keep track of:
   - Installation directory
   - Superuser (usually ``postgres``)
   - Port (usually ``5432``)
   - Password (**save this**)

   2.3. Ensure `pgAdmin` is installed during setup.

   2.4. Restart your computer.

   2.5. Open `pgAdmin`, access the **Server**, and enter your password if needed.

   2.6. Right-click **Databases**, click **Create**, and create a new database, preferably named ``measurements``.

   .. note::
      Tables will be created once the back-end server runs, so no need to create them now.

3. **Create a `.env` file** in the root directory:

   .. code-block:: ini

      # needed for back-end (server)
      DB_NAME=measurements
      DB_USER=postgres
      DB_PASSWORD=postgres
      DB_HOST=db
      DB_PORT=5432
      ripe_api_token={ripe API with permission to perform measurements}
      ripe_account_email={email of your ripe account}
      ACCOUNT_ID={geolite account id}
      LICENSE_KEY={geolite key}
      UPDATE_CRON_SCHEDULE=0 0 * * *
      CLIENT_URL=http://localhost:5173

      # needed for front-end (client)
      DOCKER_NETWORK_SUBNET=2001:db8:1::/64
      DOCKER_NETWORK_GATEWAY=2001:db8:1::1
      VITE_CLIENT_HOST=localhost
      VITE_CLIENT_PORT=5173
      VITE_SERVER_HOST_ADDRESS=http://localhost:8000
      VITE_STATUS_THRESHOLD=1000

   Additionally, the configuration file `server/server_config.yaml` contains editable variables:

   .. code-block:: yaml

      ntp:
        version: 4
        timeout_measurement_s: 7
        number_of_measurements_for_calculating_jitter: 8
        server_timeout: 60

      edns:
        mask_ipv4: 24
        mask_ipv6: 56
        default_order_of_edns_servers:
          - "8.8.8.8"
          - "1.1.1.1"
          - "2001:4860:4860::8888"
        edns_timeout_s: 3

      ripe_atlas:
        timeout_per_probe_ms: 4000
        packets_per_probe: 3
        number_of_probes_per_measurement: 3

      bgp_tools:
        anycast_prefixes_v4_url: "https://raw.githubusercontent.com/bgptools/anycast-prefixes/master/anycatch-v4-prefixes.txt"
        anycast_prefixes_v6_url: "https://raw.githubusercontent.com/bgptools/anycast-prefixes/master/anycatch-v6-prefixes.txt"

      max_mind:
        path_city: "GeoLite2-City.mmdb"
        path_country: "GeoLite2-Country.mmdb"
        path_asn: "GeoLite2-ASN.mmdb"

   .. note::
      Make sure PostgreSQL is running and accessible with the provided credentials.
      The server will inform you if any variables are missing or misconfigured.

4. **Install backend dependencies**

   .. code-block:: bash

      cd server
      pip install -r requirements.txt

5. **Download MaxMind and BGP Tools databases and schedule updates**

   To initialize and schedule database updates (run from the root directory):

   .. code-block:: bash

      cd ..
      crontab -e
      0 1 * * * /bin/bash /full_path_to/update_geolite_and_bgptools_dbs.sh >> /full_path_to/update_geolite_and_bgptools_dbs.log 2>&1

   Replace ``/full_path_to`` with the output of:

   .. code-block:: bash

      pwd

   Or to download once without scheduling:

   .. code-block:: bash

      ./update_geolite_and_bgptools_dbs.sh

   **Common Errors**

   - Windows-style line endings in `.env` may break Linux/WSL scripts. Use:

     .. code-block:: bash

        dos2unix .env

   - For `bad interpreter` error on WSL/Linux:

     Convert CRLF to LF using VS Code or:

     .. code-block:: bash

        dos2unix update_geolite_and_bgptools_dbs.sh

   - Geolite downloads are limited per account per day.

   .. note::
      Update the databases regularly for accurate results.

6. **Run the server**

   From the root directory, run:

   .. code-block:: bash

      uvicorn server.app.main:create_app --reload --factory

   The server should now be running!
