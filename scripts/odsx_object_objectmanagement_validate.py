import argparse
import os
import sys

import requests
from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_app_config import getYamlFilePathInsideFolder, readValuefromAppConfig, set_value_in_property_file
from utils.ods_manager import getManagerHost, getManagerInfo
from utils.odsx_keypress import userInputWrapper
from utils.odsx_objectmanagement_utilities import getPivotHost

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


def displaySummary():
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
            Fore.GREEN+"Selected DDL file  = "+
            Fore.GREEN+selectedddlFilename+Fore.RESET)
    print(Fore.GREEN+"6. "+
            Fore.GREEN+"Report File location  = "+
            Fore.GREEN+reportFilePath+Fore.RESET)
    
    verboseHandle.printConsoleWarning("------------------------------------------------------------")

def getDataList():
    data = {
        "lookupGroup": "" + lookupGroup + "",
        "lookupLocator": "" + lookupLocator + ""
    }
    return data

def getData():
    
    data = {
        "ddlFileName": "" + selectedddlFilename + "",
        "reportFilePath" :""+reportFilePath+""
    }
    return data


def setInputs():
    global spaceName
    global objectMgmtHost
    global ddlAndPropertiesBasePath
    global tableNameFromddlFileName
    global ddlfileOptions
    global selectedddlFilename
    global objectMgmtHost
    global lookupGroup
    global lookupLocator
    global managerHost
    global reportFilePath

    managerHost = getManagerHost()

    managerInfo = getManagerInfo()

    lookupGroup = str(managerInfo['lookupGroups'])
    lookupLocator = str(managerHost)+":4174"

    tableListfilePath = str(getYamlFilePathInsideFolder(".object.config.ddlparser.ddlBatchFileName")).replace("//","/")
    ddlAndPropertiesBasePath = os.path.dirname(tableListfilePath) +"/"

    #ddlAndPropertiesBasePath = str(getYamlFilePathInsideFolder(".object.config.ddlparser"))
    tableNameFromddlFileName = ''
    objectMgmtHost = getPivotHost()
    
    spaceName = readValuefromAppConfig("app.objectmanagement.space")
    if(spaceName is None or spaceName=="" or len(str(spaceName))<0):
        spaceName = readValuefromAppConfig("app.tieredstorage.pu.spacename")
        set_value_in_property_file("app.objectmanagement.space",spaceName)
    
    ddlfileOptions = {}
    counter = 1
    for file in os.listdir(ddlAndPropertiesBasePath):
        if file.endswith(".ddl"):
            print("[" + str(counter) + "]  " + file)
            ddlfileOptions.update({counter: file})
            counter = counter + 1

    selectedOption = str(
        userInputWrapper(Fore.YELLOW + "Select file to load ddl :" + Fore.RESET))
    if(selectedOption.isnumeric()==True):
        if len(selectedOption) <= 0 or int(selectedOption) not in ddlfileOptions:
            verboseHandle.printConsoleError("Invalid Option!")
            exit(0)
    else:    
        verboseHandle.printConsoleError("Invalid Option!")
        exit(0)
    selectedddlFilename = ddlfileOptions.get(int(selectedOption))
    tableName = selectedddlFilename.replace(".ddl", "")

    reportFilePath = readValuefromAppConfig("app.objectmanagement.validate.reportlocation")
    if(reportFilePath is None or reportFilePath=="" or len(str(reportFilePath))<0):
        reportFilePath = ddlAndPropertiesBasePath+"/validate_report_"+tableName+".txt"
        set_value_in_property_file("app.objectmanagement.validate.reportlocation",ddlAndPropertiesBasePath)
    else:
        reportFilePath = reportFilePath+"/validate_report_"+tableName+".txt"
    
    displaySummary()

    summaryConfirm = str(userInputWrapper(Fore.YELLOW+"Do you want to continue validation with above inputs ? [Yes (y) / No (n)]: "+Fore.RESET))
    while(len(str(summaryConfirm))==0):
        summaryConfirm = str(userInputWrapper(Fore.YELLOW+"Do you want to continue validation with above inputs ? [Yes (y) / No (n)]: "+Fore.RESET))

    if(str(summaryConfirm).casefold()=='n' or str(summaryConfirm).casefold()=='no'):
        logger.info("Exiting without validation")
        exit(0)

def validate():
    logger.info("unregister object")
    # print(getData())
    response = requests.post('http://' + objectMgmtHost + ':7001/validate', data=getData(),
                             headers={'Accept': 'application/json'})
    if(response.status_code==200 or response.status_code==202):
        verboseHandle.printConsoleInfo("Validate report is generated successfully on "+response.text)
    else:
        verboseHandle.printConsoleError("Error in validation.")


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Object Management -> Validate')
    try:
        args = []
        menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
        args.append(sys.argv[0])
        myCheckArg()
        setInputs()
        validate()
    except Exception as e:
        handleException(e)
