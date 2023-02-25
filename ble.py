from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
import sys
import asyncio
from bleak import BleakScanner
from threading import Thread
from itertools import count, takewhile
from typing import Iterator
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from queue import Queue
from time import sleep
from PyQt5.QtGui import QPixmap


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('ble.ui', self)
        self.UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
        self.UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
        self.UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E" 
        self.devices = None
        self.doneFlag = False
        self.target_device = None
        self.client = None
        self.BLEOut = None
        self.BLEOut_old = None
        self.triangle_green_up = QPixmap("assets/triangle_green_up.png")
        self.triangle_gray_up = QPixmap("assets/triangle_gray_up.png")
        self.triangle_green_right = QPixmap("assets/triangle_green_right.png")
        self.triangle_gray_right = QPixmap("assets/triangle_gray_right.png")
        self.triangle_green_left = QPixmap("assets/triangle_green_left.png")
        self.triangle_gray_left = QPixmap("assets/triangle_gray_left.png")
        self.triangle_green_down = QPixmap("assets/triangle_green_down.png")
        self.triangle_gray_down = QPixmap("assets/triangle_gray_down.png")
        self.lblConStats.setText("Disconnected")
        self.lblConStats.setStyleSheet("background-color: red")
        self.data_queue = Queue()
        self.btnRefresh.clicked.connect(self.refresh)
        self.btnConnect.clicked.connect(self.connect)
        self.btnDisconnect.clicked.connect(self.disconnect)
        Thread(target=self.controlThread, args=()).start()
        self.show()

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(
                self, 'Quit?',
                'Are you sure you want to quit?',
                QtWidgets.QMessageBox.Yes , QtWidgets.QMessageBox.No
            )

        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
            # To kill two threads and disconnet from BLE.
            self.data_queue.put("q")    
            self.BLEOut = "q"
        else:
            event.ignore()
        
    def controlThread(self) -> None:
        while True:
            if self.BLEOut is not None and self.BLEOut != self.BLEOut_old:
                if self.BLEOut == "q":
                    break
                self.data_queue.put(self.BLEOut)
                self.BLEOut_old = self.BLEOut
            sleep(0.01)                        

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_D:
            print("Right")
            self.BLEOut = "r3"
            self.img_right.setPixmap(self.triangle_green_right)
        elif event.key() == Qt.Key_A:
            print("Left")
            self.BLEOut = "r2"
            self.img_left.setPixmap(self.triangle_green_left)
        elif event.key() == Qt.Key_W:
            print("Up")
            self.BLEOut = "r0"
            self.img_up.setPixmap(self.triangle_green_up)
        elif event.key() == Qt.Key_S:
            print("Down")
            self.BLEOut = "r1"
            self.img_down.setPixmap(self.triangle_green_down)


    def keyReleaseEvent(self, event) -> None:
        if not event.isAutoRepeat():    
            if event.key() == Qt.Key_D:
                print("Right Released")
                self.img_right.setPixmap(self.triangle_gray_right)
            elif event.key() == Qt.Key_A:
                print("Left Released")
                self.img_left.setPixmap(self.triangle_gray_left)
            elif event.key() == Qt.Key_W:
                print("Up Released")
                self.img_up.setPixmap(self.triangle_gray_up)
            elif event.key() == Qt.Key_S:
                print("Down Released")
                self.img_down.setPixmap(self.triangle_gray_down)
            self.BLEOut = "r4"
        
    async def scanner(self) -> None:
        self.devices = await BleakScanner.discover()
        for d in self.devices:
            print(d)
        self.doneFlag = True

    def handle_disconnect(self, _: BleakClient) -> None:
        print("Device was disconnected, goodbye.")
        #for task in asyncio.all_tasks():
        #    task.cancel()
    
    def handle_rx(self, _: BleakGATTCharacteristic, data: bytearray) -> None:
        print("received:", data)

    def sliced(self, data: bytes, n: int) -> Iterator[bytes]:
        return takewhile(len, (data[i : i + n] for i in count(0, n)))

    async def connecter(self) -> None:
        async with BleakClient(self.target_device, disconnected_callback=self.handle_disconnect) as self.client:
            await self.client.start_notify(self.UART_TX_CHAR_UUID, self.handle_rx)

            if self.client.is_connected:
                self.lblConStats.setText("Connected")
                self.lblConStats.setStyleSheet("background-color: lightgreen")
                self.lblConStats.adjustSize()

            nus = self.client.services.get_service(self.UART_SERVICE_UUID)
            rx_char = nus.get_characteristic(self.UART_RX_CHAR_UUID)

            while True:
                data = self.data_queue.get()
                if data is not None:
                    if data == "q":
                        print("closing...")
                        await self.client.disconnect()
                        print("closed...")
                        if not self.client.is_connected:
                            self.lblConStats.setText("Disconnected")
                            self.lblConStats.setStyleSheet("background-color: red")
                            self.lblConStats.adjustSize()
                        break
                    else:    
                        for s in self.sliced(data, rx_char.max_write_without_response_size):
                            await self.client.write_gatt_char(rx_char, s.encode())
                        print("send: ", data)

    def apiMethod(self, selector) -> None:
        if selector == "scan":
            asyncio.run(self.scanner())
        elif selector == "connect":
            asyncio.run(self.connecter())
        
    def refresh(self) -> None:
        self.btnRefresh.setEnabled(False)
        Thread(target=self.apiMethod, args=("scan",)).start()
        while not self.doneFlag:
            QtWidgets.QApplication.processEvents()
        self.cmbBles.clear()
        for device in self.devices:
            self.cmbBles.addItem(device.name) 
        self.btnRefresh.setEnabled(True)
        
    def connect(self) -> None:
        target_device_name = self.cmbBles.currentText()
        for device in self.devices:
            if device.name == target_device_name:
                self.target_device = device
        Thread(target=self.apiMethod, args=("connect",)).start()

    def disconnect(self) -> None:
        self.BLEOut = "q"
        self.data_queue.put("q")

if __name__ == "__main__":    
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    sys.exit(app.exec_())