mosquitto_pub -h test.mosquitto.org -t calvin/beta/washer/test -m "On"
watch -n10 'mosquitto_pub -h test.mosquitto.org -t calvin/beta/washer/test -m "Off" && sleep 10 && mosquitto_pub -h test.mosquitto.org -t calvin/beta/washer/test -m "On"'
