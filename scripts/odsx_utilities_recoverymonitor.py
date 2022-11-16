#!/usr/bin/env python3
import argparse
import json
import os
import sys

import requests
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_dataIntegration_nodes, config_get_dataValidation_nodes, \
    config_get_manager_node, config_get_space_hosts
from utils.ods_ssh import executeRemoteShCommandAndGetOutput, executeRemoteCommandAndGetOutputPython36, \
    executeRemoteCommandAndGetOutput
from scripts.spinner import Spinner
from scripts.odsx_datavalidator_list import listDVServers
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_db2feeder_utilities import host_dictionary_obj
from utils.odsx_print_tabular_data import printTabular

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


def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])

def getDVServerHostList():
    nodeList = config_get_dataValidation_nodes()
    nodes=""
    for node in nodeList:
        #if(str(node.role).casefold() == 'server'):
        if(len(nodes)==0):
            nodes = node.ip
        else:
            nodes = nodes+','+node.ip
    return nodes

def startDataValidationService(args):
    try:
        listDVServers()
        nodes = getDVServerHostList()
        choice = str(input(Fore.YELLOW+"Are you sure, you want to start data validation service for ["+str(nodes)+"] ? (y/n)"+Fore.RESET))
        if choice.casefold() == 'n':
            exit(0)
        for node in config_get_dataValidation_nodes():
            cmd = "systemctl start odsxdatavalidation.service"
            logger.info("Getting status.. odsxdatavalidation:"+str(cmd))
            user = 'root'
            with Spinner():
                output = executeRemoteCommandAndGetOutputPython36(node.ip, user, cmd)
                if (output == 0):
                    verboseHandle.printConsoleInfo("Service data validation started successfully on "+str(node.ip))
                else:
                    verboseHandle.printConsoleError("Service data validation failed to start")

    except Exception as e:
        handleException(e)

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

def managerHostList(managerHost):
    logger.info("managerHost : "+str(managerHost))
    try:
        with Spinner():
            if(len(str(managerHost))>0):
                # getGSInfo(managerHost)
                print("hello")
            else:
                logger.info("Unable to retrive GS Info no manager status ON.")
                verboseHandle.printConsoleInfo("Unable to retrive GS Info no manager status ON.")
            headers = [Fore.YELLOW+"Srno."+Fore.RESET,
                       Fore.YELLOW+"Host"+Fore.RESET]
            data=[]
            managerNodes = config_get_manager_node()
            count=0
            spaceDict={}

            for node in managerNodes:
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

def listDeployed(managerHost):
    global gs_space_dictionary_obj
    try:
        logger.info("managerHost :"+str(managerHost))
        response = requests.get("http://"+str(managerHost)+":8090/v2/spaces")
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



def executeCommandForInstall(space):

    logger.info("executeCommandForInstall(): start")
    try:
        path = str(readValuefromAppConfig("app.utilities.recoverymonitor.file"))
        with Spinner():
            os.system('python3 '+path+' '+space)
    except Exception as e:
        handleException(e)
    logger.info("executeCommandForInstall(): end")

def displaySummary():
    jcmd = str(readValuefromAppConfig("app.utilities.recoverymonitor.file"))
    spaceName = str(readValuefromAppConfig("app.utilities.recovery.monitor.space.name"))
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleWarning("***Summary***")
    print(Fore.GREEN+"1. "+
          Fore.GREEN+"Recovery monitor file path = "+
          Fore.GREEN+jcmd+Fore.RESET)
    print(Fore.GREEN+"2. "+
          Fore.GREEN+"Space name = "+
          Fore.GREEN+spaceName+Fore.RESET)
    verboseHandle.printConsoleWarning("------------------------------------------------------------")


if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Utilities -> Recovery Monitor")
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
            displaySummary()
            logger.info("spaceNodes: main" + str(spaceNodes))
            logger.info("managerHost : main" + str(managerHost))
            if (len(str(spaceNodes)) > 0):
                hostNo = str(readValuefromAppConfig("app.utilities.recovery.monitor.space.name"))
                executeCommandForInstall(hostNo)
            else:
                logger.info("Please check space server status.")
                verboseHandle.printConsoleInfo("Please check space server status.")
        else:
            logger.info("No Manager configuration found please check.")
            verboseHandle.printConsoleInfo("No Manager configuration found please check.")

    except Exception as e:
        handleException(e)

