import asyncio
from bleak import BleakScanner
from itertools import count, takewhile
from typing import Iterator
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from queue import Queue

class BLE:
    def __init__(self) -> None:
        self.devices = None
        self.target_device = None
        self.scan_done = False
        self.is_connected = False
        self.data_queue = Queue()
        self.UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
        self.UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
        self.UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E" 
    
    def handle_rx(self, _: BleakGATTCharacteristic, data: bytearray) -> None:
        print("received:", data)

    def sliced(self, data: bytes, n: int) -> Iterator[bytes]:
        return takewhile(len, (data[i : i + n] for i in count(0, n)))

    def handle_disconnect(self, _: BleakClient) -> None:
        print("Device was disconnected, goodbye.")
        self.is_connected = False
    
    def isScanDone(self) -> bool:
        return self.scan_done

    def isConnected(self) -> bool:
        return self.is_connected

    def scanDevices(self) -> None:
        asyncio.run(self.scanner())
    
    def connectToDevice(self, device) -> None:
        self.target_device = device
        print(self.target_device)
        asyncio.run(self.setConnection())
    
    def pushQueue(self, data) -> None:
        self.data_queue.put(data)

    def getDeviceList(self) -> list:
        return self.devices

    async def commLoop(self, rx_char) -> None:
        while True:
            data = self.data_queue.get()
            if data is not None:
                if data == "q":
                    print("closing...")
                    await self.client.disconnect()
                    print("closed...")
                    break
                else:    
                    for s in self.sliced(data, rx_char.max_write_without_response_size):
                        await self.client.write_gatt_char(rx_char, s.encode())
                    print("send: ", data)

    async def scanner(self) -> None:
        self.devices = await BleakScanner.discover()
        for d in self.devices:
            print(d)
        self.scan_done = True

    async def setConnection(self) -> None:
        async with BleakClient(self.target_device, disconnected_callback=self.handle_disconnect) as self.client:
            await self.client.start_notify(self.UART_TX_CHAR_UUID, self.handle_rx)

            self.is_connected = True
            nus = self.client.services.get_service(self.UART_SERVICE_UUID)
            rx_char = nus.get_characteristic(self.UART_RX_CHAR_UUID)
            await self.commLoop(rx_char = rx_char)