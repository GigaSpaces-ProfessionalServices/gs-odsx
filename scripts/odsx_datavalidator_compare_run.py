#!/usr/bin/env python3

import os.path, argparse
from scripts.logManager import LogManager
from colorama import Fore

from scripts.odsx_datavalidator_install_list import getDataValidationHost
from utils.odsx_print_tabular_data import printTabular
from utils.ods_cluster_config import config_get_dataValidation_nodes
import requests, json

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
    verboseHandle.printConsoleWarning('');
    verboseHandle.printConsoleWarning('Measurement List:');
    resultCount = printmeasurementtable(dataValidatorServiceHost)
    if resultCount > 0:
        measurementIdA = str(input("Select 1st measurement Id for comparison : "))
        while(measurementIdA not in measurementids):
          print(Fore.YELLOW +"Please select 1st measurement Id from above list"+Fore.RESET)
          measurementIdA = str(input("Select 1st measurement Id for comparison :"))
        if (len(str(measurementIdA)) == 0):
          measurementIdA = '1'
        measurementIdB = str(input("Select 2nd measurement Id for comparison : "))
        while(measurementIdB not in measurementids):
           print(Fore.YELLOW +"Please select 2nd measurement Id from above list"+Fore.RESET)
           measurementIdB = str(input("Select 2nd measurement Id for comparison :"))
        if (len(str(measurementIdB)) == 0):
          measurementIdB = '1'

        executionTime = str(input("Execution time delay (in minutes) [0]: "))
        if (len(str(executionTime)) == 0):
            executionTime = '0'

        # http://localhost:7890/compare/avg?dataSource1Type=gigaspaces&dataSource1HostIp=localhost&dataSource1Port=414&schemaName1=demo&dataSource2Type=gigaspaces&dataSource2HostIp=localhost&dataSource2Port=4174&schemaName2=demo2&tableName=com.mycompany.app.Person&fieldName=salary
        response = requests.get(
            "http://" + dataValidatorServiceHost + ":7890/compare/" + measurementIdA + "/" + measurementIdB
            + "?executionTime=" + executionTime)

        if response.status_code == 200:
            jsonArray = json.loads(response.text)
            response = json.loads(jsonArray["response"])
            #print(str(response))

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
        else:
            verboseHandle.printConsoleInfo("No measurement available.Please Register first.")

measurementids=[]
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


if __name__ == '__main__':
    logger.info("MENU -> Data Validator -> Perform Validation -> Run Test -> Compare Test")
    verboseHandle.printConsoleWarning('MENU -> Data Validator -> Perform Validation -> Run Test -> Compare Test')
    verboseHandle.printConsoleWarning('');
    try:
        # with Spinner():
        doValidate()
    except Exception as e:
        logger.error("Exception in Menu->Validators" + str(e))
        verboseHandle.printConsoleError("Exception in Menu->Validators" + str(e))
