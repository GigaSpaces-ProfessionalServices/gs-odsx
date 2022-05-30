import argparse
import os
import sys

import requests
from colorama import Fore
from configobj import ConfigObj

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


def setUserInputs1():
    global ddlAndPropertiesBasePath
    global tableNameFromddlFileName

    ddlAndPropertiesBasePathDefault = '/home/jay/work/gigaspace/bofLeumi/DdlParser-David-leumicode/src/main/resources'

    ddlAndPropertiesBasePath = str(
        input(
            Fore.YELLOW + "Enter base path for ddl, properties file [" + ddlAndPropertiesBasePathDefault + "] :" + Fore.RESET))
    if (len(str(ddlAndPropertiesBasePath)) == 0):
        ddlAndPropertiesBasePath = ddlAndPropertiesBasePathDefault

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
    if len(selectedOption) <= 0 or int(selectedOption) not in ddlfileOptions:
        verboseHandle.printConsoleError("Wrong option selected")
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
    supportDynamicPropertiesDefault = readValuefromConfig("supportDynamicProperties")
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

    verboseHandle.printConsoleWarning("***Summary***")
    verboseHandle.printConsoleInfo("1. Space Id : " + spaceIdValue)
    verboseHandle.printConsoleInfo("2. Space ID Type : " + spaceIdTypeValue)
    verboseHandle.printConsoleInfo("3. Routing Value : " + routingValue)
    verboseHandle.printConsoleInfo("4. Index : " + indexValue)
    verboseHandle.printConsoleInfo("5. Index Type : " + indexTypeValue)
    verboseHandle.printConsoleInfo("6. Support Dynamic Properties : " + supportDynamicProperties)
    confirm = str(input(
        Fore.YELLOW + "Are you sure want to continue updating " + propertiesFileName + " ? [yes (y)] / [no (n)]" + Fore.RESET))
    while (len(str(confirm)) == 0):
        confirm = str(input(
            Fore.YELLOW + "Are you sure want to continue updating " + propertiesFileName + " ? [yes (y)] / [no (n)]" + Fore.RESET))
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
    if len(supportDynamicProperties) > 0 and supportDynamicProperties != "":
        set_value_in_property_file("supportDynamicProperties", supportDynamicProperties)


def setUserInputs3():
    #    global spaceName
    global objectMgmtHost
    global lookupGroup
    global lookupLocator

    #    spaceNameDefault = 'bllspace'
    objectMgmtHostDefault = 'localhost'
    lookupGroupDefault = "xap-16.2.0"
    lookupLocatorDefault = readValuefromAppConfig("app.manager.hosts")
    # lookupLocatorDefault = ""
    # if (str(managerServerConfig).__contains__(',')):  # if cluster manager configured
    #    managerServerConfig = str(managerServerConfig).replace('"', '')
    #    for managerServer in managerServerConfig.split(','):
    #        lookupLocatorDefault = lookupLocatorDefault + managerServer + ":4174 "
    # else:
    #    lookupLocatorDefault = managerServerConfig + ":4174 "

    #    spaceName = str(
    #        input(Fore.YELLOW + "Enter Space name [" + spaceNameDefault + "]:" + Fore.RESET))
    #    if (len(str(spaceName)) == 0):
    #        spaceName = spaceNameDefault

    objectMgmtHost = str(
        input(Fore.YELLOW + "Object management host (pivot) [" + objectMgmtHostDefault + "] :" + Fore.RESET))
    if (len(str(objectMgmtHost)) == 0):
        objectMgmtHost = objectMgmtHostDefault

    lookupGroup = str(
        input(Fore.YELLOW + "Lookup group [" + lookupGroupDefault + "] :" + Fore.RESET))
    if (len(str(lookupGroup)) == 0):
        lookupGroup = lookupGroupDefault

    lookupLocator = str(
        input(Fore.YELLOW + "Lookup locator [" + lookupLocatorDefault + "] :" + Fore.RESET))
    if (len(str(lookupLocator)) == 0):
        lookupLocator = lookupLocatorDefault


def setUserInputs4():
    global spaceName
    global objectMgmtHost
    global lookupGroup
    global lookupLocator

    spaceNameDefault = 'bllspace'
    objectMgmtHostDefault = 'localhost'
    lookupGroupDefault = "xap-16.2.0"
    lookupLocatorDefault = readValuefromAppConfig("app.manager.hosts")
    # lookupLocatorDefault = ""
    # if (str(managerServerConfig).__contains__(',')):  # if cluster manager configured
    #    managerServerConfig = str(managerServerConfig).replace('"', '')
    #    for managerServer in managerServerConfig.split(','):
    #        lookupLocatorDefault = lookupLocatorDefault + managerServer + ":4174 "
    # else:
    #    lookupLocatorDefault = managerServerConfig + ":4174 "

    spaceName = str(
        input(Fore.YELLOW + "Enter Space name [" + spaceNameDefault + "]:" + Fore.RESET))
    if (len(str(spaceName)) == 0):
        spaceName = spaceNameDefault

    objectMgmtHost = str(
        input(Fore.YELLOW + "Object management host (pivot) [" + objectMgmtHostDefault + "] :" + Fore.RESET))
    if (len(str(objectMgmtHost)) == 0):
        objectMgmtHost = objectMgmtHostDefault

    lookupGroup = str(
        input(Fore.YELLOW + "Lookup group [" + lookupGroupDefault + "] :" + Fore.RESET))
    if (len(str(lookupGroup)) == 0):
        lookupGroup = lookupGroupDefault

    lookupLocator = str(
        input(Fore.YELLOW + "Lookup locator [" + lookupLocatorDefault + "] :" + Fore.RESET))
    if (len(str(lookupLocator)) == 0):
        lookupLocator = lookupLocatorDefault


def getDataSandbox():
    data = {
        "ddlAndPropertiesBasePath": "" + ddlAndPropertiesBasePath + "",
        "tableName": "" + tableNameFromddlFileName + "",
        "lookupGroup": "" + lookupGroup + "",
        "lookupLocator": "" + lookupLocator + ""
    }
    return data


def getData():
    data = {
        "ddlAndPropertiesBasePath": "" + ddlAndPropertiesBasePath + "",
        "spaceName": "" + spaceName + "",
        "tableName": "" + tableNameFromddlFileName + "",
        "lookupGroup": "" + lookupGroup + "",
        "lookupLocator": "" + lookupLocator + ""
    }
    return data


def registerInSandbox():
    logger.info("registerInSandbox object")
    # print(getData())
    response = requests.post('http://' + objectMgmtHost + ':7001/registertype/sandbox', data=getDataSandbox(),
                             headers={'Accept': 'application/json'})
    verboseHandle.printConsoleInfo(response.text)


def registerInSingle():
    logger.info("registerInSingle object")
    # print(getData())
    response = requests.post('http://' + objectMgmtHost + ':7001/registertype/single', data=getData(),
                             headers={'Accept': 'application/json'})
    verboseHandle.printConsoleInfo(response.text)


def showMenuOptions():
    menus = "Load From DDL,Edit Properties,Register Type To Sandbox,Register Type,EXIT"
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
    verboseHandle.printConsoleWarning('Menu -> Object Management -> Register type')
    try:
        args = []
        menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
        args.append(sys.argv[0])
        myCheckArg()
        showMenuOptions()
        selectedOption = str(
            input(Fore.YELLOW + "Select option to perform :" + Fore.RESET))

        while len(selectedOption) <= 0 or int(selectedOption) not in registerTypeOptions or int(selectedOption) != 99:
            if len(selectedOption) <= 0 or int(selectedOption) not in registerTypeOptions:
                verboseHandle.printConsoleError("Wrong option selected")
                exit(0)
            if int(selectedOption) == 1:
                setUserInputs1()
            if int(selectedOption) == 2:
                setUserInputs2(tableNameFromddlFileName, ddlAndPropertiesBasePath)
            if int(selectedOption) == 3:
                setUserInputs3()
                registerInSandbox()
            if int(selectedOption) == 4:
                setUserInputs4()
                registerInSingle()
            showMenuOptions()
            selectedOption = str(
                input(Fore.YELLOW + "Select option to perform :" + Fore.RESET))

    except Exception as e:
        handleException(e)
