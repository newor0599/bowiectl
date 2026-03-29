import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice


class BaseusError(RuntimeError):
    """Base exception for Baseus API errors."""


class DeviceNotConnectedError(BaseusError):
    """Raised when an operation requires an active BLE connection."""


class DeviceNotFoundError(BaseusError):
    """Raised when no compatible Baseus device is found."""


@dataclass(frozen=True)
class BatteryStatus:
    left: int
    case: int
    right: int


@dataclass(frozen=True)
class ANC_PRESETS:
    general: str = "ba340165"
    on: str = "ba340165"
    indoor: str = "ba340166"
    outdoor: str = "ba340167"
    off: str = "ba3400ff"
    transparent: str = "ba3402ff"


class BaseusClient:
    """High-level API for Baseus Bowie MA10 Pro earbuds.

    This class is intended to be imported and used from other Python modules.
    """

    def __init__(
        self,
        *,
        verbose: bool = False,
    ):
        # UUIDs
        self.verbose = verbose
        self.write_char_uuid = "654b749c-e37f-ae1f-ebab-40ca133e3690"
        self.write_char_uuid = "ee684b1a-1e9b-ed3e-ee55-f894667e92ac"
        self.device_name = "Bowie MA10 Pro"

        self.address: str | None = None
        self.client: BleakClient | None = None
        self.devices: list[BLEDevice] = []

        self._last_data: bytearray | None = None
        self._response_event = asyncio.Event()
        self._notification_callbacks: list[
            Callable[[bytes], Awaitable[None] | None]
        ] = []
        self._notifier_started = False

    async def __aenter__(self) -> "BaseusClient":
        await self.init()
        return self

    async def __aexit__(self, *_):
        await self.exit()

    def add_notification_callback(
        self,
        callback: Callable[[bytes], Awaitable[None] | None],
    ) -> None:
        """Register a callback executed for each incoming BLE notification."""
        self._notification_callbacks.append(callback)

    async def scan(self, timeout: float = 0.5) -> list[BLEDevice]:
        """Refresh and return visible BLE devices."""
        if self.verbose:
            print("Updating device list")
        self.devices = await BleakScanner.discover(timeout)
        if self.verbose:
            print(f"Device list updated ({len(self.devices)} devices)")
        return self.devices

    async def find_device(self) -> str | None:
        """Find and remember the first matching Baseus device address."""
        for device in self.devices:
            device_name = (device.name or "").strip()
            if self.device_name in device_name:
                self.address = device.address
                if self.verbose:
                    print(f"Found {self.address}")
                return self.address
        return None

    async def ensure_connected(self) -> None:
        """Connect to the device and ensure notifications are active."""
        if self.client and self.client.is_connected:
            return

        if self.address is None:
            await self.scan()
            await self.find_device()

        if self.address is None:
            raise DeviceNotFoundError(f"No {self.device_name!r} device found")

        self.client = self.client or BleakClient(self.address)
        if self.verbose:
            print("Connecting device")
        await self.client.connect()
        if self.verbose:
            print("Device connected")
        await self.start_notifier()

    async def write_raw(self, data_hex: str) -> None:
        """Write a raw hex command to the write characteristic."""
        if not data_hex:
            raise ValueError("data_hex is required")
        await self.ensure_connected()
        if not self.client:
            raise DeviceNotConnectedError("BLE client is unavailable")

        await self.client.write_gatt_char(
            self.write_char_uuid,
            bytes.fromhex(data_hex),
            response=True,
        )

    async def _notification_handler(self, _, data: bytearray) -> None:
        self._last_data = data
        self._response_event.set()

        data_hex = data.hex()
        if data_hex == "aa123c721867aa4100000000000001":
            print("Left earbud was disconnected")
        elif data_hex == "aa123c721867aa4100000000000000":
            print("Right earbud was disconnected")
        elif data_hex == "aa025a005a01":
            print("Both earbud are connected")
        elif self.verbose:
            print(data_hex)

        for callback in self._notification_callbacks:
            result = callback(bytes(data))
            if asyncio.iscoroutine(result):
                await result

    async def read_raw(
        self, request_hex: str, timeout: float = 1.0
    ) -> bytearray | None:
        """Send a request command and wait for the next notification payload."""
        self._last_data = None
        self._response_event.clear()
        await self.write_raw(request_hex)

        if self.verbose:
            print("Awaiting data")

        try:
            await asyncio.wait_for(self._response_event.wait(), timeout=timeout)
        except TimeoutError:
            return None

        return self._last_data

    async def start_notifier(self) -> None:
        if not self.client or not self.client.is_connected:
            raise DeviceNotConnectedError("BLE client is unavailable")
        if self._notifier_started:
            return

        if self.verbose:
            print("Starting notification receiver")
        await self.client.start_notify(self.read_char_uuid, self._notification_handler)
        self._notifier_started = True
        if self.verbose:
            print("Notification receiver started")

    async def init(self) -> None:
        """Compatibility helper for older callers."""
        await self.ensure_connected()

    async def exit(self) -> None:
        if self.client and self.client.is_connected:
            await self.client.disconnect()
        self._notifier_started = False

    async def set_anc(self, value: str | int) -> None:
        """Set ANC mode using preset names or intensity values (0-10)."""
        code = _resolve_anc_command(value)
        await self.write_raw(code)

    async def anc(self, value: str | int):
        """Backward compatible alias for set_anc."""
        await self.set_anc(value)

    async def get_battery_status(self) -> BatteryStatus | None:
        """Return battery percentages for left earbud, case, and right earbud."""
        buds = await self.read_raw("ba02")
        case = await self.read_raw("ba27")
        if buds is None or case is None:
            return None
        return BatteryStatus(left=buds[2], case=case[2], right=buds[4])


def _resolve_anc_command(value: str | int) -> str:
    text = str(value).strip().lower()

    if text in ANC_PRESETS:
        return ANC_PRESETS[text]

    if text.isdigit():
        n = int(text)
        if not 0 <= n <= 10:
            raise ValueError("ANC intensity must be between 0 and 10")
        return "ba3400ff" if n == 0 else f"ba3401{n:02x}"

    raise ValueError(f"Invalid ANC value: {value!r}")


async def test():
    async with BaseusClient(verbose=True) as base:
        bud_data = await base.read_raw("ba02")
        case_data = await base.read_raw("ba27")
        if bud_data and case_data:
            print(f"Left earbud  : {bud_data[2]}")
            print(f"Right earbud : {bud_data[4]}")
            print(f"Case         : {case_data[2]}")
        while True:
            if await asyncio.to_thread(input, "Bobby ") == "exit":
                break


if __name__ == "__main__":
    asyncio.run(test())
