#!/usr/bin/env python3

import json
import os.path
import requests
from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_datavalidator_list import getDataValidationHost
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
    while (len(str(measurementId)) == 0):
        measurementId = str(input(Fore.YELLOW + "Enter measurement id to edit: " + Fore.RESET))

    if response:
        for measurement in response:
            if str(measurement["id"]) == measurementId:
                verboseHandle.printConsoleWarning('');
                verboseHandle.printConsoleWarning('Update values for measurement id:' + measurementId);
                verboseHandle.printConsoleWarning('Note: Leave blank new value if you do not want to change the value');
                verboseHandle.printConsoleWarning('')
                test = str(
                    input("Test type (count/avg/min/max/sum) [Current value: '" + measurement["type"] + "'] New value: "))
                if (len(str(test)) == 0):
                    test = measurement["type"]
                dataSource1Type = str(input(
                    "DataSource Type (gigaspaces/ms-sql/db2/mysql) [Current value: '" + measurement[
                        "dataSourceType"] + "'] New value: "))
                if (len(str(dataSource1Type)) == 0):
                    dataSource1Type = measurement["dataSourceType"]
                dataSource1HostIp = str(
                    input("DataSource Host Ip [Current value: '" + measurement["dataSourceHostIp"] + "'] New value: "))
                if (len(str(dataSource1HostIp)) == 0):
                    dataSource1HostIp = measurement["dataSourceHostIp"]
                dataSource1Port = str(
                    input("DataSource Port [Current value: '" + measurement["dataSourcePort"] + "'] New value: "))
                if (len(str(dataSource1Port)) == 0):
                    dataSource1Port = measurement["dataSourcePort"]
                username1 = str(input("User name [Current value: '" + measurement["username"] + "'] New value: "))
                if (len(str(username1)) == 0):
                    username1 = measurement["username"]
                password1 = str(input("Password [Current value: '" + measurement["password"] + "'] New value: "))
                if (len(str(password1)) == 0):
                    password1 = measurement["password"]
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

                IntegratedSecurity = ''
                AuthenticationScheme=''
                Properties=''
                #print(measurement)
                if (dataSource1Type == 'ms-sql'):
                 IntegratedSecurity = str(input("IntegratedSecurity [true/false] [Current value: '" + measurement["integratedSecurity"] + "'] New value:"))
                 if (len(str(IntegratedSecurity)) == 0):
                  IntegratedSecurity = measurement["integratedSecurity"]
                 AuthenticationScheme = str(input("AuthenticationScheme[JavaKerberos/NTLM] [Current value: '" + measurement["authenticationScheme"] + "'] New value:"))
                 if (len(str(AuthenticationScheme)) == 0):
                  AuthenticationScheme = measurement["authenticationScheme"]
                 Properties = str(input("Connection properties( ex.Key=value;... ) [Current value: '" + measurement["properties"] + "'] New value:"))
                 if (len(str(Properties)) == 0):
                  Properties = measurement["properties"]

                verboseHandle.printConsoleWarning('');
                data = {
                    "measurementId": measurementId,
                    "test": test,
                    "dataSourceType": dataSource1Type,
                    "dataSourceHostIp": dataSource1HostIp,
                    "dataSourcePort": dataSource1Port,
                    "username": username1,
                    "password": password1,
                    "schemaName": schemaName1,
                    "tableName": tableName1,
                    "fieldName": fieldName1,
                    "whereCondition": whereCondition,
                    "integratedSecurity":IntegratedSecurity,
                    "authenticationScheme":AuthenticationScheme,
                    "properties":Properties
                }
                headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
                response = requests.post("http://" + dataValidatorServiceHost + ":7890/measurement/update"
                                         , data=json.dumps(data)
                                         , headers=headers)

                logger.info(str(response.status_code))
                jsonArray = json.loads(response.text)

                verboseHandle.printConsoleWarning("")
                verboseHandle.printConsoleWarning("------------------------------------------------------------")
                verboseHandle.printConsoleInfo("Response:  " + jsonArray["response"])
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
        return response
    return 0


if __name__ == '__main__':
    logger.info("MENU -> Data Validator -> Perform Validation -> Measurement -> Edit")
    verboseHandle.printConsoleWarning('MENU -> Data Validator -> Perform Validation -> Measurement -> Edit')
    verboseHandle.printConsoleWarning('');
    try:
        # with Spinner():
        doValidate()
    except Exception as e:
        logger.error("Exception in Menu->Validators" + str(e))
        verboseHandle.printConsoleError("Exception in Menu->Validators" + str(e))
