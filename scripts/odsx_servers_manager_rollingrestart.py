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
from utils.ods_cluster_config import config_get_manager_node, isInstalledAndGetVersionOldGS, \
    config_get_manager_listWithStatus
from utils.ods_scp import scp_upload
from utils.ods_ssh import executeRemoteCommandAndGetOutputValuePython36, executeRemoteCommandAndGetOutputPython36
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_print_tabular_data import printTabular
from utils.odsx_db2feeder_utilities import getPasswordByHost, getUsernameByHost
from requests.auth import HTTPBasicAuth

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



def proceedForRollingRestart(host):
    logger.info("proceedForRollingRestart")
    cmdList = ["systemctl stop gsa.service;sleep 20","systemctl daemon-reload","systemctl start gsa.service;sleep 30"]
    user='root'
    infoDict = {}
    infoDict.update({1:"Stopping service..."})
    infoDict.update({2:"Reloading service..."})
    infoDict.update({3:"Starting service..."})
    counter=1
    with Spinner():
        for cmd in cmdList:
            verboseHandle.printConsoleInfo(infoDict.get(counter))
            output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
            counter=counter+1
        if validateServer(host)==True:
            verboseHandle.printConsoleInfo("Validation successful manager is started " + host)
        else:
            verboseHandle.printConsoleError("Validation failed, manager is not started " + host)
    pass


if __name__ == '__main__':
    logger.info("Menu -> Security ->servers - manager - rollback ")
    verboseHandle.printConsoleWarning('Menu -> Servers -> Manager ->  Rolling restart')
    args = []
    menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
    args.append(sys.argv[0])
    upgradedManagerDict = {}

    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    hostsConfig = ''
    hostsConfig = getManagerHostFromEnv()
    try:
     managerDict = config_get_manager_listWithStatus()
     inputChoice = str(input(Fore.GREEN+"[1] For individual\n[Enter] For all. :"+Fore.RESET))
     if inputChoice=='99':
         quit(0)
     if inputChoice=='1':
         hostNumber = str(input(Fore.YELLOW+"Enter host number for rolling restart: "))
         host = managerDict.get(int(hostNumber))
         confirm = str(input(Fore.YELLOW + "Are you sure want to continue gs manager rolling restart? [yes (y)] / [no (n)] : " + Fore.RESET))
         if confirm == 'yes' or confirm == 'y':
            proceedForRollingRestart(os.getenv(host.ip))
         #proceedForRollingRestart(host)
     if inputChoice=="":
        confirm = str(input(Fore.YELLOW + "Are you sure want to continue gs manager rolling restart? [yes (y)] / [no (n)] : " + Fore.RESET))
        if confirm == 'yes' or confirm == 'y':
            for host in hostsConfig.split(','):
                proceedForRollingRestart(host)
    except Exception as e:
        handleException(e)

