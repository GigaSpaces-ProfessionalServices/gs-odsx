#!/usr/bin/env python3

import os.path
from scripts.logManager import LogManager
from colorama import Fore

from scripts.odsx_datavalidator_list import getDataValidationHost
from utils.odsx_print_tabular_data import printTabular
from utils.ods_cluster_config import config_get_dataValidation_nodes
from utils.ods_validation import getSpaceServerStatus
import requests, json, subprocess

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


def getPort(dataSource):
    if (dataSource == 'gigaspaces'):
        return '4174'

    if (dataSource == 'mysql'):
        return '3306'

    if (dataSource == 'db2'):
        return '446'

    if (dataSource == 'ms-sql'):
        return '1433'


def doValidate():
    dataValidationNodes = config_get_dataValidation_nodes()
    dataValidationHost = getDataValidationHost(dataValidationNodes)
    logger.info("dataValidationHost : " + str(dataValidationHost))

    if str(dataValidationHost) == "":
        verboseHandle.printConsoleError("")
        verboseHandle.printConsoleError(
            "Failed to connect to the Data validation server. Please check that it is running.")
        return

    # dataValidatorServiceHost = str(input("Data validator service host ["+str(dataValidationHost)+"]: "))
    # if (len(str(dataValidatorServiceHost)) == 0):
    #    dataValidatorServiceHost = dataValidationHost

    dataValidatorServiceHost = dataValidationHost

    verboseHandle.printConsoleWarning('Measurements List:');
    resultCount = printmeasurementtable(dataValidatorServiceHost)

    registernew = 'yes'
    if resultCount <= 0:
        verboseHandle.printConsoleWarning("No measurement available.")
        return

    measurementId = str(input(Fore.YELLOW + "Enter measurement id to remove: " + Fore.RESET))
    while (len(str(measurementId)) == 0):
        measurementId = str(input(Fore.YELLOW + "Enter measurement id to remove: " + Fore.RESET))

    response = requests.delete(
        "http://" + dataValidatorServiceHost + ":7890/measurement/remove/" + measurementId)

    logger.info(str(response.status_code))
    jsonArray = json.loads(response.text)

    verboseHandle.printConsoleWarning("")
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleInfo("Response: " + jsonArray["response"])
    verboseHandle.printConsoleWarning("------------------------------------------------------------")


def printmeasurementtable(dataValidatorServiceHost):
    try:
        response = requests.get("http://" + dataValidatorServiceHost + ":7890/measurement/list")
    except:
        print("An exception occurred")

    if response.status_code == 200:
        # logger.info(str(response.status_code))
        jsonArray = json.loads(response.text)
        response = json.loads(jsonArray["response"])
        # print("response2 "+response[0])
        # print(isinstance(response, list))

        headers = [Fore.YELLOW + "Measurement Id" + Fore.RESET,
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
                             Fore.GREEN + measurement["dataSourceType"] + "(schema=" + measurement[
                                 "schemaName"] + ", host=" + measurement["dataSourceHostIp"] + ")" + Fore.RESET,
                             Fore.GREEN + queryDetail + Fore.RESET
                             ]
                data.append(dataArray)

        printTabular(None, headers, data)
        verboseHandle.printConsoleWarning('');
        return len(response)
    return 0


if __name__ == '__main__':
    logger.info("MENU -> Data Validator -> Perform Validation -> Measurement -> Remove")
    verboseHandle.printConsoleWarning('MENU -> Data Validator -> Perform Validation -> Measurement -> Remove')
    verboseHandle.printConsoleWarning('');
    try:
        # with Spinner():
        doValidate()
    except Exception as e:
        logger.error("Exception in Menu->Validators" + str(e))
        verboseHandle.printConsoleError("Exception in Menu->Validators" + str(e))
