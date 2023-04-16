import sqlite3
import time
import json
import paho.mqtt.client as mqtt
from google.cloud import pubsub_v1

####


########## Create database table ##############
con = sqlite3.connect("test.db")
cur = con.cursor()
cur.execute(
    """CREATE TABLE IF NOT EXISTS LaundryMachines (
        name text NOT NULL, 
        location text NOT NULL, 
        startTime integer, 
        stopTime integer,
        runTime, integer
    );"""
)

########## GOOGLE CLOUD PUBSUB STUFF ###########
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path("knightwash-webui-angular", "machines_pubsub")
payloadMessage = "calvin/test/dryer/location"
data = payloadMessage.encode("utf-8")
################################################

############## MQTT CLIENT STUFF ###############
MQTTServerName = "test.mosquitto.org"
client = mqtt.Client("knightwash-tester")
client.connect(MQTTServerName)
################################################

########### MACHINE INFO #######################
machineName = "calvin/test/dryer/location"
location = machineName.split("/")[1]
publishTopic = machineName
startTime = 0
stopTime = 0
runTime = 0
################################################

while True:
    ########### MACHINE TURNS ON #############
    print("\nStarting test machine")
    client.publish(
        publishTopic,
        qos=1,
        payload=("On|" + str(int(time.time()))),
        retain=True,
    )

    ###### LOG START TIME #######
    startTime = int(time.time())

    ##### SLEEP #####
    time.sleep(8)

    ########### MACHINE TURNS OFF ############
    print("Stopping test machine")
    client.publish(
        publishTopic,
        qos=1,
        payload=("Off|" + str(int(time.time()))),
        retain=True,
    )

    ###### LOG STOP TIME ########
    stopTime = int(time.time())
    runTime = stopTime - startTime
    print(f"Ran for {runTime} seconds")

    ####### TRIGGER CLOUD PUBSUB #######
    print(f"Sent pubsub message")
    future = publisher.publish(topic_path, data)
    print(future.result())

    ###### WRITE CURRENT RUN INFO TO DATABASE #######
    cur.execute(
        f"""
        INSERT INTO LaundryMachines VALUES
        ('{machineName}', '{location}', {startTime}, {stopTime}, {runTime})
        """
    )
    ##### SLEEP #####
    time.sleep(8)
