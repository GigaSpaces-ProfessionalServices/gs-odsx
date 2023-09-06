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
    verboseHandle.printConsoleWarning('')

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

    verboseHandle.printConsoleWarning('');
    verboseHandle.printConsoleWarning('Existing Measurements :');
    resultCount = printmeasurementtable(dataValidatorServiceHost)

    registernew = 'yes'
    if resultCount < 0:
        verboseHandle.printConsoleWarning("No measurement available. Please add one")

    if registernew == 'yes':
        verboseHandle.printConsoleWarning('');
        verboseHandle.printConsoleWarning('Add new Measurement:');
        test = str(userInputWrapper("Test type (count/avg/min/max/sum) [count]: "))
        while(test not in testTypes):
            print(Fore.YELLOW +"Please select Test type from given list"+Fore.RESET)
            test = str(userInputWrapper("Test type (count/avg/min/max/sum) [count]: "))

        if (len(str(test)) == 0):
            test = 'count'


        verboseHandle.printConsoleWarning('');
        verboseHandle.printConsoleWarning('Available DataSource which are assigned to Agent:');
        datasourceRowCount = printDatasourcetable(dataValidatorServiceHost)

        if datasourceRowCount <= 0:
            verboseHandle.printConsoleWarning("No Datasource available. Please add atleast one datasources")
            return

        DataSourceId = str(userInputWrapper("Select DataSource Id from above table: "))
        while(DataSourceId not in dataSourceIds):
            print(Fore.YELLOW +"Invalid DataSource Id "+Fore.RESET)
            DataSourceId = str(userInputWrapper("DataSource Id from above table: "))


        for idx, x in enumerate(dataSourceIds):
            if DataSourceId == x:
                dataSType = dataSourceTypes[idx]
        #print("dataSType"+dataSType)

        schemaNameDefault = 'demo'
        if dataSType == 'gigaspaces':
            schemaNameDefault = str(readValuefromAppConfig("app.dataengine.mssql-feeder.space.name"))
        elif dataSType == 'ms-sql':
            schemaNameDefault = 'DB_Central'

        schemaName1 = str(userInputWrapper("Schema Name["+schemaNameDefault+"]: "))
        if (len(str(schemaName1)) == 0):
            schemaName1 = schemaNameDefault

        tableName1 = str(userInputWrapper("Table Name : "))
        while (len(str(tableName1)) == 0):
            print(Fore.YELLOW +"Table Name is invalid (Empty)"+Fore.RESET)
            tableName1 = str(userInputWrapper("Table Name : "))

        if test != 'count':
            fieldName1 = str(userInputWrapper("Field Name : "))
            while (len(str(fieldName1)) == 0):
                print(Fore.YELLOW +"Field Name is invalid (Empty)"+Fore.RESET)
                fieldName1 = str(userInputWrapper("Field Name : "))
        else:
            fieldName1 = '*'

        if test != 'lastvalue':
            whereCondition = str(userInputWrapper("Where Condition [''] : "))
            if (len(str(whereCondition)) == 0):
                whereCondition = ''

        verboseHandle.printConsoleWarning('');
        data = {
            "test":test,
            "dataSourceId": DataSourceId,
            "schemaName": schemaName1,
            "tableName": tableName1,
            "fieldName": fieldName1,
            "whereCondition": whereCondition,
        }

        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
        response = requests.post("http://" + dataValidatorServiceHost + ":"+str(readValuefromAppConfig("app.dv.server.port"))+"/measurement/register"
                                 , data=json.dumps(data)
                                 , headers=headers)

        logger.info(str(response.status_code))
        jsonArray = json.loads(response.text)

        verboseHandle.printConsoleWarning("")
        verboseHandle.printConsoleWarning("------------------------------------------------------------")
        verboseHandle.printConsoleInfo("  " + jsonArray["response"])
        verboseHandle.printConsoleWarning("------------------------------------------------------------")


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
                   Fore.YELLOW + "Measurement Datasource" + Fore.RESET,
                   Fore.YELLOW + "Agent" + Fore.RESET,
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
                             Fore.GREEN +"(Type:"+ measurement["dataSource"]["dataSourceType"] +",schema=" + measurement[
                                 "schemaName"] + ", host=" + measurement["dataSource"]["dataSourceHostIp"] + ")" + Fore.RESET,
                             Fore.GREEN +  measurement["dataSource"]["agent"]["hostIp"] + Fore.RESET,
                             Fore.GREEN + queryDetail + Fore.RESET
                             ]
                data.append(dataArray)

        printTabular(None, headers, data)
        verboseHandle.printConsoleWarning('');
        return len(response)
    return 0

dataSourceIds=[]
dataSourceTypes=[]
testTypes =["count","avg","min","max","sum",""]
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

        headers = [Fore.YELLOW + " Id" + Fore.RESET,
                   Fore.YELLOW + "Datasource Name" + Fore.RESET,
                   Fore.YELLOW + "Type" + Fore.RESET,
                   Fore.YELLOW + "Datasource Host IP" + Fore.RESET,
                   Fore.YELLOW + "Agent Host IP" + Fore.RESET
                   ]
        data = []
        if response:
            for datasource in response:
                #print(datasource)
                if datasource["agentHostIp"] == "-1":
                    continue
                dataSourceIds.append(str(datasource["id"]))
                dataSourceTypes.append(datasource["dataSourceType"])
                dataArray = [Fore.GREEN + str(datasource["id"]) + Fore.RESET,
                             Fore.GREEN + datasource["dataSourceName"] + Fore.RESET,
                             Fore.GREEN + datasource["dataSourceType"] + Fore.RESET,
                             Fore.GREEN + datasource["dataSourceHostIp"] + Fore.RESET,
                             Fore.GREEN + datasource["agentHostIp"] + Fore.RESET
                             ]
                data.append(dataArray)

        printTabular(None, headers, data)
        verboseHandle.printConsoleWarning('');
        return len(response)
    return 0


if __name__ == '__main__':
    logger.info("MENU -> Data Validator -> Measurement -> Add")
    verboseHandle.printConsoleWarning('MENU -> Data Validator -> Measurement -> Add')
    verboseHandle.printConsoleWarning('');
    try:
        # with Spinner():
        doValidate()
    except Exception as e:
        logger.error("Exception in Menu->Validators" + str(e))
        verboseHandle.printConsoleError("Exception in Menu->Validators" + str(e))