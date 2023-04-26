# Knightwash Backend Service

This repo contains the backend code that runs on the RaspberryPi.

[/archive](./archive/) - Contains the bash scripts used to initially test the feasability of the app.

[/test-scripts](./test-scripts/) - Contains the python scripts used to simulate a fake machine for testing purposes. This was used to test subscribing to notifications, sending push notifications, and storing and publishing information to/from the local SQLite database.

[addresses.txt](./addresses.txt) - Contains the list of IP addresses of the Kasa Smart Plugs that the washers and dryers are plugged into. Used by [scan-plugs.py](./scan-plugs.py) to find the plugs and ping them for status updates.

[scan-plugs.py](./scan-plugs.py) - The python script that runs on the RaspberryPi. It pings the smart plugs to get the current status of each machine and for each plug, it does the following:

    Publish Machine Status to MQTT

    - Checks the power being drawn using the emeter in the smart plug
    - Determines whether the machine is on or off by checking if the power level is above a certain threshold
    - Whenever the machine's state changes(goes from `On` to `Off` or the other way around), it posts an MQTT message to a topic that is unique for each machine along with the status of the machine (`On` or `Off`).

    #### Send Google Cloud PubSub message

    - Whenever the machine status goes from `On` to `Off`, it also simultaneously sends a Cloud Pubsub Message containing the name of the machine to our Firebase Cloud Function (which is responsible for sending push notifications to subscribed users).

    #### Perform Database Operations

    - After a machine has finished running, it stores the machine's name, location, startTime and stopTime in the local SQLite database.
    - Every hour, it queries the database to get the machine runs from the last 7 days, converts it to JSON, and publishes it to the MQTT topic for usage-analytics.

---
