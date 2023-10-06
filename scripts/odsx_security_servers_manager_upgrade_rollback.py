#!/usr/bin/env python3
# s6.py
# !/usr/bin/python
import argparse
import json
import os
import sys

import requests
from colorama import Fore
from requests.auth import HTTPBasicAuth

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_manager_node
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36
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

def getManagerHostFromEnv():
    logger.info("getManagerHostFromEnv()")
    hosts = ''
    managerNodes = config_get_manager_node()
    for node in managerNodes:
        hosts+=str(os.getenv(str(node.ip)))+','
    hosts=hosts[:-1]
    return hosts

def config_get_manager_listWithStatus(filePath='config/cluster.config'):
    headers = [Fore.YELLOW + "SrNo." + Fore.RESET,
               Fore.YELLOW + "Manager Name" + Fore.RESET,
               Fore.YELLOW + "IP" + Fore.RESET,
               Fore.YELLOW + "Version" + Fore.RESET,
               Fore.YELLOW + "Status" + Fore.RESET]
    data = []
    managerDict = {}
    counter = 0
    global username
    global password
    managerNodes = config_get_manager_node()
    for node in managerNodes:
        username = "gs-admin"#str(getUsernameByHost(str(os.getenv(node.ip)),appId,safeId,objectId))
        password = "gs-admin"#str(getPasswordByHost(str(os.getenv(node.ip)),appId,safeId,objectId))
        status = getSpaceServerStatus(os.getenv(node.ip))
        counter = counter + 1
        managerDict.update({counter: node})
        version = "NA"
        try:
            managerInfoResponse = requests.get(('http://' + str(os.getenv(node.ip)) + ':8090/v2/info'),
                                               headers={'Accept': 'application/json'},auth = HTTPBasicAuth(username, password))
            output = managerInfoResponse.content.decode("utf-8")
            logger.info("Json Response container:" + str(output))
            managerInfo = json.loads(managerInfoResponse.text)
            version = str(managerInfo["revision"])
        except Exception as e:
            version = "NA"
        if (status == "ON"):
            dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                         Fore.GREEN + os.getenv(node.ip) + Fore.RESET,
                         Fore.GREEN + os.getenv(node.ip) + Fore.RESET,
                         Fore.GREEN + version + Fore.RESET,
                         Fore.GREEN + status + Fore.RESET]
        else:
            dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                         Fore.GREEN + os.getenv(node.ip) + Fore.RESET,
                         Fore.GREEN + os.getenv(node.ip) + Fore.RESET,
                         Fore.GREEN + version + Fore.RESET,
                         Fore.RED + status + Fore.RESET]
        data.append(dataArray)
    printTabular(None, headers, data)

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


def proceedForRollback(host):
    logger.info("proceedForRollback")
    dbaGigaPath=str(readValuefromAppConfig("app.giga.path"))
    cmdList = ["systemctl stop gsa","cd "+dbaGigaPath+";rm -f gigaspaces-smart-ods;mv "+dbaGigaPath+"gigaspaces-smart-ods-old "+dbaGigaPath+"gigaspaces-smart-ods","systemctl start gsa"]
    for cmd in cmdList:
        #print("Executing "+str(cmd)+" : "+str(host))
        logger.info("Getting status.. odsxgs :"+str(cmd))
        user = 'root'
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
            if (output == 0):
                verboseHandle.printConsoleInfo("Server rollback successfully on "+str(host))
            else:
                verboseHandle.printConsoleError("Server not able to rollback on "+str(host))


if __name__ == '__main__':
    logger.info("Menu -> Security ->servers - manager - upgrade - manual ")
    verboseHandle.printConsoleWarning('Menu -> Servers -> Manager -> Rollback')
    username = ""
    password = ""
    appId=""
    safeId=""
    objectId=""
    appId = str(readValuefromAppConfig("app.space.security.appId")).replace('"','')
    safeId = str(readValuefromAppConfig("app.space.security.safeId")).replace('"','')
    objectId = str(readValuefromAppConfig("app.space.security.objectId")).replace('"','')
    logger.info("appId : "+appId+" safeID : "+safeId+" objectID : "+objectId)
    args = []
    menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
    args.append(sys.argv[0])

    managerDict = config_get_manager_listWithStatus()
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    hostsConfig = ''
    hostsConfig = getManagerHostFromEnv()
    global inputChoice
    inputChoice = str(userInputWithEscWrapper(Fore.YELLOW+"[1] For individual\n[Enter] For all. \n[99] For exit. :"+Fore.RESET))
    if inputChoice=='99':
        quit(0)
    if inputChoice=='1':
        confirm = str(userInputWrapper(Fore.YELLOW + "Are you sure want to continue gs manager upgradation rollback? [yes (y)] / [no (n)] : " + Fore.RESET))
        if confirm == 'yes' or confirm == 'y':
            inputHostNuber = str(userInputWrapper(Fore.YELLOW+"Enter host number to rollback. :"+Fore.RESET))
            host = managerDict.get(int(inputHostNuber))
            host = os.getenv(host.ip)
            proceedForRollback(host)
    if inputChoice=='':
     try:
         confirm = str(userInputWrapper(Fore.YELLOW + "Are you sure want to continue gs manager upgradation rollback? [yes (y)] / [no (n)] : " + Fore.RESET))
         if confirm == 'yes' or confirm == 'y':
            for host in hostsConfig.split(','):
                proceedForRollback(host)
     except Exception as e:
        handleException(e)
        logger.error("Invalid arguement " + str(e))
        verboseHandle.printConsoleError("Invalid argument" + str(e))
