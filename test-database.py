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

machineName = "calvin/test/dryer/location"
client = mqtt.Client("knightwash")
publishTopic = machineName
machineState = "On|"
startTime = 0
stopTime = 0

while True:
    client.publish(
        publishTopic,
        qos=1,
        payload=(machineState + str(int(time.time()))),
        retain=True,
    )

    # Change machine state on each iteration
    if machineState == "On|":
        machineState = "Off|"
    else:
        machineState = "On|"

    time.sleep(15)
