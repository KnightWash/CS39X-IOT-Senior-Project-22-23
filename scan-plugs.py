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



async def main():
    oneRunBefore = False
    twoRunsBefore = False

    plugAddresses = open("addresses.txt", "r")
    scanList = plugAddresses.readlines()
    plugList = [p.strip() for p in scanList]
    startTime = time.time()
    plugAddresses.close()


    while(True):
        print("hello world")
        print(plugList)
        for plug in plugList:
            print(plug)
            # log_file = open("testKasaOutput.csv", "a+")

            currentPlug = SmartPlug(plug)
            # currentTime=$(echo "$(date +%s.%N) $KASA_SCRIPT_START_TIME" | awk '{print $1 - $2}')
            currentTime = (startTime - time.time())

            # csv.writer(log_file).writerow(currentTime)

            await currentPlug.update()  # Request an update
            eMeterCheck = currentPlug.emeter_realtime
            # let's pull the actual number we want out of eMeterCheck
            powerLevel = float(str(eMeterCheck).split("=", 1)[1].split(" ", 1)[0])
            print(powerLevel)

            # # publishing to mqtt broker
            client = mqtt.Client("Beta")
            client.connect("test.mosquitto.org")
            print("Publishing to " + currentPlug.alias)

            # Only publish on state change
            if powerLevel > 11:
                currentRun = True
                if currentRun == oneRunBefore == twoRunsBefore:
                    # do nothing
                    continue
                else:
                    print("print 'On' to mqtt here")
                    client.publish(currentPlug.alias, "On")
            else:
                currentRun = False
                if currentRun == oneRunBefore == twoRunsBefore:
                    # do nothing
                    continue
                else:
                    print("print 'Off' to mqtt here")
                client.publish(currentPlug.alias, "Off")
        
            #don't put anything after this line in the for loop - we need it to save every plug's ping data
            # log_file.close()

        twoRunsBefore = oneRunBefore
        oneRunBefore = powerLevel

if __name__ == "__main__":
    asyncio.run(main())
