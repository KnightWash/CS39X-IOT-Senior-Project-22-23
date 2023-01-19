import time
import asyncio
import paho.mqtt.client as mqtt
from kasa import SmartPlug
from datetime import datetime
import csv

MQTTServerName = "test.mosquitto.org"

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


async def main():
    plugAddresses = open("addresses.txt", "r")
    scanList = plugAddresses.readlines()
    plugAddresses.close()
    # strip newlines out of the list of plugs from the document...
    IPList = [p.strip() for p in scanList]
    # startTime = time.time()

    plugList = [LaundryMachine() for p in IPList]
    for i in range(len(plugList)):
        plugList[i].oneRunBefore = 2
        plugList[i].twoRunsBefore = 2
        plugList[i].IP = IPList[i]
        plugList[i].previousMachineState = 2

    print(plugList[0].oneRunBefore)
    print(plugList[0].twoRunsBefore)
    print(plugList[0].previousMachineState)
    print(plugList[0].IP)
    print(plugList)

    while(True):
        # print("hello world")
        # print(IPList)

        for plug in plugList:
            # log_file = open("testKasaOutput.csv", "a+")

            currentPlug = SmartPlug(plug.IP)
            # currentTime = (startTime - time.time())

            # csv.writer(log_file).writerow(currentTime)

            await currentPlug.update()  # Request an update
            print(currentPlug.alias + "'s power level is...")
            eMeterCheck = currentPlug.emeter_realtime
            # let's pull the actual number we want out of eMeterCheck
            powerLevel = float(str(eMeterCheck).split(
                "=", 1)[1].split(" ", 1)[0])
            print(powerLevel)

            # # publishing to mqtt broker
            client = mqtt.Client("Beta")
            client.connect(MQTTServerName)

            # Only publish on state change
            if powerLevel > 11:
                plug.currentRun = 0
                if plug.currentRun != plug.previousMachineState:
                    if plug.currentRun == plug.oneRunBefore == plug.twoRunsBefore:
                        plug.previousMachineState = 0
                        print("print 'On' to mqtt here")
                        client.publish(currentPlug.alias,
                                       payload="On", retain=True)
            else:
                plug.currentRun = 1
                if plug.currentRun != plug.previousMachineState:
                    if plug.currentRun == plug.oneRunBefore == plug.twoRunsBefore:
                        plug.previousMachineState = 1
                        print("print 'Off' to mqtt here")
                        client.publish(currentPlug.alias,
                                       payload="Off", retain=True)

            # don't put anything after this line in the for loop - we need it to save every plug's ping data
            # log_file.close()

            plug.twoRunsBefore = plug.oneRunBefore
            plug.oneRunBefore = plug.currentRun

if __name__ == "__main__":
    asyncio.run(main())
