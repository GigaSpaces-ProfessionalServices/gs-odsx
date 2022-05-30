import argparse
import os
import sys

import requests
from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig

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
    global tableListfilePath
    global ddlAndPropertiesBasePath
    global spaceName
    global objectMgmtHost
    global lookupGroup
    global lookupLocator

    tableListfilePathDefault = '/home/jay/work/gigaspace/bofLeumi/DdlParser-David-leumicode/src/main/resources/tableList.txt'
    ddlAndPropertiesBasePathDefault = '/home/jay/work/gigaspace/bofLeumi/DdlParser-David-leumicode/src/main/resources'
    spaceNameDefault = 'bllspace'
    objectMgmtHostDefault = 'localhost'

    tableListfilePath = str(
        input(Fore.YELLOW + "Enter full file path for table list [" + tableListfilePathDefault + "] :" + Fore.RESET))
    if (len(str(tableListfilePath)) == 0):
        tableListfilePath = tableListfilePathDefault

    ddlAndPropertiesBasePath = str(
        input(
            Fore.YELLOW + "Enter base path for ddl, properties file [" + ddlAndPropertiesBasePathDefault + "] :" + Fore.RESET))
    if (len(str(ddlAndPropertiesBasePath)) == 0):
        ddlAndPropertiesBasePath = ddlAndPropertiesBasePathDefault

    objectMgmtHost = str(
        input(Fore.YELLOW + "object management host (pivot) [" + objectMgmtHostDefault + "] :" + Fore.RESET))
    if (len(str(objectMgmtHost)) == 0):
        objectMgmtHost = objectMgmtHostDefault

    spaceName = str(
        input(Fore.YELLOW + "Enter Space name [" + spaceNameDefault + "]:" + Fore.RESET))
    if (len(str(spaceName)) == 0):
        spaceName = spaceNameDefault

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
        "spaceName": "" + spaceName + "",
        "ddlAndPropertiesBasePath": "" + ddlAndPropertiesBasePath + "",
        "tableListfilePath": "" + tableListfilePath + "",
        "lookupGroup": "" + lookupGroup + "",
        "lookupLocator": "" + lookupLocator + ""
    }
    return data


def registerInBatch():
    logger.info("registerInBatch object")
    # print(getData())
    response = requests.post('http://' + objectMgmtHost + ':7001/registertype/batch', data=getData(),
                             headers={'Accept': 'application/json'})
    verboseHandle.printConsoleInfo(response.text)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Object Management -> Register type in batch')
    try:
        args = []
        menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
        args.append(sys.argv[0])
        myCheckArg()
        setUserInputs()
        registerInBatch()
    except Exception as e:
        handleException(e)
