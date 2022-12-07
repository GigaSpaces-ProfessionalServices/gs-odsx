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

    # dataValidatorServiceHost = str(userInputWrapper("Data validator service host ["+str(dataValidationHost)+"]: "))
    # if (len(str(dataValidatorServiceHost)) == 0):
    #    dataValidatorServiceHost = dataValidationHost

    dataValidatorServiceHost = dataValidationHost

    verboseHandle.printConsoleWarning('');
    verboseHandle.printConsoleWarning('Existing DataSource:');
    response = printDatasourcetable(dataValidatorServiceHost)
    
    if len(response) < 0:
        verboseHandle.printConsoleWarning("No dataSource available.")
        return

    datasourceId = str(userInputWrapper(Fore.YELLOW + "Enter dataSource id to edit: " + Fore.RESET))
    while (len(str(datasourceId)) == 0):
        datasourceId = str(userInputWrapper(Fore.YELLOW + "Enter dataSource id to edit: " + Fore.RESET))
    
    if response:
        for datasource in response:
            if str(datasource["id"]) == datasourceId:
                verboseHandle.printConsoleWarning('');
                verboseHandle.printConsoleWarning('Update values for datasource id:' + datasourceId);
                verboseHandle.printConsoleWarning('Note: Leave blank new value if you do not want to change the value');
                verboseHandle.printConsoleWarning('')
                
                dataSourceName= str(userInputWrapper("DataSource Name [Current value: '" + datasource["dataSourceName"] + "'] New value: "))
                if (len(str(dataSourceName)) == 0):
                    dataSourceName = datasource["dataSourceName"]
                else:    
                 while(dataSourceName in dataSourceNames):
                   if (len(str(dataSourceName)) == 0 or dataSourceName == datasource["dataSourceName"]):
                    dataSourceName = datasource["dataSourceName"]   
                    break
                   print(Fore.YELLOW +"A data source name with the same name already exists ["+dataSourceName+"]"+Fore.RESET)
                   dataSourceName = str(userInputWrapper("DataSource Name [Current value: '" + datasource["dataSourceName"] + "'] New value:"))
                      
                
                dataSource1Type = str(userInputWrapper("DataSource Type (gigaspaces/ms-sql/db2/mysql) [Current value: '" + datasource["dataSourceType"] + "'] New value: "))
                if (len(str(dataSource1Type)) == 0):
                           dataSource1Type = datasource["dataSourceType"]
                else:
                 while(dataSource1Type not in dataSourceTypes):
                   if (len(str(dataSource1Type)) == 0 or dataSource1Type == datasource["dataSourceType"]):
                    dataSource1Type = datasource["dataSourceType"]
                    break
                   print(Fore.YELLOW +"Please select DataSource Type from given list"+Fore.RESET)
                   dataSource1Type = str(userInputWrapper("DataSource Type (gigaspaces/ms-sql/db2/mysql) [Current value: '" + datasource["dataSourceType"] + "'] New value: "))
                  
                            
                dataSource1HostIp = str(userInputWrapper("DataSource Host Ip [Current value: '" + datasource["dataSourceHostIp"] + "'] New value: "))
                if (len(str(dataSource1HostIp)) == 0):
                            dataSource1HostIp = datasource["dataSourceHostIp"]
                dataSource1Port = str(userInputWrapper("DataSource Port [Current value: '" + datasource["dataSourcePort"] + "'] New value: "))
                if (len(str(dataSource1Port)) == 0):
                            dataSource1Port = datasource["dataSourcePort"]
                username1 = str(userInputWrapper("User name [Current value: '" + datasource["username"] + "'] New value: "))
                if (len(str(username1)) == 0):
                            username1 = datasource["username"]
                password1 = str(userInputWrapper("Password [Current value: '" + datasource["password"] + "'] New value: "))
                if (len(str(password1)) == 0):
                            password1 = datasource["password"]
                
                IntegratedSecurity = ''
                AuthenticationScheme=''
                Properties=''
                if (dataSource1Type == 'ms-sql'):
                 print(Fore.YELLOW +"If not use below properties , leave it blank"+Fore.RESET)
                
                 IntegratedSecurity = str(userInputWrapper("IntegratedSecurity [true/false] [Current value: '" + datasource["integratedSecurity"] + "'] New value:"))
                 while(IntegratedSecurity not in trueFalse):
                  print(Fore.YELLOW +"Please select IntegratedSecurity's value from given list"+Fore.RESET)
                  IntegratedSecurity = str(userInputWrapper("IntegratedSecurity [true/false] [Current value: '" + datasource["integratedSecurity"] + "'] New value:"))
                
                 AuthenticationScheme = str(userInputWrapper("AuthenticationScheme[JavaKerberos/NTLM] [Current value: '" + datasource["authenticationScheme"] + "'] New value:"))
                 while(AuthenticationScheme not in authenticationSchemes):
                  print(Fore.YELLOW +"Please select AuthenticationScheme's value from given list"+Fore.RESET)
                  AuthenticationScheme = str(userInputWrapper("AuthenticationScheme[JavaKerberos/NTLM] [Current value: '" + datasource["authenticationScheme"] + "'] New value:"))
                 
                 Properties = str(userInputWrapper("Connection properties( ex.Key=value;) [Current value: '" + datasource["properties"] + "'] New value:"))
                
                
                verboseHandle.printConsoleWarning('');
                data = {
                    "dataSourceId":datasourceId,
                    "dataSourceName":dataSourceName,
                    "dataSourceType": dataSource1Type,
                    "dataSourceHostIp": dataSource1HostIp,
                    "dataSourcePort": dataSource1Port,
                    "username": username1,
                    "password": password1,
                    "integratedSecurity":IntegratedSecurity,
                    "authenticationScheme":AuthenticationScheme,
                    "properties":Properties
                }
                headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
                response = requests.post("http://" + dataValidatorServiceHost + ":"+str(readValuefromAppConfig("app.dv.server.port"))+"/datasource/update"
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
