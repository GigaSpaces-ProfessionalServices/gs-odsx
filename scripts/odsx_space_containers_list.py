#!/usr/bin/env python3

import json
import os

import requests
from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_dataIntegration_nodes, config_get_dataEngine_nodes
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_ssh import executeRemoteCommandAndGetOutput, executeRemoteCommandAndGetOutputValuePython36
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_keypress import userInputWithEscWrapper
from utils.odsx_print_tabular_data import printTabular, printTabularGrid

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
confirmCreateContainer = ''

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
            spaceDict.update({counter: data})
            dataTable.append(dataArray)
        printTabularGrid(None,headers,dataTable)
    except Exception as e:
        handleException(e)
    return spaceDict
def getManagerHost(managerNodes):
    managerHost=""
    try:
        logger.info("getManagerHost() : managerNodes :"+str(managerNodes))
        for node in managerNodes:
            status = getSpaceServerStatus(os.getenv(node.ip))
            if(status=="ON"):
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

def getContainersbyZone():

    try:

        response = requests.get("http://"+managerHost+":8090/v2/containers")
        logger.info("response.text : "+str(response.text))
        jsonArray = json.loads(response.text)
        zoneList = getZoneList()

        zoneGSCNo = str(input(Fore.YELLOW + "Enter Srno. zone of GSC to show : " + Fore.RESET))

        while (len(str(zoneGSCNo)) == 0):
            zoneGSCNo = str(input(Fore.YELLOW + "Enter Srno. zone of GSC to show : " + Fore.RESET))

        zoneGSC = zoneList.get(int(zoneGSCNo))

        zoneGSC = zoneGSC['zones'][0]

        verboseHandle.printConsoleWarning("List of containers:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Container ID"+Fore.RESET,
                   Fore.YELLOW+"PID"+Fore.RESET,
                   Fore.YELLOW+"Zones"+Fore.RESET
                   ]
        logger.info("zoneGSC :" + str(zoneGSC))
        filterArray = [x for x in jsonArray if x['zones'][0] == str(zoneGSC)]

        counter=0
        dataTable=[]
        for data in filterArray:
            dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                         Fore.GREEN+data["id"]+Fore.RESET,
                         Fore.GREEN+str(data["pid"])+Fore.RESET,
                         Fore.GREEN+str(data["zones"])+Fore.RESET
                         ]
            counter=counter+1
            dataTable.append(dataArray)
        printTabularGrid(None,headers,dataTable)
    except Exception as e:
        handleException(e)

def getContainersbyHost():
    hostName = str(input(Fore.YELLOW + "Enter host  : " + Fore.RESET))
    logger.info("host  :" + str(hostName))

    commandToExecute = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh container list "+str(hostName)
    logger.info(commandToExecute)
    with Spinner():
        output = executeRemoteCommandAndGetOutput(managerHost, 'root', commandToExecute)
        logger.info("Output:" + str(output))
        print(output)

def getContainers():
    try:
        response = requests.get("http://"+managerHost+":8090/v2/containers")
        logger.info("response.text : "+str(response.text))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("List of containers:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Container ID"+Fore.RESET,
                   Fore.YELLOW+"PID"+Fore.RESET,
                   Fore.YELLOW+"Zones"+Fore.RESET
                   ]
        counter=0
        dataTable=[]

        for data in jsonArray:
            dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                         Fore.GREEN+data["id"]+Fore.RESET,
                         Fore.GREEN+str(data["pid"])+Fore.RESET,
                         Fore.GREEN+str(data["zones"])+Fore.RESET
                         ]
            counter=counter+1
            dataTable.append(dataArray)
        printTabularGrid(None,headers,dataTable)
    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Space -> Containers -> List\n')
    try:
        managerNodes = config_get_manager_node()
        logger.info("managerNodes: main" + str(managerNodes))
        managerHost = getManagerHost(managerNodes)
        logger.info(" Container list")
        exitMenu = True
        while exitMenu:
            containerListType = str(userInputWithEscWrapper(Fore.YELLOW+"press [1] For Zone. \nPress [Enter] for All. \nPress [99] for exit.: "+Fore.RESET))
            logger.info("containerRemoveType:"+str(containerListType))
            if(containerListType=='1'):
                 getContainersbyZone()
            elif(len(str(containerListType))==0):
                getContainers()
            elif(containerListType =='99'):
                logger.info("99")
                exitMenu = False
    except Exception as e:
        handleException(e)
