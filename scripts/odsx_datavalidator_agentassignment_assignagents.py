#!/usr/bin/env python3

import json
import os.path
import requests
from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_datavalidator_install_list import getDataValidationHost
from utils.ods_cluster_config import config_get_dataValidation_nodes
from utils.odsx_keypress import userInputWithEscWrapper
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


    # dataValidatorServiceHost = str(userInputWrapper("Data validator service host ["+str(dataValidationHost)+"]: "))
    # if (len(str(dataValidatorServiceHost)) == 0):
    #    dataValidatorServiceHost = dataValidationHost

    dataValidatorServiceHost = dataValidationHost


    ##  Print Agents
    verboseHandle.printConsoleWarning('');
    verboseHandle.printConsoleWarning('Available Agents:');
    resultCount = printAgenttable(dataValidatorServiceHost)

    if resultCount <= 0:
        verboseHandle.printConsoleWarning("No agents available. Please add one")
        return

    agentId = str(userInputWithEscWrapper("Select Agent Id from list \n OR [99] ESC:"))
    while(len(agentId) == 0):
        print(Fore.YELLOW +"Agent Id is invalid or Empty"+Fore.RESET)
        agentId = str(userInputWithEscWrapper("Select Agent Id from list \n OR [99] ESC:"))

    if(agentId=='99'):
        return

    verboseHandle.printConsoleWarning('');
    verboseHandle.printConsoleWarning('Available Unassigned DataSource:');
    resultCount = printDatasourcetable(dataValidatorServiceHost)
    #print("DS count: "+str(resultCount))
    if resultCount <= 0:
        verboseHandle.printConsoleWarning("No dataSource available. Please add one")
        return

    verboseHandle.printConsoleWarning('');
    #verboseHandle.printConsoleWarning('Select Data Source:');

    dataSourceIds = str(userInputWithEscWrapper("Select data source id from list.You can specify multiple Ids with comma separated \n OR [99] ESC:"))
    while(len(dataSourceIds) == 0):
        print(Fore.YELLOW +"DataSource Id is invalid (Empty)"+Fore.RESET)
        dataSourceIds = str(userInputWithEscWrapper("Select data source id from list.You can specify multiple Ids with comma separated \n OR [99] ESC:"))
        #while(dataSourceName in dataSourceNames):
        #     print(Fore.YELLOW +"A data source name with the same name already exists ["+dataSourceName+"]"+Fore.RESET)
        #     dataSourceName = str(userInputWrapper("DataSource Name:"))
    if(dataSourceIds=='99'):
        return

    verboseHandle.printConsoleWarning('');
    data = {
        }
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post("http://" + dataValidatorServiceHost + ":"+str(readValuefromAppConfig("app.dv.server.port"))+"/assignment/add/"+agentId+"/"+dataSourceIds
                                 , data=json.dumps(data)
                                 , headers=headers)

    logger.info(str(response.status_code))
    jsonArray = json.loads(response.text)

    verboseHandle.printConsoleWarning("")
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleInfo("  " + jsonArray["response"])
    verboseHandle.printConsoleWarning("------------------------------------------------------------")

dataSourceNames=[]
trueFalse=["true","false",""]
authenticationSchemes = ["JavaKerberos","NTLM",""]
dataSourceTypes=["gigaspaces","ms-sql","db2","mysql",""]
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
                   Fore.YELLOW + "Type" + Fore.RESET
                   ]
        data = []
        if response:
            for datasource in response:
                if datasource["agentHostIp"] != "-1":
                    continue
                dataSourceNames.append(datasource["dataSourceName"] )

                dataArray = [Fore.GREEN + str(datasource["id"]) + Fore.RESET,
                             Fore.GREEN + datasource["dataSourceName"] + Fore.RESET,
                             Fore.GREEN + datasource["dataSourceType"] + Fore.RESET
                             ]
                data.append(dataArray)

        printTabular(None, headers, data)
        verboseHandle.printConsoleWarning('');
        return len(response)
    return 0

def printAgenttable(dataValidatorServiceHost):
    try:
        response = requests.get("http://" + dataValidatorServiceHost + ":"+str(readValuefromAppConfig("app.dv.server.port"))+"/agent/list")
    except:
        print("An exception occurred")

    if response.status_code == 200:
        # logger.info(str(response.status_code))
        jsonArray = json.loads(response.text)
        response = json.loads(jsonArray["response"])
        # print("response2 "+response[0])
        # print(isinstance(response, list))

        headers = [Fore.YELLOW + "Agent Id" + Fore.RESET,
                   Fore.YELLOW + "Host Ip" + Fore.RESET
                   ]
        data = []
        if response:
            for datasource in response:
                dataArray = [Fore.GREEN + str(datasource["id"]) + Fore.RESET,
                             Fore.GREEN + datasource["hostIp"] + Fore.RESET
                             ]
                data.append(dataArray)

        printTabular(None, headers, data)
        verboseHandle.printConsoleWarning('');
        return len(response)
    return 0


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('MENU -> Data Validator -> Agent Assignment -> Assign Agents')
    verboseHandle.printConsoleWarning('');
    try:
        doValidate()
    except Exception as e:
        logger.error("Exception in Menu->Validators " + str(e))
        verboseHandle.printConsoleError("Exception in Menu->Validators " + str(e))
