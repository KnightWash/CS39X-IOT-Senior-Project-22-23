mosquitto_pub -h test.mosquitto.org -t calvin/test/dryer/location -m "On"
watch -n10 'mosquitto_pub -h test.mosquitto.org -t calvin/test/dryer/location -m "Off" && sleep 10 && mosquitto_pub -h test.mosquitto.org -t calvin/test/dryer/location -m "On"'
