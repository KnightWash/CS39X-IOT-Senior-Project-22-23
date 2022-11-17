import asyncio
from kasa import SmartPlug

async def main():
    plug_1 = SmartPlug("153.106.213.230")

    await plug_1.update() # Request the update
    print(plug_1.alias) # Print out the alias
    print(plug_1.emeter_realtime) # Print out current emeter status

    await plug_1.turn_off() # Turn the device off
    await plug_1.turn_on() # Turn the device on

if __name__ == "__main__":
    asyncio.run(main())