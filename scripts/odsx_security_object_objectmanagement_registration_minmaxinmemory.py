import argparse
import json
import os
import sys

import requests
from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_manager import getManagerHost, getManagerInfo
from utils.odsx_db2feeder_utilities import getPasswordByHost, getUsernameByHost
from utils.odsx_keypress import userInputWithEscWrapper, userInputWrapper
from utils.odsx_objectmanagement_utilities import getPivotHost
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
    parser.add_argument('-dryrun', '--dryrun',
                        help='Dry run flag',
                        default='false', action='store_true')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])


def setUserInputs():
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
    password = str(getPasswordByHost())

    managerInfo = getManagerInfo(True, username, password)

    lookupGroup = str(managerInfo['lookupGroups'])
    lookupLocator = str(managerHost) + ":4174"
    objectMgmtHost = getPivotHost()


def validateUserInput():
    global selectedSpace
    global selectedType
    global minColName
    global maxColName

    isValid = False
    objectMgmtTableInput = str(
        userInputWithEscWrapper(Fore.YELLOW + "Select object to get memory min,max \n or exit [99] :" + Fore.RESET))

    if objectMgmtTableInput.isnumeric() == True and objectMgmtTableInput!="99":
        objectMgmtTableInput = int(objectMgmtTableInput)
        if objectMgmtTableInput > 0 and objectMgmtTableInput in dataSpaceDict:
            isValid = True
            selectedSpace = dataSpaceDict.get(objectMgmtTableInput)
            selectedType = dataTableDict.get(objectMgmtTableInput)
            minColName = str(
                userInputWithEscWrapper(Fore.YELLOW + "min of column (column name) :" + Fore.RESET))
            maxColName = str(
                userInputWithEscWrapper(Fore.YELLOW + "max of column (column name) :" + Fore.RESET))
            #displaySummary()
            #summaryConfirm = str(userInputWrapper(
            #    Fore.YELLOW + "Do you want to unregister object with above inputs ? [Yes (y) / No (n)] [n]: " + Fore.RESET))
            # while(len(str(summaryConfirm))==0):
            #    summaryConfirm = str(userInputWrapper(Fore.YELLOW+"Do you want to unregister object with above inputs ? [Yes (y) / No (n)] [n]: "+Fore.RESET))
            #if len(str(summaryConfirm)) == 0:
            #    summaryConfirm = "n"
            #if (str(summaryConfirm).casefold() == 'n' or str(summaryConfirm).casefold() == 'no'):
            #    logger.info("Exiting without unregistering object")
            #    exit(0)
    elif objectMgmtTableInput=="99":
        exit(0)
    if (isValid == False):
        verboseHandle.printConsoleError("Invalid option!")
        exit(0)


def displaySummary():
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleWarning("***Summary***")
    print(Fore.GREEN + "1. " +
          Fore.GREEN + "Lookup Manager = " +
          Fore.GREEN + lookupLocator + Fore.RESET)
    print(Fore.GREEN + "2. " +
          Fore.GREEN + "Lookup Group = " +
          Fore.GREEN + lookupGroup + Fore.RESET)
    print(Fore.GREEN + "3. " +
          Fore.GREEN + "Object Management Host = " +
          Fore.GREEN + objectMgmtHost + Fore.RESET)
    print(Fore.GREEN + "4. " +
          Fore.GREEN + "Space Name = " +
          Fore.GREEN + selectedSpace + Fore.RESET)
    print(Fore.GREEN + "5. " +
          Fore.GREEN + "Selected Object = " +
          Fore.GREEN + selectedType + Fore.RESET)

    verboseHandle.printConsoleWarning("------------------------------------------------------------")


def getDataList():
    data = {
        "lookupGroup": "" + lookupGroup + "",
        "lookupLocator": "" + lookupLocator + ""
    }
    return data


def getData():
    data = {
        "objectType": "" + selectedType + "",
        "minColName": "" + minColName + "",
        "maxColName": "" + maxColName + ""
    }
    return data


def listObjects():
    logger.info("list object")
    global dataSpaceDict
    global dataTableDict
    response = requests.get('http://' + objectMgmtHost + ':7001/list',
                            headers={'Accept': 'application/json'})
    objectJson = json.loads(response.text)
    headers = [Fore.YELLOW + "Sr Num" + Fore.RESET,
               Fore.YELLOW + "Space Name" + Fore.RESET,
               Fore.YELLOW + "Object Name" + Fore.RESET
               ]
    data = []
    counter = 1
    #    print(objectJson)
    #    print(objectJson[0]["objects"])
    dataSpaceDict = {}
    dataTableDict = {}
    for spaces in objectJson:
        #        print(spaces["objects"])
        for object in spaces["objects"]:
            dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                         Fore.GREEN + str(spaces["spacename"]) + Fore.RESET,
                         Fore.GREEN + str(object["tablename"]) + Fore.RESET]
            dataSpaceDict.update({counter: spaces["spacename"]})
            dataTableDict.update({counter: object["tablename"]})
            counter = counter + 1
            data.append(dataArray)
    printTabular(None, headers, data)


def memoryCount():
    logger.info("memoryCount object")
    # print(getData())
    response = requests.get('http://' + objectMgmtHost + ':7001/inmemory/minmax', params=getData(),
                             headers={'Accept': 'application/json'})
    verboseHandle.printConsoleInfo("Count in memory : " + response.text)

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Object Management -> Registration -> Count In Memory')
    try:
        args = []
        menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
        args.append(sys.argv[0])
        myCheckArg()
        setUserInputs()
        listObjects()
        validateUserInput()
        memoryCount()
    except Exception as e:
        handleException(e)
