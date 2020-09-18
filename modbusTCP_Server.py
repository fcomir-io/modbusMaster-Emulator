import sys
import os
from pathlib import Path
import json
import logging
import threading
import time
import argparse
from pyModbusTCP.server import ModbusServer
from modbusTCP_Master import modbusTCP_Master
import subprocess

def CheckModbusDeviceListFile(jsonFile):
    # Check if argument is a file or a directory
    if (jsonFile.startswith('/')):
        # --> User introduced a path
        fileToCheck = Path(jsonFile)
    else:
        # --> User introduced a name of a file located in the same path
        fileToCheck = Path(os.getcwd() + "/" + jsonFile)

    # Check if file exists 
    if fileToCheck.is_file():
        # Check if file is JSON ok
        try:
            # Since we re working with python v3.5, open needs a string as argument
            json_object = json.loads(open(str(fileToCheck)).read())
        except Exception as e:
            return [2, ""]
        return [0, json_object]    
    else:
        return [1, ""]
   
def SetupModbusServerDevice(device):
    
    global arrayOfModbusServers
    global modbusDeviceList_Counter

    # Extracting information from device object
    deviceHost = device["host"]
    devicePort = device["port"]
    deviceData = device["data"]

    # parse args
    parser = argparse.ArgumentParser()
    # --- Identify argument already defined by user
    parser.add_argument('file')
    # --- Include arguments needed by ModbusServer
    parser.add_argument('-H', '--host', type=str, default=deviceHost, help='Host')
    parser.add_argument('-p', '--port', type=int, default=devicePort, help='TCP port')    
    args = parser.parse_args()
    # Start modbus server    
    try:
        # Create Modbus Server        
        server = ModbusServer(host=args.host, port=args.port, no_block=True)     
        # Start Modbus Server
        server.start()
        # If everything ok, create an object ID for the server and append it into array        
        temp = {
            "id" : modbusDeviceList_Counter,
            "host" : str(deviceHost),
            "port" :  str(devicePort),
            "data" : deviceData,
            "waitingTime" :  device["waitingTime"],
            "object" : server
        }
        arrayOfModbusServers.append(temp)
        modbusDeviceList_Counter = modbusDeviceList_Counter + 1
        # Info message for the user
        print('    [OK] Started Modbus Server on port: ' + str(devicePort))
    except Exception as e:
        print(" [ERROR] Problems starting Modbus Server on " + str(deviceHost) + " - " + str(devicePort) + " ---> " + str(e))
        # Update Server Counter
        modbusDeviceList_Counter = modbusDeviceList_Counter + 1           

def PrintMenu():    
    print(" " + 71*"*")
    print(" * - Enter 'status' to check the state of the servers ")
    print(" * - Enter 'stop {server ID}' to stop a given server ")
    print(" * - Enter 'start {server ID}' to re-start a given server ")
    print(" * - Enter 'exit' to stop all running servers and temrinate application ")
    print(" " + 71*"*")
    
if __name__ == '__main__':

    # Array to store started servers
    arrayOfModbusServers = [];
    modbusDeviceList_Counter = 0 

    # Check list of Modbus Devices from file
    result = CheckModbusDeviceListFile(sys.argv[1])

    ### modbusDevicesList is an array of two values:
    #   - Positon 0 ==> Error code. 
    #     * '0' ==> No error
    #     * '1' ==> File not found
    #     * '2' ==> Not JSON format
    #   - Positon 1 ==> JSON data with Modbus Devices List or empty string if there was an error
    ############################################################################################
       
    error = result[0]    
    modbusDevicesList = result[1]
    amountOfServersToStart = len(modbusDevicesList)    

    if (error == 0): 
        for item in modbusDevicesList:              
            #print(f' Configuring: {item} - Type: {type(item)}')
            #print(f' Configuring: {item["host"]} : Type: {type(item["host"])} - {item["port"]} : Type: {type(item["port"])}')
            logging.info("\nMain    : creating port for device")
            #x = threading.Thread(target=SetupModbusServerDevice, args=(item["host"], item["port"], item["data"], ))
            x = threading.Thread(target=SetupModbusServerDevice, args=(item, ))
            logging.info("Main    : just about to start the thread")
            x.start()    

        # Waiting for the threads to be created ==> Sever setup
        while(amountOfServersToStart > modbusDeviceList_Counter):
            pass

        # Start Master Emulation
        for server in arrayOfModbusServers:
            # For each device, the master emulaiton will be instanciated
            emulator = modbusTCP_Master(server)
            server["emulator"] = emulator
        ####

        # Threads already created
        loop_flag = True
        # Print Menu
        PrintMenu()
        while(loop_flag):
            try: 
                # Wait for an option from the user
                enteredOption = input("\n   Enter an option to proceed: ")
                # Convert the entered string into an array of arguments
                enteredOption = enteredOption.split(' ')

                # Check first argument

                #--- STATUS
                if (enteredOption[0] == "status"):
                    print("\n ---> Status of running Modbus Servers ")
                    for server in arrayOfModbusServers:
                        status = " is running" if server["object"].is_run else " is NOT running"
                        print(" + Server [ID: " + str(server["id"]) + "] ==> " + server["host"] + " @ port: " + server["port"] + status)

                #--- STOP and START
                elif (enteredOption[0] == "stop") or (enteredOption[0] == "start"):
                    # This action requires the id of the server to stop/start
                    if (len(enteredOption) > 1) and (enteredOption[1].isdigit()):
                        serverId = int(enteredOption[1])
                        serverFoundOnList = False
                        severSelected = ""

                        # Look for server object
                        for server in arrayOfModbusServers:
                            if (serverId == server["id"]):                    
                                serverFoundOnList = True 
                                severSelected = server
                                break;

                        # Proceed with the action                
                        if serverFoundOnList:
                            try:
                                #--- STOP 
                                if (enteredOption[0] == "stop"):                     
                                    server["object"].stop()
                                    server["emulator"].StopEmulation()
                                    server["emulator"] = ""
                                    print("\n ---> Server [ID: " + str(severSelected["id"]) + "] ==> Stopped")                      
                                #--- START
                                elif (enteredOption[0] == "start"):
                                    if not server["object"].is_run:
                                        server["object"].start()
                                        emulator = modbusTCP_Master(server)
                                        server["emulator"] = emulator
                                        print("\n ---> Server [ID: " + str(severSelected["id"]) + "] ==> Re-Started")
                                    else:
                                        print("\n ---> Server [ID: " + str(severSelected["id"]) + "] is already running ")
                            except Exception as e:
                                #--- STOP 
                                if (enteredOption[0] == "stop"):  
                                    print(" ---> Server [ID: " + str(severSelected["id"]) + "] ==> Could not be stopped - " + str(e))
                                #--- START
                                elif (enteredOption[0] == "start"):
                                    print(" ---> Server [ID: " + str(severSelected["id"]) + "] ==> Could not be re-started - " + str(e))                        
                        else:
                            print(" [ERROR] Server with ID: " + str(serverId) + " ==> Not found !!! ")
                    else:
                        print(" [ERROR] Server ID needed to proceed with the action ")

                #--- MENU
                elif (enteredOption[0] == "menu"):
                    print("\n")
                    PrintMenu()

                #--- EXIT   
                elif (enteredOption[0] == "exit"):
                    print("\n ---> Servers will be stopped and programm terminated ")
                    for server in arrayOfModbusServers:
                        server["object"].stop()
                        server["emulator"].StopEmulation()
                    loop_flag = False;

            except Exception as e:
                print(e)

    else:
        if (error == 1):
            print("\n [ERROR] Entered file was not found !!! ")
        elif (error == 2):
            print("\n [ERROR] Selected file is not JSON format !!! ")
        else:
            print("\n [ERROR] Unknown !!!")

    print("\n --- End of Program --- \n")