import asyncio
from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice

# UUID
# Read  : 654b749c-e37f-ae1f-ebab-40ca133e3690
# Write : ee684b1a-1e9b-ed3e-ee55-f894667e92ac


class BASEUS:
    def __init__(self):
        self.address: str = None
        self.client: BleakClient = None
        self.devices: list[BLEDevice] = []
        self.data: bytearray = None
        self.verbose = False
        self.code_write = "ee684b1a-1e9b-ed3e-ee55-f894667e92ac"
        self.code_read = "654b749c-e37f-ae1f-ebab-40ca133e3690"

    async def get_bowie(self) -> str:
        if None in (self.devices):
            return
        for device in self.devices:
            if "Bowie MA10 Pro" in str(device.name).strip():
                self.address = device.address
                if self.verbose:
                    print(f"Found {self.address}")
                return device.address
        return None

    async def update_devices(self) -> None:
        if self.verbose:
            print("Updating device list")
        self.devices = await BleakScanner.discover(0.5)
        if self.verbose:
            print("Device list updated")

    async def connect_device(self) -> None:
        if self.address is None:
            print("No address!")
            return
        if self.client is None:
            self.client = BleakClient(self.address)
        if self.verbose:
            print("Connecting device")
        await self.client.connect()
        if self.verbose:
            print("Device connected")

    async def write(self, data: str = None) -> None:
        if None in (self.client, data):
            return
        await self.client.write_gatt_char(
            self.code_write,
            bytes.fromhex(data),
            response=True,
        )

    async def notif_handler(self, _, data) -> None:
        self.data = data
        data_str = data.hex()
        if data_str == "aa123c721867aa4100000000000001":
            print("Left earbud was disconnected")
            return
        if data_str == "aa123c721867aa4100000000000000":
            print("Right earbud was disconnected")
            return
        if data_str == "aa025a005a01":
            print("Both earbud are connected")
            return
        if self.verbose:
            print(data.hex())

    async def read(self, data: str = None) -> bytearray:
        self.data = None
        await self.write(data)
        if self.verbose:
            print("Awaiting data")
        for _ in range(10):
            if self.data is not None:
                return self.data
            if self.verbose:
                print(".")
            await asyncio.sleep(0.1)

    async def start_notifier(self):
        if self.client is None:
            return
        if self.verbose:
            print("Starting notification receiver")
        await self.client.start_notify(self.code_read, self.notif_handler)
        if self.verbose:
            print("Notification receiver started")

    async def init(self):
        await self.update_devices()
        await self.get_bowie()
        await self.connect_device()
        await self.start_notifier()

    async def exit(self):
        if self.client is None:
            return
        await self.client.disconnect()

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
                if self.verbose:
                    print("[ERROR] Out of range")
                return
            code = "ba3400ff" if n == 0 else f"ba3401{n:02x}"
        else:
            if self.verbose:
                print("[ERROR] Invalid input")
            return

        await self.write(code)

    # Left, Right, Case
    async def get_battery(self) -> list[int]:
        if self.client is None:
            return
        buds = await self.read("ba02")  # Buds battery
        case = await self.read("ba27")  # Case Battery
        if None in (buds, case):
            return
        return (buds[2], case[2], buds[4])


async def test():
    base = BASEUS()
    base.verbose = True
    await base.init()
    if base.client is None:
        return
    bud_data = await base.read("ba02")
    case_data = await base.read("ba27")
    print(f"Left earbud  : {bud_data[2]}")
    print(f"Right earbud : {bud_data[4]}")
    print(f"Case         : {case_data[2]}")
    while True:
        if await asyncio.to_thread(input, "Bobby ") == "exit":
            break
    await base.exit()


if __name__ == "__main__":
    asyncio.run(test())
