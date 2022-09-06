#!/usr/bin/env python3
import os
from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig, readValueByConfigObj, getYamlFilePathInsideFolder
from utils.ods_ssh import connectExecuteSSH, executeRemoteCommandAndGetOutputValuePython36
from scripts.spinner import Spinner
from colorama import Fore
from scripts.odsx_servers_grafana_stop import getGrafanaServerHostList
from scripts.odsx_servers_influxdb_stop import getInfluxdbServerHostList
from utils.ods_cluster_config import getManagerHostFromEnv, config_get_space_hosts, config_get_manager_node
from scripts.odsx_servers_space_install import getSpaceHostFromEnv

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR

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

def getSpaceHostFromEnv():
    logger.info("getSpaceHostFromEnv()")
    hosts = ''
    spaceNodes = config_get_space_hosts()
    for node in spaceNodes:
        hosts+=str(os.getenv(str(node.ip)))+','
    hosts=hosts[:-1]
    return hosts

def getManagerHostFromEnv():
    logger.info("getManagerHostFromEnv()")
    hosts = ''
    managerNodes = config_get_manager_node()
    for node in managerNodes:
        hosts+=str(os.getenv(str(node.ip)))+','
    hosts=hosts[:-1]
    return hosts

def configureLicenseManagerAndSpace():
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    watchdogHost = str(readValuefromAppConfig("app.iidr.watchdog.host"))
    sourcePath= sourceInstallerDirectory+"/iidr/watchdog/"
    targetPathService=str(readValuefromAppConfig("app.iidr.watchdog.service.target"))
    targetPathScripts=str(readValuefromAppConfig("app.iidr.watchdog.script.target"))
    verboseHandle.printConsoleWarning("-------------------Summary-----------------")
    verboseHandle.printConsoleInfo("1. Source files : "+sourcePath)
    verboseHandle.printConsoleInfo("2. *.service target files : "+targetPathService)
    verboseHandle.printConsoleInfo("3. *.timer target files : "+targetPathService)
    verboseHandle.printConsoleInfo("4. *.sh target files : "+targetPathScripts)
    verboseHandle.printConsoleInfo("5. *.txt target files : "+targetPathScripts)
    #licenseConfig='"\\"{}\\""'.format(licenseConfig)
    confirm = str(input(Fore.YELLOW+"Are you sure want to proceed ? (y/n) [y] : "+Fore.RESET))
    if confirm=='y' or confirm=='':
        commandToExecute = "cp "+sourcePath+"*.service "+targetPathService
        logger.info("commandToExecute:"+commandToExecute)
        outputShFile = executeRemoteCommandAndGetOutputValuePython36(watchdogHost, 'root', commandToExecute)
        verboseHandle.printConsoleInfo("Files *.service copied for for host:"+watchdogHost)

        commandToExecute = "cp "+sourcePath+"*.timer "+targetPathService
        logger.info("commandToExecute:"+commandToExecute)
        outputShFile = executeRemoteCommandAndGetOutputValuePython36(watchdogHost, 'root', commandToExecute)
        verboseHandle.printConsoleInfo("Files *.timer copied for for host:"+watchdogHost)

        commandToExecute = "cp "+sourcePath+"*.sh "+targetPathService
        logger.info("commandToExecute:"+commandToExecute)
        outputShFile = executeRemoteCommandAndGetOutputValuePython36(watchdogHost, 'root', commandToExecute)
        verboseHandle.printConsoleInfo("Files *.sh copied for for host:"+watchdogHost)

        commandToExecute = "cp "+sourcePath+"*.txt "+targetPathService
        logger.info("commandToExecute:"+commandToExecute)
        outputShFile = executeRemoteCommandAndGetOutputValuePython36(watchdogHost, 'root', commandToExecute)
        verboseHandle.printConsoleInfo("Files *.txt copied for for host:"+watchdogHost)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Utilities -> Watchdog")
    logger.info("Utilities - Watchdog")
    try:
        configureLicenseManagerAndSpace()
    except Exception as e:
        handleException(e)