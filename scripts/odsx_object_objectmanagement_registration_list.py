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
    logger.info("list object")
    global managerHost
    managerHost = getManagerHost()
    
    
    objectMgmtHost = getPivotHost()
    response = requests.get('http://' + objectMgmtHost + ':7001/list',
                            headers={'Accept': 'application/json'})
    objectJson = json.loads(response.text)
    headers = [Fore.YELLOW + "Sr Num" + Fore.RESET,
               Fore.YELLOW + "Space Name" + Fore.RESET,
               Fore.YELLOW + "Object Name" + Fore.RESET,
           #    Fore.YELLOW + "Space Id" + Fore.RESET,
           #    Fore.YELLOW + "Space Routing" + Fore.RESET,
           #    Fore.YELLOW + "Indexes" + Fore.RESET,
           #    Fore.YELLOW + "Tier Criteria" + Fore.RESET
               Fore.YELLOW + "DDl File exist" + Fore.RESET,
               Fore.YELLOW + "Properties File exist" + Fore.RESET,
               Fore.YELLOW + "Total records in ram" + Fore.RESET,
               Fore.YELLOW + "Total records in disk" + Fore.RESET
               ]
    data = []
    counter = 1
    #    print(objectJson)
    #    print(objectJson[0]["objects"])
    dataColumnsDict = {}
    dataTableColumnsDict = {}
    #print("objectJson ->"+str(objectJson))
    tableListfilePath = str(getYamlFilePathInsideFolder(".object.config.ddlparser.ddlBatchFileName")).replace("//","/")
    ddlAndPropertiesBasePath = os.path.dirname(tableListfilePath) +"/"
    spaceName = readValuefromAppConfig("app.objectmanagement.space")
    # getData()
    if (spaceName is None or spaceName == "" or len(str(spaceName)) < 0):
        spaceName = readValuefromAppConfig("app.tieredstorage.pu.spacename")
    response = requests.get("http://" + managerHost + ":8090/v2/spaces/" + str(spaceName) + "/statistics/types")
    logger.info(response.text)
    jsonData = json.loads(response.text)

    logger.info("response : " + str(jsonData))
    #if (str(jsonData["status"]).__contains__("failed")):

    for spaces in objectJson:
        #        print(spaces["objects"])
        for object in spaces["objects"]:
            ddlFileCheck = Fore.RED + "No" + Fore.RESET
            propertiesFileCheck = Fore.RED + "No" + Fore.RESET
            if os.path.isfile(ddlAndPropertiesBasePath + str(object["tablename"]) + ".ddl"):
                ddlFileCheck= Fore.GREEN + "Yes"+ Fore.RESET
            if os.path.isfile(ddlAndPropertiesBasePath + str(object["tablename"]) + ".properties"):
                propertiesFileCheck= Fore.GREEN + "Yes" + Fore.RESET

            dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                         Fore.GREEN + str(spaces["spacename"]) + Fore.RESET,
                         Fore.GREEN + str(object["tablename"]) + Fore.RESET,
                    #     Fore.GREEN + str(object["spaceId"]) + Fore.RESET,
                    #     Fore.GREEN + str(object["routing"]) + Fore.RESET,
                    #     Fore.GREEN + str(object["index"]) + Fore.RESET,
                    #     Fore.GREEN + str(object["criteria"]) + Fore.RESET
                         ddlFileCheck,
                         propertiesFileCheck,
                         Fore.GREEN + str(object["objectInMemory"]) + Fore.RESET,
                         Fore.GREEN + str(jsonData[str(object["tablename"])]["entries"]) + Fore.RESET,
                        ]
            dataColumnsDict.update({counter: object["columns"]})
            dataTableColumnsDict.update({counter: object["tablename"]})
            counter = counter + 1
            data.append(dataArray)
    printTabular(None, headers, data)
    if len(data) == 0:
        exit(0)
    while True:
        objectMgmtColumnsInput = str(
            input(Fore.YELLOW + "Select object to show more details \n [0] Show List again \n or exit [99] :" + Fore.RESET))

        if len(objectMgmtColumnsInput)<0:
            objectMgmtColumnsInput = "99"
        if objectMgmtColumnsInput == "0":
            listObjects()
            exit(0)

        if (objectMgmtColumnsInput.isnumeric()==True and objectMgmtColumnsInput!="99"):
            data = []
            counter = 1
            # print(dataColumnsDict)
            # print(dataColumnsDict.get(int(objectMgmtColumnsInput)))
            verboseHandle.printConsoleInfo("Selected Table Name : " + dataTableColumnsDict.get(int(objectMgmtColumnsInput)))
            headers = [
                       Fore.YELLOW + "Sr Num" + Fore.RESET,
                       Fore.YELLOW + "Name" + Fore.RESET,
                       Fore.YELLOW + "Data Type" + Fore.RESET,

                       Fore.YELLOW + "Space Id" + Fore.RESET,
                       Fore.YELLOW + "Space Routing" + Fore.RESET,
                       Fore.YELLOW + "Indexes" + Fore.RESET,
                       Fore.YELLOW + "Tier Criteria" + Fore.RESET
                     ]
            if(dataColumnsDict.get(int(objectMgmtColumnsInput))!=None):
                for object in dataColumnsDict.get(int(objectMgmtColumnsInput)):
                    dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                                    Fore.GREEN + str(object["columnname"]) + Fore.RESET,
                                    Fore.GREEN + str(object["columntype"]) + Fore.RESET,

                                    Fore.GREEN + str(object["spaceId"]) + Fore.RESET,
                                    Fore.GREEN + str(object["spaceRouting"]) + Fore.RESET,
                                    Fore.GREEN + str(object["spaceIndex"]) + Fore.RESET,
                                    Fore.GREEN + str(object["tierCriteria"]) + Fore.RESET
                                 ]
                    counter = counter + 1
                    data.append(dataArray)
                printTabular(None, headers, data)
            else:
                verboseHandle.printConsoleError("Invalid Option!")
                exit(0)
        elif(objectMgmtColumnsInput=="99"):
            exit(0)
        else:
            verboseHandle.printConsoleError("Invalid Option!")
            exit(0)

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
    verboseHandle.printConsoleWarning('Menu -> Object Management -> Registration -> List')
    try:
        args = []
        menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
        args.append(sys.argv[0])
        myCheckArg()
        #setUserInput()
        listObjects()
    except Exception as e:
        handleException(e)
