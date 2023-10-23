import argparse
import os
import sys

import requests
from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_app_config import getYamlFilePathInsideFolder, readValuefromAppConfig, set_value_in_property_file
from utils.odsx_keypress import userInputWrapper
from utils.odsx_objectmanagement_utilities import getPivotHost
from utils.ods_manager import getManagerHost, getManagerInfo

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
    global pollingFilePath
    global spaceName
    global objectMgmtHost
    global lookupGroup
    global lookupLocator
    global managerHost

    managerHost = getManagerHost()

    managerInfo = getManagerInfo()

    lookupGroup = str(managerInfo['lookupGroups'])
    lookupLocator = str(managerHost)+":4174"
    objectMgmtHost = getPivotHost()

    pollingFilePath = str(getYamlFilePathInsideFolder(".object.config.ddlparser.pollingFileName")).replace("//","/")

    spaceName = readValuefromAppConfig("app.objectmanagement.space")
    if(spaceName is None or spaceName=="" or len(str(spaceName))<0):
        spaceName = readValuefromAppConfig("app.tieredstorage.pu.spacename")
        set_value_in_property_file("app.objectmanagement.space",spaceName)

    displaySummary(lookupLocator,lookupGroup,objectMgmtHost,spaceName,pollingFilePath)
    
    summaryConfirm = str(userInputWrapper(Fore.YELLOW+"Do you want to continue polling registration with above inputs ? [Yes (y) / No (n)]: "+Fore.RESET))
    while(len(str(summaryConfirm))==0):
        summaryConfirm = str(userInputWrapper(Fore.YELLOW+"Do you want to continue polling registration with above inputs ? [Yes (y) / No (n)]: "+Fore.RESET))

    if(str(summaryConfirm).casefold()=='n' or str(summaryConfirm).casefold()=='no'):
        logger.info("Exiting without registering polling")
        exit(0)

def displaySummary(lookupLocator,lookupGroup,objectMgmtHost,spaceName,pollingFilePath):
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
            Fore.GREEN+"polling files location = "+
            Fore.GREEN+pollingFilePath+Fore.RESET)
    
    verboseHandle.printConsoleWarning("------------------------------------------------------------")

def registerInBatch():
    logger.info("registerInBatch polling")
    response = requests.post('http://' + objectMgmtHost + ':7001/polling/registerinbatch',
                             headers={'Accept': 'application/json'})
    
    print(response.text)
    verboseHandle.printConsoleInfo("Registered successfully")


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Object Management -> Registration -> Event container Obfuscation -> Polling in batch')
    try:
        args = []
        menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
        args.append(sys.argv[0])
        myCheckArg()
        setUserInputs()
        registerInBatch()
    except Exception as e:
        handleException(e)