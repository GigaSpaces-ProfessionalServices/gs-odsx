#!/usr/bin/env python3
# s6.py
# !/usr/bin/python
import argparse
import json
import os
import sys

import requests
from colorama import Fore
from scripts.odsx_servers_manager_install import getManagerHostFromEnv
from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_manager_node
from utils.ods_scp import scp_upload
from utils.ods_ssh import executeRemoteCommandAndGetOutputValuePython36
from utils.ods_validation import getSpaceServerStatus
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


def config_get_manager_listWithStatus(filePath='config/cluster.config'):
    headers = [Fore.YELLOW + "SrNo." + Fore.RESET,
               Fore.YELLOW + "Manager Name" + Fore.RESET,
               Fore.YELLOW + "IP" + Fore.RESET,
               Fore.YELLOW + "Version" + Fore.RESET,
               Fore.YELLOW + "Status" + Fore.RESET]
    data = []
    managerDict = {}
    counter = 0
    managerNodes = config_get_manager_node()
    for node in managerNodes:
        status = getSpaceServerStatus(os.getenv(node.ip))
        counter = counter + 1
        managerDict.update({counter: node})
        version = "NA"
        try:
            managerInfoResponse = requests.get(('http://' + str(os.getenv(node.ip)) + ':8090/v2/info'),
                                               headers={'Accept': 'application/json'})
            output = managerInfoResponse.content.decode("utf-8")
            logger.info("Json Response container:" + str(output))
            managerInfo = json.loads(managerInfoResponse.text)
            version = str(managerInfo["revision"])
        except Exception as e:
            version = "NA"
        if (status == "ON"):
            dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                         Fore.GREEN + os.getenv(node.name) + Fore.RESET,
                         Fore.GREEN + os.getenv(node.ip) + Fore.RESET,
                         Fore.GREEN + version + Fore.RESET,
                         Fore.GREEN + status + Fore.RESET]
        else:
            dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                         Fore.GREEN + os.getenv(node.name) + Fore.RESET,
                         Fore.GREEN + os.getenv(node.ip) + Fore.RESET,
                         Fore.GREEN + version + Fore.RESET,
                         Fore.RED + status + Fore.RESET]
        data.append(dataArray)
    printTabular(None, headers, data)
    verboseHandle.printConsoleInfo(str(99) + ". ESC" " (Escape from menu.)")
    return managerDict


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


if __name__ == '__main__':
    logger.info("servers - manager - upgrade - manual ")
    verboseHandle.printConsoleWarning('Servers -> Manager -> Upgrade -> Manual')
    args = []
    menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
    args.append(sys.argv[0])

    managerDict = config_get_manager_listWithStatus()

    hostsConfig = ''
    hostsConfig = getManagerHostFromEnv()
    logger.info("hostConfig:" + str(hostsConfig))
    hostsConfig = hostsConfig.replace('"', '')
    if (len(str(hostsConfig)) > 0):
        verboseHandle.printConsoleWarning("Current cluster configuration : [" + hostsConfig + "] ")
    hostConfiguration = str(input(Fore.YELLOW + "Select server to upgrade : " + Fore.RESET))
    logger.info("hostConfiguration" + str(hostConfiguration))

    try:
        if (len(sys.argv) == 1 or sys.argv[1] == menuDrivenFlag):
            logger.info("Menudriven..")
            args.append(menuDrivenFlag)
            if managerDict.get(int(hostConfiguration)) is not None:
                managerUpgrade = managerDict.get(int(hostConfiguration))
                sourcePath = str(input(Fore.YELLOW + "Enter source directory for new GS build : " + Fore.RESET))
                destPath = str(input(
                    Fore.YELLOW + "Enter destination directory to install new GS build [/dbagiga] : " + Fore.RESET))
                if len(str(destPath)) == 0:
                    destPath = "/dbagiga"
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
                        freeStoragePerc = executeRemoteCommandAndGetOutputValuePython36(os.getenv(managerUpgrade.ip), user, cmd)
                        managerCount = 0
                        for node in config_get_manager_node():
                            status = getSpaceServerStatus(os.getenv(node.ip))
                            if status == "ON":
                                managerCount = managerCount + 1

                        executeRemoteCommandAndGetOutputValuePython36(os.getenv(managerUpgrade.ip), user,
                                                                      "mkdir -p install/gs/upgrade/")
                        freeStoragePerc = str(freeStoragePerc).replace("\n", "")
                        print("freeStoragePerc: " + str(freeStoragePerc) + ", managerCount: " + str(managerCount))
                        if float(freeStoragePerc) > 10 and managerCount >= 2:
                            verboseHandle.printConsoleWarning("***Summary***")
                            verboseHandle.printConsoleInfo(
                                "1. Enough storage space is available : " + str(freeStoragePerc) + " % free")
                            verboseHandle.printConsoleInfo("2. Enough manager are available : " + str(managerCount))
                            verboseHandle.printConsoleInfo(
                                "3. Source path is proper. New package to upload : " + str(dir_list))
                            confirm = str(input(
                                Fore.YELLOW + "Are you sure want to continue manager gs upgradation ? [yes (y)] / [no (n)]" + Fore.RESET))
                            while (len(str(confirm)) == 0):
                                confirm = str(input(
                                    Fore.YELLOW + "Are you sure want to continue manager gs upgradation ? [yes (y)] / [no (n)]" + Fore.RESET))
                            logger.info("confirm :" + str(confirm))
                            if confirm == 'yes' or confirm == 'y':
                                scp_upload(os.getenv(managerUpgrade.ip), user, sourcePath + "/" + packageName,
                                           "install/gs/upgrade/")
                                commandToExecute = "scripts/servers_manager_upgrade_manual.sh"
                                applicativeUserFile = readValuefromAppConfig("app.server.user")
                                additionalParam = destPath + " " + packageName + " " + applicativeUserFile
                                isConnectUsingPem = readValuefromAppConfig("cluster.usingPemFile")
                                pemFileName = readValuefromAppConfig("cluster.pemFile")
                                ssh = ""
                                if isConnectUsingPem == 'True':
                                    ssh = ''.join(
                                        ['ssh', ' -i ', pemFileName, ' ', user, '@', str(os.getenv(managerUpgrade.ip)), ' '])
                                else:
                                    ssh = ''.join(['ssh', ' ', str(os.getenv(managerUpgrade.ip)), ' '])
                                cmd = ssh + 'bash' + ' -s ' + additionalParam + ' < scripts/servers_manager_upgrade_manual.sh'
                                os.system(cmd)
                                config_get_manager_listWithStatus()
                        else:
                            if managerCount < 2:
                                verboseHandle.printConsoleError(
                                    "Minimum manager required : 2, currently running manager count : " + str(
                                        managerCount))
                            else:
                                verboseHandle.printConsoleError("Not enough storage space")

                else:
                    verboseHandle.printConsoleError("source path is not proper")

        elif (hostConfiguration == '99'):
            logger.info("99 - Exist stop")
    except Exception as e:
        handleException(e)
        logger.error("Invalid arguement " + str(e))
        verboseHandle.printConsoleError("Invalid argument" + str(e))