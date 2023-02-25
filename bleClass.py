import asyncio
from bleak import BleakScanner
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from queue import Queue

class BLE:
    def __init__(self) -> None:
        self.devices = None
        self.target_device = None
        self.scan_done = False
        self.is_connected = False
        self.close_flag = False
        self.data_queue = Queue()
        self.UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
        self.UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
        self.UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E" 
    
    def handle_rx(self, _: BleakGATTCharacteristic, data: bytearray) -> None:
        print("received:", data)

    def handle_disconnect(self, _: BleakClient) -> None:
        print("Device disconnected.")
        self.is_connected = False
    
    def isScanDone(self) -> bool:
        if self.scan_done:
            self.scan_done = False
            return True
        else:
            return self.scan_done

    def isConnected(self) -> bool:
        return self.is_connected

    def scanDevices(self) -> None:
        asyncio.run(self.scanner())
    
    def connectToDevice(self, device) -> None:
        self.target_device = device
        print("Selected Device : ", self.target_device)
        asyncio.run(self.setConnection())
    
    def pushQueue(self, data) -> None:
        self.data_queue.put(data)

    def getDeviceList(self) -> list:
        return self.devices

    def disconnectFromDevice(self) -> None:
        self.data_queue.put("q")        

    async def communicationTask(self, rx_char) -> None:
        while True:
            data = self.data_queue.get()
            if data == "q":
                print("Disconnecting...")
                await self.client.disconnect()
                break
            elif data is not None:
                await self.client.write_gatt_char(rx_char, data.encode())
                print("send: ", data)

    async def scanner(self) -> None:
        self.devices = None
        self.devices = await BleakScanner.discover()
        self.scan_done = True

    async def setConnection(self) -> None:
        async with BleakClient(self.target_device, disconnected_callback=self.handle_disconnect) as self.client:
            await self.client.start_notify(self.UART_TX_CHAR_UUID, self.handle_rx)

            self.is_connected = True
            nus = self.client.services.get_service(self.UART_SERVICE_UUID)
            rx_char = nus.get_characteristic(self.UART_RX_CHAR_UUID)
            await self.communicationTask(rx_char = rx_char)