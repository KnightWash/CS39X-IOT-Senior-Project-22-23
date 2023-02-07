import time
import asyncio
import paho.mqtt.client as mqtt
from kasa import SmartPlug
from datetime import datetime
import logging  # https://docs.python.org/3/howto/logging.html

logging.basicConfig(filename='debug.log', encoding='utf-8',
                    level=logging.WARNING, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

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

    plugList = [LaundryMachine() for p in IPList]
    for i in range(len(plugList)):
        plugList[i].oneRunBefore = 2
        plugList[i].twoRunsBefore = 2
        plugList[i].IP = IPList[i]
        plugList[i].previousMachineState = 2

    # print(plugList[0].oneRunBefore)
    # print(plugList[0].twoRunsBefore)
    # print(plugList[0].previousMachineState)
    # print(plugList[0].IP)
    print(plugList)

    while(True):
        for plug in plugList:
            currentPlug = SmartPlug(plug.IP)

            try:
                await currentPlug.turn_on()
                await currentPlug.update()  # Request an update
                # despite the misleading function name, this returns daily statistics for the current month
                await currentPlug.get_emeter_daily()
            except:
                print("WARNING: SCAN FAILED FOR " + plug.IP + "...")
                logging.warning("SCAN FAILED FOR " + plug.IP)
            else:
                # print(currentPlug.get_emeter_daily(year=2023, month=1))
                print("Usage today:", currentPlug.emeter_today, "kWh")
                print("Usage this month:", currentPlug.emeter_this_month, "kWh")

                print(currentPlug.alias + "'s power level is...")
                eMeterCheck = currentPlug.emeter_realtime
                # let's pull the actual number we want out of eMeterCheck
                powerLevel = float(str(eMeterCheck).split(
                    "=", 1)[1].split(" ", 1)[0])
                print(powerLevel)

                # creating mqtt client object
                client = mqtt.Client("Beta")
                client.loop_forever(retry_first_connection=True)

                # connecting to the broker
                client.connect(MQTTServerName)


                # only publish on state change
                if powerLevel > 11:
                    plug.currentRun = 0
                    if plug.currentRun != plug.previousMachineState:
                        if plug.currentRun == plug.oneRunBefore == plug.twoRunsBefore:
                            plug.previousMachineState = 0
                            attempts = 0
                            publishSuccess = False
                            while publishSuccess is False:
                                try:
                                    print("posting 'On' to mqtt...")
                                    client.publish(currentPlug.alias,
                                                qos=1, payload="On", retain=True)
                                    publishSuccess = True
                                except:
                                    print("trying to reconnect to mqtt broker")
                else:
                    plug.currentRun = 1
                    if plug.currentRun != plug.previousMachineState:
                        if plug.currentRun == plug.oneRunBefore == plug.twoRunsBefore:
                            plug.previousMachineState = 1
                            attempts = 0
                            publishSuccess = False
                            while attempts < 3 and publishSuccess is False:
                                try:
                                    print("posting 'Off' to mqtt...")
                                    client.publish(currentPlug.alias,
                                                qos=1, payload="Off", retain=True)
                                    publishSuccess = True
                                except:
                                    print("trying to reconnect to mqtt broker")
                                    attempts += 1

                plug.twoRunsBefore = plug.oneRunBefore
                plug.oneRunBefore = plug.currentRun
            finally:
                print("=============================================")

if __name__ == "__main__":
    asyncio.run(main())
