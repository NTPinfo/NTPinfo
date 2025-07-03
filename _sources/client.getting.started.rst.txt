Client Setup and Running
========================

To set up and run the client, follow these steps carefully:

1. **Ensure prerequisites are installed**

   You need to have `Node.js` installed.

   - Download and install from: https://nodejs.org/
   - Verify the installation:

     .. code-block:: bash

        node -v
        npm -v

   .. note::
      `npm` comes bundled with `Node.js`. If you get an error, ensure Node.js was installed correctly.

2. **Create `.env` file in the client folder**

   Create a `.env` file inside the ``client`` directory with the following content:

   .. code-block:: ini

      # address of our server (back-end)
      VITE_SERVER_HOST_ADDRESS=http://localhost:8000/
      VITE_STATUS_THRESHOLD=1000
      VITE_CLIENT_HOST=localhost
      VITE_CLIENT_PORT=5173
      CLIENT_URL=http://localhost:5173

3. **Install the dependencies**

   Make sure you are in the ``client`` folder, then run:

   .. code-block:: bash

      cd ./client
      npm install

4. **Run the client**

   To start the development server, run:

   .. code-block:: bash

      npm run dev

   .. note::
      Everything should be set up and running now!
