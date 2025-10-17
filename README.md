[![Try the App](https://img.shields.io/badge/Try%20the%20App-Live-brightgreen)](https://ntpinfo.sidnlabs.nl/)
[![Docs](https://img.shields.io/badge/Docs-Live-blue)](https://ntpinfo.github.io/NTPinfo/)

# Are your time servers on time?

## Active Internet Measurements to evaluate time servers.

## About this project

This project was developed by Group 15d as part of the **CSE2000 Software Project** course at the **Faculty of
Electrical Engineering, Mathematics and Computer Science (EWI)**, **Delft University of Technology (TU Delft)**, as part
of the **BSc Computer Science and Engineering** program.

<p align="center">
  <img src="assets/NtpInfoLogo.png" alt="Project Logo" style="width:100%; max-width:100%;"/>
</p>

---

## Cloning the project

Please use `git clone --recurse-submodules https://github.com/NTPinfo/NTPinfo.git` because the project has a submodule.
If you already cloned it without `--recurse-submodules` then just run `git submodule update --init --recursive`

## Product Structure

The product is split into 2 parts:

### Server Side

- Handles time measurement logic and API interactions.
- Uses `ntplib` and the **RIPE Atlas API** for performing measurements.
- Stores results in a PostgreSQL database.
- Provides an API to:
    - Trigger and manage measurements
    - Access historical data
    - Communicate with the front-end

### Client Side

- Built with `React` and `Vite`
- Uses:
    - `ChartJS` for data visualization
    - `axios` for interacting with the API
    - Base `CSS` for styling
- Presents all the data in a user-friendly dashboard

---

## Table of Contents

- [Server Setup and Running](#server-setup-and-running)
- [Client Setup and Running](#client-setup-and-running)
- [Docker Setup](#docker-setup)
- [Contributing](#contributing)

---

## Server Setup and Running

There are 2 ways in starting the server. The first one is to manually configure it, and the second one is using a docker
container.

To set up and run the back-end server, follow these steps:

### Locally configure the server

1. **Create a virtual environment**:

    ```bash
    python -m venv venv
    ```

   Then activate the virtual environment:
    - On **macOS/Linux**:
        ```bash
        source venv/bin/activate 
        ```
    - On **Windows**:
        ```bash
        .\venv\Scripts\activate
        ```

2. **Install and prepare PostgreSQL database**

   2.1 Install PostgreSQL according to your operating system.

   👉 You can download it from the official site: https://www.postgresql.org/download/

   2.2 Make sure the PostgreSQL service is running.

   2.3 Create a database (recommended name: `measurements`)

   2.4 Keep track of:
    - **Username** (e.g., `postgres`)
    - **Password**
    - **Port** (default: `5432`)

   2.5 You can use tools like `psql` or GUI tools such as **pgAdmin** to manage your database.
   > The necessary tables will be created automatically when running the server.


4. **Create a `.env` file** in the `root` directory with your accounts credentials in the following format:

    ```dotenv
    # needed for back-end (server)
    # the database that you want to use from PostgreSQL, preferably named "measurements"
    DB_NAME=measurements
    DB_USER=postgres
    DB_PASSWORD=postgres
    # change DB_HOST to "localhost" if you run the project locally
    DB_HOST=db
    DB_PORT=5432
    ripe_api_token={ripe API with persmission to perform measurments}
    ripe_account_email={email of your ripe account (you need to have credits)}
    ACCOUNT_ID={geolite account id}
    LICENSE_KEY={geolite key}
    # once every day
    UPDATE_CRON_SCHEDULE=0 0 * * *
    # when running local
    CLIENT_URL=http://127.0.0.1:5173
    # when runing on docker
    CLIENT_URL=https://myapp.local
    #needed for front-end (client)
    DOCKER_NETWORK_SUBNET=2001:db8:1::/64
    DOCKER_NETWORK_GATEWAY=2001:db8:1::1
    # when running locally 
    VITE_CLIENT_HOST=127.0.0.1
    VITE_CLIENT_PORT=5173
    # when running locally
    VITE_SERVER_HOST_ADDRESS=http://127.0.0.1:8000
    # replace with actual domain_name/api
    VITE_SERVER_HOST_ADDRESS=https://myapp.local/api
    # in milliseconds, choose a value you think is reasonable for the offset threshold
    VITE_STATUS_THRESHOLD=1000
    # port to launch the back-end server (must match the local one in docker-compose)
    # !! must be the same as the internal one in docker-compose !!
    SERVER_BIND=[::]:8000
    # how many workers the backend should work (2 * nr_of_cores + 1)
    SERVER_WORKERS=4
    # ports exposed from local machien used for local testing on localhost
    DB_DOCKER_PORT=15432
    # when this is changed, CLIENT_URL must also be changed
    CLIENT_DOCKER_PORT=5173
    # when this is changed, VITE_SERVER_HOST_ADDRESS must also be changed
    SERVER_DOCKER_PORT=8000
    # ports where website is served
    HTTP_PORT=80
    HTTPS_PORT=443
    ```
   Besides, the config file with public data for the server is `server/server_config.yaml` and it contains the following
   variables that you can change:

      ```yaml
        ntp:
          version: 4
          timeout_measurement_s: 7  # in seconds
          number_of_measurements_for_calculating_jitter: 8
          server_timeout: 60 # in seconds


        edns:
          mask_ipv4: 24 # bits
          mask_ipv6: 56 # bits
          default_order_of_edns_servers: # you can add multiple servers ipv4 or ipv6. The first one has the highest priority.
            # The others are used in case the first one cannot solve the domain name
            - "8.8.8.8"
            - "1.1.1.1"
            - "2001:4860:4860::8888"
          edns_timeout_s: 3 # in seconds


        ripe_atlas:
          timeout_per_probe_ms: 4000
          packets_per_probe: 3
          number_of_probes_per_measurement: 3

        bgp_tools:
          anycast_prefixes_v4_url: "https://raw.githubusercontent.com/bgptools/anycast-prefixes/master/anycatch-v4-prefixes.txt"
          anycast_prefixes_v6_url: "https://raw.githubusercontent.com/bgptools/anycast-prefixes/master/anycatch-v6-prefixes.txt"

        max_mind: # see load_config_data if you want to change the path
          path_city: "GeoLite2-City.mmdb"
          path_country: "GeoLite2-Country.mmdb"
          path_asn: "GeoLite2-ASN.mmdb"
      ```

   **Note**:
    - Ensure PostgreSQL is running and accessible with the credentials provided in the `.env` file.
    - You can edit the config variables, but if there are any variables that are missing or have invalid data, the
      server will not start, and it will tell you exactly which config variables have problems.

---

4. **Install the backend dependencies**:

    ```bash
    cd server
    pip install -r requirements.txt
    ```

5. **Download the max mind and BGP tools databases, and schedule running this file once every day**

   This will initialise the local dbs for geolocation and detecting anycast, and will schedule downloading them every
   day at 1 AM.
   Be sure that you are in the root folder, and `.env` file has all variables.

   If you want to schedule updating the databases, run this:

    ```bash
    cd ..
    crontab -e
    0 1 * * * /bin/bash /full_path_to/update_geolite_and_bgptools_dbs.sh >> /full_path_to/update_geolite_and_bgptools_dbs.log 2>&1
    ```
   But replace `/full_path_to` with the output of running :
   ```bash
    pwd
    ```
   Or if you just want to download the databases once without scheduling:
    ```bash
      ./update_geolite_and_bgptools_dbs.sh
    ```

   **Common errors**:
    - If you run `update_geolite_and_bgptools_dbs.sh` from Linux or WSL, the file `.env` may contain invisible Windows
      carriage return characters and this may make the `.sh` script to fail. You can see them using `cat -A .env`. Look
      for any "^M"
      at the end of lines. You can remove them by running this command: `dos2unix .env`. This should solve the problem.
    - If you are using Linux or WSL and you received `/bin/bash^M: bad interpreter: No such file or directory` then it
      may mean that your script has Windows-style line endings (CRLF, \r\n) instead of Unix-style (LF, \n). Another
      solution to change from CRLF to LF is to open the file in VS Code and to change them to LF.
    - If downloading the Geolite databases fails, consider that downloading them has a daily limit per account. (This
      limit is only for geolite databases)

   **Notes**:
    - Be sure to schedule running this file once every day or to manually update them, if you want up-to-date
      information.

6. **Compile the NTP-NTS tool (for NTS and NTP versions analysis)**:

   You will need to have a compiled version of this tool (it will be used by Python). In case there is not already a
   compiled version, please create it using the following steps.
   Steps:
    - Go to folder `tools/ntp-nts-tool`
    - Run the following command for your system :
        - linux: `GOOS=linux GOARCH=amd64 go build -o ntpnts_linux_amd64`
        - windows: `GOOS=windows GOARCH=amd64 go build -o ntpnts_windows_amd64.exe`
7. **Run the server (from the root directory)**:

    ```bash
    uvicorn server.app.main:create_app --reload --factory
    ```

   You should see the server running now!

---

### Client Setup and Running

To set up and run the client, follow these steps carefully:

1. **Ensure you have the prerequisites installed**

- [Node.js](https://nodejs.org/)
    - npm (comes bundled with Node.js)

      ```bash
      node -v
      npm -v
      ```
      If not, install from https://nodejs.org/

2. **Create `.env` file in client**

   Create a `.env` file in `client` and add the following to the file:
    ```dotenv
    # address of our server (back-end)
    VITE_SERVER_HOST_ADDRESS=http://127.0.0.1:8000/
    VITE_STATUS_THRESHOLD=1000
    VITE_CLIENT_HOST=127.0.0.1
    VITE_CLIENT_PORT=5173
    CLIENT_URL=http://127.0.0.1:5173
     ```

3. **Install the dependencies**

   Ensure you are in the client folder
    ```bash
    cd ./client
    npm install
    ```

4. **Running the client**

    ```bash
    npm run dev
    ```
   Everything should be set now!

---

## Docker Setup

To run the full stack (server + client + database) using `docker-compose`, follow these steps:

---

1. **Install Docker**

   Follow the instructions for your OS here:
   👉 [https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/)


2. **Install `docker-compose` (Linux)**

   ```bash
   sudo apt update
   sudo apt install docker-compose
   ```

3. **Clone the project with the new module that was added**
   ```bash
   git clone --branch client-theme --recurse-submodules https://github.com/NTPinfo/NTPinfo.git
   ```

3. **Add a .env file in the root directory**

   Create a `.env` file** in the `root` directory (the same directory with you `docker-compose.yml`)
   with your accounts credentials. (You can see this `.env` at the above of the page)

4. **Create a temporary certbot container to generate your SSL certs**

   Replace the last 2 lines `--email your@email.com` and `-d yourdomain.com` with your own data
   ```bash
   docker run --rm \
     -v $(pwd)/nginx/certbot/www:/var/www/certbot \
     -v $(pwd)/nginx/certbot/conf:/etc/letsencrypt \
     certbot/certbot certonly \
     --webroot \
     --webroot-path=/var/www/certbot \
     --agree-tos \
     --no-eff-email \
     --email your@email.com \
     -d yourdomain.com
   ```
   Once completed, the certificates should be in `nginx/certbot/conf/live/yourdomain.com/`. These are then automatically
   moved when running docker-compose to `etc/letsencrypt/live/yourdomain.com/`

5. **Make sure to add the docker path to your certificates to `nginx/conf.d/default.conf`**

   **This is an example**

   **Also make sure to replace `yourdomain.com` with your actual domain.**
   ```markdown
   server {
       listen 80;
       server_name yourdomain.com;
   
       location /.well-known/acme-challenge/ {
           root /var/www/certbot;
       }
   
       location / {
           return 301 https://$host$request_uri;
       }
   }
   
   server {
       listen 443 ssl;
       server_name yourdomain.com;
   
       ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
   
       location /api/ {
           proxy_pass http://backend:8000/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   
       location / {
           proxy_pass http://frontend:80;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

6. **Build the Docker containers**

   From the root of the project, run this, but make sure that Docker Desktop is open:

   ```bash
   sudo docker-compose build
   ```

   or this command if the first one failed:

   ```bash
   sudo docker-compose build --no-cache
   ```

   **Common Errors**

    - If it fails, and you received error `error during connect`, then make sure that you have Docker Desktop open.


7. **Start the containers**

   ```bash
   sudo docker-compose up
   ```

   ### **‼️️ Very Important ‼️**

    - Every time after you run `sudo docker-compose up` and it failed, and you want to try again, you need to run
      `sudo docker-compose down` before trying again. This also applies when **you want to build again**.

   **Common Errors**

    - If it fails with `exec /app/docker-entrypoint.sh: no such file or directory, exited with code 255` then it means
      that
      the file `docker-entrypoint.sh` (or `update.sh`) has CRLF format, and you need to change it to LF.

   Use `-d` to run it in the background:

   ```bash
   sudo docker-compose up -d
   ```

   > Make sure there is not any network name `my-net` already in use.

   This can be checked by running:

   ```bash
   sudo docker network ls
   ```

8. **Shut down the containers**

   To gracefully stop all services:

   ```bash
   sudo docker-compose down
   ```

   ### This must be done every time changes have been done, or one of the containers failed.

   ### If you also want to delete the database you must run it like this:

   ```bash
   sudo docker-compose down -v
   ```

   ### This will remove all volumes, which in our case, that's just the database, and is useful if you encounter issues with it.

---

### Everything should now be running at:

- **Frontend**: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- **Backend API**: [http://127.0.0.1:8000](http://127.0.0.1:8000)

> Make sure ports `5173` (frontend) and `8000` (backend) are not in use before starting the containers.

### Other matters to consider:

- On the `docker-entrypoint.sh` file the backend server runs with multiple workers, and because of that the logs for the
  server
  were moved to the `app/logs/access.log` file in the docker container of the back-end component.

## Contributing

We appreciate any new contributions from the open-source community

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also
simply open an issue with the tag "enhancement".

1. Fork the Project
2. Create your Feature Branch (`git checkout -b branch-name`)
3. Commit your Changes (`git commit -m 'Added feature'`)
4. Push to the Branch (`git push origin branch-name`)
5. Open a Pull Request
