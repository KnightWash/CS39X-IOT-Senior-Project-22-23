watch -n30 'mosquitto_pub -h test.mosquitto.org -t calvin/beta/washer/test -m "On" && sleep 30 && mosquitto_pub -h test.mosquitto.org -t calvin/beta/washer/test -m "Off"'
