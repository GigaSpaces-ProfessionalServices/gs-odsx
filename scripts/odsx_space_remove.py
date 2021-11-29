#!/usr/bin/env python3
import os
from colorama import Fore
from scripts.logManager import LogManager
import requests, json
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from scripts.odsx_space_createnewspace import listSpacesOnServer
from scripts.odsx_space_createnewspace import getManagerHost

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR


def proceedToRemoveSpace(spaceName,gs_space_host_dictionary_obj,managerNodes):
    managerHost = getManagerHost(managerNodes)
    logger.info("gs_space_host_dictionary_obj :"+str(gs_space_host_dictionary_obj)+" managerHost: "+str(managerHost))
    #spaceName = gs_space_host_dictionary_obj.get(spaceToRemove)

    logger.info("url:   http://"+managerHost+":8090/v2/pus/"+str(spaceName))
    response = requests.delete("http://"+managerHost+":8090/v2/pus/"+str(spaceName))
    logger.info(response.status_code)
    if(response.status_code==202):
        logger.info("Space "+str(spaceName)+" has been removed.")
        verboseHandle.printConsoleInfo("Space "+str(spaceName)+" has been removed.")
    else:
        logger.info("Space "+str(spaceName)+" has not been removed.")
        verboseHandle.printConsoleInfo("Space '"+str(spaceName)+"' has not been removed.")

def removeGSC(managerHost):
    response = requests.get("http://"+managerHost+":8090/v2/containers")
    jsonArray = json.loads(response.text)
    for data in jsonArray:
        response = requests.delete("http://"+managerHost+":8090/v2/containers/"+str(data["id"]))
        if(response.status_code==202):
            print("GSC ID "+str(data["id"])+" deleted")

def listSpaceFromHosts(managerNodes):
    gs_space_host_dictionary_obj = listSpacesOnServer(managerNodes)
    typeOfRemove = str(input("[1] If you want to remove individual space \n[enter] If you want remove all spaces."))
    if(typeOfRemove=='1'):
        spaceToRemove = str(input("Enter space serial number to remove :"))
        while(len(str(spaceToRemove))==0):
            spaceToRemove = str(input("Enter space serial number to remove :"))
        spaceToRemove = str(gs_space_host_dictionary_obj.get(spaceToRemove))
        spaceToRemoveConfirm = str(input("Are you sure want to remove space "+str(gs_space_host_dictionary_obj.get(spaceToRemove))+" (y/n) [y]"))
        if(len(str(spaceToRemoveConfirm))==0):
            spaceToRemoveConfirm='y'
        if(spaceToRemoveConfirm=='y'):
            proceedToRemoveSpace(spaceToRemove,gs_space_host_dictionary_obj,managerNodes)
    else:
        spaceToRemoveConfirm = str(input("Are you sure want to remove all spaces?(y/n) [y] :"))
        if(len(str(spaceToRemoveConfirm))==0):
            spaceToRemoveConfirm='y'
        if(spaceToRemoveConfirm=='y'):
            for i in range(1,len(gs_space_host_dictionary_obj)+1):
                spaceToRemove = str(gs_space_host_dictionary_obj.get(str(i)))
                print(spaceToRemove)
                proceedToRemoveSpace(spaceToRemove,gs_space_host_dictionary_obj,managerNodes)
    gscRemove = str(input(Fore.YELLOW+"Do you want to remove gsc? (y/n) :"+Fore.RESET))
    if(len(str(gscRemove))==0):
        gscRemove='y'
    if(gscRemove=='y'):
        managerHost = getManagerHost(managerNodes)
        removeGSC(managerHost)

if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Space -> Remove")
    managerNodes = config_get_manager_node()
    listSpaceFromHosts(managerNodes)

