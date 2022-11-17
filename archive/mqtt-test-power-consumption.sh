#!/usr/bin/bash
while getopts i:d: flag; do
  case "${flag}" in
  i) KASA_CURRENT_IP=${OPTARG} ;;
  d) DEBUG_MODE=${OPTARG} ;; #unused
  esac
done

KASA_SCRIPT_START_TIME=$(date +%s.%N)

if [ -v KASA_CURRENT_IP ]; then
  echo "Attempting to connect to $KASA_CURRENT_IP..."

  echo "You won't see any output in the terminal, but check the testKasaOutput.txt file for results as it progresses. When you're ready to stop this script, press Ctrl+C at any time."
  echo "Time,Power" >>testKasaOutput.csv

  plugName=$(kasa --type plug --host $KASA_CURRENT_IP sysinfo | grep alias | awk '{print $2}' | tr -d "'" | tr -d ",")

  while true; do
    # currentTime=$(date +%s.%N)
    currentTime=$(echo "$(date +%s.%N) $KASA_SCRIPT_START_TIME" | awk '{print $1 - $2}')
    echo -n "$currentTime," >>testKasaOutput.csv

    # kasa --type plug --host $KASA_CURRENT_IP emeter | grep Power || (echo -e "\e[31mConnection lost! Check the testKasaOutput.txt file for results up to this point. \e[0m" && exit 1)
    power=$(kasa --type plug --host $KASA_CURRENT_IP emeter | grep Power | awk '{print $2}' || echo -e "\e[31mConnection lost! Check the testKasaOutput.txt file for results up to this point. \e[0m")
    echo $power >>testKasaOutput.csv

    # publishing to mqtt broker
    # mosquitto_pub -h test.mosquitto.org -t washer -m "Time: $currentTime, Power: $power"

    echo "publishing to $plugName"
    if (($(echo "$power 9" | awk '{print ($1 > $2)}'))); then
      mosquitto_pub -h test.mosquitto.org -t $plugName -m "On" || (echo -e "\e[31mERROR: $KASA_CURRENT_IP failed at $(date +%s.%N) \e[0m" && exit 1)
      # echo "ON"
    else
      mosquitto_pub -h test.mosquitto.org -t $plugName -m "Off" || (echo -e "\e[31mERROR: $KASA_CURRENT_IP failed at $(date +%s.%N) \e[0m" && exit 1)
      # echo "OFF"
    fi

    # sleep 0.1
  done
else
  clear
  echo "You need to specify your plug's IP with the command:"
  echo -e "\e[34m./filepath/flags.sh -i [your plug's IP without brackets]\e[0m"
  echo ""
  echo -e "Not sure what the IP is? Set up your plug with the smartphone app then run \e[32mkasa discover\e[0m in a terminal."
fi
