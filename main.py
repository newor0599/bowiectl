import asyncio
from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice

# UUID
# Read  : 654b749c-e37f-ae1f-ebab-40ca133e3690
# Write : ee684b1a-1e9b-ed3e-ee55-f894667e92ac


class BASEUS:
    async def init(self):
        print("[INFO] Updating bluetooth devices list")
        self.devices: list[BLEDevice] = await BleakScanner.discover(0.5)
        self.address: str = await self.get_bowie()
        if self.address == "":
            return None
        self.client = BleakClient(self.address)
        await self.client.connect()

    async def get_bowie(self) -> str:
        for device in self.devices:
            if str(device.name).find("Bowie MA10 Pro") >= 0:
                return device.address
        return ""

    async def write(self, data: str):
        await self.client.write_gatt_char(
            "ee684b1a-1e9b-ed3e-ee55-f894667e92ac",
            bytes.fromhex(data),
            response=True,
        )


"""
Command
anc {value:int,str}
*Set Active noise cancellation profile*
- 0-10 : ANC Intensity
- general
- indoor
- outdoor
- off : same as 0
- on : same as general
- transparent

quit
*Quit program*
"""


class APP:
    async def main(self):
        self.base = BASEUS()
        await self.base.init()
        if self.base.address == "":
            print("[INFO] No Baseus Bowie MA10 Pro found!")
            print("[INFO] Quitting!")
            return
        print("[INFO] Earbud found")
        await self.base.client.start_notify(
            "654b749c-e37f-ae1f-ebab-40ca133e3690", self.notif_hander
        )
        print("[INFO] Setup notification handler")
        while True:
            out = input(f"[{self.base.address}] ")
            out = out.split(" ")
            match out[0]:
                case "anc":
                    await self.anc(out[1])
                case "quit" | "exit":
                    break
                case "battery":
                    await self.base.write("ba02")  # Left Right Battery
                    await self.base.write("ba27")  # Case Battery
                case "help":
                    print("anc {value:int|str}")
                    print(" Sets ANC profile")
                    print("     0-10 : ANC Intensity")
                    print("     off : same as 0")
                    print("     on : same as 1")
                    print("     general")
                    print("     indoor")
                    print("     outdoor")
                    print("     transparent")
                    print("quit")
                    print(" quit program")
                    print("help")
                    print(" print help")
                case _:
                    print("Invalid command")
        print("[INFO] Cleaning up")
        await self.base.client.disconnect()

    async def notif_hander(self, sender, data):
        if data[0] == 170 and data[1] == 2:
            print(f"Left earbud  : {data[2]}")
            print(f"Right earbud : {data[4]}")
            return
        if data[0] == 170 and data[1] == 39:
            print(f"Case         : {data[2]}")
            return
        print(f"[NOTIF] {sender} -> {data.hex()}\n")

    async def anc(self, value: str):
        presets = {
            "general": "ba340165",
            "on": "ba340165",
            "indoor": "ba340166",
            "outdoor": "ba340167",
            "off": "ba3400ff",
            "transparent": "ba3402ff",
        }

        if value in presets:
            code = presets[value]
        elif value.isdigit():
            n = int(value)
            if not 0 <= n <= 10:
                print("[ERROR] Out of range")
                return
            code = "ba3400ff" if n == 0 else f"ba3401{n:02x}"
        else:
            print("[ERROR] Invalid input")
            return

        await self.base.write(code)


if __name__ == "__main__":
    asyncio.run(APP().main())
