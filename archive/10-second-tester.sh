mosquitto_pub -h test.mosquitto.org -t calvin/test/machine/location -m "On"
watch -n10 'mosquitto_pub -h test.mosquitto.org -t calvin/test/machine/location -m "Off" && sleep 10 && mosquitto_pub -h test.mosquitto.org -t calvin/test/machine/location -m "On"'
