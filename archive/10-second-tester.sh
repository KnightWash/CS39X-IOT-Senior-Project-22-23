watch -n10 'mosquitto_pub -h test.mosquitto.org -t calvin/beta/washer/test -m "On" && sleep 10 && mosquitto_pub -h test.mosquitto.org -t calvin/beta/washer/test -m "Off"'
