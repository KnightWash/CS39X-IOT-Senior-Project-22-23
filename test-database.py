import sqlite3
import time
import json
import paho.mqtt.client as mqtt

MQTTServerName = "test.mosquitto.org"

# Create database table
con = sqlite3.connect("test.db")
cur = con.cursor()
cur.execute(
    """CREATE TABLE IF NOT EXISTS LaundryMachines (
        id integer PRIMARY KEY,
        name text NOT NULL, 
        location text NOT NULL, 
        startTime integer, 
        stopTime integer
    );"""
)

client = mqtt.Client("knightwash-tester")
client.connect(MQTTServerName)

machineName = "calvin/test/dryer/location"
publishTopic = machineName
startTime = 0
stopTime = 0
runTime = 0

while True:
    print("Starting test machine")
    client.publish(
        publishTopic,
        qos=1,
        payload=("On|" + str(int(time.time()))),
        retain=True,
    )

    startTime = int(time.time())
    time.sleep(15)

    print("Stopping test machine")
    client.publish(
        publishTopic,
        qos=1,
        payload=("Off|" + str(int(time.time()))),
        retain=True,
    )

    stopTime = int(time.time())
    runTime = stopTime - startTime
    print(f"Ran for {runTime} seconds\n")

    time.sleep(10)
