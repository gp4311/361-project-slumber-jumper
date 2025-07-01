import asyncio
from bleak import BleakScanner, BleakClient

SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"

async def notification_handler(sender, data):
    print(f"Received from {sender}: {data.decode()}")

async def main():
    print("Scanning for PiBLE...")
    devices = await BleakScanner.discover(timeout=10)

    pi_device = next((d for d in devices if d.name == "PiBLE"), None)
    if not pi_device:
        print("PiBLE not found. Is it powered and running?")
        return

    async with BleakClient(pi_device.address) as client:
        print(f"Connected to {pi_device.address}")
        await client.start_notify(CHAR_UUID, notification_handler)
        print("Receiving notifications... Press Ctrl+C to exit")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await client.stop_notify(CHAR_UUID)
            print("Stopped")

asyncio.run(main())
