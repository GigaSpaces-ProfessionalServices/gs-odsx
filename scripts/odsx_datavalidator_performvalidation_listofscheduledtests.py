#!/usr/bin/env python3

import json
import os.path
import requests
from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_datavalidator_list import getDataValidationHost
from utils.ods_cluster_config import config_get_dataValidation_nodes
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

    response = requests.get("http://" + dataValidatorServiceHost + ":"+str(readValuefromAppConfig("app.dv.server.port"))+"/scheduledtasks")
    logger.info(str(response.status_code))
    jsonArray = json.loads(response.text)
    response = json.loads(jsonArray["response"])
    # print("response "+response)
    # print("response2 "+response[0])
    # print(isinstance(response, list))

    headers = [Fore.YELLOW + "Request Id" + Fore.RESET,
               Fore.YELLOW + "Test Name" + Fore.RESET,
               Fore.YELLOW + "Test Details" + Fore.RESET,
               Fore.YELLOW + "Datasource Details" + Fore.RESET,
               Fore.YELLOW + "Status/Result" + Fore.RESET
               ]
    data = []
    counter = 1
    if response:
        for task in response:
            #print(task)
            #print(task["measurementList"])

#"'" + task["measurementList"][0]["type"] + "' of '" + task["measurementList"][0]["fieldName"] + "' FROM '" + task["measurementList"][0]["tableName"] + "'"

            testDetail=""
            status = Fore.GREEN + task["result"] + Fore.RESET
            dataSouceDetail="";
            dataSouceDetai2="";
            if task["result"].startswith('FAIL'):
                status = Fore.RED + task["result"] + Fore.RESET

            if(task["measurementList"]!=None):

                if(task["measurementList"][0]!=None):
                 testDetail = "'" + task["measurementList"][0]["type"] + "' of '" + task["measurementList"][0]["fieldName"] + "' FROM '" + task["measurementList"][0]["tableName"] + "'"

                 if(task["measurementList"][0]["whereCondition"]!=""):
                   testDetail += " WHERE " + task["measurementList"][0]["whereCondition"]

            if (task["type"]!=None ):
                if (task["type"] == "Measure" and task["measurementList"][0]!=None):
                 #print( task["measurementList"][0]["dataSource"])
                 dataSouceDetail +=  "   Ds1:|"+task["measurementList"][0]["type"]+"| Name:"+task["measurementList"][0]["dataSource"]["dataSourceName"]+",Ip:"+task["measurementList"][0]["dataSource"]["dataSourceHostIp"]+",User:"+task["measurementList"][0]["dataSource"]["username"]

                if (task["type"] == "Compare" and task["measurementList"][0]!=None and task["measurementList"][1]!=None):
                 dataSouceDetail +=  "   Ds1:|"+task["measurementList"][0]["type"]+"| Name:"+task["measurementList"][0]["dataSource"]["dataSourceName"]+",Ip:"+task["measurementList"][0]["dataSource"]["dataSourceHostIp"]+",User:"+task["measurementList"][0]["dataSource"]["username"]
                 dataSouceDetai2 +=  "Vs Ds2:|"+task["measurementList"][1]["type"]+"| Name:"+task["measurementList"][1]["dataSource"]["dataSourceName"]+",Ip:"+task["measurementList"][1]["dataSource"]["dataSourceHostIp"]+",User:"+task["measurementList"][1]["dataSource"]["username"]
                # if(task["measurementList"][0]["datasource"]!=None):
                #   dataSouceDetail += task["measurementList"][0]["datasource"]["dataSourceName"]

            dataArray = [Fore.GREEN + str(task["id"])  + Fore.RESET,
                         Fore.GREEN + task["type"] + Fore.RESET,
                         Fore.GREEN + testDetail + Fore.RESET,
                         Fore.GREEN + dataSouceDetail + Fore.RESET,
                         status
                         ]
            data.append(dataArray)
            if(dataSouceDetai2!=""):
             dataArray = ["","","",Fore.GREEN + dataSouceDetai2 + Fore.RESET,""]
             data.append(dataArray)


            counter = counter + 1

    printTabular(None, headers, data)


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

        headers = [Fore.YELLOW + "Measurement Id" + Fore.RESET,
                   Fore.YELLOW + "Measurement Datasource" + Fore.RESET,
                   Fore.YELLOW + "Measurement Query" + Fore.RESET
                   ]
        data = []
        if response:
            for measurement in response:
                print(measurement)
                queryDetail = "'" + measurement["type"] + "' of '" + measurement["fieldName"] + "' FROM '" + \
                              measurement["tableName"] + "'"
                if measurement["whereCondition"] != "":
                    queryDetail += " WHERE " + measurement["whereCondition"]

                dataArray = [Fore.GREEN + str(measurement["id"]) + Fore.RESET,
                             Fore.GREEN +  measurement["dataSource"]["dataSourceType"] + "(schema=" + measurement[
                                 "schemaName"] + ", host=" +  measurement["dataSource"]["dataSourceHostIp"] + ")" + Fore.RESET,
                             Fore.GREEN + queryDetail + Fore.RESET
                             ]
                data.append(dataArray)

        printTabular(None, headers, data)
        verboseHandle.printConsoleWarning('');
        return len(response)
    return 0


if __name__ == '__main__':
    logger.info("MENU -> Data Validator -> Perform Validation -> List od Scheduled Tests")
    verboseHandle.printConsoleWarning('MENU -> Data Validator -> Perform Validation -> List of Scheduled Tests')
    verboseHandle.printConsoleWarning('');
    try:
        # with Spinner():
        doValidate()
    except Exception as e:
        logger.error("Exception in Menu->Validators" + str(e))
        verboseHandle.printConsoleError("Exception in Menu->Validators" + str(e))
