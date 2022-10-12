#!/usr/bin/env python3
import json
import os
import requests
from colorama import Fore
from requests.auth import HTTPBasicAuth
from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_ssh import executeRemoteCommandAndGetOutput
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_db2feeder_utilities import getPasswordByHost, getUsernameByHost
from utils.odsx_print_tabular_data import printTabularGrid, printTabular

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

def createContainers(managerHost,hostData):
    logger.info("createContainers()")
    global numberOfGSC
    global zoneGSC
    global memoryContainer
    global createcontainer
    global hostName

    try:
        hostName = ''
        while (len(str(hostName)) == 0):
            hostName=str(input(Fore.YELLOW + "Enter host Srno. : " + Fore.RESET))
            hostId = hostData.get(int(hostName))
            logger.info("host  :" + str(hostId))

        numberOfGSC = str(input(Fore.YELLOW + "Enter number of GSCs per host [1] : " + Fore.RESET))
        while (len(str(numberOfGSC)) == 0):
            numberOfGSC = 1
        logger.info("numberOfGSC :" + str(numberOfGSC))

        zoneGSC = str(input(Fore.YELLOW + "Enter zone of GSC to create [bll] : " + Fore.RESET))
        while (len(str(zoneGSC)) == 0):
            zoneGSC = 'bll'
        logger.info("zoneGSC :" + str(zoneGSC))

        memoryGSC = str(input(Fore.YELLOW + "Enter memory of GSC [4g] : " + Fore.RESET))
        while (len(str(memoryGSC)) == 0):
            memoryGSC = '4g'

        confirmCreateContainer = str(input(Fore.YELLOW + "Do you want to create container ? (y/n) [y] : "))

        if (len(str(confirmCreateContainer)) == 0 or confirmCreateContainer == 'y' or confirmCreateContainer == 'yes'):

            commandToExecute = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh --username="+username+" --password="+password+" container create --count=" + str(numberOfGSC) + " --zone=" + str(zoneGSC) + " --memory=" + str(memoryGSC) + " " + str(hostId)
            logger.info(commandToExecute)
            with Spinner():
                output = executeRemoteCommandAndGetOutput(managerHost, 'root', commandToExecute)
                logger.info("Output:" + str(output))
                print(output)

        elif(confirmCreateContainer =='no' or confirmCreateContainer=='n'):
            if(isMenuDriven=='m'):
                logger.info("menudriven")
                os.system('python3 scripts/odsx_security_space_containers_create.py'+' '+isMenuDriven)

        # commandToExecute = "container create --count="+str(numberOfGSC)+" --zone="+str(zoneGSC)+" --memory="+str(memoryGSC)+" "+str(hostName)
    except Exception as e:
        handleException(e)

def getContainers():
    try:
        response = requests.get("http://"+managerHost+":8090/v2/containers",auth = HTTPBasicAuth(username, password))
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

def get_gs_host_details(managerHost):
    logger.info("get_gs_host_details()")
    response = requests.get('http://'+managerHost+':8090/v2/hosts', headers={'Accept': 'application/json'},auth = HTTPBasicAuth(username, password))

    jsonArray = json.loads(response.text)
    gs_servers_host_dictionary_obj = host_dictionary_obj()
    for data in jsonArray:
        gs_servers_host_dictionary_obj.add(str(data['address']),str(data['address']))
    return gs_servers_host_dictionary_obj

def hostList():
    try:
        logger.debug("listing space host")
        logger.info("hostList()")
        spaceServers = config_get_space_hosts()
        headers = [Fore.YELLOW + "Sr No." + Fore.RESET,
                   Fore.YELLOW + "Host" + Fore.RESET
                   ]
        data = []
        counter = 0
        spaceDict = {}
        for server in spaceServers:
            host = os.getenv(server.ip)
            counter = counter + 1
            spaceDict.update({counter: host})
            dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                         Fore.GREEN + host + Fore.RESET]
            data.append(dataArray)
        printTabular(None, headers, data)

    except Exception as e:
        logger.error("Error in odsx_space_container_create " + str(e))
    return spaceDict


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Space -> Containers -> Create\n')
    isMenuDriven=''
    username = ""
    password = ""
    appId=""
    safeId=""
    objectId=""
    try:
        appId = str(readValuefromAppConfig("app.space.security.appId")).replace('"','')
        safeId = str(readValuefromAppConfig("app.space.security.safeId")).replace('"','')
        objectId = str(readValuefromAppConfig("app.space.security.objectId")).replace('"','')
        logger.info("appId : "+appId+" safeID : "+safeId+" objectID : "+objectId)
        managerNodes = config_get_manager_node()
        logger.info("managerNodes: main" + str(managerNodes))
        managerHost= getManagerHost(managerNodes)
        logger.info("managerNodes: main" + str(managerNodes))
        if (len(str(managerNodes)) > 0):
            spaceNodes = config_get_space_hosts()
            logger.info("managerHost : main" + str(managerHost))
            username = str(getUsernameByHost(managerHost,appId,safeId,objectId))
            password = str(getPasswordByHost(managerHost,appId,safeId,objectId))
            hostID = hostList()
            exitMenu = True
            while exitMenu:
                containerRemoveType = str(input(
                    Fore.YELLOW + "press [Enter] if you want to Create container. \nPress [99] for exit.: " + Fore.RESET))
                logger.info("containerRemoveType:" + str(containerRemoveType))
                if len(str(containerRemoveType)) == 0:
                    createContainers(managerHost, hostID)
                elif containerRemoveType == '99':
                    logger.info("99")
                    exitMenu = False
        else:
            logger.info("No Manager configuration found please check.")
            verboseHandle.printConsoleInfo("No Manager configuration found please check.")

    except Exception as e:
        handleException(e)