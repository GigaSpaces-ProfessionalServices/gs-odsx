import argparse
import json
import os
import sys

import requests
from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_manager import getManagerHost, getManagerInfo
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

    managerInfo = getManagerInfo()

    lookupGroup = str(managerInfo['lookupGroups'])
    lookupLocator = str(managerHost) + ":4174"
    objectMgmtHost = getPivotHost()


def validateUserInput():
    global selectedSpace
    global selectedType

    isValid = False
    objectMgmtTableInput = str(
        input(Fore.YELLOW + "Select object to unregister type :" + Fore.RESET))

    if objectMgmtTableInput.isnumeric() == True:
        objectMgmtTableInput = int(objectMgmtTableInput)
        if objectMgmtTableInput > 0 and objectMgmtTableInput in dataSpaceDict:
            isValid = True
            selectedSpace = dataSpaceDict.get(objectMgmtTableInput)
            selectedType = dataTableDict.get(objectMgmtTableInput)
            displaySummary()
            summaryConfirm = str(input(
                Fore.YELLOW + "Do you want to unregister object with above inputs ? [Yes (y) / No (n)] [n]: " + Fore.RESET))
            # while(len(str(summaryConfirm))==0):
            #    summaryConfirm = str(input(Fore.YELLOW+"Do you want to unregister object with above inputs ? [Yes (y) / No (n)] [n]: "+Fore.RESET))
            if len(str(summaryConfirm)) == 0:
                summaryConfirm = "n"
            if (str(summaryConfirm).casefold() == 'n' or str(summaryConfirm).casefold() == 'no'):
                logger.info("Exiting without unregistering object")
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
        "type": "" + selectedType + ""
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


def unregisterType():
    logger.info("unregister object")
    # print(getData())
    response = requests.post('http://' + objectMgmtHost + ':7001/unregistertype', data=getData(),
                             headers={'Accept': 'application/json'})
    if (response.text == "success"):
        verboseHandle.printConsoleInfo("Object is removed successfully!!")
    else:
        verboseHandle.printConsoleError("Error in removing object.")


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Object Management -> Registration -> Unregister type')
    try:
        args = []
        menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
        args.append(sys.argv[0])
        myCheckArg()
        setUserInputs()
        listObjects()
        validateUserInput()
        unregisterType()
    except Exception as e:
        handleException(e)
