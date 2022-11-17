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

    plugAddresses = open("addresses.txt", "r")
    plugList = plugAddresses.readlines()
    startTime = time.time()
    plugAddresses.close()


    while(True):
        print("hello world")

        for plug in plugList:
            log_file = open("testKasaOutput.csv", "a+")

            currentPlug = SmartPlug(plug)
            # currentTime=$(echo "$(date +%s.%N) $KASA_SCRIPT_START_TIME" | awk '{print $1 - $2}')
            currentTime = (startTime - time.time())

            # echo -n "$currentTime," >>testKasaOutput.csv
            csv.writer(log_file).writerow(currentTime)

            # # kasa --type plug --host $KASA_CURRENT_IP emeter | grep Power || (echo -e "\e[31mConnection lost! Check the testKasaOutput.txt file for results up to this point. \e[0m" && exit 1)
            # power=$(kasa --type plug --host $KASA_CURRENT_IP emeter | grep Power | awk '{print $2}' || echo -e "\e[31mConnection lost! Check the testKasaOutput.txt file for results up to this point. \e[0m")
            # echo $power >>testKasaOutput.csv
            await plug.update()  # Request an update
            print(plug.emeter_realtime)


            # # publishing to mqtt broker
            # # mosquitto_pub -h test.mosquitto.org -t washer -m "Time: $currentTime, Power: $power"
            client = mqtt.Client("Beta")
            client.connect("test.mosquitto.org")
            client.publish(currentPlug.alias, "testing")
            

            # echo "publishing to $plugName"
            # if (($(echo "$power 9" | awk '{print ($1 > $2)}'))); then
            #   mosquitto_pub -h test.mosquitto.org -t $plugName -m "On" || (echo -e "\e[31mERROR: $KASA_CURRENT_IP failed at $(date +%s.%N) \e[0m" && exit 1)
            #   # echo "ON"
            # else
            #   mosquitto_pub -h test.mosquitto.org -t $plugName -m "Off" || (echo -e "\e[31mERROR: $KASA_CURRENT_IP failed at $(date +%s.%N) \e[0m" && exit 1)
            #   # echo "OFF"
            # fi
        
            #don't put anything after this line in the for loop - we need it to save every plug's ping data
            log_file.close()

if __name__ == "__main__":
    asyncio.run(main())
