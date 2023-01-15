#!/usr/bin/bash

KASA_SCRIPT_START_TIME=$(date +%s.%N)

if [ -v KASA_CURRENT_IP ]; then
  echo "Attempting to connect to $KASA_CURRENT_IP..."

  echo "You won't see any output in the terminal, but check the testKasaOutput.txt file for results as it progresses. When you're ready to stop this script, press Ctrl+C at any time."
  while true; do
    # kasa --type plug --host $KASA_CURRENT_IP emeter | grep Power || (echo -e "\e[31mConnection lost! Check the testKasaOutput.txt file for results up to this point. \e[0m" && exit 1)
    kasa --type plug --host $KASA_CURRENT_IP emeter | grep Power >>testKasaOutput.txt || echo -e "\e[31mConnection lost! Check the testKasaOutput.txt file for results up to this point. \e[0m"

    # currentTime=$(date +%s.%N)
    echo "$(date +%s.%N) $KASA_SCRIPT_START_TIME" | awk '{print $1 - $2}' >>testKasaOutput.txt

    # sleep 0.1
  done

else
  clear
  echo "You need to specify your plug's IP with the command:"
  echo -e "\e[34mexport KASA_CURRENT_IP=[your plug's IP without brackets]\e[0m"
  echo ""
  echo -e "Not sure what the IP is? Set up your plug with the smartphone app then run \e[32mkasa discover\e[0m in a terminal."
fi
