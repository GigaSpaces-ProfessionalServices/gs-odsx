#!/usr/bin/env python3
import json
import os

import requests
from colorama import Fore
from requests.auth import HTTPBasicAuth
from scripts.odsx_security_dev_tieredstorage_deploy import displaySpaceHostWithNumber
from scripts.odsx_servers_manager_list import getGSInfo
from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_ssh import connectExecuteSSH, executeRemoteCommandAndGetOutput
from utils.ods_cluster_config import config_get_manager_node, config_get_space_hosts
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_db2feeder_utilities import host_dictionary_obj, getUsernameByHost, getPasswordByHost
from utils.odsx_keypress import userInputWrapper
from utils.odsx_print_tabular_data import printTabularGrid, printTabular

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR


def handleException(e):
    logger.info("handleException()")
    trace = []
    tb = e.__traceback__
    while tb is not None:
        trace.append({
            "filename": tb.tb_frame.f_code.co_filename,
            "name": tb.tb_frame.f_code.co_name,
            "lineno": tb.tb_lineno
        })
        tb = tb.tb_next
    logger.error(str({
        'type': type(e).__name__,
        'message': str(e),
        'trace': trace
    }))
    verboseHandle.printConsoleError((str({
        'type': type(e).__name__,
        'message': str(e),
        'trace': trace
    })))


def getManagerHostFromEnv():
    logger.info("getManagerHostFromEnv()")
    hosts = ''
    managerNodes = config_get_manager_node()
    for node in managerNodes:
        hosts += str(os.getenv(str(node.ip))) + ','
    hosts = hosts[:-1]
    return hosts


def getManagerHost(managerNodes):
    managerHost = ""
    try:
        logger.info("getManagerHost() : managerNodes :" + str(managerNodes))
        for node in managerNodes:
            status = getSpaceServerStatus(os.getenv(node.ip))
            if (status == "ON"):
                managerHost = os.getenv(node.ip)
        return managerHost
    except Exception as e:
        handleException(e)


def executeCommandForInstall(zone,host):

    logger.info("executeCommandForInstall(): start")
    try:
        dbaGigaDir=str(readValuefromAppConfig("app.giga.path"))
        path = str(readValuefromAppConfig("app.utilities.gcexplicit.file")).replace("/dbagiga/",dbaGigaDir)
        with Spinner():
            os.system('sh '+path+' -z '+zone+' -n '+host)
    except Exception as e:
        handleException(e)
    logger.info("executeCommandForInstall(): end")


def exitAndDisplay(isMenuDriven):
    logger.info("exitAndDisplay(isMenuDriven)")
    if (isMenuDriven == 'm'):
        logger.info("exitAndDisplay(MenuDriven) ")
        os.system('python3 scripts/odsx_utilities_gcexplicit.py' + ' ' + isMenuDriven)
    else:
        cliArgumentsStr = ''
        for arg in cliArguments:
            cliArgumentsStr += arg
            cliArgumentsStr += ' '
        os.system('python3 scripts/odsx_utilities_gcexplicit.py' + ' ' + cliArgumentsStr)

def remove_duplicate_items(_api_data, _key):
    logger.info("remove_duplicate_items()")
    unique_elements = []
    cleaned_data = []
    keys = []
    for i, j in enumerate(_api_data):
        if _api_data[i][_key] not in unique_elements:
            unique_elements.append(_api_data[i][_key])
            keys.append(i)
    for key in keys:
        cleaned_data.append(_api_data[key])
    return cleaned_data

# def getZoneList():
#     try:
#         response = requests.get("http://"+managerHost+":8090/v2/containers")
#         logger.info("response.text : "+str(response.text))
#         jsonArray = json.loads(response.text)
#         zoneList = remove_duplicate_items(jsonArray,'zones')
#         verboseHandle.printConsoleWarning("List of Zone:")
#         headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
#                    Fore.YELLOW+"Zones"+Fore.RESET
#                    ]
#         counter=0
#         dataTable=[]
#         spaceDict={}
#         for data in zoneList:
#             dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
#                          Fore.GREEN+str(data["zones"])+Fore.RESET
#                          ]
#             counter=counter+1
#             spaceDict.update({counter: data})
#             dataTable.append(dataArray)
#         printTabularGrid(None,headers,dataTable)
#     except Exception as e:
#         handleException(e)
#     return spaceDict

def managerHostList(spaceNodes):
    logger.info("managerHost : "+str(spaceNodes))
    try:
        with Spinner():
            headers = [Fore.YELLOW+"Srno."+Fore.RESET,
                       Fore.YELLOW+"Host"+Fore.RESET]
            data=[]
            count=0
            spaceDict={}

            for node in spaceNodes:
                count=count+1
                hostIp=os.getenv(str(node.ip))
                dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                           Fore.GREEN+str(hostIp)+Fore.RESET]
                spaceDict.update({count: hostIp})
                data.append(dataArray)

        printTabular(None,headers,data)
    except Exception as e:
        handleException(e)
    return spaceDict


def displaySummary():
    dbaGigaDir=str(readValuefromAppConfig("app.giga.path"))
    jcmd = str(readValuefromAppConfig("app.utilities.gcexplicit.file")).replace("/dbagiga/",dbaGigaDir)
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleWarning("***Summary***")
    print(Fore.GREEN+"1. "+
          Fore.GREEN+"jcmd_exec.sh path = "+
          Fore.GREEN+jcmd+Fore.RESET)
    verboseHandle.printConsoleWarning("------------------------------------------------------------")

def getZoneList():
    profile=str(readValuefromAppConfig("app.setup.profile"))
    if profile=='security':
        appId = str(readValuefromAppConfig("app.space.security.appId")).replace('"','')
        safeId = str(readValuefromAppConfig("app.space.security.safeId")).replace('"','')
        objectId = str(readValuefromAppConfig("app.space.security.objectId")).replace('"','')
        logger.info("appId : "+appId+" safeID : "+safeId+" objectID : "+objectId)
        username = str(getUsernameByHost(managerHost,appId,safeId,objectId))
        password = str(getPasswordByHost(managerHost,appId,safeId,objectId))
    try:
        if profile == 'security':
            response = requests.get("http://"+managerHost+":8090/v2/containers",auth = HTTPBasicAuth(username, password))
        else:
            response = requests.get("http://"+managerHost+":8090/v2/containers")
        logger.info("response.text : "+str(response.text))
        jsonArray = json.loads(response.text)
        zoneList = remove_duplicate_items(jsonArray,'zones')
        verboseHandle.printConsoleWarning("List of Zone:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Zones"+Fore.RESET
                   ]
        counter=0
        dataTable=[]
        spaceDict={}
        for data in zoneList:
            dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                         Fore.GREEN+str(data["zones"])+Fore.RESET
                         ]
            counter=counter+1
            spaceDict.update({counter: data["zones"][0]})
            dataTable.append(dataArray)
        printTabularGrid(None,headers,dataTable)
        return spaceDict
    except Exception as e:
        handleException(e)

if __name__ == '__main__':
    logger.info("Menu -> Utilities -> GC Explicit")
    verboseHandle.printConsoleWarning('Menu -> Utilities -> GC Explicit')
    try:
        streamResumeStream = ''
        optionMainMenu = ''
        choice = ''
        cliArguments = ''
        isMenuDriven = ''
        managerRemove = ''
        user = 'root'
        logger.info("user :" + str(user))

        managerNodes = config_get_manager_node()
        logger.info("managerNodes: main" + str(managerNodes))
        managerHost = getManagerHost(managerNodes)
        logger.info("managerNodes: main" + str(managerNodes))
        if (len(str(managerNodes)) > 0):
            spaceNodes = config_get_space_hosts()
            logger.info("spaceNodes: main" + str(spaceNodes))
            logger.info("managerHost : main" + str(managerHost))
            if (len(str(managerHost)) > 0):
                displaySummary()
                zoneList = getZoneList()
                zoneGSCNo = str(userInputWrapper(Fore.YELLOW + "Enter Zone Srno. : " + Fore.RESET))
                while (len(str(zoneGSCNo)) == 0):
                    zoneGSCNo = str(userInputWrapper(Fore.YELLOW + "Enter Zone  Srno. : " + Fore.RESET))
                zoneAddr=zoneList.get(int(zoneGSCNo))
                hostSpecific = str(userInputWrapper(Fore.YELLOW + "Do you want to run on specific host [y/n] [n]: " + Fore.RESET))
                while (len(str(hostSpecific)) == 0):
                    hostSpecific = 'n'
                if(hostSpecific == 'y' or hostSpecific == "Y"):
                    hostList=managerHostList(spaceNodes)
                    hostNo = str(userInputWrapper(Fore.YELLOW + "Enter host Srno. : " + Fore.RESET))
                    while (len(str(hostNo)) == 0):
                        hostNo = str(userInputWrapper(Fore.YELLOW + "Enter host Srno. : " + Fore.RESET))
                    hostAddr=hostList.get(int(hostNo))
                    executeCommandForInstall(zoneAddr,hostAddr)

                elif(hostSpecific == 'n' or hostSpecific == "N"):
                    hostList=managerHostList(spaceNodes)
                    for node in hostList:
                        executeCommandForInstall(zoneAddr,hostList.get(int(node)))
            else:
                logger.info("Please check manager server status.")
                verboseHandle.printConsoleInfo("Please check manager server status.")
        else:
            logger.info("No Manager configuration found please check.")
            verboseHandle.printConsoleInfo("No Manager configuration found please check.")

    except Exception as e:
        handleException(e)