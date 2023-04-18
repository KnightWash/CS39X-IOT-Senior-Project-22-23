import sqlite3
import asyncio
import time
from datetime import datetime
import json
import logging
import paho.mqtt.client as mqtt
from kasa import SmartPlug
from enum import Enum
from google.cloud import pubsub_v1

# Config for debug log
logging.basicConfig(
    filename="debug.log",
    encoding="utf-8",
    level=logging.WARNING,
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)

# MQTT Setup
MQTTServerName = "test.mosquitto.org"
analyticsLocations = ("bolt", "heyns", "timmer")
"""Names of the hall to publish analytics to"""
analyticsClient = mqtt.Client("knightwash-analytics")
"""mqtt client object to publish usage analytics"""


# timeBetweenAnalyticsPosts = 3600 * 12  # 12 hours
timeBetweenPosts = 5 * 60  #  5 minutes
"""amount of time (in seconds) to wait between mqtt posts to make sure that plug is online"""
timeBetweenAnalyticsPosts = 2 * 60  # 2 minutes
"""amount of time (in seconds) to wait between mqtt posts to publish usage analytics"""
powerOnThreshold = 11  # power in watts
"""Power level (in watts) above which laundry machine turns on."""

publisher = pubsub_v1.PublisherClient()
"""Cloud pubsub client object"""

# Database connection
dbPath = "knightwash.db"
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


class Status(Enum):
    """The possible states that a laundry machine can be in"""

    notRunning = 0
    running = 1
    unknown = 2


class LaundryMachine:
    """Object representing a laundry machine"""

    def __init__(self):
        self.currentRun = Status.unknown
        self.twoRunsBefore = Status.unknown
        self.oneRunBefore = Status.unknown
        self.previousMachineState = Status.unknown
        self.IP = str("127.0.0.1")
        self.date = 0
        self.analyticsPostDate = 0

        self.machineName = ""
        self.location = ""
        self.startTime = int(time.time())
        self.stopTime = int(time.time())
        self.startTimeRounded = roundTimeToHour(self.startTime)
        self.runTime = 0

    def isTimeToRepost(self) -> bool:
        """Returns True if enough time has passed since the last mqtt post"""
        if int(time.time()) - self.date >= timeBetweenPosts:
            return True
        return False

    def isStateChanged(self) -> bool:
        """Returns true if the machine state has changed since the last iteration of the loop"""
        if self.currentRun != self.previousMachineState:
            return True
        return False

    def isPowerLevelStable(self) -> bool:
        """Returns true if the power level has remained consistent for the last 3 iterations of the loop.
        \nEliminates false positives due to random spikes in power levels"""
        if self.currentRun == self.oneRunBefore == self.twoRunsBefore:
            return True
        return False

    def writeToDatabase(self) -> None:
        """Write usage data from the last run of the laundry machine to the database"""
        print("Writing to database")
        logging.info("Writing to database")

        attempts = 0
        retries = 3
        while attempts < retries:
            try:
                cur.execute(
                    f"""
                    INSERT INTO TestMachines (name, location, startTime, stopTime, startTimeRounded, runTime) 
                    VALUES ('{self.machineName}', '{self.location}', {self.startTime}, {self.stopTime}, {self.startTimeRounded}, {self.runTime})
                    """
                )
                con.commit()
            except:
                logging.warning("Failed writing to database, retrying...")
            else:
                print("Wrote to database")
                break

    def handlePublishing(self, mqttClient, publishTopic) -> None:
        """
        Publish machine state if all the conditions are met

        Publishes the state of the machine to the topic by checking if:
            1) the state of the machine has changed

            2) enough time has passed since the last mqtt post

            3) the machine's power level isn't spiking, leading to false positives
        """

        if self.isStateChanged() is False and self.isTimeToRepost() is False:
            return
        if self.isPowerLevelStable() is False:
            return

        # Publish every 5 minutes or when machine state changes, whichever comes first
        if self.currentRun == Status.running:
            if self.isStateChanged():
                self.startTime = getCurrentUnixTime()
                self.startTimeRounded = roundTimeToHour(self.startTime)
                print("Machine started")
                logging.info("Machine started")
            displayedMessage = "Posting 'On' to MQTT..."
            payloadMessage = "On|"
        else:
            if self.isStateChanged():
                self.stopTime = getCurrentUnixTime()
                print("Machine stopped")
                self.runTime = (
                    self.stopTime - self.startTime
                ) / 60  # runtime in minutes
                logging.info("Machine stopped")
            displayedMessage = "posting 'Off' to MQTT..."
            payloadMessage = "Off|"

        # send pubsub notifications out to people subscribed to machines
        if self.isStateChanged() is True and self.currentRun == Status.notRunning:
            # fire notifications when state changes from on to off
            # pubSubMachineName = publishTopic.replace("/", "-") # convert / in topic name to - since pubsub topics can't handle slashes
            # The `topic_path` method creates a fully qualified identifier
            # in the form `projects/{project_id}/topics/{topic_id}`

            # topic_path = publisher.topic_path("knightwash-webui-angular", pubSubTopic)
            topic_path = publisher.topic_path(
                "knightwash-webui-angular", "machines_pubsub"
            )

            # data = payloadMessage.replace("|", "").encode("utf-8")
            data = publishTopic.encode("utf-8")

            # When you publish a message, the client returns a future.
            future = publisher.publish(topic_path, data)
            print(future.result())
            print("posted to pubsub!")
            self.writeToDatabase()
            print("stored last run info in database")

        attempts = 0
        while attempts < 3:
            try:
                print(displayedMessage)
                mqttClient.publish(
                    publishTopic,
                    qos=1,
                    payload=(payloadMessage + str(int(time.time()))),
                    retain=True,
                )
                self.previousMachineState = self.currentRun
                self.date = int(time.time())
                break
            except:
                print("Trying to reconnect to MQTT broker")
                attempts += 1
            if attempts >= 3:
                print(f"Posting failed for {publishTopic} at {self.date}")
                logging.warning(f"Posting failed for {publishTopic} at {self.date}")

    def isTimeToPublishAnalytics(self):
        """Returns True if enough time has passed since the last analytics post"""

        if int(time.time()) - self.analyticsPostDate >= timeBetweenAnalyticsPosts:
            self.analyticsPostDate = int(time.time())
            return True
        return False

    def handlePublishAnalytics(self, mqttClient):
        """
        If enough time has passed since last analytics post, query
        the database and publish analytics for each hall separately
        """
        if self.isTimeToPublishAnalytics():
            for location in analyticsLocations:
                selectLastWeekInfo = f"SELECT startTimeRounded as hour, COUNT(*) as count FROM TestMachines WHERE startTime >= strftime('%s', datetime('now', '-7 days')) AND location='{location}' GROUP BY startTimeRounded;"
                payload = queryToJson(selectLastWeekInfo)
                publishTopic = f"calvin/knightwash/analytics/{location}"
                try:
                    print(f"PUBLISHING ANALYTICS TO '{publishTopic}'")
                    mqttClient.connect(MQTTServerName)
                    mqttClient.publish(
                        publishTopic,
                        qos=1,
                        payload=payload,
                        retain=True,
                    )
                except:
                    print(
                        f"FAILED TO PUBLISH ANALYTICS to 'calvin/knightwash/{location}'"
                    )
                    logging.warning(
                        f"FAILED TO PUBLISH ANALYTICS to 'calvin/knightwash/{location}'"
                    )
                else:
                    print(
                        f"SUCCESSFULLY PUBLISHED ANALYTICS to 'calvin/knightwash/{location}'"
                    )
        return


def queryToJson(query):
    """Executes an sql query and returns the results as a json formatted string"""
    cur = con.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    columns = [description[0] for description in cur.description]
    result = [dict(zip(columns, row)) for row in rows]
    print("JSON dump: ", result)
    return json.dumps(result)


def roundTimeToHour(unix_time):
    """Takes input time in unix epoch and returns an integer representing the hour"""
    dt = datetime.fromtimestamp(unix_time)
    rounded_dt = dt.replace(minute=0, second=0)
    return rounded_dt.hour


def getCurrentUnixTime():
    """Returns the current time in unix epoch"""
    return int(time.time())


async def main():
    plugAddresses = open("addresses.txt", "r")
    scanList = plugAddresses.readlines()
    plugAddresses.close()
    # strip newlines out of the list of plugs from the document...
    IPList = [p.strip() for p in scanList]

    plugList = [LaundryMachine() for p in IPList]
    for i in range(len(plugList)):
        plugList[i].oneRunBefore = Status.unknown
        plugList[i].twoRunsBefore = Status.unknown
        plugList[i].IP = IPList[i]
        plugList[i].previousMachineState = Status.unknown
        plugList[i].date = 0
    print(plugList)

    while True:
        for plug in plugList:
            currentPlug = SmartPlug(plug.IP)

            try:
                await currentPlug.turn_on()
                await currentPlug.update()  # Request an update
                # despite the misleading function name, this returns daily statistics for the current month
                await currentPlug.get_emeter_daily()
                plug.machineName = currentPlug.alias
                plug.location = plug.machineName.split("/")[1]
            except:
                print("WARNING: SCAN FAILED FOR " + plug.IP + "...")
                logging.warning("SCAN FAILED FOR " + plug.IP + "...")
                print("=============================================")
                continue

            # print(currentPlug.get_emeter_daily(year=2023, month=1))
            print("Usage today:", currentPlug.emeter_today, "kWh")
            print("Usage this month:", currentPlug.emeter_this_month, "kWh")
            print(currentPlug.alias + "'s power level is...")

            eMeterCheck = currentPlug.emeter_realtime
            # let's pull the actual number we want out of eMeterCheck
            powerLevel = float(str(eMeterCheck).split("=", 1)[1].split(" ", 1)[0])
            print(powerLevel)

            client = mqtt.Client("knightwash")
            try:
                client.connect(MQTTServerName)
            except:
                print(
                    "Dropped connection to MQTT broker - this is okay, we'll just wait until the next loop..."
                )
                logging.warning(
                    "Dropped connection to MQTT broker - this is okay, we'll just wait until the next loop..."
                )
                continue

            if powerLevel > powerOnThreshold:
                plug.currentRun = Status.running
            else:
                plug.currentRun = Status.notRunning

            plug.handlePublishing(mqttClient=client, publishTopic=currentPlug.alias)
            plug.twoRunsBefore = plug.oneRunBefore
            plug.oneRunBefore = plug.currentRun
            print("=============================================")
        plug.handlePublishAnalytics(mqttClient=analyticsClient)


if __name__ == "__main__":
    asyncio.run(main())
