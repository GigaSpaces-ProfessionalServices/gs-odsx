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
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig, getYamlFilePathInsideFolder
from utils.ods_cluster_config import config_get_manager_node, isInstalledAndGetVersionOldGS
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
    #global username
    #global password
    managerNodes = config_get_manager_node()
    for node in managerNodes:
        #username = str(getUsernameByHost(str(os.getenv(node.ip)),appId,safeId,objectId))
        #password = str(getPasswordByHost(str(os.getenv(node.ip)),appId,safeId,objectId))
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
            managerInfoResponse = requests.get(('http://' + str(os.getenv(node.ip)) + ':8090/v2/info'),
                                               headers={'Accept': 'application/json'})
            output = managerInfoResponse.content.decode("utf-8")
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

def validateServer(host):
    status = getSpaceServerStatus(host)
    #print(status)
    version = getGSVersion(host)
    if status == "ON" and version != "NA":
        return True

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

def proceedForRollback(host):
    logger.info("proceedForRollback")
    upgradedManagerDict.update({host:"N/A"})
    user = 'root'
    isConnectUsingPem = readValuefromAppConfig("cluster.usingPemFile")
    pemFileName = readValuefromAppConfig("cluster.pemFile")
    ssh = ""

    cefLoggingJarInput = str(getYamlFilePathInsideFolder(".security.jars.cef.cefjar")).replace('[','').replace(']','')
    cefLoggingJarInputTarget = str(readValuefromAppConfig("app.manager.cefLogging.jar.target")).replace('[','').replace(']','')
    springLdapCoreJarInput = str(getYamlFilePathInsideFolder(".security.jars.springldapcore")).replace('[','').replace(']','')
    springLdapJarInput = str(getYamlFilePathInsideFolder(".security.jars.springldapjar")).replace('[','').replace(']','')
    vaultSupportJarInput = str(getYamlFilePathInsideFolder(".security.jars.vaultsupportjar")).replace('[','').replace(']','')
    javaPasswordJarInput = str(getYamlFilePathInsideFolder(".security.jars.javapassword")).replace('[','').replace(']','')

    springTargetJarInput = str(readValuefromAppConfig("app.manager.security.spring.jar.target")).replace('[','').replace(']','')

    additionalParam=cefLoggingJarInput+" "+cefLoggingJarInputTarget+" "+springLdapCoreJarInput+" "+springLdapJarInput+" "+vaultSupportJarInput+" "+javaPasswordJarInput+" "+springTargetJarInput

    if isConnectUsingPem == 'True':
        ssh = ''.join(
            ['ssh', ' -i ', pemFileName, ' ', user, '@', str(host), ' '])
    else:
        ssh = ''.join(['ssh', ' ', str(host), ' '])
    cmd = ssh + 'bash' + ' -s ' + additionalParam + ' < scripts/servers_manager_upgrade_rollback.sh'
    with Spinner():
        os.system(cmd)
        pass
    if validateServer(host)==True:
        verboseHandle.printConsoleInfo("Validation successful manager is started " + host)
    else:
        verboseHandle.printConsoleError("Validation failed, manager is not started " + host)
    config_get_manager_listWithStatus()

if __name__ == '__main__':
    logger.info("Menu -> Security ->servers - manager - rollback ")
    verboseHandle.printConsoleWarning('Menu -> Servers -> Manager ->  Rollback')
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
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    hostsConfig = ''
    hostsConfig = getManagerHostFromEnv()
    global inputChoice
    inputChoice = str(userInputWithEscWrapper(Fore.YELLOW+"[1] For individual\n[Enter] For all. \n[99] For exit. :"+Fore.RESET))
    if inputChoice=='99':
        quit(0)
    if inputChoice=='1':
        inputHostNuber = str(userInputWrapper(Fore.YELLOW+"Enter host number to rollback. :"+Fore.RESET))
        host = managerDict.get(int(inputHostNuber))
        host = os.getenv(host.ip)
        confirm = str(userInputWrapper(Fore.YELLOW + "Are you sure want to continue gs manager upgradation rollback? [yes (y)] / [no (n)] : " + Fore.RESET))
        if confirm == 'yes' or confirm == 'y':
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
