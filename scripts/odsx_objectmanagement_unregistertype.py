import argparse
import json
import os
import sys

import requests
from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
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

    objectMgmtHostDefault = 'localhost'

    objectMgmtHost = str(
        input(Fore.YELLOW + "object management host (pivot) [" + objectMgmtHostDefault + "] :" + Fore.RESET))
    if len(str(objectMgmtHost)) == 0:
        objectMgmtHost = objectMgmtHostDefault

    lookupGroupDefault = "xap-16.2.0"
    lookupLocatorDefault = readValuefromAppConfig("app.manager.hosts")

    lookupGroup = str(
        input(Fore.YELLOW + "Lookup group [" + lookupGroupDefault + "] :" + Fore.RESET))
    if (len(str(lookupGroup)) == 0):
        lookupGroup = lookupGroupDefault

    lookupLocator = str(
        input(Fore.YELLOW + "Lookup locator [" + lookupLocatorDefault + "] :" + Fore.RESET))
    if (len(str(lookupLocator)) == 0):
        lookupLocator = lookupLocatorDefault


def validateUserInput():
    global selectedSpace
    global selectedType

    objectMgmtTableInput = str(
        input(Fore.YELLOW + "Select object to unregister type :" + Fore.RESET))
    objectMgmtTableInput = int(objectMgmtTableInput)
    if objectMgmtTableInput > 0 and objectMgmtTableInput in dataSpaceDict:
        selectedSpace = dataSpaceDict.get(objectMgmtTableInput)
        selectedType = dataTableDict.get(objectMgmtTableInput)
    else:
        verboseHandle.printConsoleError("Wrong input selected")
        exit(0)

def getDataList():
    data = {
        "lookupGroup": "" + lookupGroup + "",
        "lookupLocator": "" + lookupLocator + ""
    }
    return data

def getData():
    data = {
        "spaceName": "" + selectedSpace + "",
        "type": "" + selectedType + "",
        "lookupGroup": "" + lookupGroup + "",
        "lookupLocator": "" + lookupLocator + ""
    }
    return data


def listObjects():
    logger.info("list object")
    global dataSpaceDict
    global dataTableDict
    response = requests.get('http://' + objectMgmtHost + ':7001/list',
                            headers={'Accept': 'application/json'},params=getDataList())
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
    verboseHandle.printConsoleInfo(response.text)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Object Management -> Unregister type')
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
