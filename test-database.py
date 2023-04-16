import sqlite3
import time
import schedule
import json
import paho.mqtt.client as mqtt
from google.cloud import pubsub_v1

####


########## Create database table ##############
con = sqlite3.connect("test.db")
cur = con.cursor()
cur.execute(
    """CREATE TABLE IF NOT EXISTS TestMachines (
        id INTEGER PRIMARY KEY,
        name text NOT NULL, 
        location text NOT NULL, 
        startTime integer, 
        stopTime integer,
        runTime integer
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


def query_to_json(con, query):
    cur = con.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    columns = [description[0] for description in cur.description]
    result = [dict(zip(columns, row)) for row in rows]
    print("JSON dump: ", result)
    return json.dumps(result)


def publishAnalytics():
    selectAllQuery = "SELECT * FROM TestMachines"
    payload = query_to_json(con, selectAllQuery)
    client.publish(
        "calvin/knightwash/analytics",
        qos=1,
        payload=payload,
        retain=True,
    )
    print("PUBLISHED ANALYTICS TO 'calvin/knightwash/analytics'")
    return


######## SCHEDULED FUNCTION TO PUBILSH ANALYTICS EVERY n MINUTES #########
n = 1
schedule.every(n).minutes.do(publishAnalytics)

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
    time.sleep(10)

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
        INSERT INTO TestMachines (name, location, startTime, stopTime, runTime) 
        VALUES ('{machineName}', '{location}', {startTime}, {stopTime}, {runTime})
        """
    )
    print("Wrote to database")
    ##### SLEEP #####
    time.sleep(10)

    ########## PRINTING ALL ROWS OF DATABASE ###########
    # Execute the SELECT statement
    cur.execute("SELECT * FROM TestMachines")

    # Fetch all rows
    rows = cur.fetchall()

    # Iterate through the rows and print them
    for row in rows:
        print(row)

    ################# SCHEDULED JOB ####################
    schedule.run_pending()
    time.sleep(1)
