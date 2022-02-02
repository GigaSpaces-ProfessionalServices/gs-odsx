#!/usr/bin/env python3

import os, time, subprocess
from colorama import Fore
from scripts.logManager import LogManager
import requests, json, math
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_app_config import readValuefromAppConfig, set_value_in_property_file
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


def proceedForNodeConfiguration(flag,nodes,sourceFile,targetFile):
    logger.info("proceedForNodeConfiguration() ")
    for node in nodes:
        host = node.ip;
        verboseHandle.printConsoleInfo("Processing configuration for host :"+host)
        logger.info("Processing configuration for host :"+host)
        commandToExecute = "scripts/logs_enablecef.sh"
        additionalParam = flag+' '+targetFile

        logger.info("Additinal Param:" + additionalParam + " cmdToExec:" + commandToExecute + " Host:" + str(host) )
        with Spinner():
            outputShFile = connectExecuteSSH(host, 'root', commandToExecute, additionalParam)
            #print(outputShFile)
            logger.info("outputShFile logs enable CEF : " + str(outputShFile))
            scp_upload(host,'root',sourceCefLogInput,targetCefLogInput)
            #scp_upload(host,'root',cefLoggingJarInput,cefLoggingJarInputTarget)

def proceedForInputParam(configXapLogLocation):
    logger.info("proceedForInputParam() ")
    #configXapLogLocation = os.path.dirname(configXapLogLocation)
    #verboseHandle.printConsoleInfo("xap_logging.properties location ["+configXapLogLocation+"]")
    global sourceCefLogInput
    sourceCefLogConfig = str(readValuefromAppConfig("app.manager.cefXapLogging.source.file"))
    sourceCefLogInput = str(input(Fore.YELLOW+"Enter source CEF configured xap_logging.properties file ["+sourceCefLogConfig+"] :"))
    if(len(str(sourceCefLogInput))==0):
        sourceCefLogInput = sourceCefLogConfig
    #check source file exist
    global targetCefLogInput
    if(os.path.isfile(sourceCefLogInput)):
        targetCefLogConfig = str(readValuefromAppConfig("app.manager.cefXapLogging.target.file"))
        targetCefLogInput = str(input(Fore.YELLOW+"Enter target CEF configured xap_logging.properties file ["+targetCefLogConfig+"] : "))
        if(len(str(targetCefLogInput))==0):
            targetCefLogInput=targetCefLogConfig
    else:
        verboseHandle.printConsoleInfo("Source file does not exist")
        logger.info("Source file does not exist")
    '''
    global cefLoggingJarInput
    global cefLoggingJarInputTarget
    cefLoggingJarConfig = str(readValuefromAppConfig("app.manager.cefLogging.jar")).replace('[','').replace(']','')
    cefLoggingJarInput = str(input(Fore.YELLOW+"Enter source path of CEFLogger-1.0-SNAPSHOT.jar ["+cefLoggingJarConfig+"] : "+Fore.RESET))
    if(len(str(cefLoggingJarInput))==0):
        cefLoggingJarInput=cefLoggingJarConfig
    if(os.path.isfile(cefLoggingJarInput)):
        cefLoggingJarConfigTarget = str(readValuefromAppConfig("app.manager.cefLogging.jar.target")).replace('[','').replace(']','')
        cefLoggingJarInputTarget = str(input(Fore.YELLOW+"Enter target path of CEFLogger-1.0-SNAPSHOT.jar ["+cefLoggingJarConfigTarget+"] : "+Fore.RESET))
        if(len(str(cefLoggingJarInputTarget))==0):
            cefLoggingJarInputTarget=cefLoggingJarConfigTarget
    else:
        verboseHandle.printConsoleInfo("Source file does not exist"+str(os.path.isfile(cefLoggingJarInput)))
        logger.info("Source file does not exist")
    '''
    confirmManagerInstall = str(input(Fore.YELLOW+"Are you sure want to enable CEF logs for manager servers ? (y/n) [y]: "+Fore.RESET))
    if(len(str(confirmManagerInstall))==0):
        confirmManagerInstall='y'
    if(confirmManagerInstall=='y'):
        managerNodes = config_get_manager_node()
        proceedForNodeConfiguration("enable",managerNodes,sourceCefLogInput,targetCefLogInput)
    confirmManagerInstall = str(input(Fore.YELLOW+"Are you sure want to enable CEF logs for space servers ? (y/n) [y]: "+Fore.RESET))
    if(len(str(confirmManagerInstall))==0):
        confirmManagerInstall='y'
    if(confirmManagerInstall=='y'):
        spaceNodes = config_get_space_hosts()
        proceedForNodeConfiguration("enable",spaceNodes,sourceCefLogInput,targetCefLogInput)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Logs -> Enable CEF')
    try:
        configXapLogLocation = str(readValuefromAppConfig("app.manager.gsLogsConfigFile"))
        proceedForInputParam(configXapLogLocation)
    except Exception as e:
        logger.error("Exception in Logs -> Enable CEF : "+str(e))
        verboseHandle.printConsoleError("Exception in Logs -> Enable CEF : "+str(e))
        handleException(e)