#!/usr/bin/env python3
import os, requests,json
import signal

from colorama import Fore
from requests.auth import HTTPBasicAuth
from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from scripts.odsx_tieredstorage_undeploy import getManagerHost
from utils.ods_ssh import executeRemoteCommandAndGetOutput
from utils.odsx_db2feeder_utilities import getUsernameByHost, getPasswordByHost
from utils.odsx_print_tabular_data import printTabular
from utils.ods_cleanup import signal_handler


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

def listDeployed(managerHost,spaceName):
    try:
        logger.info("managerHost :"+str(managerHost))
        response = requests.get("http://"+str(managerHost)+":8090/v2/spaces/"+str(spaceName)+"/instances",auth = HTTPBasicAuth(username,password))
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Resources on cluster:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Instances"+Fore.RESET,
                   Fore.YELLOW+"Mode"+Fore.RESET,
                   Fore.YELLOW+"HostId"+Fore.RESET,
                   Fore.YELLOW+"Container Ids"+Fore.RESET
                   # Fore.YELLOW+"Suspend Type "+Fore.RESET
                   ]
        gs_space_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_dictionary_obj : "+str(gs_space_dictionary_obj))
        counter=0
        dataTable=[]
        spaceDict = {}
        for data in jsonArray:
            counter=counter+1
            dataArray = [Fore.GREEN+str(counter)+Fore.RESET,
                         Fore.GREEN+data["id"]+Fore.RESET,
                         Fore.GREEN+data["mode"]+Fore.RESET,
                         Fore.GREEN+str(data["hostId"])+Fore.RESET,
                         Fore.GREEN+str(data["containerId"])+Fore.RESET
                         ]
            spaceDict.update({counter: data})
            dataTable.append(dataArray)
        printTabular(None,headers,dataTable)
    except Exception as e:
        handleException(e)
    return spaceDict

def listOfSpacename(managerHost):
    try:
        logger.info("managerHost :"+str(managerHost))
        response = requests.get("http://"+str(managerHost)+":8090/v2/spaces/",auth = HTTPBasicAuth(username,password))
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Instance of space:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Name"+Fore.RESET
                   ]
        gs_space_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_dictionary_obj : "+str(gs_space_dictionary_obj))
        counter=0
        dataTable=[]
        # spaceDict = {}
        for data in jsonArray:
            # spaceDict.update({counter: data})
            dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                         Fore.GREEN+data["name"]+Fore.RESET
                         ]
            gs_space_dictionary_obj.add(str(counter+1),str(data["name"]))
            counter=counter+1
            dataTable.append(dataArray)
        printTabular(None,headers,dataTable)
        return gs_space_dictionary_obj
    except Exception as e:
        handleException(e)

def instancelistFromHosts(managerNodes):
    global instanceList
    optionMainMenu = ''
    signal.signal(signal.SIGINT, signal_handler)
    try:
        if(len(str(managerNodes))>0):
            logger.info("managerNodes: main"+str(managerNodes))
            managerHost = getManagerHost(managerNodes)
            logger.info("managerHost : "+str(managerHost))
            if(len(str(managerHost))>0):
                logger.info("Manager Host :"+str(managerHost))
                spacename = listOfSpacename(managerHost)
                if(len(spacename)>0):
                    optionMainMenu = str(input("Enter your space srno. for instance remove: "))
                    logger.info("Enter your space srno. for instance list:" + str(optionMainMenu))

                    if len(spacename) >= int(optionMainMenu):
                        host = spacename.get(optionMainMenu)
                        instanceList = listDeployed(managerHost,host)
                else:
                    logger.info("No Space Found.")
                    verboseHandle.printConsoleInfo("No Space Found.")
            else:
                logger.info("Please check manager server status.")
                verboseHandle.printConsoleInfo("Please check manager server status.")
        else:
            logger.info("No Manager configuration found please check.")
            verboseHandle.printConsoleInfo("No Manager configuration found please check.")
    except Exception as e:
        verboseHandle.printConsoleError("Error in odsx_space_space_instances_list.py : "+str(e))
        logger.error("Exception in odsx_space_space_instances_list.py"+str(e))
        handleException(e)
    return instanceList

def removeInstanceContainer(hosts):
    logger.info("removeInstanceContainer")
    try:
        for instance in hosts:
            commandToExecute = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh --username="+username+" --password="+password+" container kill " + str(instance['containerId'])
            logger.info(commandToExecute)
            with Spinner():
                output = executeRemoteCommandAndGetOutput(managerHost, 'root', commandToExecute)
                logger.info("Output:" + str(output))
                print(output)
    except Exception as e:
        handleException(e)

if __name__ == '__main__':
    isMenuDriven =''
    verboseHandle.printConsoleWarning("Menu -> Space -> Space -> Instances -> Remove")
    optionMainMenu = ''
    username = ""
    password = ""
    appId=""
    safeId=""
    objectId=""
    host = []
    value = []
    appId = str(readValuefromAppConfig("app.space.security.appId")).replace('"','')
    safeId = str(readValuefromAppConfig("app.space.security.safeId")).replace('"','')
    objectId = str(readValuefromAppConfig("app.space.security.objectId")).replace('"','')
    logger.info("appId : "+appId+" safeID : "+safeId+" objectID : "+objectId)
    signal.signal(signal.SIGINT, signal_handler)
    try:

        exitMenu = True
        while exitMenu:
            managerNodes = config_get_manager_node()
            managerHost = getManagerHost(managerNodes)
            username = str(getUsernameByHost(managerHost,appId,safeId,objectId))
            password = str(getPasswordByHost(managerHost,appId,safeId,objectId))
            streamDict = instancelistFromHosts(managerNodes)
            containerRemoveType = str(input(
                Fore.YELLOW + "press [1] if you want to remove container by Srno. \nPress [99] for exit.: " + Fore.RESET))
            logger.info("containerRemoveType:" + str(containerRemoveType))
            verboseHandle.printConsoleInfo("Delete using single or range(1-3)")
            if containerRemoveType == '1':
                optionMainMenu = str(input("Enter your srno to remove container: "))
                logger.info("Enter your srno to remove container:" + str(optionMainMenu))

                if optionMainMenu != '99':
                    confirm=''
                    confirm = str(input(Fore.YELLOW+"Are you sure want to remove instance container ? [yes (y)] / [no (n)] : "+Fore.RESET))
                    while(len(str(confirm))==0):
                        confirm = str(input(Fore.YELLOW+"Are you sure want to remove instance container ? [yes (y)] / [no (n)] : "+Fore.RESET))
                    logger.info("confirm :"+str(confirm))
                    if(confirm=='yes' or confirm=='y'):
                        if ('-' in str(optionMainMenu)):
                            host = optionMainMenu.split('-')
                            if(len(host) == 2):
                                firstIndex = int(host[0])
                                lastIndex = int(host[-1])
                                for data in range(firstIndex,lastIndex):
                                    value.append(streamDict.get(int(data)))
                                removeInstanceContainer(value)
                                value.clear()
                            else:
                                verboseHandle.printConsoleError("Please enter two integer only")
                        else:
                            value.append(streamDict.get(int(optionMainMenu)))
                            removeInstanceContainer(value)
                            value.clear()
                    elif(confirm =='no' or confirm=='n'):
                        if(isMenuDriven=='m'):
                            logger.info("menudriven")
                            os.system('python3 scripts/odsx_security_space_space_instances_remove.py'+' '+isMenuDriven)
            elif(str(containerRemoveType) == '99'):
                exitMenu = False
    except Exception as e:
        verboseHandle.printConsoleError("Eror in odsx_security_space_space_instances_remove.py : "+str(e))
        logger.error("Exception in odsx_security_space_space_instances_remove.py"+str(e))
        handleException(e)