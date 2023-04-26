# KnightWash Backend Service

This repo contains the backend code that runs on the RaspberryPi.

[/archive](./archive/) - Contains the bash scripts used to initially test the feasability of the app.

[/systemd-service](./systemd-service/) - Contains the systemd service file used for creating a systemd service for `scan-plugs.py` on the RaspberryPi.

[/test-scripts](./test-scripts/) - Contains the python scripts used to simulate a fake machine for testing purposes. This was used to test subscribing to notifications, sending push notifications, and storing and publishing information to/from the local SQLite database.

[requirements.txt](./requirements.txt) - List of project dependencies

[addresses.txt](./addresses.txt) - Contains the list of IP addresses of the Kasa Smart Plugs that the washers and dryers are plugged into. Used by [scan-plugs.py](./scan-plugs.py) to find the plugs and ping them for status updates.

[scan-plugs.py](./scan-plugs.py) - The python script that runs on the RaspberryPi. It pings the smart plugs to get the current status of each machine and for each plug, it does the following:

#### Publish Machine Status to MQTT

- Checks the power being drawn using the emeter in the smart plug
- Determines whether the machine is on or off by checking if the power level is above a certain threshold
- Whenever the machine's state changes(goes from `On` to `Off` or the other way around), it posts an MQTT message to a topic that is unique for each machine along with the status of the machine (`On` or `Off`).

#### Send Google Cloud PubSub message

- Whenever the machine status goes from `On` to `Off`, it also simultaneously sends a Cloud Pubsub Message containing the name of the machine to our Firebase Cloud Function (which is responsible for sending push notifications to subscribed users).

#### Perform Database Operations

- Checks if the SQLite database `knightwash.db` exists in the current directory and creates
- After a machine has finished running, it stores the machine's name, location, startTime and stopTime in the local SQLite database.
- Every hour, it queries the database to get the machine runs from the last 7 days, converts it to JSON, and publishes it to the MQTT topic for usage-analytics.

---

## Installation and Setup

### Installing dependencies

Install the required python modules using the following command:

    pip install -r requirements.txt

### Setting up a systemd service on the RaspberryPi

Since `scan-plugs.py` will stop running whenever the RaspberryPi restarts due to power failures, we want to create a systemd service so that the script starts running automatically whenever the RaspberryPi boots up. Follow these steps to create a systemd service.

- Copy the systemd service file [systemd-service/scan-plugs.service](./systemd-service/scan-plugs.service) into `/etc/systemd/system`
- Once the service file has been copied to the `/etc/systemd/system` directory, we need to issue the following command to tell systemd to read our service file:

        sudo systemctl daemon-reload

- Now we can enable our systemd service using the following command:

        sudo systemctl enable scan-plugs.service

- To manually start the service, use the following command:

        sudo systemctl start scan-plugs.service

- Now, `scan-plugs.py` should start running automatically whenever the RaspberryPi restarts. To check the status of the service, use the following command:

        sudo systemctl status scan-plugs.service
