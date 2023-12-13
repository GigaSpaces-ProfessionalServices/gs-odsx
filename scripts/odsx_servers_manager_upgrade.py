#!/usr/bin/env python3
# s6.py
# !/usr/bin/python
import argparse
import json
import os
import sys

import requests
from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_servers_manager_install import getManagerHostFromEnv
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig, getYamlFilePathInsideFolder
from utils.ods_cluster_config import config_get_manager_node, isInstalledAndGetVersionOldGS
from utils.ods_ssh import executeRemoteCommandAndGetOutputValuePython36
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_keypress import userInputWithEscWrapper, userInputWrapper
from utils.odsx_print_tabular_data import printTabular

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR


def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    parser.add_argument('--host',
                        help='host ip',
                        required='True',
                        default='localhost')
    parser.add_argument('-u', '--user',
                        help='user name',
                        default='root')
    parser.add_argument('-dryrun', '--dryrun',
                        help='Dry run flag',
                        default='false', action='store_true')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])


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


def getGSVersion(host):
    #print('http://' + str(host) + ':8090/v2/info')
    managerInfoResponse = requests.get(('http://' + str(host) + ':8090/v2/info'),
                                       headers={'Accept': 'application/json'})
    output = managerInfoResponse.content.decode("utf-8")
    #print(output)
    logger.info("Json Response container:" + str(output))
    try:
        managerInfo = json.loads(managerInfoResponse.text)
        return str(managerInfo["revision"])
    except Exception as e:
        return "NA"

managerOldVersionDict = {}

def config_get_manager_listWithStatus(filePath='config/cluster.config'):
    headers = [Fore.YELLOW + "SrNo." + Fore.RESET,
               Fore.YELLOW + "Manager Name" + Fore.RESET,
               Fore.YELLOW + "Current Version" + Fore.RESET,
               Fore.YELLOW + "Previous Version" + Fore.RESET,
               Fore.YELLOW + "Status" + Fore.RESET]
    data = []
    managerDict = {}
    counter = 0
    global username
    global password
    managerNodes = config_get_manager_node()
    for node in managerNodes:
        #username = "gs-admin"#str(getUsernameByHost())
        #password = "gs-admin"#str(getPasswordByHost())
        status = getSpaceServerStatus(os.getenv(node.ip))
        counter = counter + 1
        managerDict.update({counter: node})
        currentVersion = "NA"
        previousVersion = "NA"
        oldVersion = isInstalledAndGetVersionOldGS(os.getenv(node.ip))
        if(len(str(oldVersion))>8):
            #if os.getenv(node.ip) in upgradedManagerDict:
            previousVersion = oldVersion
        try:
            #print('http://' + str(os.getenv(node.ip)) + ':8090/v2/info')
            managerInfoResponse = requests.get(('http://' + str(os.getenv(node.ip)) + ':8090/v2/info'),
                                               headers={'Accept': 'application/json'})
            output = managerInfoResponse.content.decode("utf-8")
            #print(output)
            logger.info("Json Response container:" + str(output))
            managerInfo = json.loads(managerInfoResponse.text)
            currentVersion = str(managerInfo["revision"])
            if os.getenv(node.ip) not in managerOldVersionDict:
                managerOldVersionDict.update({os.getenv(node.ip): currentVersion})
        except Exception as e:
            currentVersion = "NA"
            managerOldVersionDict.update({os.getenv(node.ip): currentVersion})
        if (status == "ON"):
            dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                         Fore.GREEN + os.getenv(node.ip) + Fore.RESET,
                         Fore.GREEN + currentVersion + Fore.RESET,
                         Fore.GREEN + previousVersion + Fore.RESET,
                         Fore.GREEN + status + Fore.RESET]
        else:
            dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                         Fore.GREEN + os.getenv(node.ip) + Fore.RESET,
                         Fore.GREEN + currentVersion + Fore.RESET,
                         Fore.GREEN + previousVersion + Fore.RESET,
                         Fore.RED + status + Fore.RESET]
        data.append(dataArray)
    printTabular(None, headers, data)
    # verboseHandle.printConsoleInfo(str(99) + ". ESC" " (Escape from menu.)")
    return managerDict



def validateServer(host):
    status = getSpaceServerStatus(host)
    #print(status)
    version = getGSVersion(host)
    if status == "ON" and version != "NA":
        return True
    return False


def proceedForManagerUpgrade(managerStatusIP, managerStatus):
    upgradedManagerDict.update({managerStatusIP:"N/A"})
    managerStatusIP = str(managerStatusIP)
    if managerStatus == "OFF":
        verboseHandle.printConsoleError(
            "manager is not running, upgrade will not be performed")
    else:
        verboseHandle.printConsoleInfo(
            "Starting upgradation for manager " + managerStatusIP)
        #scp_upload(managerStatusIP, user, sourcePath + "/" + packageName,
        #           "install/gs/upgrade/")
        cefLoggingJarInput = str(getYamlFilePathInsideFolder(".security.jars.cef.cefjar")).replace('[','').replace(']','')
        cefLoggingJarInputTarget = str(readValuefromAppConfig("app.manager.cefLogging.jar.target")).replace('[','').replace(']','')
        springLdapCoreJarInput = str(getYamlFilePathInsideFolder(".security.jars.springldapcore")).replace('[','').replace(']','')
        springLdapJarInput = str(getYamlFilePathInsideFolder(".security.jars.springldapjar")).replace('[','').replace(']','')
        vaultSupportJarInput = str(getYamlFilePathInsideFolder(".security.jars.vaultsupportjar")).replace('[','').replace(']','')
        javaPasswordJarInput = str(getYamlFilePathInsideFolder(".security.jars.javapassword")).replace('[','').replace(']','')
        springTargetJarInput = str(readValuefromAppConfig("app.manager.security.spring.jar.target")).replace('[','').replace(']','')

        commandToExecute = "scripts/servers_manager_upgrade_manual.sh"
        applicativeUserFile = readValuefromAppConfig("app.server.user")
        additionalParam = destPath + " " + packageName + " " + applicativeUserFile+ " " +sourcePath+'/'+packageName+" " \
           ""+cefLoggingJarInput+" "+cefLoggingJarInputTarget+" "+springLdapCoreJarInput+" "+springLdapJarInput+" "+vaultSupportJarInput+" "+javaPasswordJarInput+" "+springTargetJarInput
        #print(additionalParam)
        isConnectUsingPem = readValuefromAppConfig("cluster.usingPemFile")
        pemFileName = readValuefromAppConfig("cluster.pemFile")
        ssh = ""
        if isConnectUsingPem == 'True':
            ssh = ''.join(
                ['ssh', ' -i ', pemFileName, ' ', user, '@', str(managerStatusIP), ' '])
        else:
            ssh = ''.join(['ssh', ' ', str(managerStatusIP), ' '])
        cmd = ssh + 'bash' + ' -s ' + additionalParam + ' < scripts/servers_manager_upgrade_manual.sh'
        with Spinner():
            os.system(cmd)
            pass
        verboseHandle.printConsoleInfo("Done upgradation for manager " + managerStatusIP)
        if validateServer(managerStatusIP)==True:
            verboseHandle.printConsoleInfo("Validation successful manager is started " + managerStatusIP)
        else:
            verboseHandle.printConsoleError("Validation failed, manager is not started " + managerStatusIP)
        config_get_manager_listWithStatus()


if __name__ == '__main__':
    logger.info("Menu -> Security -> Servers - Manager - upgrade - manual ")
    verboseHandle.printConsoleWarning('Menu -> Servers -> Manager -> Upgrade')
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    '''
    username = ""
    password = ""
    appId=""
    safeId=""
    objectId=""
    appId = str(readValuefromAppConfig("app.space.security.appId")).replace('"','')
    safeId = str(readValuefromAppConfig("app.space.security.safeId")).replace('"','')
    objectId = str(readValuefromAppConfig("app.space.security.objectId")).replace('"','')
    logger.info("appId : "+appId+" safeID : "+safeId+" objectID : "+objectId)
    '''
    args = []
    menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
    args.append(sys.argv[0])
    upgradedManagerDict = {}

    managerDict = config_get_manager_listWithStatus()

    hostsConfig = ''
    hostsConfig = getManagerHostFromEnv()
    logger.info("hostConfig:" + str(hostsConfig))
    hostsConfig = hostsConfig.replace('"', '')
    if (len(str(hostsConfig)) > 0):
        verboseHandle.printConsoleWarning("Current cluster configuration : [" + hostsConfig + "] ")
    # hostConfiguration = str(userInputWrapper(Fore.YELLOW + "Select server to upgrade : " + Fore.RESET))
    # logger.info("hostConfiguration" + str(hostConfiguration))

    try:
        if (len(sys.argv) == 1 or sys.argv[1] == menuDrivenFlag):
            logger.info("Menudriven..")
            args.append(menuDrivenFlag)
            # if managerDict.get(int(hostConfiguration)) is not None:
            #    managerUpgrade = managerDict.get(int(hostConfiguration))
            #/dbagiga/gs_jars/CEFLogger-1.0-SNAPSHOT.jar
            sourcePath= sourceInstallerDirectory+"/gs/upgrade"
            destPath="/dbagiga"
            verboseHandle.printConsoleWarning("------------------Summary-----------------")
            verboseHandle.printConsoleWarning("Enter source directory for new GS build : "+sourcePath)
            verboseHandle.printConsoleWarning("Enter destination directory to install new GS build : "+str(destPath))

            if os.path.isdir(sourcePath):
                dir_list = os.listdir(sourcePath)
                if (len(dir_list) > 1):
                    verboseHandle.printConsoleError("multiple packages exist in source path " + str(dir_list))
                else:
                    packageName = dir_list[0]
                    user = 'root'
                    scriptUser = 'dbsh'
                    # cmd = "free | grep Mem | awk '{print $4/$2 * 100.0}'"

                    cmd = "df " + destPath + "|grep -v Avail|awk '{print $4/$2 * 100.0}'"
                    managerCount = 0
                    managerStorageDict = {}
                    managerRunningStatusDict = {}
                    for node in config_get_manager_node():
                        status = getSpaceServerStatus(os.getenv(node.ip))
                        freeStoragePerc = executeRemoteCommandAndGetOutputValuePython36(os.getenv(node.ip), user,
                                                                                        cmd)
                        freeStoragePerc = str(freeStoragePerc).replace("\n", "")
                        managerStorageDict.update({os.getenv(node.ip): freeStoragePerc})
                        if status == "ON":
                            managerRunningStatusDict.update({os.getenv(node.ip): "ON"})
                            managerCount = managerCount + 1
                        else:
                            managerRunningStatusDict.update({os.getenv(node.ip): "OFF"})

                    # print("freeStoragePerc: " + str(freeStoragePerc) + ", managerCount: " + str(managerCount))

                    verboseHandle.printConsoleInfo("1. Enough manager are available : " + str(managerCount))
                    verboseHandle.printConsoleInfo(
                        "2. Source path is proper. New package to upload : " + str(dir_list))
                    managerCountStorage = 2
                    for managerIp, managerStorageSpace in managerStorageDict.items():
                        managerIp = str(managerIp)
                        managerCountStorage = managerCountStorage + 1
                        if float(managerStorageSpace) > 10:
                            verboseHandle.printConsoleInfo(
                                str(managerCountStorage) + ". Enough storage space is available in manager [" + managerIp + "] : " + str(
                                    managerStorageSpace) + " % free")
                        else:
                            verboseHandle.printConsoleError(
                                str(managerCountStorage) + ". Enough storage space is not available in [" + managerIp + "] : " + str(
                                    managerStorageSpace) + " % free")
                    verboseHandle.printConsoleWarning("------------------------------------------")
                    inputChoice = str(userInputWithEscWrapper(Fore.YELLOW+"[1] For individual\n[Enter] For all. \n[99] For exit. :"+Fore.RESET))
                    if inputChoice=='99':
                        quit(0)
                    if inputChoice=='1':
                        inputHostNuber = str(userInputWrapper(Fore.YELLOW+"Enter host number to upgrade. :"+Fore.RESET))
                        managerIP = managerDict.get(int(inputHostNuber))
                        managerIP = os.getenv(managerIP.ip)
                        managerStatus = managerRunningStatusDict.get(managerIP)
                        confirm = str(userInputWrapper(Fore.YELLOW + "Are you sure want to continue gs manager upgradation upgrade? [yes (y)] / [no (n)] : " + Fore.RESET))
                        if confirm == 'yes' or confirm == 'y':
                            proceedForManagerUpgrade(managerIP,managerStatus)
                    if inputChoice=='':
                        confirm = str(userInputWrapper(Fore.YELLOW + "Are you sure want to continue manager gs upgradation ? [yes (y)] / [no (n)] : " + Fore.RESET))
                        if managerCount >= 2:
                            while (len(str(confirm)) == 0):
                                confirm = str(userInputWrapper(Fore.YELLOW + "Are you sure want to continue manager gs upgradation ? [yes (y)] / [no (n)] : " + Fore.RESET))
                            logger.info("confirm :" + str(confirm))
                            if confirm == 'yes' or confirm == 'y':
                                for managerStatusIP, managerStatus in managerRunningStatusDict.items():
                                    proceedForManagerUpgrade(managerStatusIP,managerStatus)
                        else:
                            if managerCount < 2:
                                verboseHandle.printConsoleError(
                                    "Minimum manager required : 2, currently running manager count : " + str(
                                        managerCount))
                            else:
                                verboseHandle.printConsoleError("Not enough storage space")

            else:
                verboseHandle.printConsoleError("source path is not proper")

        # elif (hostConfiguration == '99'):
        #    logger.info("99 - Exist stop")
    except Exception as e:
        handleException(e)
        logger.error("Invalid arguement " + str(e))
        verboseHandle.printConsoleError("Invalid argument" + str(e))
