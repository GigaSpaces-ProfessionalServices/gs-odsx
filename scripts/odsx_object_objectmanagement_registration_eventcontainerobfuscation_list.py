import argparse
import json
import os
import sys

import requests
from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig, getYamlFilePathInsideFolder
from utils.ods_manager import getManagerHost, getManagerInfo
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36
from utils.ods_validation import getDataValidationServerStatus
from utils.odsx_keypress import userInputWithEscWrapper
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


def getData():
    
    managerInfo = getManagerInfo()
    lookupGroup = str(managerInfo['lookupGroups'])
    lookupLocator = str(managerHost)+":4174"

    data = {
        "lookupGroup": "" + lookupGroup + "",
        "lookupLocator": "" + lookupLocator + ""
    }
    return data


def listObjects():
    logger.info("list polling")
    global managerHost
    managerHost = getManagerHost()
    
    
    objectMgmtHost = getPivotHost()
    response = requests.get('http://' + objectMgmtHost + ':7001/polling/list',
                            headers={'Accept': 'application/json'})
    objectJson = json.loads(response.text)
    headers = [Fore.YELLOW + "Sr Num" + Fore.RESET,
               Fore.YELLOW + "Type" + Fore.RESET,
               Fore.YELLOW + "Src Property" + Fore.RESET,
               Fore.YELLOW + "Dest Property" + Fore.RESET,
               Fore.YELLOW + "Obfuscate Property" + Fore.RESET,
               Fore.YELLOW + "Obfuscation Type" + Fore.RESET,
               Fore.YELLOW + "Space Id" + Fore.RESET
               ]
    data = []
    counter = 1
    pollingtypes = json.loads(response.text)
    for pollingtype in pollingtypes:
        dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                     Fore.GREEN + str(pollingtype["type"]) + Fore.RESET,
                     Fore.GREEN + str(pollingtype["srcPropName"]) + Fore.RESET,
                     Fore.GREEN + str(pollingtype["destPropName"]) + Fore.RESET,
                     Fore.GREEN + str(pollingtype["obfuscatePropName"]) + Fore.RESET,
                     Fore.GREEN + str(pollingtype["obfuscationType"]) + Fore.RESET,
                     Fore.GREEN + str(pollingtype["spaceId"]) + Fore.RESET
                    ]
        data.append(dataArray)
        counter = counter + 1
    printTabular(None, headers, data)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Object Management -> Registration -> Event container Obfuscation -> List')
    try:
        args = []
        menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
        args.append(sys.argv[0])
        myCheckArg()
        #setUserInput()
        listObjects()
    except Exception as e:
        handleException(e)
