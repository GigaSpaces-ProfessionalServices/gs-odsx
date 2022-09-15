#!/usr/bin/env python3
import argparse
import os
import signal
import sys

from utils.ods_cleanup import signal_handler
from utils.odsx_objectmanagement_utilities import getManagerHost
from utils.ods_manager import getManagerInfo
from utils.ods_scp import scp_upload

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from colorama import Fore
from utils.ods_scp import scp_upload
from utils.ods_app_config import set_value_in_property_file, readValuefromAppConfig, getYamlFilePathInsideFolder

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
serviceName = "object-management.service"
user = "root"
app_config_space_key = 'app.tieredstorage.pu.spacename'

def setupService():
    global defaultManagerServer
    defaultManagerServer = getManagerHost()
    
    logger.info("setupService() : start")

    managerServer=defaultManagerServer

   
#    ddlAndPropertiesBasePath = str(getYamlFilePathInsideFolder(".object.config.ddlparser"))
#    ddlAndPropertiesBasePath = ddlAndPropertiesBasePath+"/"
    tableListfilePath = str(getYamlFilePathInsideFolder(".object.config.ddlparser.ddlBatchFileName")).replace("//","/")
    ddlAndPropertiesBasePath = os.path.dirname(tableListfilePath) +"/"
    spaceName = readValuefromAppConfig("app.objectmanagement.space")
    if(spaceName is None or spaceName=="" or len(str(spaceName))<0):
        spaceName = readValuefromAppConfig("app.tieredstorage.pu.spacename")
        set_value_in_property_file("app.objectmanagement.space",spaceName)

    managerInfo = getManagerInfo()
    lookupGroup = str(managerInfo['lookupGroups'])
    for lookupManager in managerInfo['managers']:
        lookupLocator = str(lookupManager)+":4174,"
    if lookupLocator.endswith(","):
        lookupLocator = lookupLocator[:-1]
    #lookupLocator = str(managerServer)+":4174"
    displaySummary(managerServer,spaceName,ddlAndPropertiesBasePath,tableListfilePath)

    confirmMsg = Fore.YELLOW + "Are you sure, you want to setup Object Management service ? (Yes/No) [Yes]:" + Fore.RESET
    choice = str(input(confirmMsg))
    while(len(choice) == 0):
        choice = 'y'

    while(choice.casefold()!='yes' and choice.casefold()!='no' and choice.casefold()!='y' and choice.casefold()!='n'):
        verboseHandle.printConsoleError("Invalid input")
        choice = str(input(confirmMsg))

    if (choice.casefold() == 'no' or choice.casefold()=='n'):
        logger.info("Exiting without registering object management service")
        exit(0)

    #set_value_in_property_file(app_config_space_key,str(spaceName))

    tieredCriteriaConfigFilePath = str(getYamlFilePathInsideFolder(".gs.config.ts.criteria")).replace('"','')

    args = spaceName+" "+lookupLocator+" "+lookupGroup+" "+serviceJar+" "+ddlAndPropertiesBasePath+" "+tableListfilePath+" "+tieredCriteriaConfigFilePath
    commandToExecute = "scripts/objectmanagement_service_setup.sh "+args
    logger.info("Command "+commandToExecute)
    try:
        with Spinner():
            os.system(commandToExecute)
        
            os.system('sudo systemctl daemon-reload')
        
            

    except Exception as e:
        logger.error("error registering object management service=>"+str(e))
    
    logger.info("setupService() : end")

    verboseHandle.printConsoleInfo("Object Management Service setup successfully!")


def displaySummary(managerServer,spaceName,ddlAndPropertiesBasePath,tableListfilePath):
    global serviceJar
    serviceJar = str(getYamlFilePathInsideFolder(".object.jars.objectmanagementjar")).replace("//","/")
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleWarning("***Summary***")
    print(Fore.GREEN+"1. "+
            Fore.GREEN+"Manager Server = "+
            Fore.GREEN+managerServer+Fore.RESET)
    print(Fore.GREEN+"2. "+
            Fore.GREEN+"Space Name = "+
            Fore.GREEN+spaceName+Fore.RESET)
    print(Fore.GREEN+"3. "+
          Fore.GREEN+"Object Management jar= "+
          Fore.GREEN+str(serviceJar)+Fore.RESET)
    print(Fore.GREEN+"4. "+
          Fore.GREEN+"DDL and properties file location = "+
          Fore.GREEN+str(ddlAndPropertiesBasePath)+Fore.RESET)
    print(Fore.GREEN+"5. "+
          Fore.GREEN+"Table batch file location = "+
          Fore.GREEN+str(tableListfilePath)+Fore.RESET)
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
   
   
if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Object -> ObjectManagement -> Service -> Setup")
    signal.signal(signal.SIGINT, signal_handler)
    setupService()
    