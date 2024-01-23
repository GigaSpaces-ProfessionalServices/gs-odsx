#!/usr/bin/env python3

import os.path

import json
import requests
from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_datavalidator_install_list import getDataValidationHost
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_dataValidation_nodes
from utils.odsx_print_tabular_data import printTabular
from utils.odsx_keypress import userInputWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR


testTypes =["count","avg","min","max","sum","all",""]
def doValidate():

    verboseHandle.printConsoleWarning('Results:');

    dataValidationNodes = config_get_dataValidation_nodes()
    dataValidationHost = getDataValidationHost(dataValidationNodes)
    logger.info("dataValidationHost : "+str(dataValidationHost))

    if str(dataValidationHost) == "":
        verboseHandle.printConsoleError("")
        verboseHandle.printConsoleError("Failed to connect to the Data validation server. Please check that it is running.")
        return

    test = str(userInputWrapper("Select Test type (count/avg/min/max/sum/all) [count]: "))
    while(test not in testTypes):
        print(Fore.YELLOW +"Please select Test type from given list"+Fore.RESET)
        test = str(userInputWrapper("Test type (count/avg/min/max/sum/all) [count]: "))

    if (len(str(test)) == 0):
        test = 'count'

    try:
        response = requests.get("http://" + dataValidationHost + ":"+str(readValuefromAppConfig("app.dv.server.port"))+"/measurement/batchcompare/"+str(test))
    except:
        print("An exception occurred")

    if response.status_code == 200:
        #print("Response text: "+str(response.text))
        #jsonArray = json.loads(response.text)
        #response = json.loads(jsonArray["response"])

        json_data = response.text
        #print("Json_data: "+str(json_data))
        # Parse the outer JSON
        outer_data = json.loads(json_data)
        # Parse the inner JSON (which is stored as a string)
        inner_data_str = outer_data['response']
        inner_data = json.loads(inner_data_str)

        headers = [Fore.YELLOW + "Measurement IDs" + Fore.RESET,
                   Fore.YELLOW + "Type" + Fore.RESET,
                   Fore.YELLOW + "Table Name" + Fore.RESET,
                   Fore.YELLOW + "Result" + Fore.RESET,
                   Fore.YELLOW + "Summary" + Fore.RESET
                   ]
        data = []

        # Print the results
        for key, value in inner_data.items():
            #print(f"Key: {key}")
            #print(f"Result: {value['result']}")
            #print(f"Summary: {value['summary']}")
            #print(f"Error Summary: {value['errorSummary']}")
            #print("--------")

            dataArray = [Fore.GREEN + str(key) + Fore.RESET,
                         Fore.GREEN + str(value['type']) + Fore.RESET,
                         Fore.GREEN + str(value['tableName']) + Fore.RESET,
                         Fore.GREEN + str(value['result']) + Fore.RESET,
                         Fore.GREEN + str(value['summary']) +" "+ str(value['errorSummary']) + Fore.RESET
                         ]
            data.append(dataArray)

    printTabular(None, headers, data)
    verboseHandle.printConsoleWarning('');


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('MENU -> Batch Execute -> Execute')
    verboseHandle.printConsoleWarning('');
    try:
        # with Spinner():
        doValidate()
    except Exception as e:
        logger.error("Exception in MENU -> Batch Execute -> Execute" + str(e))
        verboseHandle.printConsoleError("Exception in MENU -> Batch Execute -> Execute" + str(e))
