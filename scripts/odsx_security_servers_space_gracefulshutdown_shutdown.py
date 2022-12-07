#!/usr/bin/env python3

import argparse
import os
import sys

from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
from utils.odsx_db2feeder_utilities import getPasswordByHost, getUsernameByHost
from utils.odsx_keypress import userInputWrapper
from utils.odsx_space_shutdown_reload_utilities import displayPus, getManagerHost, getProcessingUnitList, \
    getServiceListFromConsul, printSuccessSummary, shutdownSpaceServers, undeployFeeders, undeployMicroservices, \
    undeploySpace, validateBeforeShutdown, validateTierSpace

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
user='root'
class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR

def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
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

def shutdownServers(username,password):

    logger.info("shutdownServers() : start")



    puList =[]
    consulServiceList = []
    spaceList = []    
    validationMsg = ''
    
    spacePUName = readValuefromAppConfig("app.spacejar.pu.name")
    spaceName = readValuefromAppConfig("app.spacejar.space.name")
    tierSpacePUName = readValuefromAppConfig("app.tieredstorage.pu.name")
    tierSpace = readValuefromAppConfig("app.tieredstorage.pu.spacename")

    managerHost = getManagerHost()
    #print("managerHost=>"+str(managerHost))
    puList = getProcessingUnitList(managerHost,True,username,password)

    """
    for pu in puList:
        spacePU = str(pu['name'])
        if((spacePU == spacePUName or spacePU == tierSpacePUName) and spaceList.__contains__(spacePU)==False ):
            spaceList.append(spacePU)
    """
    spaceList.append(tierSpacePUName) 
    #try:
    #verboseHandle.printConsoleInfo("Validating .......")
    validationMsg = validateBeforeShutdown(managerHost, puList,tierSpace,True,username,password)
    if(len(str(validationMsg))>0):
        displayPus(puList)
        verboseHandle.printConsoleError(validationMsg)
        exit(0)
    else:
        validateSpaceParitions = readValuefromAppConfig("app.space.shutdown.validateTierSpacePartitions")
        logger.info("validateSpaceParitions => "+str(validateSpaceParitions))
        if(validateSpaceParitions is not None and validateSpaceParitions!='None' and validateSpaceParitions == True):
            tierSpaceValidation = validateTierSpace(managerHost, tierSpace,True,username,password)
            if(len(str(tierSpaceValidation))>0):
                verboseHandle.printConsoleError(tierSpaceValidation)
                exit(0)
        else:
            verboseHandle.printConsoleWarning("Validation for Tier Space partitions is disabled.")

        printSuccessSummary(puList)
        confirmMsg = Fore.YELLOW + "Do you really want to shutdown ? (Yes(y)/No(n)):" + Fore.RESET
        choice = str(userInputWrapper(confirmMsg))
        while(len(choice) == 0):
            choice = str(userInputWrapper(confirmMsg))

        while(choice.casefold()!='yes' and choice.casefold()!='no' and choice.casefold()!='y' and choice.casefold()!='n'):
         
            verboseHandle.printConsoleError("Invalid input")
            choice = str(userInputWrapper(confirmMsg))

        if (choice.casefold() == 'no' or choice.casefold()=='n'):
            logger.info("Exiting without performing shutdown")
            exit(0)

    consulServiceList = getServiceListFromConsul()
  
   
    feederMsg = undeployFeeders(True)
    verboseHandle.printConsoleInfo(feederMsg)

    
    puMsg = undeployMicroservices(managerHost, puList, consulServiceList,True,username,password)
    verboseHandle.printConsoleInfo(puMsg)
    

    statefulPUMsg = undeploySpace(managerHost, spaceList,True,username,password)
    verboseHandle.printConsoleInfo(statefulPUMsg)

    shutdownSpaceServers(user,True)
    
    logger.info("shutdownServers() : end")
    #except Exception as e:
    #    logger.error("error occurred in shutdownServers()")



if __name__ == '__main__':
    #args = []
    #menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
    #args.append(sys.argv[0])
    #myCheckArg()
    #with Spinner():
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
        
        managerHost = getManagerHost()
        username = str(getUsernameByHost(managerHost,appId,safeId,objectId))
        password = str(getPasswordByHost(managerHost,appId,safeId,objectId))
        shutdownServers(username,password)
    except Exception as e:
        handleException(e)

