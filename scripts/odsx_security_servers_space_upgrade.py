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
from scripts.odsx_security_dev_servers_space_list import getStatusOfSpaceHost
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig, getYamlFilePathInsideFolder
from utils.ods_cluster_config import isInstalledAndGetVersionOldGS, config_get_space_node, getSpaceHostFromEnv, \
    isInstalledAndGetVersion
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


# def getGSVersion(host):
#     #print('http://' + str(host) + ':8090/v2/info')
#     spaceInfoResponse = requests.get(('http://' + str(host) + ':8090/v2/info'),
#                                      headers={'Accept': 'application/json'})
#     output = spaceInfoResponse.content.decode("utf-8")
#     print(output)
#     logger.info("Json Response container:" + str(output))
#     try:
#         spaceInfo = json.loads(spaceInfoResponse.text)
#         print(spaceInfo)
#         return str("gigaspaces-smart-cache-enterprise-16.3.0-m5-tue-26")
#     except Exception as e:
#         return "NA"

spaceOldVersionDict = {}

def config_get_space_listWithStatus(filePath='config/cluster.config'):
    headers = [Fore.YELLOW + "SrNo." + Fore.RESET,
               Fore.YELLOW + "Space Name" + Fore.RESET,
               Fore.YELLOW + "Current Version" + Fore.RESET,
               Fore.YELLOW + "Previous Version" + Fore.RESET,
               Fore.YELLOW + "Status" + Fore.RESET]
    data = []
    spaceDict = {}
    counter = 0
    global username
    global password
    global currentVersion
    global previousVersion
    spaceNodes = config_get_space_node()
    for node in spaceNodes:
        #username = "gs-admin"#str(getUsernameByHost(str(os.getenv(node.ip)),appId,safeId,objectId))
        #password = "gs-admin"#str(getPasswordByHost(str(os.getenv(node.ip)),appId,safeId,objectId))
        status = getStatusOfSpaceHost(os.getenv(node.ip))
        # print(status)
        counter = counter + 1
        spaceDict.update({counter: node})
        currentVersion = "NA"
        previousVersion = "NA"
        oldVersion = isInstalledAndGetVersionOldGS(os.getenv(node.ip))
        if(len(str(oldVersion))>8):
            #if os.getenv(node.ip) in upgradedManagerDict:
            previousVersion = oldVersion
        try:
            #print('http://' + str(os.getenv(node.ip)) + ':8090/v2/info')
            # spaceInfoResponse = requests.get(('http://' + str(os.getenv(node.ip)) + ':8090/v2/info'),
            #                                  headers={'Accept': 'application/json'})
            # output = spaceInfoResponse.content.decode("utf-8")
            # #print(output)
            # logger.info("Json Response container:" + str(output))
            # spaceInfo = json.loads(spaceInfoResponse.text)
            # currentVersion = str(spaceInfo["revision"])
            currentVersion = isInstalledAndGetVersion(os.getenv(str(node.ip))) #str(spaceInfo["revision"])
            if(len(str(currentVersion))>8):
                #if os.getenv(node.ip) in upgradedManagerDict:
                currentVersion = currentVersion
            if os.getenv(node.ip) not in spaceOldVersionDict:
                spaceOldVersionDict.update({os.getenv(node.ip): "currentVersion"})
        except Exception as e:
            currentVersion = "NA"
            spaceOldVersionDict.update({os.getenv(node.ip): "currentVersion"})
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
    return spaceDict



def validateServer(host):
    status = getStatusOfSpaceHost(host)
    #print(status)
    # version = getGSVersion(host)
    if status == "ON":
        return True
    return False


def proceedForSpaceUpgrade(spaceStatusIP, spaceStatus):
    crnVersion=isInstalledAndGetVersion(str(spaceStatusIP));
    upgradedSpaceDict.update({spaceStatusIP:"N/A"})
    spaceStatusIP = str(spaceStatusIP)
    # print(" package name:  "+str(packageName.replace(".zip",""))+ " ...  "+ str(crnVersion))
    # print(" package compare:  "+str(packageName.replace(".zip","") == crnVersion))
    if spaceStatus == "OFF":
        verboseHandle.printConsoleError(
            "space is not running, upgrade will not be performed")
    elif packageName.replace(".zip","") == crnVersion:
        verboseHandle.printConsoleError(
            "space already upgraded")
    else:
        verboseHandle.printConsoleInfo(
            "Starting upgradation for space " + spaceStatusIP)
        #scp_upload(spaceStatusIP, user, sourcePath + "/" + packageName,
        #           "install/gs/upgrade/")
        cefLoggingJarInput = str(getYamlFilePathInsideFolder(".security.jars.cef.cefjar")).replace('[','').replace(']','')
        cefLoggingJarInputTarget = str(readValuefromAppConfig("app.space.cefLogging.jar.target")).replace('[','').replace(']','')
        springLdapCoreJarInput = str(getYamlFilePathInsideFolder(".security.jars.springldapcore")).replace('[','').replace(']','')
        springLdapJarInput = str(getYamlFilePathInsideFolder(".security.jars.springldapjar")).replace('[','').replace(']','')
        vaultSupportJarInput = str(getYamlFilePathInsideFolder(".security.jars.vaultsupportjar")).replace('[','').replace(']','')
        javaPasswordJarInput = str(getYamlFilePathInsideFolder(".security.jars.javapassword")).replace('[','').replace(']','')
        springTargetJarInput = str(readValuefromAppConfig("app.space.security.spring.jar.target")).replace('[','').replace(']','')

        commandToExecute = "scripts/servers_manager_upgrade_manual.sh"
        applicativeUserFile = readValuefromAppConfig("app.server.user")
        additionalParam = destPath + " " + packageName + " " + applicativeUserFile+ " " +sourcePath+'/'+packageName+" " \
                                                                                                                    ""+cefLoggingJarInput+" "+cefLoggingJarInputTarget+" "+springLdapCoreJarInput+" "+springLdapJarInput+" "+vaultSupportJarInput+" "+javaPasswordJarInput+" "+springTargetJarInput
        #print(additionalParam)
        isConnectUsingPem = readValuefromAppConfig("cluster.usingPemFile")
        pemFileName = readValuefromAppConfig("cluster.pemFile")
        ssh = ""
        # if(previousVersion != "N/A" and currentVersion !="N/A"):
        #     if(currentVersion == previousVersion):
        #         verboseHandle.printConsoleInfo("Space is already upgraded with this version")
        #         return
        if isConnectUsingPem == 'True':
            ssh = ''.join(
                ['ssh', ' -i ', pemFileName, ' ', user, '@', str(spaceStatusIP), ' '])
        else:
            ssh = ''.join(['ssh', ' ', str(spaceStatusIP), ' '])
        cmd = ssh + 'bash' + ' -s ' + additionalParam + ' < scripts/servers_manager_upgrade_manual.sh'
        with Spinner():
            os.system(cmd)
            pass
        verboseHandle.printConsoleInfo("Done upgradation for space " + spaceStatusIP)
        if validateServer(spaceStatusIP)==True:
            verboseHandle.printConsoleInfo("Validation successful space is started " + spaceStatusIP)
        else:
            verboseHandle.printConsoleError("Validation failed, space is not started " + spaceStatusIP)
        config_get_space_listWithStatus()


if __name__ == '__main__':
    logger.info("Menu -> Security -> Servers - Space - upgrade - manual ")
    verboseHandle.printConsoleWarning('Menu -> Servers -> Space -> Upgrade')
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    global packageName
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
    upgradedSpaceDict = {}

    spaceDict = config_get_space_listWithStatus()

    hostsConfig = ''
    hostsConfig = getSpaceHostFromEnv()
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
            # if spaceDict.get(int(hostConfiguration)) is not None:
            #    managerUpgrade = spaceDict.get(int(hostConfiguration))
            #/dbagiga/gs_jars/CEFLogger-1.0-SNAPSHOT.jar
            sourcePath= sourceInstallerDirectory+"gs/upgrade"
            destPath="/dbagiga"
            verboseHandle.printConsoleWarning("------------------Summary-----------------")
            verboseHandle.printConsoleWarning("Enter source directory for new GS build : "+sourcePath)
            verboseHandle.printConsoleWarning("Enter destination directory to install new GS build : "+str(destPath))

            if os.path.isdir(sourcePath):
                dir_list = os.listdir(sourcePath)
                # print(len(dir_list))
                # print(dir_list)
                if (len(dir_list) > 1):
                    verboseHandle.printConsoleError("multiple packages exist in source path " + str(dir_list))
                else:
                    packageName = dir_list[0]
                    user = 'root'
                    scriptUser = 'dbsh'
                    # cmd = "free | grep Mem | awk '{print $4/$2 * 100.0}'"
                    cmd = "df " + destPath + "|grep -v Avail|awk '{print $4/$2 * 100.0}'"
                    spaceCount = 0
                    spaceStorageDict = {}
                    spaceRunningStatusDict = {}
                    for node in config_get_space_node():
                        status = getStatusOfSpaceHost(os.getenv(node.ip))
                        freeStoragePerc = executeRemoteCommandAndGetOutputValuePython36(os.getenv(node.ip), user,
                                                                                        cmd)
                        freeStoragePerc = str(freeStoragePerc).replace("\n", "")
                        spaceStorageDict.update({os.getenv(node.ip): freeStoragePerc})
                        if status == "ON":
                            spaceRunningStatusDict.update({os.getenv(node.ip): "ON"})
                            spaceCount = spaceCount + 1
                        else:
                            spaceRunningStatusDict.update({os.getenv(node.ip): "OFF"})

                    # print("freeStoragePerc: " + str(freeStoragePerc) + ", spaceCount: " + str(spaceCount))

                    verboseHandle.printConsoleInfo("1. Enough space are available : " + str(spaceCount))
                    verboseHandle.printConsoleInfo(
                        "2. Source path is proper. New package to upload : " + str(dir_list))
                    spaceCountStorage = 2
                    for spaceIp, spaceStorageSpace in spaceStorageDict.items():
                        spaceIp = str(spaceIp)
                        spaceCountStorage = spaceCountStorage + 1
                        if float(spaceStorageSpace) > 10:
                            verboseHandle.printConsoleInfo(
                                str(spaceCountStorage) + ". Enough storage space is available in space [" + spaceIp + "] : " + str(
                                    spaceStorageSpace) + " % free")
                        else:
                            verboseHandle.printConsoleError(
                                str(spaceCountStorage) + ". Enough storage space is not available in [" + spaceIp + "] : " + str(
                                    spaceStorageSpace) + " % free")
                    verboseHandle.printConsoleWarning("------------------------------------------")
                    inputChoice = str(userInputWithEscWrapper(Fore.YELLOW+"[1] For individual\n[Enter] For all. \n[99] For exit. :"+Fore.RESET))
                    if inputChoice=='99':
                        quit(0)
                    if inputChoice=='1':
                        inputHostNuber = str(userInputWrapper(Fore.YELLOW+"Enter host number to upgrade. :"+Fore.RESET))
                        spaceIp = spaceDict.get(int(inputHostNuber))
                        spaceIp = os.getenv(spaceIp.ip)
                        spaceStatus = spaceRunningStatusDict.get(spaceIp)
                        confirm = str(userInputWrapper(Fore.YELLOW + "Are you sure want to continue gs space upgradation upgrade? [yes (y)] / [no (n)] : " + Fore.RESET))
                        if confirm == 'yes' or confirm == 'y':
                            proceedForSpaceUpgrade(spaceIp,spaceStatus)
                    if inputChoice=='':
                        confirm = str(userInputWrapper(Fore.YELLOW + "Are you sure want to continue space gs upgradation ? [yes (y)] / [no (n)] : " + Fore.RESET))
                        if spaceCount >= 2:
                            while (len(str(confirm)) == 0):
                                confirm = str(userInputWrapper(Fore.YELLOW + "Are you sure want to continue space gs upgradation ? [yes (y)] / [no (n)] : " + Fore.RESET))
                            logger.info("confirm :" + str(confirm))
                            if confirm == 'yes' or confirm == 'y':
                                for spaceStatusIP, spaceStatus in spaceRunningStatusDict.items():
                                    proceedForSpaceUpgrade(spaceStatusIP,spaceStatus)
                        else:
                            if spaceCount < 2:
                                verboseHandle.printConsoleError(
                                    "Minimum space required : 2, currently running space count : " + str(
                                        spaceCount))
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
