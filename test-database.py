import sqlite3
from time import sleep
from datetime import datetime
import pytz
import schedule
import json
import paho.mqtt.client as mqtt
from google.cloud import pubsub_v1


########## Create database table ##############

dbPath = "test.db"
est = pytz.timezone("US/Eastern")

con = sqlite3.connect(dbPath)
cur = con.cursor()
cur.execute(
    """CREATE TABLE IF NOT EXISTS TestMachines (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL, 
        location TEXT NOT NULL, 
        startTime INTEGER, 
        stopTime INTEGER,
        startTimeRounded INTEGER,
        runTime INTEGER
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


def getCurrentDateTime():
    return datetime.now(est)


def getCurrentUnixTime():
    return int(getCurrentDateTime().timestamp())


def queryToJson(con, query):
    cur = con.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    columns = [description[0] for description in cur.description]
    result = [dict(zip(columns, row)) for row in rows]
    print("JSON dump: ", result)
    return json.dumps(result)


def roundTimeToHour(unix_time):
    dt = datetime.fromtimestamp(unix_time)
    rounded_dt = dt.replace(minute=0, second=0)
    return rounded_dt.hour


def publishAnalytics():
    selectLastWeekInfo = "SELECT startTimeRounded as hour, COUNT(*) as count FROM TestMachines WHERE startTime >= strftime('%s', datetime('now', '-45 minutes')) AND location='test' GROUP BY startTimeRounded;"
    payload = queryToJson(con, selectLastWeekInfo)
    try:
        print("PUBLISHING ANALYTICS TO 'calvin/knightwash/analytics'")
        analyticsClient = mqtt.Client("knightwash-analytics")
        analyticsClient.connect(MQTTServerName)
        analyticsClient.publish(
            "calvin/knightwash/analytics",
            qos=1,
            payload=payload,
            retain=True,
        )
    except:
        print("FAILED TO PUBLISH ANALYTICS")
    else:
        print("SUCCESSFULLY PUBLISHED ANALYTICS")
    return


######## SCHEDULED FUNCTION TO PUBILSH ANALYTICS EVERY n MINUTES #########
n = 1
schedule.every(n).minutes.do(publishAnalytics)

while True:
    ###### LOG START TIME #######
    # startTime = int(time.time())
    startTime = getCurrentUnixTime()
    startTimeRounded = roundTimeToHour(startTime)

    ########### MACHINE TURNS ON #############
    print("\nStarting test machine")
    client.publish(
        publishTopic,
        qos=1,
        payload=("On|" + str(startTime)),
        retain=True,
    )

    ##### SLEEP #####
    sleep(10)

    ########### MACHINE TURNS OFF ############
    print("Stopping test machine")
    client.publish(
        publishTopic,
        qos=1,
        payload=("Off|" + str(startTime)),
        retain=True,
    )

    ###### LOG STOP TIME ########
    stopTime = getCurrentUnixTime()
    runTime = stopTime - startTime
    print(f"Ran for {runTime} seconds")

    ####### TRIGGER CLOUD PUBSUB #######
    print(f"Sent pubsub message")
    future = publisher.publish(topic_path, data)
    print(future.result())

    ###### WRITE CURRENT RUN INFO TO DATABASE #######
    cur.execute(
        f"""
        INSERT INTO TestMachines (name, location, startTime, stopTime, startTimeRounded, runTime) 
        VALUES ('{machineName}', '{location}', {startTime}, {stopTime}, {startTimeRounded}, {runTime})
        """
    )
    con.commit()
    print("Wrote to database")
    ##### SLEEP #####
    sleep(10)

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
    sleep(1)
