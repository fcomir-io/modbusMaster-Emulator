import sys
from modbusTCP_Slave import modbusTCP_Slave

if __name__ == "__main__":

    # Instantiate a Modbus Slave object
    resultMode = int(sys.argv[2])
    slave = modbusTCP_Slave(sys.argv[1], resultMode)
    # Setup Polling Process
    status = slave.SetupPollingProcess()

    # Check if Polling Process was initiated correctly
    if status == 0:
        # --> Slave can poll data from Master

        startMessage = "\n   Polling Data from Device   \n"
        startMessage = startMessage + " ---------------------------- \n"    
        print(startMessage)

        # Start Polling Loop        
        main_loop_flag = True
        while main_loop_flag:            
            
            # Get latest data from master
            result = slave.PollDataFromDevice()

            # Check if there is an error
            if result == -1:
                # -->  There is no Server on the other side or the connection is not possible 
                print("[ERROR] TCP Server could not be opened - ", result, " [", type(result), "]")
            else:

                ### Process Result depending on Result Mode set by execution
                #   RESULT_MODE__RETURN_ALL_VALUES__RAW ==> 0
                #   RESULT_MODE__RETURN_ALL_VALUES__FORMATTED ==> 0
                #   RESULT_MODE__RETURN_ONLY_NEW_VALUES__RAW ==> 0
                #   RESULT_MODE__RETURN_ONLY_NEW_VALUES__FORMATTED ==> 0
                ##################################################################

                if (resultMode == slave.RESULT_MODE__RETURN_ALL_VALUES__RAW):                    
                    # All data - RAW
                    if result != "":
                        print("All RAW Data: ", result)
                elif (resultMode == slave.RESULT_MODE__RETURN_ALL_VALUES__FORMATTED):
                    # All data - FORMATTED
                    if result != []:                        
                        for item in result:
                            print("All FORMATTED Data: ", item)
                elif (resultMode == slave.RESULT_MODE__RETURN_ONLY_NEW_VALUES__RAW):
                    # Only NEW data - RAW
                    if result != "":
                        print("Only NEW Data - RAW: ", result)
                elif (resultMode == slave.RESULT_MODE__RETURN_ONLY_NEW_VALUES__FORMATTED):
                    # Only NEW data - FORMATTED
                    if result != []:
                        for item in result:
                            print("Only NEW Data - FORMATTED: ", item)
                else:
                    if result != "" and result != []:
                        print("Unknown Result Mode: ", result)            
        
        # Out of the while
        client.close()
    else:
        # --> Polling process was not initiated correctly

        ### Possible errors
        #   - '1' ==> File not found
        #   - '2' ==> Not JSON format
        #############################################################################################
        print("Status: ", status)    

    print("\n --- END OF CLIENT --- \n")
    

'''
    def ProcessNewValues(self, newValues):

        # Prepare timestamp
        temp = datetime.datetime.now()
        x = temp.strftime("%x")
        y = temp.strftime("%X")
        z = temp.strftime("%f")
        timestamp = "[ " + x + " @ " + y + " - " + z[:3] + " ]"

        for data_point in newValues:
            # Prepare value
            value = str(data_point["value"][0]).rjust(5)

            # Print out information
            print(
                str(timestamp) 
                + " ---> "
                + str(self.modbusServer_Information["host"])
                + " @ Port: "
                + str(self.modbusServer_Information["port"])
                + " ==> Value: "
                + value
                + " from "
                + (data_point["type"]).rjust(8)
                + " at address: "
                + str(data_point["address"])
                + " }"
            )

            # Store data in Database
            #database_handler.Insert_Data(timestamp, value)

    def PrepareDataOutNewValues(self, lastPolling, currentValues):

        # Prepare timestamp
        temp = datetime.datetime.now()
        x = temp.strftime("%x")
        y = temp.strftime("%X")
        z = temp.strftime("%f")
        timestamp = "[ " + x + " @ " + y + " - " + z[:3] + " ]"

        for current_DP in currentValues:
            # Check if the value changed
            for last_DP in lastPolling:            
                if (
                    (last_DP["type"] == current_DP["type"])
                    and (last_DP["address"] == current_DP["address"])
                    and (last_DP["value"] != current_DP["value"])
                ):
                    # Prepare value
                    value = str(current_DP["value"][0]).rjust(5)

                    # Print out information
                    return(
                        str(timestamp) 
                        + " ---> "
                        + str(self.modbusServer_Information["host"])
                        + " @ Port: "
                        + str(self.modbusServer_Information["port"])
                        + " ==> Value: "
                        + value
                        + " from "
                        + (current_DP["type"]).rjust(8)
                        + " at address: "
                        + str(current_DP["address"])
                        + " }\n"
                    )
'''
