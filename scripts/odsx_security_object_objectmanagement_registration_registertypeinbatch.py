import argparse
import json
import os
import sys

import requests
from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_app_config import getYamlFilePathInsideFolder, readValuefromAppConfig, set_value_in_property_file
from utils.odsx_db2feeder_utilities import getPasswordByHost, getUsernameByHost
from utils.odsx_keypress import userInputWrapper
from utils.odsx_objectmanagement_utilities import getPivotHost
from utils.ods_manager import getManagerHost, getManagerInfo
from utils.odsx_print_tabular_data import printTabular

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


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


class obj_type_dictionary(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value


class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR


def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    parser.add_argument('-f', nargs='?')
    parser.add_argument('-dryrun', '--dryrun',
                        help='Dry run flag',
                        default='false', action='store_true')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])


def setUserInputs():
    global tableListfilePath
    global ddlAndPropertiesBasePath
    global spaceName
    global objectMgmtHost
    global lookupGroup
    global lookupLocator
    global managerHost

    managerHost = getManagerHost()

    global username
    global password
    global appId;
    global safeId;
    global objectId;
    
    appId = str(readValuefromAppConfig("app.space.security.appId")).replace('"','')
    safeId = str(readValuefromAppConfig("app.space.security.safeId")).replace('"','')
    objectId = str(readValuefromAppConfig("app.space.security.objectId")).replace('"','')
    logger.info("appId : "+appId+" safeID : "+safeId+" objectID : "+objectId)
        
    
    username = str(getUsernameByHost(managerHost,appId,safeId,objectId))
    password = str(getPasswordByHost(managerHost,appId,safeId,objectId))


    managerInfo = getManagerInfo(True,username,password)

    lookupGroup = str(managerInfo['lookupGroups'])
    lookupLocator = str(managerHost)+":4174"
    objectMgmtHost = getPivotHost()

    tableListfilePath = str(getYamlFilePathInsideFolder(".object.config.ddlparser.ddlBatchFileName")).replace("//","/")
    ddlAndPropertiesBasePath = os.path.dirname(tableListfilePath) +"/"

    #ddlAndPropertiesBasePath = str(getYamlFilePathInsideFolder(".object.config.ddlparser"))
     

    tableListfilePath = ddlAndPropertiesBasePath+"tableList.txt"
    spaceName = readValuefromAppConfig("app.objectmanagement.space")
    if(spaceName is None or spaceName=="" or len(str(spaceName))<0):
        spaceName = readValuefromAppConfig("app.tieredstorage.pu.spacename")
        set_value_in_property_file("app.objectmanagement.space",spaceName)

    displaySummary(lookupLocator,lookupGroup,objectMgmtHost,spaceName,ddlAndPropertiesBasePath,tableListfilePath)
    
    summaryConfirm = str(userInputWrapper(Fore.YELLOW+"Do you want to continue object registration with above inputs ? [Yes (y) / No (n)]: "+Fore.RESET))
    while(len(str(summaryConfirm))==0):
        summaryConfirm = str(userInputWrapper(Fore.YELLOW+"Do you want to continue object registration with above inputs ? [Yes (y) / No (n)]: "+Fore.RESET))

    if(str(summaryConfirm).casefold()=='n' or str(summaryConfirm).casefold()=='no'):
        logger.info("Exiting without registering object")
        exit(0)

def displaySummary(lookupLocator,lookupGroup,objectMgmtHost,spaceName,ddlAndPropertiesBasePath,tableListfilePath):
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleWarning("***Summary***")
    print(Fore.GREEN+"1. "+
            Fore.GREEN+"Lookup Manager = "+
            Fore.GREEN+lookupLocator+Fore.RESET)
    print(Fore.GREEN+"2. "+
            Fore.GREEN+"Lookup Group = "+
            Fore.GREEN+lookupGroup+Fore.RESET)
    print(Fore.GREEN+"3. "+
            Fore.GREEN+"Object Management Host = "+
            Fore.GREEN+objectMgmtHost+Fore.RESET)
    print(Fore.GREEN+"4. "+
            Fore.GREEN+"Space Name = "+
            Fore.GREEN+spaceName+Fore.RESET)
    print(Fore.GREEN+"5. "+
            Fore.GREEN+"DDL files location = "+
            Fore.GREEN+ddlAndPropertiesBasePath+Fore.RESET)
    print(Fore.GREEN+"6. "+
            Fore.GREEN+"Table list file location = "+
            Fore.GREEN+tableListfilePath+Fore.RESET)
    
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
        
def getData():
    data = {
        "ddlAndPropertiesBasePath": "" + ddlAndPropertiesBasePath + "",
        "tableListfilePath": "" + tableListfilePath + ""
    }
    return data


def registerInBatch():
    logger.info("registerInBatch object")
    # print(getData())
    response = requests.post('http://' + objectMgmtHost + ':7001/registertype/batch',
                             headers={'Accept': 'application/json'})
    objectJson = json.loads(response.text)
    headers = [Fore.YELLOW + "Sr Num" + Fore.RESET,
               Fore.YELLOW + "Object Name" + Fore.RESET,
               Fore.YELLOW + "Registered or not" + Fore.RESET
               ]
    data = []
    counter = 1
    logger.info(objectJson)
    for k,v in objectJson.items():
        if v == "Already exist so not registered":
            v = Fore.YELLOW + v + Fore.RESET
        else:
            v =  Fore.GREEN + v + Fore.RESET

        dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                     Fore.GREEN + k + Fore.RESET,
                     Fore.GREEN + v + Fore.RESET
                     ]
        counter = counter+1
        data.append(dataArray)
    printTabular(None, headers, data)
    #if(response.text=="success"):
    #    verboseHandle.printConsoleInfo("All objects are registered successfully!!")
    #else:
    #    verboseHandle.printConsoleError("Error in registering objects batch.")


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Object Management -> Registration -> Register type in batch')
    try:
        args = []
        menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
        args.append(sys.argv[0])
        myCheckArg()
        setUserInputs()
        registerInBatch()
    except Exception as e:
        handleException(e)
