#!/usr/bin/env python3

import os, time
from colorama import Fore
import requests, json, math
from scripts.logManager import LogManager
from utils.odsx_print_tabular_data import printTabular
from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_ssh import executeRemoteShCommandAndGetOutput, executeRemoteCommandAndGetOutputPython36, executeRemoteCommandAndGetOutput

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '[92m'  # GREEN
    WARNING = '[93m'  # YELLOW
    FAIL = '[91m'  # RED
    RESET = '[0m'  # RESET COLOR

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


def getManagerServerHostList():
    nodeList = config_get_manager_node()
    nodes=""
    for node in nodeList:
        #if(str(node.role).casefold() == 'server'):
        if(len(nodes)==0):
            nodes = node.ip
        else:
            nodes = nodes+','+node.ip
    return nodes

def getSpaceServerHostList():
    nodeList = config_get_space_hosts()
    nodes=""
    for node in nodeList:
        #if(str(node.role).casefold() == 'server'):
        if(len(nodes)==0):
            nodes = node.ip
        else:
            nodes = nodes+','+node.ip
    return nodes

def getOptions():
    logger.info("getOptions()")
    options = {}
    counter = 1
    options.update({counter : "Manager servers"})
    options.update({counter + 1: "Space servers"})
    #options.update({counter + 3: "By host name"})
    #options.update({counter + 3: "Northbound servers"})
    #options.update({counter + 4: "Cdc servers"})
    #options.update({counter + 5: "Specific servers"})
    options.update({99: "ESC"})
    return options


def cleanUpManagerServers():
    logger.info("cleanUpManagerServers()")
    managerNodes = config_get_manager_node()
    if(len(str(managerNodes))>0):
        logger.info("managerNodes: main"+str(managerNodes))
        verboseHandle.printConsoleInfo("Cleaning [/dbagigawork] and [/dbagigalogs]")
        managerHosts = getManagerServerHostList()
        confirm = str(input(Fore.YELLOW+"Are you sure want to delete above directories on [ "+str(managerHosts)+" ] ? (y/n) : "+Fore.RESET))
        if(confirm=='y' or len(confirm)==0):
            cmd = "rm -rf /dbagigawork/*;rm -f /dbagigalogs/*"
            user = 'root'
            for node in managerNodes:
                with Spinner():
                    output = executeRemoteCommandAndGetOutputPython36(node.ip, user, cmd)
                    if (output == 0):
                        verboseHandle.printConsoleInfo("Directories cleaned up on host :"+str(node.ip))
                    else:
                        verboseHandle.printConsoleError("Unable to clean directories on host :"+str(node.ip))
    else:
        logger.info("No Manager configuration found please check.")
        verboseHandle.printConsoleInfo("No Manager configuration found please check.")

def cleanUpSpaceServers():
    logger.info("cleanUpSpaceServers()")
    spaceNodes = config_get_space_hosts()
    if(len(str(spaceNodes))>0):
        logger.info("spaceNodes: main"+str(spaceNodes))
        verboseHandle.printConsoleInfo("Cleaning [/dbagigadata] ,[/dbagigalogs] and [GS_HOME/deploy] *exclude [GS_HOME/deploy/templates]")
        spaceHosts = getSpaceServerHostList()
        confirm = str(input(Fore.YELLOW+"Are you sure want to delete above directories on [ "+str(spaceHosts)+" ] ? (y/n) : "+Fore.RESET))
        if(confirm=='y' or len(confirm)==0):
            cmd = "rm -rf /dbagigadata/*;rm -f /dbagigalogs/*;source setenv.sh;cd $GS_HOME/deploy;find $GS_HOME/deploy/ -mindepth 1 -name templates -prune -o -exec rm -rf {} \;"
            user = 'root'
            for node in spaceNodes:
                with Spinner():
                    output = executeRemoteCommandAndGetOutputPython36(node.ip,user,cmd)
                    #if (output == 0):
                    verboseHandle.printConsoleInfo("Directories cleaned up on host :"+str(node.ip))
                    #else:
                    #    verboseHandle.printConsoleError("Unable to clean directories on host :"+str(node.ip))
    else:
        logger.info("No Manager configuration found please check.")
        verboseHandle.printConsoleInfo("No Manager configuration found please check.")

def showAndSelectOption():
    logger.info("showAndSelectOption()")
    print("\n")
    for key, value in getOptions().items():
        print("[" + str(key) + "] " + value)
    optionSelected = input("Enter your option [1]: ")
    if optionSelected == "":
        optionSelected = "1"
    elif int(optionSelected) == 99 :
        exit(0)
    elif int(optionSelected) > len(getOptions().items()):
        verboseHandle.printConsoleError("Invalid option selected")
        exit(0)
    print(optionSelected)
    logger.info("optionSelected :"+str(optionSelected))
    if(optionSelected=="1"):
        cleanUpManagerServers()
    elif(optionSelected=="2"):
        cleanUpSpaceServers()


if __name__ == '__main__':
    logger.info("odsx_utilities_cleandirectories_manager")
    verboseHandle.printConsoleWarning("Menu -> Utilitites -> Clean Directories")
    try:
        showAndSelectOption()

    except Exception as e:
        verboseHandle.printConsoleError("Eror in odsx_tieredstorage_undeployed : "+str(e))
        logger.error("Exception in tieredStorage_undeployed.py"+str(e))
        handleException(e)