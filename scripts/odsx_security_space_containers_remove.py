#!/usr/bin/env python3
import argparse
import json
import os
import sys

import requests
from colorama import Fore
from requests.auth import HTTPBasicAuth

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_dataIntegration_nodes, config_get_dataEngine_nodes
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_ssh import executeRemoteCommandAndGetOutput
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_db2feeder_utilities import getUsernameByHost, getPasswordByHost
from utils.odsx_print_tabular_data import printTabular, printTabularGrid

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
confirmCreateContainer = ''


class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR


def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    parser.add_argument('--host',
                        help='host ip',
                        required='True',
                        default='localhost')
    parser.add_argument('-u', '--user',
                        help='user name',
                        default='root')
    parser.add_argument('-dryrun', '--dryrun',
                        help='Dry run flag',
                        default='false', action='store_true')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])


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


class host_dictionary_obj(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

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


def getZoneList():
    try:
        response = requests.get("http://"+managerHost+":8090/v2/containers",auth = HTTPBasicAuth(username, password))
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
            spaceDict.update({counter: data})
            dataTable.append(dataArray)
        printTabularGrid(None,headers,dataTable)
    except Exception as e:
        handleException(e)
    return spaceDict


def getContainersList():
    containerRemoveType = str(
        input(Fore.YELLOW + "press [1] Show by zones. \nPress [Enter] for all. \nPress [99] for exit.: " + Fore.RESET))
    logger.info("containerRemoveType:" + str(containerRemoveType))
    filterArray = ''
    try:
        response = requests.get("http://" + managerHost + ":8090/v2/containers",auth = HTTPBasicAuth(username, password))
        logger.info("response.text : " + str(response.text))
        jsonArray = json.loads(response.text)

        if (str(containerRemoveType) == '1'):
            zoneList = getZoneList()
            zoneGSCNo = str(input(Fore.YELLOW + "Enter Srno. zone of GSC to remove : " + Fore.RESET))
            while (len(str(zoneGSCNo)) == 0):
                zoneGSCNo = str(input(Fore.YELLOW + "Enter Srno. zone of GSC to remove : " + Fore.RESET))
            zoneGSC = zoneList.get(int(zoneGSCNo))

            logger.info("zoneGSC :" + str(zoneGSC))
            zoneGSC = zoneGSC['zones'][0]
            filterArray = [x for x in jsonArray if x['zones'][0] == str(zoneGSC)]
        if (len(str(containerRemoveType)) == 0):
            filterArray = jsonArray
        verboseHandle.printConsoleWarning("List of containers:")
        headers = [Fore.YELLOW + "Sr No." + Fore.RESET,
                   Fore.YELLOW + "Container ID" + Fore.RESET,
                   Fore.YELLOW + "PID" + Fore.RESET,
                   Fore.YELLOW + "Zones" + Fore.RESET
                   ]
        counter = 0
        dataTable = []
        spaceDict = {}
        for data in filterArray:
            counter = counter + 1
            spaceDict.update({counter: data})
            dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                         Fore.GREEN + str(data["id"]) + Fore.RESET,
                         Fore.GREEN + str(data["pid"]) + Fore.RESET,
                         Fore.GREEN + str(data["zones"]) + Fore.RESET
                         ]
            dataTable.append(dataArray)
        printTabularGrid(None, headers, dataTable)
    except Exception as e:
        handleException(e)
    return spaceDict


def exitAndDisplay(isMenuDriven):
    logger.info("exitAndDisplay(isMenuDriven)")
    if (isMenuDriven == 'm'):
        logger.info("exitAndDisplay(isMenuDriven) : MenuDriven")
        os.system('python3 scripts/odsx_security_space_containers_remove.py' + ' ' + isMenuDriven)
    else:
        cliArgumentsStr = ''
        for arg in cliArguments:
            cliArgumentsStr += arg
            cliArgumentsStr += ' '
        os.system('python3 scripts/odsx_security_space_containers_remove.py' + ' ' + cliArgumentsStr)


def removeByContainer(containerid):
    logger.info("removeContainer")
    try:
        for data in containerid:
            commandToExecute = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh --username="+username+" --password="+password+" container kill " + str(
                data['id'])
            logger.info(commandToExecute)
            with Spinner():
                output = executeRemoteCommandAndGetOutput(managerHost, 'root', commandToExecute)
                logger.info("Output:" + str(output))
                print(output)
    except Exception as e:
        handleException(e)


# def getContainers():
#     try:
#         response = requests.get("http://" + managerHost + ":8090/v2/containers",auth = HTTPBasicAuth(username, password))
#         logger.info("response.text : " + str(response.text))
#         jsonArray = json.loads(response.text)
#         verboseHandle.printConsoleWarning("List of containers:")
#         headers = [Fore.YELLOW + "Sr No." + Fore.RESET,
#                    Fore.YELLOW + "Container ID" + Fore.RESET,
#                    Fore.YELLOW + "PID" + Fore.RESET,
#                    Fore.YELLOW + "Zones" + Fore.RESET
#                    ]
#         counter = 0
#         dataTable = []
#         zoneGSC = str(input(Fore.YELLOW + "Enter zone of GSC to remove [bll] : " + Fore.RESET))
#         while (len(str(zoneGSC)) == 0):
#             zoneGSC = 'bll'
#         logger.info("zoneGSC :" + str(zoneGSC))
#         filterArray = [x for x in jsonArray if x['zones'][0] == str(zoneGSC)]
#         filterData = json.dumps(filterArray)
#         spaceDict = {}
#         for data in filterData:
#             counter = counter + 1
#             spaceDict.update({counter: data})
#             dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
#                          Fore.GREEN + str(data["id"]) + Fore.RESET,
#                          Fore.GREEN + str(data["pid"]) + Fore.RESET,
#                          Fore.GREEN + str(data["zones"]) + Fore.RESET
#                          ]
#
#             dataTable.append(dataArray)
#         printTabularGrid(None, headers, dataTable)
#     except Exception as e:
#         handleException(e)
#     return spaceDict


def  removeByZone():
    logger.info("removeByZoner")
    try:
        zoneName = str(input(Fore.YELLOW + "Enter zone : " + Fore.RESET))
        confirm = str(input(Fore.YELLOW + "Are you sure want to container ? [yes (y)] / [no (n)] : " + Fore.RESET))
        while (len(str(confirm)) == 0):
            confirm = str(input(Fore.YELLOW + "Are you sure want to container ? [yes (y)] / [no (n)] : " + Fore.RESET))
        logger.info("confirm :" + str(confirm))
        if (confirm == 'yes' or confirm == 'y'):
            commandToExecute = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh --username="+username+" --password="+password+" container kill --zones=" + str(
                zoneName)
            logger.info(commandToExecute)
            with Spinner():
                output = executeRemoteCommandAndGetOutput(managerHost, 'root', commandToExecute)
                logger.info(output)
                print(output)
        elif confirm == 'no' or confirm == 'n':
            if isMenuDriven == 'm':
                logger.info("menudriven")
                os.system('python3 scripts/odsx_security_space_containers_remove.py' + ' ' + isMenuDriven)
    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Space -> Containers -> Remove\n')
    username = ""
    password = ""
    appId=""
    safeId=""
    objectId=""
    args = []
    menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
    args.append(sys.argv[0])
    try:
        optionMainMenu = ''
        choice = ''
        cliArguments = ''
        isMenuDriven = ''
        host = []
        appId = str(readValuefromAppConfig("app.space.security.appId")).replace('"','')
        safeId = str(readValuefromAppConfig("app.space.security.safeId")).replace('"','')
        objectId = str(readValuefromAppConfig("app.space.security.objectId")).replace('"','')
        logger.info("appId : "+appId+" safeID : "+safeId+" objectID : "+objectId)
        managerNodes = config_get_manager_node()
        logger.info("managerNodes: main" + str(managerNodes))
        managerHost = getManagerHost(managerNodes)
        logger.info(" Container list")
        # getContainers()

        username = str(getUsernameByHost(managerHost,appId,safeId,objectId))
        password = str(getPasswordByHost(managerHost,appId,safeId,objectId))
        exitMenu = True
        while exitMenu:
            streamDict = getContainersList()
            containerRemoveType = str(input(
                Fore.YELLOW + "press [1] if you want to remove container by Srno. \nPress [Enter] by zone. \nPress [99] for exit.: " + Fore.RESET))
            logger.info("containerRemoveType:" + str(containerRemoveType))
            verboseHandle.printConsoleInfo("Delete using single or multiple using comma (1,2,3)")
            if containerRemoveType == '1':
                optionMainMenu = str(input("Enter your srno to remove container: "))
                logger.info("Enter your srno to remove container:" + str(optionMainMenu))
                if optionMainMenu != 99:
                    removeList = [x.strip() for x in optionMainMenu.split(',')]
                    for data in removeList:
                        host.append(streamDict.get(int(data)))
                    choice = str(input(
                        Fore.YELLOW + "Are you sure want to remove server ? [yes (y)] / [no (n)] / [cancel (c)] :" + Fore.RESET))
                    while len(str(choice)) == 0:
                        choice = str(input(
                            Fore.YELLOW + "Are you sure want to remove server ? [yes (y)] / [no (n)] / [cancel (c)] :" + Fore.RESET))
                    logger.info("choice :" + str(choice))
                    if choice.casefold() == 'yes' or choice.casefold() == 'y':
                        removeByContainer(host)
                        host.clear()
            elif len(str(containerRemoveType)) == 0:
                removeByZone()
            elif containerRemoveType == '99':
                logger.info("99")
                exitMenu = False
    except Exception as e:
        handleException(e)
