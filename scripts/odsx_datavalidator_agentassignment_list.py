#!/usr/bin/env python3

import json
import os.path
import requests
from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_datavalidator_install_list import getDataValidationHost
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

    ## Bypass for now

    #if str(dataValidationHost) == "":
    #    verboseHandle.printConsoleError("")
    #    verboseHandle.printConsoleError(
    #        "Failed to connect to the Data validation server. Please check that it is running.")
    #    return


    # dataValidatorServiceHost = str(input("Data validator service host ["+str(dataValidationHost)+"]: "))
    # if (len(str(dataValidatorServiceHost)) == 0):
    #    dataValidatorServiceHost = dataValidationHost

    dataValidatorServiceHost = dataValidationHost


    ##  Print Agents and clients
    verboseHandle.printConsoleWarning('');
    response = printAssignmentTable(dataValidatorServiceHost)

    if len(response) <= 0:
        verboseHandle.printConsoleWarning("No assignment available. Please add one")
        return


def printAssignmentTable(dataValidatorServiceHost):
    try:
        response = requests.get("http://" + dataValidatorServiceHost + ":"+str(readValuefromAppConfig("app.dv.server.port"))+"/assignment/list")
    except:
        print("An exception occurred")

    if response.status_code == 200:
        # logger.info(str(response.status_code))
        jsonArray = json.loads(response.text)
        response = json.loads(jsonArray["response"])
        #print("response1 "+str(response))
        # print(isinstance(response, list))

        headers = [Fore.YELLOW + "Agent Id" + Fore.RESET,
                   Fore.YELLOW + "Agent Host IP" + Fore.RESET,
                   Fore.YELLOW + "Datasource Id" + Fore.RESET,
                   Fore.YELLOW + "Datasource Name" + Fore.RESET,
                   Fore.YELLOW + "Datasource Type" + Fore.RESET,
                   Fore.YELLOW + "Datasource Host IP" + Fore.RESET,
                   ]
        data = []
        agentId =''
        agentHostIp=''
        prevAgentId=''
        if response:
            for agentDSrow in response:
                agentId =str(agentDSrow["agentId"])
                agentHostIp=agentDSrow["agentHostIp"]
                if prevAgentId == str(agentDSrow["agentId"]):
                    agentId =''
                    agentHostIp=''
                prevAgentId = str(agentDSrow["agentId"])
                dataArray = [Fore.GREEN + agentId + Fore.RESET,
                             Fore.GREEN + agentHostIp + Fore.RESET,
                             Fore.GREEN + str(agentDSrow["dataSourceId"]) + Fore.RESET,
                             Fore.GREEN + agentDSrow["dataSourceName"] + Fore.RESET,
                             Fore.GREEN + agentDSrow["dataSourceType"] + Fore.RESET,
                             Fore.GREEN + agentDSrow["dataSourceHostIp"] + Fore.RESET
                             ]
                data.append(dataArray)
            printTabular(None, headers, data)
            verboseHandle.printConsoleWarning('');
    return response


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('MENU -> Data Validator -> Agent Assignment -> List')
    verboseHandle.printConsoleWarning('');
    try:
        # with Spinner():
        doValidate()
    except Exception as e:
        logger.error("Exception in MENU -> Data Validator -> Agent Assignment -> List " + str(e))
        verboseHandle.printConsoleError("Exception in MENU -> Data Validator -> Agent Assignment -> List " + str(e))
