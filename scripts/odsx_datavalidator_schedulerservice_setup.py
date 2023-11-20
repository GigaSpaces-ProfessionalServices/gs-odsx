import json
import os
import sqlite3

import requests
from colorama import Fore
from scripts.logManager import LogManager
from scripts.odsx_datavalidator_list import getDataValidationHost
from utils.ods_app_config import readValuefromAppConfig, readValueByConfigObj
from utils.ods_ssh import connectExecuteSSH
from utils.odsx_print_tabular_data import printTabular
from utils.odsx_keypress import userInputWithEscWrapper, userInputWrapper
from utils.odsx_keypress import userInputWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
logger = verboseHandle.logger
serviceName = "datavalidator-measurment.service"
user = "root"

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR

def handleException(e):
    logger.info("handleException()")
    trace = []
    tb = e.__traceback__
    while tb is not None:
        trace.append({
            "filename": tb.tb_frame.f_code.co_filename,
            "name": tb.tb_frame.f_code.co_name,
            "lineno": tb.tb_lineno
        })
        tb = tb.tb_next
    logger.error(str({
        'type': type(e).__name__,
        'message': str(e),
        'trace': trace
    }))
    verboseHandle.printConsoleError((str({
        'type': type(e).__name__,
        'message': str(e),
        'trace': trace
    })))


class host_dictionary_obj(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

def doValidate():
    # dataValidationNodes = config_get_dataValidation_nodes()
    dataValidationHost = os.getenv("pivot1")
    logger.info("dataValidationHost : " + str(dataValidationHost))

    if str(dataValidationHost) == "":
        verboseHandle.printConsoleError("")
        verboseHandle.printConsoleError(
            "Failed to connect to the Data validation server. Please check that it is running.")
        return

    dataValidatorServiceHost = dataValidationHost
    verboseHandle.printConsoleWarning('');
    verboseHandle.printConsoleWarning('Measurement List:');
    resultCount = printmeasurementtable(dataValidatorServiceHost)
    if resultCount > 0:
        from utils.odsx_keypress import userInputWrapper
        measurementIdA = str(userInputWithEscWrapper("Select 1st measurement Id for comparison : "))
        while(measurementIdA not in measurementids):
            print(Fore.YELLOW +"Please select 1st measurement Id from above list"+Fore.RESET)
            from utils.odsx_keypress import userInputWrapper
            measurementIdA = str(userInputWithEscWrapper("Select 1st measurement Id for comparison :"))
        if (len(str(measurementIdA)) == 0):
            measurementIdA = '1'
        from utils.odsx_keypress import userInputWrapper
        measurementIdB = str(userInputWithEscWrapper("Select 2nd measurement Id for comparison : "))
        while(measurementIdB not in measurementids):
            print(Fore.YELLOW +"Please select 2nd measurement Id from above list"+Fore.RESET)
            from utils.odsx_keypress import userInputWrapper
            measurementIdB = str(userInputWithEscWrapper("Select 2nd measurement Id for comparison :"))
        if (len(str(measurementIdB)) == 0):
            measurementIdB = '1'

        from utils.odsx_keypress import userInputWrapper
        executionTime = str(userInputWrapper("Execution time delay (in minutes) [0]: "))
        if (len(str(executionTime)) == 0):
            executionTime = '0'

        measurmentArray.append({
            "measurementIdA": measurementIdA,
            "measurementIdB": measurementIdB,
            "executionTime": executionTime
        })

def printSchedulerTable():
    headers = [Fore.YELLOW + "Id" + Fore.RESET,
               Fore.YELLOW + "MeasurementId A" + Fore.RESET,
               Fore.YELLOW + "MeasurementId B" + Fore.RESET,
               Fore.YELLOW + "Execution Time" + Fore.RESET
               ]
    dataList = []
    count = 1;
    for measurement in measurmentArray:

            dataArray = [Fore.GREEN + str(count) + Fore.RESET,
                         Fore.GREEN +  measurement["measurementIdA"] + Fore.RESET,
                         Fore.GREEN +  measurement["measurementIdB"] + Fore.RESET,
                         Fore.GREEN +  measurement["executionTime"] + Fore.RESET
                         ]
            dataList.append(dataArray)
            count= count+1
    printTabular(None, headers, dataList)

measurementids=[]
def printmeasurementtable(dataValidatorServiceHost):
    try:
        response = requests.get("http://" + dataValidatorServiceHost + ":"+str(readValuefromAppConfig("app.dv.server.port"))+"/measurement/list")
    except:
        print("An exception occurred")

    if response.status_code == 200:
        # logger.info(str(response.status_code))
        jsonArray = json.loads(response.text)
        response = json.loads(jsonArray["response"])
        # print("response2 "+response[0])
        # print(isinstance(response, list))

        headers = [Fore.YELLOW + "Id" + Fore.RESET,
                   Fore.YELLOW + "Datasource Name" + Fore.RESET,
                   Fore.YELLOW + "Measurement Datasource" + Fore.RESET,
                   Fore.YELLOW + "Measurement Query" + Fore.RESET
                   ]
        data = []
        if response:
            for measurement in response:
                # print(measurement)
                queryDetail = "'" + measurement["type"] + "' of '" + measurement["fieldName"] + "' FROM '" + \
                              measurement["tableName"] + "'"
                if measurement["whereCondition"] != "":
                    queryDetail += " WHERE " + measurement["whereCondition"]

                dataArray = [Fore.GREEN + str(measurement["id"]) + Fore.RESET,
                             Fore.GREEN +  measurement["dataSource"]["dataSourceName"] + Fore.RESET,
                             Fore.GREEN +"(Type:"+ measurement["dataSource"]["dataSourceType"] +",schema=" + measurement[
                                 "schemaName"] + ", host=" + measurement["dataSource"]["dataSourceHostIp"] + ")" + Fore.RESET,
                             Fore.GREEN + queryDetail + Fore.RESET
                             ]
                data.append(dataArray)
                measurementids.append(str(measurement["id"]) )
        printTabular(None, headers, data)
        verboseHandle.printConsoleWarning('');
        return len(response)
    return 0

def setupService():
    printSchedulerTable()
    ipAddress= os.getenv("pivot1")
    portNumber= readValuefromAppConfig("app.dv.server.port")#7890
    # timeRestart= #5
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleWarning("***Summary***")
    print(Fore.GREEN+"1. "+
          Fore.GREEN+"Pivot IP Address = "+
          Fore.GREEN+ipAddress+Fore.RESET)
    print(Fore.GREEN+"2. "+
          Fore.GREEN+"Port Number = "+
          Fore.GREEN+portNumber.replace('"','')+Fore.RESET)
    print(Fore.GREEN+"3. "+
          Fore.GREEN+"Waiting time(in seconds) = "+
          Fore.GREEN+timeRestart.replace('"','').replace( "\\",'')+Fore.RESET)
    verboseHandle.printConsoleWarning("------------------------------------------------------------")

    confirmMsg = Fore.YELLOW + "Are you sure, you want to setup DataValidator Scheduler service ? (y/n) [y]:" + Fore.RESET

    choice = str(userInputWrapper(confirmMsg))
    if choice.casefold() == 'n':
        exit(0)

    commandToExecute = "scripts/setupDataValidatorSchedulerService.sh "+str(portNumber)+" "+str(timeRestart)+" "+str(ipAddress)+" "+str(str(json.dumps(json.dumps(measurmentArray, separators=(',', ':')))));
    logger.info("Command "+commandToExecute)
    try:
        os.system("chmod 333 scripts/setupDataValidatorSchedulerService.sh")
        os.system(commandToExecute)
        logger.info("setupService() completed")
        verboseHandle.printConsoleInfo("Service setup successfully done")
    except Exception as e:
        logger.error("error occurred in setupService()")
        verboseHandle.printConsoleError("Service not able to setup")

    logger.info("setupService() : end")


if __name__ == '__main__':
    logger.info("MENU -> Data Validator -> Scheduler Service -> Setup")
    verboseHandle.printConsoleWarning('MENU -> Data Validator-> Scheduler Service -> Setup')
    verboseHandle.printConsoleWarning('');
    try:
        # with Spinner():
        global measurmentArray
        global timeRestart
        timeRestart= readValuefromAppConfig("app.dv.measurement.time")
        measurmentArray=[]
        optionForFilter=0
        # optionForFilter = str(userInputWithEscWrapper(
        #     Fore.YELLOW + "press [Enter] For Continue  \nPress [99] for exit.: " + Fore.RESET))
        # Fore.YELLOW + "press [1] if you want to Filter by Mode.\npress [2] if you want to Filter by Host.\n[Enter] For all  \nPress [99] for exit.: " + Fore.RESET))
        while optionForFilter != '99':
            doValidate()
            optionForFilter = str(userInputWithEscWrapper(
                Fore.YELLOW + "press [Enter] to add another. \nPress [99] for save your measurment compare.: " + Fore.RESET))
        timeRestart = str(userInputWrapper(Fore.YELLOW + "Enter the scheduler time (seconds) ? ["+str(timeRestart)+"] : " + Fore.RESET))
        logger.info("timeRestart :" + str(timeRestart))
        setupService()
    except Exception as e:
        logger.error("Exception in Menu->Validators" + str(e))
        verboseHandle.printConsoleError("Exception in Menu->Validators" + str(e))
