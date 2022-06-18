#!/usr/bin/env python3

import os, time
from colorama import Fore
from scripts.logManager import LogManager
import requests, json, math
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_app_config import readValuefromAppConfig, set_value_in_property_file, getYamlFilePathInsideFolder
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_print_tabular_data import printTabular
from scripts.spinner import Spinner
from utils.ods_ssh import executeRemoteCommandAndGetOutput, connectExecuteSSH
from utils.ods_scp import scp_upload
import logging

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


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


def proceedForNodeConfiguration(flag,nodes,targetDir):
    logger.info("proceedForNodeConfiguration() ")
    for node in nodes:
        host = node.ip;
        verboseHandle.printConsoleInfo("Processing configuration for host :"+host)
        logger.info("Processing configuration for host :"+host)
        commandToExecute = "scripts/logs_enablecef.sh"
        additionalParam = flag+' '+targetDir

        logger.info("Additinal Param:" + additionalParam + " cmdToExec:" + commandToExecute + " Host:" + str(host) )
        with Spinner():
            outputShFile = connectExecuteSSH(host, 'root', commandToExecute, additionalParam)
            print(outputShFile)
            logger.info("outputShFile kafka : " + str(outputShFile))

def proceedForInputParam(configXapLogLocation):
    configXapLogLocation = str(readValuefromAppConfig("app.manager.cefXapLogging.target.file"))
    verboseHandle.printConsoleInfo("xap_logging.properties location ["+configXapLogLocation+"]")
    confirmManagerInstall = str(input(Fore.YELLOW+"Are you sure want to disable CEF logs for manager servers ? (y/n) [y]: "+Fore.RESET))
    if(len(str(confirmManagerInstall))==0):
        confirmManagerInstall='y'
    if(confirmManagerInstall=='y'):
        managerNodes = config_get_manager_node()
        proceedForNodeConfiguration("disable",managerNodes,configXapLogLocation)
    confirmManagerInstall = str(input(Fore.YELLOW+"Are you sure want to disable CEF logs for space servers ? (y/n) [y]: "+Fore.RESET))
    if(len(str(confirmManagerInstall))==0):
        confirmManagerInstall='y'
    if(confirmManagerInstall=='y'):
        spaceNodes = config_get_space_hosts()
        proceedForNodeConfiguration("disable",spaceNodes,configXapLogLocation)

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Logs -> Disable CEF')
    try:
        configXapLogLocation = str(getYamlFilePathInsideFolder(".gs.config.log.xap_logging")).replace('[','').replace(']','')
        proceedForInputParam(configXapLogLocation)
    except Exception as e:
        logger.error("Exception in Logs -> Disable CEF : "+str(e))
        verboseHandle.printConsoleError("Exception in Logs -> Disable CEF : "+str(e))
        handleException(e)