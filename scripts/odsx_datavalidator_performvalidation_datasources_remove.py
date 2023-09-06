#!/usr/bin/env python3

import os.path

import json
import requests
from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_datavalidator_list import getDataValidationHost
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_dataValidation_nodes
from utils.odsx_keypress import userInputWrapper
from utils.odsx_print_tabular_data import printTabular

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
    dataValidationNodes = config_get_dataValidation_nodes()
    dataValidationHost = getDataValidationHost(dataValidationNodes)
    logger.info("dataValidationHost : " + str(dataValidationHost))

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
    resultCount = printDatasourcetable(dataValidatorServiceHost)

    registernew = 'yes'
    if resultCount <= 0:
        verboseHandle.printConsoleWarning("No Datasource available.")
        return

    datasourceId = str(userInputWrapper(Fore.YELLOW + "Enter Datasource id to remove: " + Fore.RESET))
    while (len(str(datasourceId)) == 0 or datasourceId not in datasourceIds):
        if(datasourceId not in datasourceIds):
         print(Fore.YELLOW +"Please select DataSource Id from above list"+Fore.RESET)
         datasourceId = str(userInputWrapper(Fore.YELLOW + "Enter Datasource id to remove: " + Fore.RESET))
        else:
         datasourceId = str(userInputWrapper(Fore.YELLOW + "Enter Datasource id to remove: " + Fore.RESET))



    response = requests.delete(
        "http://" + dataValidatorServiceHost + ":"+str(readValuefromAppConfig("app.dv.server.port"))+"/datasource/remove/" + datasourceId)

    logger.info(str(response.status_code))
    jsonArray = json.loads(response.text)

    verboseHandle.printConsoleWarning("")
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleInfo(" " + jsonArray["response"])
    verboseHandle.printConsoleWarning("------------------------------------------------------------")

datasourceIds=[]
def printDatasourcetable(dataValidatorServiceHost):
    try:
        response = requests.get("http://" + dataValidatorServiceHost + ":"+str(readValuefromAppConfig("app.dv.server.port"))+"/datasource/list")
    except:
        print("An exception occurred")

    if response.status_code == 200:
        # logger.info(str(response.status_code))
        jsonArray = json.loads(response.text)
        response = json.loads(jsonArray["response"])
        # print("response2 "+response[0])
        # print(isinstance(response, list))

        headers = [Fore.YELLOW + "Datasource Id" + Fore.RESET,
                   Fore.YELLOW + "Datasource Name" + Fore.RESET,
                   Fore.YELLOW + "Type" + Fore.RESET ,
                   Fore.YELLOW + "Host Ip" + Fore.RESET
                   ]
        data = []
        if response:
            for datasource in response:
                #print(datasource)
                datasourceIds.append(str(datasource["id"]) )

                dataArray = [Fore.GREEN + str(datasource["id"]) + Fore.RESET,
                             Fore.GREEN + datasource["dataSourceName"] + Fore.RESET,
                             Fore.GREEN + datasource["dataSourceType"] + Fore.RESET,
                             Fore.GREEN + datasource["dataSourceHostIp"] + Fore.RESET
                             ]
                data.append(dataArray)

        printTabular(None, headers, data)
        verboseHandle.printConsoleWarning('');
        return len(response)
    return 0


if __name__ == '__main__':
    logger.info("MENU -> Data Validator -> Perform Validation -> Datasource -> Remove")
    verboseHandle.printConsoleWarning('MENU -> Data Validator -> Perform Validation -> Datasource -> Remove')
    verboseHandle.printConsoleWarning('');
    try:
        # with Spinner():
        doValidate()
    except Exception as e:
        logger.error("Exception in Menu->Validators" + str(e))
        verboseHandle.printConsoleError("Exception in Menu->Validators" + str(e))
