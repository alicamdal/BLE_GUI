from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
from threading import Thread
from queue import Queue
from time import sleep
from PyQt5.QtGui import QPixmap
from bleClass import BLE

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('ble.ui', self)
        self.ble = BLE()
        self.devices = None
        self.target_device = None
        self.close_flag = False
        self.BLEOut = None
        self.BLEOut_old = None
        self.pixMaps = {
            "gray_up"     : QPixmap("assets/triangle_gray_up.png"),
            "green_up"    : QPixmap("assets/triangle_green_up.png"),
            "gray_down"   : QPixmap("assets/triangle_gray_down.png"),
            "green_down"  : QPixmap("assets/triangle_green_down.png"),
            "gray_right"  : QPixmap("assets/triangle_gray_right.png"),
            "green_right" : QPixmap("assets/triangle_green_right.png"),
            "gray_left"   : QPixmap("assets/triangle_gray_left.png"),
            "green_left"  : QPixmap("assets/triangle_green_left.png")
        }
        self.lblConStats.setText("Disconnected")
        self.lblConStats.setStyleSheet("background-color: red")
        self.btnRefresh.clicked.connect(self.refresh)
        self.btnConnect.clicked.connect(self.connect)
        self.btnDisconnect.clicked.connect(self.disconnect)
        self.createThread(target_func = self.controlThread)
        self.createThread(target_func = self.checkConnection)
        self.show()

    def checkConnection(self) -> None:
        while True:
            if self.close_flag:
                break
            else:
                if self.ble.isConnected():
                    self.lblConStats.setText("Connected")
                    self.lblConStats.setStyleSheet("background-color: lightgreen")
                    self.lblConStats.adjustSize()
                else:
                    self.lblConStats.setText("Disconnected")
                    self.lblConStats.setStyleSheet("background-color: red")
                    self.lblConStats.adjustSize()
            sleep(0.1)
    
    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(
                self, 'Quit?',
                'Are you sure you want to quit?',
                QtWidgets.QMessageBox.Yes , QtWidgets.QMessageBox.No
            )

        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
            # To kill two threads and disconnet from BLE.
            self.disconnect()
            self.close_flag = True
        else:
            event.ignore()
        
    def controlThread(self) -> None:
        while True:
            if self.BLEOut is not None and self.BLEOut != self.BLEOut_old:
                if self.BLEOut == "q":
                    break
                self.ble.pushQueue(self.BLEOut)
                self.BLEOut_old = self.BLEOut
            sleep(0.01)                        

    def keyPressEvent(self, event) -> None:
        if self.ble.isConnected():    
            if event.key() == Qt.Key_D:
                print("Right")
                self.BLEOut = "r3"
                self.img_right.setPixmap(self.pixMaps["green_right"])
            elif event.key() == Qt.Key_A:
                print("Left")
                self.BLEOut = "r2"
                self.img_left.setPixmap(self.pixMaps["green_left"])
            elif event.key() == Qt.Key_W:
                print("Up")
                self.BLEOut = "r0"
                self.img_up.setPixmap(self.pixMaps["green_up"])
            elif event.key() == Qt.Key_S:
                print("Down")
                self.BLEOut = "r1"
                self.img_down.setPixmap(self.pixMaps["green_down"])

    def keyReleaseEvent(self, event) -> None:
        if not event.isAutoRepeat() and self.ble.isConnected():    
            if event.key() == Qt.Key_D:
                print("Right Released")
                self.img_right.setPixmap(self.pixMaps["gray_right"])
            elif event.key() == Qt.Key_A:
                print("Left Released")
                self.img_left.setPixmap(self.pixMaps["gray_left"])
            elif event.key() == Qt.Key_W:
                print("Up Released")
                self.img_up.setPixmap(self.pixMaps["gray_up"])
            elif event.key() == Qt.Key_S:
                print("Down Released")
                self.img_down.setPixmap(self.pixMaps["gray_down"])
            self.BLEOut = "r4"
        
    def createThread(self, **kwargs) -> None:
        try:
            Thread(target = kwargs["target_func"], args = (kwargs["args"], )).start()
        except KeyError:
            Thread(target = kwargs["target_func"], args=()).start()

    def setComboBox(self) -> None:
        self.cmbBles.clear()
        for device in self.devices:
            self.cmbBles.addItem(device.name) 

    def refresh(self) -> None:
        self.btnRefresh.setEnabled(False)
        self.createThread(target_func = self.ble.scanDevices)

        while not self.ble.isScanDone():
            QtWidgets.QApplication.processEvents()

        self.devices = self.ble.getDeviceList()
        self.setComboBox()
        self.btnRefresh.setEnabled(True)
        
    def connect(self) -> None:
        target_device_name = self.cmbBles.currentText()
        for device in self.devices:
            if device.name == target_device_name:
                self.target_device = device
        self.createThread(target_func = self.ble.connectToDevice, args = self.target_device)

    def disconnect(self) -> None:
        self.BLEOut = "q"
        self.ble.pushQueue("q")
