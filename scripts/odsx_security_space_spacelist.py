#!/usr/bin/env python3
import os, requests,json
import signal

from colorama import Fore
from requests.auth import HTTPBasicAuth
from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from scripts.odsx_tieredstorage_undeploy import getManagerHost
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

def listDeployed(managerHost,username,password):
    global gs_space_dictionary_obj
    try:
        logger.info("managerHost :"+str(managerHost))
        response = requests.get("http://"+str(managerHost)+":8090/v2/spaces",auth = HTTPBasicAuth(username,password))
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Space List:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Name"+Fore.RESET,
                   # Fore.YELLOW+"Topology"+Fore.RESET,
                   # Fore.YELLOW+"Instances Id "+Fore.RESET,
                   ]
        gs_space_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_dictionary_obj : "+str(gs_space_dictionary_obj))
        counter=0
        dataTable=[]
        for data in jsonArray:
            dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                         Fore.GREEN+data["name"]+Fore.RESET,
                         # Fore.GREEN+data["topology"]["instances"]+Fore.RESET,
                         # Fore.GREEN+str(data["instancesIds"])+Fore.RESET
                         ]
            gs_space_dictionary_obj.add(str(counter+1),str(data["name"]))
            counter=counter+1
            dataTable.append(dataArray)
        printTabular(None,headers,dataTable)
        return gs_space_dictionary_obj
    except Exception as e:
        handleException(e)

def listSpaceFromHosts(managerNodes):
    username = ""
    password = ""
    appId=""
    safeId=""
    objectId=""
    signal.signal(signal.SIGINT, signal_handler)
    try:
        appId = str(readValuefromAppConfig("app.space.security.appId")).replace('"','')
        safeId = str(readValuefromAppConfig("app.space.security.safeId")).replace('"','')
        objectId = str(readValuefromAppConfig("app.space.security.objectId")).replace('"','')
        logger.info("appId : "+appId+" safeID : "+safeId+" objectID : "+objectId)

        if(len(str(managerNodes))>0):
            logger.info("managerNodes: main"+str(managerNodes))
            managerHost = getManagerHost(managerNodes)
            logger.info("managerHost : "+str(managerHost))
            if(len(str(managerHost))>0):
                logger.info("Manager Host :"+str(managerHost))
                managerHost= getManagerHost(managerNodes)
                username = str(getUsernameByHost(managerHost,appId,safeId,objectId))
                password = str(getPasswordByHost(managerHost,appId,safeId,objectId))
                listDeployed(managerHost,username,password)
            else:
                logger.info("Please check manager server status.")
                verboseHandle.printConsoleInfo("Please check manager server status.")
        else:
            logger.info("No Manager configuration found please check.")
            verboseHandle.printConsoleInfo("No Manager configuration found please check.")
    except Exception as e:
        verboseHandle.printConsoleError("Error in odsx_security_space_spacelist_list.py : "+str(e))
        logger.error("Exception in odsx_security_space_spacelist_list.py"+str(e))
        handleException(e)

    # managerHost= getManagerHost(managerNodes)
    # listDeployed(managerHost)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Space -> Space -> List")
    managerNodes = config_get_manager_node()
    listSpaceFromHosts(managerNodes)