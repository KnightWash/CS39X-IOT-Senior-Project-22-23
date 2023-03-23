import time
import asyncio
import paho.mqtt.client as mqtt
from kasa import SmartPlug
from datetime import datetime
import logging  # https://docs.python.org/3/howto/logging.html

logging.basicConfig(
    filename="debug.log",
    encoding="utf-8",
    level=logging.WARNING,
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)
MQTTServerName = "test.mosquitto.org"
timeBetweenPosts = 5 * 60  # 5 minutes in seconds
powerOnThreshold = 11  # power in watts

#### reference code ####
#### https://python-kasa.readthedocs.io/en/latest/smartdevice.html ####
# plug_1 = SmartPlug("153.106.213.230")
# await plug_1.update() # Request the update
# print(plug_1.alias) # Print out the alias
# print(plug_1.emeter_realtime) # Print out current emeter status


class LaundryMachine:
    def __init__(self):
        self.currentRun = 2
        self.twoRunsBefore = 2
        self.oneRunBefore = 2
        self.previousMachineState = 2
        self.IP = str("127.0.0.1")
        self.date = 0

    def isTimeToRepost(self) -> bool:
        if int(datetime.now().timestamp()) - self.date >= timeBetweenPosts:
            return True
        return False

    def isStateChanged(self) -> bool:
        if self.currentRun != self.previousMachineState:
            return True
        return False

    def isPowerLevelStable(self) -> bool:
        if self.currentRun == self.oneRunBefore == self.twoRunsBefore:
            return True
        return False

    def handlePublishing(self, mqttClient, publishTopic):
        if self.isStateChanged() is False and self.isTimeToRepost() is False:
            return
        if self.isPowerLevelStable() is False:
            return
        if self.currentRun == 0:
            displayedMessage = "Posting 'On' to MQTT..."
            payloadMessage = "On|"
        else:
            displayedMessage = "posting 'Off' to MQTT..."
            payloadMessage = "Off|"

        attempts = 0
        while attempts < 3:
            try:
                print(displayedMessage)
                mqttClient.publish(
                    publishTopic,
                    qos=1,
                    payload=(payloadMessage + str(int(datetime.now().timestamp()))),
                    retain=True,
                )
                self.previousMachineState = self.currentRun
                break
            except:
                print("Trying to reconnect to MQTT broker")
                attempts += 1
            if attempts >= 3:
                print(f"Posting failed for {publishTopic} at {self.date}")
                logging.warning(f"Posting failed for {publishTopic} at {self.date}")
        return


async def main():
    plugAddresses = open("addresses.txt", "r")
    scanList = plugAddresses.readlines()
    plugAddresses.close()
    # strip newlines out of the list of plugs from the document...
    IPList = [p.strip() for p in scanList]

    plugList = [LaundryMachine() for p in IPList]
    for i in range(len(plugList)):
        plugList[i].oneRunBefore = 2
        plugList[i].twoRunsBefore = 2
        plugList[i].IP = IPList[i]
        plugList[i].previousMachineState = 2
        plugList[i].date = 0

    # print(plugList[0].oneRunBefore)
    # print(plugList[0].twoRunsBefore)
    # print(plugList[0].previousMachineState)
    # print(plugList[0].IP)
    print(plugList)

    while True:
        for plug in plugList:
            currentPlug = SmartPlug(plug.IP)

            try:
                await currentPlug.turn_on()
                await currentPlug.update()  # Request an update
                # despite the misleading function name, this returns daily statistics for the current month
                await currentPlug.get_emeter_daily()
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
                plug.currentRun = 0
            else:
                plug.currentRun = 1

            plug.handlePublishing(mqttClient=client, publishTopic=currentPlug.alias)
            plug.twoRunsBefore = plug.oneRunBefore
            plug.oneRunBefore = plug.currentRun
            print("=============================================")


if __name__ == "__main__":
    asyncio.run(main())
