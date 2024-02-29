import argparse
import json
import os
import sys

import requests
from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_app_config import getYamlFilePathInsideFolder, readValuefromAppConfig, set_value_in_property_file
from utils.odsx_keypress import userInputWrapper
from utils.odsx_objectmanagement_utilities import getPivotHost
from utils.ods_manager import getManagerHost, getManagerInfo
from utils.odsx_print_tabular_data import printTabular
from utils.odsx_db2feeder_utilities import getPasswordByHost, getUsernameByHost

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
    global batchIndexFilePath
    global pollingContainerFilePath
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

    appId = str(readValuefromAppConfig("app.space.security.appId")).replace('"', '')
    safeId = str(readValuefromAppConfig("app.space.security.safeId")).replace('"', '')
    objectId = str(readValuefromAppConfig("app.space.security.objectId")).replace('"', '')
    logger.info("appId : " + appId + " safeID : " + safeId + " objectID : " + objectId)

    username = str(getUsernameByHost())
    password = str(getPasswordByHost("object"))

    managerInfo = getManagerInfo(True, username, password)

    lookupGroup = str(managerInfo['lookupGroups'])
    lookupLocator = str(managerHost)+":4174"
    objectMgmtHost = getPivotHost()

    batchIndexFilePath = str(getYamlFilePathInsideFolder(".object.config.ddlparser.indexBatchFileName")).replace("//","/")
    ddlAndPropertiesBasePath = os.path.dirname(batchIndexFilePath) +"/"

    batchIndexFilePath = ddlAndPropertiesBasePath+"batchIndexes.csv"
    pollingContainerFilePath = ddlAndPropertiesBasePath+"pollingcontainer.txt"
    spaceName = readValuefromAppConfig("app.objectmanagement.space")
    if(spaceName is None or spaceName=="" or len(str(spaceName))<0):
        spaceName = readValuefromAppConfig("app.tieredstorage.pu.spacename")
        set_value_in_property_file("app.objectmanagement.space",spaceName)

    displaySummary(lookupLocator,lookupGroup,objectMgmtHost,spaceName,ddlAndPropertiesBasePath,batchIndexFilePath,pollingContainerFilePath)

    summaryConfirm = str(userInputWrapper(Fore.YELLOW+"Do you want to continue object registration with above inputs ? [Yes (y) / No (n)]: "+Fore.RESET))
    while(len(str(summaryConfirm))==0):
        summaryConfirm = str(userInputWrapper(Fore.YELLOW+"Do you want to continue object registration with above inputs ? [Yes (y) / No (n)]: "+Fore.RESET))

    if(str(summaryConfirm).casefold()=='n' or str(summaryConfirm).casefold()=='no'):
        logger.info("Exiting without registering object")
        exit(0)

def displaySummary(lookupLocator,lookupGroup,objectMgmtHost,spaceName,ddlAndPropertiesBasePath,batchIndexFilePath,pollingContainerFilePath):
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
          Fore.GREEN+"Batch index file location = "+
          Fore.GREEN+batchIndexFilePath+Fore.RESET)
    print(Fore.GREEN+"7. "+
          Fore.GREEN+"Polling container file location = "+
          Fore.GREEN+pollingContainerFilePath+Fore.RESET)

    verboseHandle.printConsoleWarning("------------------------------------------------------------")

def getData():
    data = {
        "ddlAndPropertiesBasePath": "" + ddlAndPropertiesBasePath + "",
        "batchIndexFilePath": "" + batchIndexFilePath + ""
    }
    return data


def addindexInBatch():
    logger.info("addindexInBatch object")
    # print(getData())
    response = requests.post('http://' + objectMgmtHost + ':7001/index/addinbatch',
                             headers={'Accept': 'application/json'})
    jsonArray = json.loads(response.text)
    headers = [Fore.YELLOW + "Sr Num" + Fore.RESET,
               Fore.YELLOW + "Type" + Fore.RESET,
               Fore.YELLOW + "Property" + Fore.RESET,
               Fore.YELLOW + "Index Type" + Fore.RESET,
               Fore.YELLOW + "Added index or not" + Fore.RESET
               ]
    dataTable = []
    counter = 1
    logger.info(jsonArray)
    for data in jsonArray:
        indexResponse=""
        if data["response"] == "error":
            indexResponse = Fore.YELLOW + "Failed to add Index" + Fore.RESET
        else:
            indexResponse =  Fore.GREEN + "Index successfully added" + Fore.RESET
        dataArray = [
            Fore.GREEN + str(counter) + Fore.RESET,
            Fore.GREEN + data["tableName"] + Fore.RESET,
            Fore.GREEN + data["propertyName"] + Fore.RESET,
            Fore.GREEN + data["indexType"] + Fore.RESET,
            Fore.GREEN + indexResponse + Fore.RESET
        ]
        dataTable.append(dataArray)
        counter=counter+1
    printTabular(None, headers, dataTable)
    #if(response.text=="success"):
    #    verboseHandle.printConsoleInfo("All objects are registered successfully!!")
    #else:
    #    verboseHandle.printConsoleError("Error in registering objects batch.")


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Object Management -> Registration -> Add index in batch')
    try:
        args = []
        menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
        args.append(sys.argv[0])
        myCheckArg()
        setUserInputs()
        addindexInBatch()
    except Exception as e:
        handleException(e)
