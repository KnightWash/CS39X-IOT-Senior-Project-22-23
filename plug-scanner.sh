File="addresses.txt"
Lines=$(cat $File)

# initial check to make sure everything's online - will fail if it can't turn ANY plug on
# unsure if this command "fails" when the plug is already on, TESTING NEEDED
for Line in $Lines; do
	kasa --type plug --host $Line on || (echo -e "\e[31mERROR: Couldn't contact the plug on $Line. Please check the list file. \e[0m" && exit 1)
done

for Line in $Lines; do
	# leave the & at the end!
	# that lets the line run in the background w/o waiting for the previous one to finish
	# we obviously don't want that...
	./mqtt-test-power-consumption.sh -i $Line &
done
