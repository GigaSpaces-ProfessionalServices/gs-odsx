import argparse
import os
import sys

import requests
from colorama import Fore
from configobj import ConfigObj

from scripts.logManager import LogManager
from utils.ods_app_config import getYamlFilePathInsideFolder, readValuefromAppConfig,set_value_in_property_file as config_set_value_in_property_file
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
    parser.add_argument('-dryrun', '--dryrun',
                        help='Dry run flag',
                        default='false', action='store_true')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])


def setUserInputs1():
    global ddlAndPropertiesBasePath
    global tableNameFromddlFileName


    tableListfilePath = str(getYamlFilePathInsideFolder(".object.config.ddlparser.ddlBatchFileName")).replace("//","/")
    ddlAndPropertiesBasePath = os.path.dirname(tableListfilePath) +"/"
#ddlAndPropertiesBasePath = str(getYamlFilePathInsideFolder(".object.config.ddlparser"))
    global ddlfileOptions
    ddlfileOptions = {}
    counter = 1
    for file in os.listdir(ddlAndPropertiesBasePath):
        if file.endswith(".ddl"):
            print("[" + str(counter) + "]  " + file)
            ddlfileOptions.update({counter: file})
            counter = counter + 1

    selectedOption = str(
        input(Fore.YELLOW + "Select file to load ddl :" + Fore.RESET))
    if (selectedOption.isnumeric() == True):    
        if len(selectedOption) <= 0 or int(selectedOption) not in ddlfileOptions:
            verboseHandle.printConsoleError("Invalid Option!")
            exit(0)
    else:
        verboseHandle.printConsoleError("Invalid Option!")
        exit(0)
    selectedddlFilename = ddlfileOptions.get(int(selectedOption))
    tableNameFromddlFileName = selectedddlFilename.replace(".ddl", "")
    # print(tableNameFromddlFileName)


configProperties = {}


def setConfigProperties():
    propertiesFilePath = ddlAndPropertiesBasePath + "/" + propertiesFileName
    # print(propertiesFilePath)
    file1 = open(propertiesFilePath, 'r')
    Lines = file1.readlines()
    for line in Lines:
        if (line.startswith("#")) or len(line) < 2:
            continue
        line = line.replace("\n", "")
        configProperties.update({line.split("=")[0]: line.split("=")[1]})


def readValuefromConfig(key, verbose=False):
    return configProperties.get(key)


def set_value_in_property_file(key, value):
    propertiesFilePath = ddlAndPropertiesBasePath + "/" + propertiesFileName
    config = ConfigObj(propertiesFilePath)
    if (len(value) == 0):
        value = ''
    config[key] = value  # Update Key
    config.write()  # Write Content
    x = open(propertiesFilePath)
    s = x.read().replace(' = ', '=')
    x.close()
    x = open(propertiesFilePath, "w")
    x.write(s)
    x.close


def setUserInputs2(tableNameFromddlFileName, ddlAndPropertiesBasePath):
    global propertiesFileName

    propertiesFileNameDefault = tableNameFromddlFileName + ".properties"
    propertiesFileName = str(
        input(
            Fore.YELLOW + "Properties filename to edit [" + propertiesFileNameDefault + "] :" + Fore.RESET))
    if (len(str(propertiesFileName)) == 0):
        propertiesFileName = propertiesFileNameDefault
    setConfigProperties()
    spaceIdDefault = readValuefromConfig("spaceId")
    spaceIdTypeDefault = readValuefromConfig("spaceIdType")
    routingDefault = readValuefromConfig("routing")
    indexDefault = readValuefromConfig("index")
    indexTypeDefault = readValuefromConfig("indexType")
    #supportDynamicPropertiesDefault = readValuefromConfig("supportDynamicProperties")
    verboseHandle.printConsoleWarning("Set properties values in " + propertiesFileName)
    if indexDefault is None:
        spaceIdValue = str(
            input(
                Fore.YELLOW + "Space ID [" + spaceIdDefault + "] :" + Fore.RESET))
    if (len(str(spaceIdValue)) == 0):
        spaceIdValue = spaceIdDefault

    if spaceIdTypeDefault is None:
        spaceIdTypeDefault = ""
        spaceIdTypeValue = str(
            input(
                Fore.YELLOW + "Space ID Type :" + Fore.RESET))

    else:
        spaceIdTypeValue = str(
            input(
                Fore.YELLOW + "Space ID Type [" + spaceIdTypeDefault + "] :" + Fore.RESET))
    if (len(str(spaceIdTypeValue)) == 0):
        spaceIdTypeValue = spaceIdTypeDefault

    if routingDefault is None:
        routingDefault = ""
        routingValue = str(
            input(
                Fore.YELLOW + "Routing Value :" + Fore.RESET))
    else:
        routingValue = str(
            input(
                Fore.YELLOW + "Routing Value [" + routingDefault + "] :" + Fore.RESET))
    if (len(str(routingDefault)) == 0):
        routingValue = routingDefault

    if indexDefault is None:
        indexDefault = ""
        indexValue = str(
            input(
                Fore.YELLOW + "Index :" + Fore.RESET))
    else:
        indexValue = str(
            input(
                Fore.YELLOW + "Index [" + indexDefault + "] :" + Fore.RESET))
    if (len(str(indexValue)) == 0):
        indexValue = indexDefault

    if indexTypeDefault is None:
        indexTypeDefault = ""
        indexTypeValue = str(
            input(
                Fore.YELLOW + "Index Type :" + Fore.RESET))
    else:
        indexTypeValue = str(
            input(
                Fore.YELLOW + "Index Type [" + indexTypeDefault + "] :" + Fore.RESET))
    if (len(str(indexTypeValue)) == 0):
        indexTypeValue = indexTypeDefault

    """
    if supportDynamicPropertiesDefault is None:
        supportDynamicPropertiesDefault = ""
        supportDynamicProperties = str(
            input(
                Fore.YELLOW + "Support Dynamic Properties :" + Fore.RESET))
    else:
        supportDynamicProperties = str(
            input(
                Fore.YELLOW + "Support Dynamic Properties [" + supportDynamicPropertiesDefault + "] :" + Fore.RESET))
    if (len(str(supportDynamicPropertiesDefault)) == 0):
        supportDynamicProperties = supportDynamicPropertiesDefault
    """

    verboseHandle.printConsoleWarning("***Summary***")
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleInfo("1. Space Id : " + spaceIdValue)
    verboseHandle.printConsoleInfo("2. Space ID Type : " + spaceIdTypeValue)
    verboseHandle.printConsoleInfo("3. Routing Value : " + routingValue)
    verboseHandle.printConsoleInfo("4. Index : " + indexValue)
    verboseHandle.printConsoleInfo("5. Index Type : " + indexTypeValue)
    #verboseHandle.printConsoleInfo("6. Support Dynamic Properties : " + supportDynamicProperties)
    verboseHandle.printConsoleWarning("------------------------------------------------------------")

    confirm = str(input(
        Fore.YELLOW + "Are you sure want to edit " + propertiesFileName + " ? [yes (y)] / [no (n)]" + Fore.RESET))
    while (len(str(confirm)) == 0):
        confirm = str(input(
            Fore.YELLOW + "Are you sure want to edit " + propertiesFileName + " ? [yes (y)] / [no (n)]" + Fore.RESET))
    print(confirm)
    if confirm.lower() != "y" and confirm.lower() != "yes":
        exit(0)

    if len(spaceIdValue) > 0 and spaceIdValue != "":
        set_value_in_property_file("spaceId", spaceIdValue)
    if len(spaceIdTypeValue) > 0 and spaceIdTypeValue != "":
        set_value_in_property_file("spaceIdType", spaceIdTypeValue)
    if len(routingValue) > 0 and routingValue != "":
        set_value_in_property_file("routing", routingValue)
    if len(indexValue) > 0 and indexValue != "":
        set_value_in_property_file("index", indexValue)
    if len(indexTypeValue) > 0 and indexTypeValue != "":
        set_value_in_property_file("indexType", indexTypeValue)
    #if len(supportDynamicProperties) > 0 and supportDynamicProperties != "":
    #    set_value_in_property_file("supportDynamicProperties", supportDynamicProperties)


def setInputs(isSandbox):
    global spaceName
    global objectMgmtHost
    global ddlAndPropertiesBasePath
    global tableNameFromddlFileName
    global ddlfileOptions
    global sandboxSpaceName

    sandboxSpaceName = readValuefromAppConfig("app.objectmanagement.sandboxspace")
    if(sandboxSpaceName is None or sandboxSpaceName=="" or len(str(sandboxSpaceName))<0):
        sandboxSpaceName = "demo"
        config_set_value_in_property_file("app.objectmanagement.sandboxspace",sandboxSpaceName)

    tableListfilePath = str(getYamlFilePathInsideFolder(".object.config.ddlparser.ddlBatchFileName")).replace("//","/")
    ddlAndPropertiesBasePath = os.path.dirname(tableListfilePath) +"/"

    #ddlAndPropertiesBasePath = str(getYamlFilePathInsideFolder(".object.config.ddlparser"))
    tableNameFromddlFileName = ''
    objectMgmtHost = getPivotHost()
    
    spaceName = readValuefromAppConfig("app.objectmanagement.space")
    if(spaceName is None or spaceName=="" or len(str(spaceName))<0):
        spaceName = readValuefromAppConfig("app.tieredstorage.pu.spacename")
        config_set_value_in_property_file("app.objectmanagement.space",spaceName)
    
    ddlfileOptions = {}
    counter = 1
    for file in os.listdir(ddlAndPropertiesBasePath):
        if file.endswith(".ddl"):
            print("[" + str(counter) + "]  " + file)
            ddlfileOptions.update({counter: file})
            counter = counter + 1

    selectedOption = str(
        input(Fore.YELLOW + "Select file to load ddl :" + Fore.RESET))
    if(selectedOption.isnumeric()==True):
        if len(selectedOption) <= 0 or int(selectedOption) not in ddlfileOptions:
            verboseHandle.printConsoleError("Invalid Option!")
            exit(0)
    else:    
        verboseHandle.printConsoleError("Invalid Option!")
        exit(0)
    selectedddlFilename = ddlfileOptions.get(int(selectedOption))
    tableNameFromddlFileName = selectedddlFilename.replace(".ddl", "")

    if(isSandbox == True):
        displaySummary(lookupLocator,lookupGroup,objectMgmtHost,sandboxSpaceName,selectedddlFilename,tableNameFromddlFileName)
    else:
        displaySummary(lookupLocator,lookupGroup,objectMgmtHost,spaceName,selectedddlFilename,tableNameFromddlFileName)

    summaryConfirm = str(input(Fore.YELLOW+"Do you want to continue object registration with above inputs ? [Yes (y) / No (n)]: "+Fore.RESET))
    while(len(str(summaryConfirm))==0):
        summaryConfirm = str(input(Fore.YELLOW+"Do you want to continue object registration with above inputs ? [Yes (y) / No (n)]: "+Fore.RESET))

    if(str(summaryConfirm).casefold()=='n' or str(summaryConfirm).casefold()=='no'):
        logger.info("Exiting without registering object")
        exit(0)

def displaySummary(lookupLocator,lookupGroup,objectMgmtHost,spaceName,selectedddlFilename,tableName):
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
            Fore.GREEN+"Selected DDL File = "+
            Fore.GREEN+selectedddlFilename+Fore.RESET)
    print(Fore.GREEN+"6. "+
            Fore.GREEN+"Table Name = "+
            Fore.GREEN+tableName+Fore.RESET)
    
    verboseHandle.printConsoleWarning("------------------------------------------------------------")

def getDataSandbox():
    data = {
        "tableName": "" + tableNameFromddlFileName + "",
        "spaceName": "" +sandboxSpaceName+""
        
    }
    return data


def getData():
    data = {
        "tableName": "" + tableNameFromddlFileName + ""
        
    }
    return data


def registerInSandbox():
    logger.info("registerInSandbox object")
    # print(getData())
    response = requests.post('http://' + objectMgmtHost + ':7001/registertype/sandbox', data=getDataSandbox(),
                             headers={'Accept': 'application/json'})
    if(response.text=="success"):
        verboseHandle.printConsoleInfo("Object is registered to sandbox successfully!!")
    else:
        verboseHandle.printConsoleError("Error in registering object to sandbox.")


def registerInSingle():
    logger.info("registerInSingle object")
    # print(getData())
    response = requests.post('http://' + objectMgmtHost + ':7001/registertype/single', data=getData(),
                             headers={'Accept': 'application/json'})
    if(response.text=="success"):
        verboseHandle.printConsoleInfo("Object is registered successfully!!")
    elif(response.text=="duplicate"):
        verboseHandle.printConsoleError("Object is already registered.")
    else:
        verboseHandle.printConsoleError("Error in registering object.")


def showMenuOptions():
    #menus = "Load From DDL,Edit Properties,Register Type To Sandbox,Register Type,EXIT"
    menus = "Edit Properties,Register Type To Sandbox,Register Type,EXIT"
    counter = 1
    global registerTypeOptions
    registerTypeOptions = {}
    for option in menus.split(","):
        if option == "EXIT":
            print("[99]  " + option)
            registerTypeOptions.update({99: option})
        else:
            print("[" + str(counter) + "]  " + option)
            registerTypeOptions.update({counter: option})
            counter = counter + 1


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Object Management -> Registration -> Register type')
    global lookupGroup
    global lookupLocator
    global managerHost
    managerHost = getManagerHost()
    managerInfo = getManagerInfo()
    lookupGroup = str(managerInfo['lookupGroups'])
    lookupLocator = str(managerHost)+":4174"
    try:
        args = []
        menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
        args.append(sys.argv[0])
        myCheckArg()
        showMenuOptions()
        
        selectedOption = str(
            input(Fore.YELLOW + "Select an option to perform :" + Fore.RESET))

        if selectedOption.isnumeric() == True:
            while len(selectedOption) <= 0 or int(selectedOption) not in registerTypeOptions or int(selectedOption) != 99:
                if len(selectedOption) <= 0 or int(selectedOption) not in registerTypeOptions:
                    verboseHandle.printConsoleError("Invalid option!")
                    exit(0)
                if int(selectedOption) == 1:
                    setUserInputs1()
                #if int(selectedOption) == 2:    
                    setUserInputs2(tableNameFromddlFileName, ddlAndPropertiesBasePath)
                if int(selectedOption) == 2:
                    setInputs(True)
                    registerInSandbox()
                if int(selectedOption) == 3:
                    setInputs(False)
                    registerInSingle()
                showMenuOptions()
                selectedOption = str(
                    input(Fore.YELLOW + "Select an option to perform :" + Fore.RESET))
        else:
            verboseHandle.printConsoleError("Invalid option!")
            exit(0)

    except Exception as e:
        handleException(e)