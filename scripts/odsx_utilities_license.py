#!/usr/bin/env python3
import os

from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_servers_space_install import getSpaceHostFromEnv
from utils.ods_app_config import getYamlFilePathInsideFolder, readValueByConfigObj
from utils.ods_cluster_config import getManagerHostFromEnv, config_get_space_hosts, config_get_manager_node
from utils.ods_ssh import executeRemoteCommandAndGetOutputValuePython36
from utils.odsx_keypress import userInputWrapper

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
    managerHosts = getManagerHostFromEnv()
    spaceHosts = getSpaceHostFromEnv()
    sourceGSLicense = str(getYamlFilePathInsideFolder(".gs.config.license.gslicense"))
    dbaGigaDir=str(readValueByConfigObj("app.giga.path"))
    targetGSLicense = dbaGigaDir+"/gigaspaces-smart-ods/"
    verboseHandle.printConsoleWarning("-------------------Summary-----------------")
    verboseHandle.printConsoleInfo("License source file :"+str(sourceGSLicense))
    verboseHandle.printConsoleInfo("License target : "+str(targetGSLicense))
    verboseHandle.printConsoleInfo("Manager hosts : "+managerHosts)
    verboseHandle.printConsoleInfo("Space hosts : "+spaceHosts)
    #licenseConfig='"\\"{}\\""'.format(licenseConfig)
    confirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to proceed ? (y/n) [y] : "+Fore.RESET))
    if confirm=='y' or confirm=='':
        #commandToExecute = "sed -i '/export GS_LICENSE*/c\export GS_LICENSE=\""+licenseConfig+"\"'  /dbagiga/gigaspaces-smart-ods/bin/setenv-overrides.sh"

        commandToExecute = "cp "+sourceGSLicense+" "+targetGSLicense
        logger.info("commandToExecute:"+commandToExecute)

        for host in managerHosts.split(','):
            outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
            verboseHandle.printConsoleInfo("License configured for host:"+host)

        for host in spaceHosts.split(','):
            outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
            verboseHandle.printConsoleInfo("License configured for host:"+host)

if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Utilities -> License")
    logger.info("Utilities - License")
    try:
        configureLicenseManagerAndSpace()
    except Exception as e:
        handleException(e)