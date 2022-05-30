import argparse
import json
import os
import sys

import requests
from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36
from utils.ods_validation import getDataValidationServerStatus
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


def getConsolidatedStatus(node):
    output = ''
    logger.info("getConsolidatedStatus() : " + str(node.ip))
    cmdList = ["systemctl status odsxdatavalidation"]
    for cmd in cmdList:
        logger.info("cmd :" + str(cmd) + " host :" + str(node.ip))
        logger.info("Getting status.. :" + str(cmd))
        user = 'root'
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(node.ip, user, cmd)
            logger.info("output1 : " + str(output))
            if (output != 0):
                # verboseHandle.printConsoleInfo(" Service :"+str(cmd)+" not started.")
                logger.info(" Service :" + str(cmd) + " not started." + str(node.ip))
                return output
    return output


def setUserInput():
    global lookupGroup
    global lookupLocator

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


def getData():
    data = {
        "lookupGroup": "" + lookupGroup + "",
        "lookupLocator": "" + lookupLocator + ""
    }
    return data


def listObjects():
    logger.info("list object")
    objectMgmtHost = str(
        input(Fore.YELLOW + "object management host [localhost (pivot)] :" + Fore.RESET))
    if (len(str(objectMgmtHost)) == 0):
        objectMgmtHost = 'localhost'
    response = requests.get('http://' + objectMgmtHost + ':7001/list', params=getData(),
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
    dataColumnsDict = {}
    for spaces in objectJson:
        #        print(spaces["objects"])
        for object in spaces["objects"]:
            dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                         Fore.GREEN + str(spaces["spacename"]) + Fore.RESET,
                         Fore.GREEN + str(object["tablename"]) + Fore.RESET]
            dataColumnsDict.update({counter: object["columns"]})
            counter = counter + 1
            data.append(dataArray)
    printTabular(None, headers, data)
    if len(data) == 0:
        exit(0)
    objectMgmtColumnsInput = str(
        input(Fore.YELLOW + "Select object to show more details :" + Fore.RESET))
    if len(objectMgmtColumnsInput) > 0:
        data = []
        counter = 1
        # print(dataColumnsDict)
        # print(dataColumnsDict.get(int(objectMgmtColumnsInput)))
        headers = [Fore.YELLOW + "Sr Num" + Fore.RESET,
                   Fore.YELLOW + "Name" + Fore.RESET,
                   Fore.YELLOW + "Data Type" + Fore.RESET
                   ]
        for object in dataColumnsDict.get(int(objectMgmtColumnsInput)):
            dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                         Fore.GREEN + str(object["columnname"]) + Fore.RESET,
                         Fore.GREEN + str(object["columntype"]) + Fore.RESET]
            counter = counter + 1
            data.append(dataArray)
        printTabular(None, headers, data)


def getDataValidationHost(dataValidationNodes):
    logger.info("getDataValidationHost()")
    dataValidationHost = ""
    status = ""
    try:
        logger.info("getDataValidationHost() : dataValidationNodes :" + str(dataValidationNodes))
        for node in dataValidationNodes:
            status = getDataValidationServerStatus(node.ip, "7890")
            if (status == "ON"):
                dataValidationHost = node.ip
        return dataValidationHost
    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Object Management -> List')
    try:
        args = []
        menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
        args.append(sys.argv[0])
        myCheckArg()
        setUserInput()
        listObjects()
    except Exception as e:
        handleException(e)
