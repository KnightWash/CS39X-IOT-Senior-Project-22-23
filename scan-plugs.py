import time
import asyncio
import paho.mqtt.client as mqtt
from kasa import SmartPlug
from datetime import datetime
import csv

#### reference code ####
#### https://python-kasa.readthedocs.io/en/latest/smartdevice.html ####
# plug_1 = SmartPlug("153.106.213.230")
# await plug_1.update() # Request the update
# print(plug_1.alias) # Print out the alias
# print(plug_1.emeter_realtime) # Print out current emeter status


class LaundryMachine:
    def __init__(plug):
        plug.twoRunsBefore = False
        plug.oneRunBefore = False


async def main():

    plugAddresses = open("addresses.txt", "r")
    scanList = plugAddresses.readlines()
    plugAddresses.close()
    # strip newlines out of the list of plugs from the document...
    plugList = [p.strip() for p in scanList]
    # startTime = time.time()

    # for plug in plugList:
    #     client = mqtt.Client("Beta")
    #     client.connect("test.mosquitto.org")

    #     currentPlug = SmartPlug(plug)
    #     await currentPlug.update()  # Request an update

    #     client.publish(currentPlug.alias, payload = "Off", retain=True)

    # for plug in plugList:
    #     plugHistory = LaundryMachine(plug)
    #     print(plugHistory.oneRunBefore)
    #     print(plugHistory.twoRunsBefore)

    objs = [LaundryMachine() for i in plugList]
    for obj in objs:
        obj.oneRunBefore = False
        obj.twoRunsBefore = False

    print(objs[0].oneRunBefore)
    print(objs[0].twoRunsBefore)
    print(objs)

    while(True):
        print("hello world")
        # print(plugList)

        for plug in plugList:
            # log_file = open("testKasaOutput.csv", "a+")

            currentPlug = SmartPlug(plug)
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
            client.connect("test.mosquitto.org")
            # print("Publishing to " + currentPlug.alias)

            # Only publish on state change
            if powerLevel > 11:
                currentRun = True
                if currentRun == oneRunBefore == twoRunsBefore:
                    print("print 'On' to mqtt here")
                    client.publish(currentPlug.alias, payload = "On", retain=True)
                else:
                    # do nothing
                    continue
            else:
                currentRun = False
                if currentRun == oneRunBefore == twoRunsBefore:
                    print("print 'Off' to mqtt here")
                    client.publish(currentPlug.alias, payload = "Off", retain=True)
                else:
                    # do nothing
                    continue

            # don't put anything after this line in the for loop - we need it to save every plug's ping data
            # log_file.close()

            twoRunsBefore = oneRunBefore
            oneRunBefore = currentRun

if __name__ == "__main__":
    asyncio.run(main())
