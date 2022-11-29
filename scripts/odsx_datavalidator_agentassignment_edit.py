#!/usr/bin/env python3

import json
import os.path
import requests
from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_datavalidator_agentassignment_list import printAssignmentTable
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
    verboseHandle.printConsoleWarning('Existing Agent Assignments:');
    response = printAssignmentTable(dataValidatorServiceHost)
    
    if len(response) < 0:
        verboseHandle.printConsoleWarning("No assignments available.")
        return

    editAgentId = str(input(Fore.YELLOW + "Enter agent id to edit: " + Fore.RESET))
    while (len(str(editAgentId)) == 0):
        editAgentId = str(input(Fore.YELLOW + "Enter agent id to edit: " + Fore.RESET))


    if response:
            assignDataSources=""
            for agentDSrow in response:
                agentId =str(agentDSrow["agentId"])
                if (agentId == editAgentId):
                    assignDataSources+=str(agentDSrow["dataSourceId"])
                    assignDataSources+=","

            if(len(assignDataSources)>0):
                assignDataSources = assignDataSources[:-1]

            verboseHandle.printConsoleWarning('');
            verboseHandle.printConsoleWarning('Update values for agent id:' + editAgentId);
            verboseHandle.printConsoleWarning('Note: Leave blank new value if you do not want to change the value');
            verboseHandle.printConsoleWarning('')

            verboseHandle.printConsoleWarning('');
            verboseHandle.printConsoleWarning('Existing DataSources:');
            printDatasourcetable(dataValidatorServiceHost)

            dataSourceIds= str(input("Assign DataSources [Current value: '" + assignDataSources + "'] New value: "))
            if (len(str(dataSourceIds)) == 0):
                dataSourceIds = assignDataSources

            verboseHandle.printConsoleWarning('');
            data = {}
            headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
            response = requests.post("http://" + dataValidatorServiceHost + ":"+str(readValuefromAppConfig("app.dv.server.port"))+"/assignment/update/"+editAgentId+"/"+dataSourceIds
                                             , data=json.dumps(data)
                                             , headers=headers)

            logger.info(str(response.status_code))
            jsonArray = json.loads(response.text)

            verboseHandle.printConsoleWarning("")
            verboseHandle.printConsoleWarning("------------------------------------------------------------")
            verboseHandle.printConsoleInfo("  " + jsonArray["response"])
            verboseHandle.printConsoleWarning("------------------------------------------------------------")

dataSourceNames=[]
dataSourceNames.append("")
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
                   Fore.YELLOW + "Type" + Fore.RESET , 
                   Fore.YELLOW + "Host Ip" + Fore.RESET
                   ]
        data = []
        if response:
            for datasource in response:
                #print(datasource)
                dataSourceNames.append(datasource["dataSourceName"] )
                
                dataArray = [Fore.GREEN + str(datasource["id"]) + Fore.RESET,
                             Fore.GREEN + datasource["dataSourceName"] + Fore.RESET,
                             Fore.GREEN + datasource["dataSourceType"] + Fore.RESET,
                             Fore.GREEN + datasource["dataSourceHostIp"] + Fore.RESET
                             ]
                data.append(dataArray)

        printTabular(None, headers, data)
        verboseHandle.printConsoleWarning('');
        return response
    return 0



if __name__ == '__main__':
    logger.info("MENU -> Data Validator -> Data Source Registration -> Edit")
    verboseHandle.printConsoleWarning('MENU -> Data Validator -> Data Source Registration -> Edit')
    verboseHandle.printConsoleWarning('');
    try:
        # with Spinner():
        doValidate()
    except Exception as e:
        logger.error("Exception in Menu->Validators" + str(e))
        verboseHandle.printConsoleError("Exception in Menu->Validators" + str(e))
