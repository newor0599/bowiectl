import asyncio
from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice


class BASEUS:
    def __init__(self):
        self.address: str = None
        self.client: BleakClient = None
        self.devices: list[BLEDevice] = []
        self.data: bytearray = None
        self.verbose = True

    async def get_bowie(self) -> str:
        if None in (self.devices):
            return
        for device in self.devices:
            if "Bowie MA10 Pro" in str(device.name).strip():
                self.address = device.address
                if self.verbose:
                    print("Found {}".format(self.address))
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
            "ee684b1a-1e9b-ed3e-ee55-f894667e92ac",
            bytes.fromhex(data),
            response=True,
        )

    async def notif_handler(self, _, data) -> None:
        self.data = data

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
        await self.client.start_notify(
            "654b749c-e37f-ae1f-ebab-40ca133e3690", self.notif_handler
        )
        if self.verbose:
            print("Notification receiver started")

    async def init(self):
        await self.update_devices()
        await self.get_bowie()
        await self.connect_device()
        await self.start_notifier()


async def test():
    base = BASEUS()
    # base.verbose = False
    await base.init()
    if base.client is None:
        return
    bud_data = await base.read("ba02")
    case_data = await base.read("ba27")
    print(f"Left earbud  : {bud_data[2]}")
    print(f"Right earbud : {bud_data[4]}")
    print(f"Case         : {case_data[2]}")


if __name__ == "__main__":
    asyncio.run(test())
