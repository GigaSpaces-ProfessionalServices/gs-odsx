#!/usr/bin/env python3

import json
import os.path
import requests
from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_datavalidator_install_list import getDataValidationHost
from utils.ods_cluster_config import config_get_dataValidation_nodes
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
    verboseHandle.printConsoleWarning('')

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
    verboseHandle.printConsoleWarning('Existing Measurements:');
    response = printmeasurementtable(dataValidatorServiceHost)

    if len(response) < 0:
        verboseHandle.printConsoleWarning("No measurement available.")
        return

    measurementId = str(input(Fore.YELLOW + "Enter measurement id to edit: " + Fore.RESET))
    while (measurementId not in measurementIds):
        print(Fore.YELLOW +"Enter measurement id from above list"+Fore.RESET)
        measurementId = str(input(Fore.YELLOW + "Enter measurement id to edit: " + Fore.RESET))

    if response:
        for measurement in response:
            if str(measurement["id"]) == measurementId:
                verboseHandle.printConsoleWarning('');
                verboseHandle.printConsoleWarning('Update values for measurement id:' + measurementId);
                verboseHandle.printConsoleWarning('Note: Leave blank new value if you do not want to change the value');
                verboseHandle.printConsoleWarning('')
                test = str(input("Test type (count/avg/min/max/sum) [Current value: '" + measurement["type"] + "'] New value: "))

                while(test not in testTypes):
                  print(Fore.YELLOW +"Please select Test type from given list"+Fore.RESET)
                  test = str(input("Test type (count/avg/min/max/sum) [Current value: '" + measurement["type"] + "'] New value: "))
                if (len(str(test)) == 0):
                    test = measurement["type"]

                datasourceRowCount = printDatasourcetable(dataValidatorServiceHost)
                if datasourceRowCount <= 0:
                    verboseHandle.printConsoleWarning("No Datasource available. Please add atleast one datasource")
                    return

                DataSourceId = str(input("DataSource Id [Current value: '" +str(measurement["dataSourceId"])+ " '] New value: "))
                while(DataSourceId not in dataSourceIds):
                  if (len(str(DataSourceId)) == 0 or DataSourceId ==  measurement["dataSourceId"]):
                    DataSourceId = str(measurement["dataSourceId"])
                    break
                  print(Fore.YELLOW +"Invalid DataSource Id "+Fore.RESET)
                  DataSourceId = str(input("DataSource Id [Current value: '" + str(measurement["dataSourceId"]) + " '] New value: "))


                schemaName1 = str(input("Schema Name [Current value: '" + measurement["schemaName"] + " '] New value: "))
                if (len(str(schemaName1)) == 0):
                    schemaName1 = measurement["schemaName"]

                tableName1 = str(input("Table Name [Current value: '" + measurement["tableName"] + "'] New value: "))
                if (len(str(tableName1)) == 0):
                    tableName1 = measurement["tableName"]
                fieldName1 = str(input("Field Name [Current value: '" + measurement["fieldName"] + "'] New value: "))
                if (len(str(fieldName1)) == 0):
                    fieldName1 = measurement["fieldName"]
                if test != 'lastvalue':
                    whereCondition = str(
                        input("Where Condition [Current value: '" + measurement["whereCondition"] + "'] New value: "))
                    if (len(str(whereCondition)) == 0):
                        whereCondition = measurement["whereCondition"]



                verboseHandle.printConsoleWarning('');
                data = {
                    "measurementId": measurementId,
                    "test": test,
                    "dataSourceId": DataSourceId,
                    "schemaName": schemaName1,
                    "tableName": tableName1,
                    "fieldName": fieldName1,
                    "whereCondition": whereCondition

                }
                headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
                response = requests.post("http://" + dataValidatorServiceHost + ":7890/measurement/update"
                                         , data=json.dumps(data)
                                         , headers=headers)

                logger.info(str(response.status_code))
                jsonArray = json.loads(response.text)

                verboseHandle.printConsoleWarning("")
                verboseHandle.printConsoleWarning("------------------------------------------------------------")
                verboseHandle.printConsoleInfo("  " + jsonArray["response"])
                verboseHandle.printConsoleWarning("------------------------------------------------------------")

dataSourceIds=[]
measurementIds=[]
testTypes =["count","avg","min","max","sum",""]
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
                   Fore.YELLOW + "Measurement Datasource" + Fore.RESET,
                   Fore.YELLOW + "Agent" + Fore.RESET,
                   Fore.YELLOW + "Measurement Query" + Fore.RESET
                   ]
        data = []
        if response:
            for measurement in response:
                # print(measurement)
                measurementIds.append(str(measurement["id"]))

                queryDetail = "'" + measurement["type"] + "' of '" + measurement["fieldName"] + "' FROM '" + \
                              measurement["tableName"] + "'"
                if measurement["whereCondition"] != "":
                    queryDetail += " WHERE " + measurement["whereCondition"]

                dataArray = [Fore.GREEN + str(measurement["id"]) + Fore.RESET,
                             Fore.GREEN +"( Type:"+ measurement["dataSource"]["dataSourceType"] +",schema=" + measurement[
                                 "schemaName"] + ", host=" + measurement["dataSource"]["dataSourceHostIp"] + ")" + Fore.RESET,
                             Fore.GREEN +  measurement["dataSource"]["agent"]["hostIp"] + Fore.RESET,
                             Fore.GREEN + queryDetail + Fore.RESET
                             ]
                data.append(dataArray)

        printTabular(None, headers, data)
        verboseHandle.printConsoleWarning('');
        return response
    return 0

def printDatasourcetable(dataValidatorServiceHost):
    try:
        response = requests.get("http://" + dataValidatorServiceHost + ":7890/datasource/list")
    except:
        print("An exception occurred")

    if response.status_code == 200:
        # logger.info(str(response.status_code))
        jsonArray = json.loads(response.text)
        response = json.loads(jsonArray["response"])
        # print("response2 "+response[0])
        # print(isinstance(response, list))

        headers = [Fore.YELLOW + " Id" + Fore.RESET,
                   Fore.YELLOW + "Datasource Name" + Fore.RESET,
                   Fore.YELLOW + "Type" + Fore.RESET
                   ]
        data = []
        if response:
            for datasource in response:
                #print(datasource)
                dataSourceIds.append(str(datasource["id"]))
                dataArray = [Fore.GREEN + str(datasource["id"]) + Fore.RESET,
                             Fore.GREEN + datasource["dataSourceName"] + Fore.RESET,
                             Fore.GREEN + datasource["dataSourceType"] + Fore.RESET
                             ]
                data.append(dataArray)

        printTabular(None, headers, data)
        verboseHandle.printConsoleWarning('');
        return len(response)
    return 0

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('MENU -> Data Validator -> Measurement -> Edit')
    verboseHandle.printConsoleWarning('');
    try:
        # with Spinner():
        doValidate()
    except Exception as e:
        logger.error("Exception in Menu->Validators" + str(e))
        verboseHandle.printConsoleError("Exception in Menu->Validators" + str(e))
