#!/usr/bin/env python3

import json
import os.path
import requests
from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_datavalidator_install_list import getDataValidationHost
from utils.ods_cluster_config import config_get_dataValidation_nodes
from utils.odsx_keypress import userInputWrapper
from utils.odsx_print_tabular_data import printTabular
from utils.ods_app_config import readValuefromAppConfig

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR


class host_dictionary_obj(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

def doValidate():
    verboseHandle.printConsoleWarning('');

    dataValidationNodes = config_get_dataValidation_nodes()
    dataValidationHost = getDataValidationHost(dataValidationNodes)

    if str(dataValidationHost) == "":
        verboseHandle.printConsoleError("")
        verboseHandle.printConsoleError(
            "Failed to connect to the Data validation server. Please check that it is running.")
        return

    # dataValidatorServiceHost = str(userInputWrapper("Data validator service host ["+str(dataValidationHost)+"]: "))
    # if (len(str(dataValidatorServiceHost)) == 0):
    #    dataValidatorServiceHost = dataValidationHost

    dataValidatorServiceHost = dataValidationHost

    verboseHandle.printConsoleWarning('Measurements List:');
    resultCount = printmeasurementtable(dataValidatorServiceHost)

    if resultCount <= 0:
        verboseHandle.printConsoleWarning("No measurement available. Please add one")
        return

    verboseHandle.printConsoleWarning('');
    measurementId = str(userInputWrapper("Select measurement by id to run [1] : "))
    if (len(str(measurementId)) == 0):
        measurementId = '1'
    while(measurementId not in measurementids):
      print(Fore.YELLOW +"Please select measurement Id from above list"+Fore.RESET)
      measurementId = str(userInputWrapper("Select measurement by id to run [1]:"))



    executionTime = str(userInputWrapper("Execution time delay (in minutes) [0]: "))
    if (len(str(executionTime)) == 0):
        executionTime = '0'

    response = requests.get(
            "http://" + dataValidatorServiceHost + ":"+str(readValuefromAppConfig("app.dv.server.port"))+"/measurement/run/" + measurementId + "?executionTime=" + executionTime)

    jsonArray = json.loads(response.text)
    response = json.loads(jsonArray["response"])

    verboseHandle.printConsoleWarning("")
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    # verboseHandle.printConsoleInfo("Test Result:  "+jsonArray["response"])
    if response["result"] == 'pending':
        verboseHandle.printConsoleInfo("Test is scheduled")
    elif response["result"].startswith('FAIL'):
        verboseHandle.printConsoleError("Test Failed")
        verboseHandle.printConsoleError("Details: "+response["errorSummary"])
    else:
        verboseHandle.printConsoleInfo("Test Result: " + response["result"])
        verboseHandle.printConsoleInfo("Query: " + response["query"])
    verboseHandle.printConsoleWarning("------------------------------------------------------------")

measurementids=[]
def printmeasurementtable(dataValidatorServiceHost):
    try:
        response = requests.get("http://" + dataValidatorServiceHost + ":"+str(readValuefromAppConfig("app.dv.server.port"))+"/measurement/list")
    except:
        print("An exception occurred")

    if response.status_code == 200:
        jsonArray = json.loads(response.text)
        response = json.loads(jsonArray["response"])

        headers = [Fore.YELLOW + "Id" + Fore.RESET,
                   Fore.YELLOW + "Datasource Name" + Fore.RESET,
                   Fore.YELLOW + "Measurement Datasource" + Fore.RESET,
                   Fore.YELLOW + "Measurement Query" + Fore.RESET
                   ]
        data = []
        if response:
            for measurement in response:
                #print(measurement)

                queryDetail = "'" + measurement["type"] + "' of '" + measurement["fieldName"] + "' FROM '" + \
                              measurement["tableName"] + "'"
                if measurement["whereCondition"] != "":
                    queryDetail += " WHERE " + measurement["whereCondition"]

                dataArray = [Fore.GREEN + str(measurement["id"]) + Fore.RESET,
                             Fore.GREEN +  measurement["dataSource"]["dataSourceName"] + Fore.RESET,
                             Fore.GREEN +"(Type:"+ measurement["dataSource"]["dataSourceType"] +",schema=" + measurement[
                                 "schemaName"] + ")" + Fore.RESET,
                             Fore.GREEN + queryDetail + Fore.RESET
                             ]
                data.append(dataArray)
                measurementids.append(str(measurement["id"]) )
        printTabular(None, headers, data)
        verboseHandle.printConsoleWarning('');
        return len(response)
    return 0


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('MENU -> Data Validator -> Perform Validation -> Run Test -> Measurement Test')
    verboseHandle.printConsoleWarning('');
    try:
        # with Spinner():
        doValidate()
    except Exception as e:
        logger.error("Exception in Menu->Validators" + str(e))
        verboseHandle.printConsoleError("Exception in Menu->Validators" + str(e))
