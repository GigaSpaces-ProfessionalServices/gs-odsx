#!/usr/bin/env python3

import os.path
from scripts.logManager import LogManager
from colorama import Fore

from scripts.odsx_datavalidator_agentassignment_list import printAssignmentTable
from scripts.odsx_datavalidator_install_list import getDataValidationHost
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

    verboseHandle.printConsoleWarning('Assignment List:');
    response = printAssignmentTable(dataValidatorServiceHost)

    registernew = 'yes'
    if len(response) <= 0:
        verboseHandle.printConsoleWarning("No Assignment available.")
        return

    '''datasourceId = str(input(Fore.YELLOW + "Enter Agent id to remove: " + Fore.RESET))
    while (len(str(datasourceId)) == 0 or datasourceId not in datasourceIds):
        if(datasourceId not in datasourceIds):
         print(Fore.YELLOW +"Please select Agent Id from above list"+Fore.RESET)
         datasourceId = str(input(Fore.YELLOW + "Enter Agent id to remove: " + Fore.RESET))
        else:
         datasourceId = str(input(Fore.YELLOW + "Enter Agent id to remove: " + Fore.RESET))
'''
    agentId = str(input(Fore.YELLOW + "Enter Agent id to remove: " + Fore.RESET))
    while (len(str(agentId)) == 0):
        agentId = str(input(Fore.YELLOW + "Enter Agent id to remove: " + Fore.RESET))


    response = requests.delete(
        "http://" + dataValidatorServiceHost + ":7890/assignment/remove/" + agentId)

    logger.info(str(response.status_code))
    jsonArray = json.loads(response.text)

    verboseHandle.printConsoleWarning("")
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleInfo(" " + jsonArray["response"])
    verboseHandle.printConsoleWarning("------------------------------------------------------------")


if __name__ == '__main__':
    logger.info("MENU -> Data Validator -> Agent Assignment -> Remove")
    verboseHandle.printConsoleWarning('MENU -> Data Validator -> Agent Assignment -> Remove')
    verboseHandle.printConsoleWarning('');
    try:
        # with Spinner():
        doValidate()
    except Exception as e:
        logger.error("Exception in Menu->Validators" + str(e))
        verboseHandle.printConsoleError("Exception in Menu->Validators" + str(e))
