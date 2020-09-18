
from pyModbusTCP.client import ModbusClient
import os
import subprocess
import threading
import socket
import time
import math

class modbusTCP_Master:
    def __init__(self, _masterDevice):
        self.socketPort = 8001 + _masterDevice["id"]
        self.host = _masterDevice["host"]
        self.port = _masterDevice["port"]
        self.data = _masterDevice["data"]
        self.waitingTime = _masterDevice["waitingTime"]

        # Create thread to print out Master Emulation
        self.OutputConsole_Thread = threading.Thread(name="Terminal", target=self.SetupOutputConsole, args=())
        self.OutputConsole_Thread.start()

        time.sleep(5) # delay sending of message making sure port is listening

        # Socket to comunicate to other terminal
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('localhost', self.socketPort ))            

        # Setup Master
        self.SetupMasterDevice();
        # Start Emulation
        self.loopFlag = True
        self.MasterEmulation_Thread = threading.Thread(name="Emulation", target=self.StartSimulation, args=())
        self.MasterEmulation_Thread.start()

        # General counter
        self.counter = 0

    def SetupOutputConsole(self):
        monitorshell = subprocess.Popen("x-terminal-emulator --command=\"nc -l " + str(self.socketPort) + "\"",shell=True)                

    def SetupMasterDevice(self):
        self.device = ModbusClient()
        # uncomment this line to see debug message
        #self.device.debug(True)
        # define modbus server host, port
        self.device.host(self.host)
        self.device.port(self.port)
        self.device.unit_id(1)

    def StartSimulation(self):

        #os.system("x-terminal-emulator -e /bin/zsh")
        
        startMessage =                "   Modbus Master Emulator   \n"
        startMessage = startMessage + " -------------------------- \n"
        startMessage = startMessage + "\n"

        self.sock.send(startMessage.encode())

        toggle = True
        while self.loopFlag:
            # open or reconnect TCP to server
            if not self.device.is_open():
                if not self.device.open():
                    errorMessage = "[ERROR] Unable to connect to "+ self.host + ":" + str(self.port) + "\n"
                    self.sock.send(errorMessage.encode())
            
            if self.device.is_open():

                # Go through data and act correspondingly
                for data_point in self.data:
                    addr = data_point["address"]
                    if data_point["type"] == "coil":
                        is_ok = self.device.write_single_coil(addr, toggle)
                        self.PrintInfo(is_ok, data_point["type"], addr, toggle)

                    elif data_point["type"] == "register":
                        # Calculate value to send based on the function selected in the json file
                        dataToSend = self.CalculateNextValue(data_point["value_function"])
                        # Send value 
                        is_ok = self.device.write_single_register(addr, dataToSend)
                        self.PrintInfo(is_ok, data_point["type"], addr, dataToSend)

                toggle = not toggle
                # sleep Xs before next polling
                waitMessage = "\n [ Waiting " + str(self.waitingTime) + " seconds until next write ] \n"
                waitMessage = waitMessage + "\n"
                self.sock.send(waitMessage.encode())

                time.sleep(self.waitingTime)


        endMessage = "\n --- END OF MASTER EMULATOR IN 5s --- \n"
        endMessage = endMessage + "\n"
        self.sock.send(endMessage.encode())
        time.sleep(5)
        self.sock.close()

    def CalculateNextValue(self, value_function):
        x = int(round(time.time() * 1000))
        self.counter = self.counter + 1
        if value_function == "sin":
            # Calculate sin(x)
            result = math.sin(x)
            # Normalize the value so it is an int
            return int(result * 1000) + 1000
        elif value_function == "cosin":
            # Calculate cosin(x)
            result = math.cos(x)
            # Normalize the value so it is an int
            return int(result * 1000) + 1000
        elif value_function == "log":            
            # Calculate log10(x)
            return int(math.log10(self.counter ))
        else:
            # Calculate f(x) = x*2 [0 - 10000]            
            result = (self.counter) * 2
            if result > 10000:
                result = 0
            return result

    def PrintInfo(self, is_ok, type, address, value):
        messageToSend = ""
        if is_ok:    
            messageToSend = " ---> " + str(self.host) + " @ Port: " + str(self.port) + " - writes - " + str(value) + " ==> " + type + " at address: " + str(address) + "\n"
        else:
            messageToSend = " ---> " + str(self.host) + " @ Port: " + str(self.port) + " - could NOT write - " + str(value) + " ==> " + type + " at address: " + str(address) + "\n"

        self.sock.send(messageToSend.encode())

    def StopEmulation(self):
        self.loopFlag = False