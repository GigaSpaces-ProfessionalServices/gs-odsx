#!/usr/bin/env python3

import os

from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_ssh import connectExecuteSSH
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

def installUserAndTargetDirectory():
    logger.info("installUserAndTargetDirectory():")
    try:
        global user
        global hostList
        global port
        port = "9092"
        user="root"
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))#str(readValuefromAppConfig("app.setup.sourceInstaller"))
        hostList = os.getenv("pivot1")
        packageName=""
        dir_list=""
        sourcePath= sourceInstallerDirectory+"/kapacitor/"
        packageName = [f for f in os.listdir(sourcePath) if f.endswith('.rpm')]
        verboseHandle.printConsoleWarning("------------------------summary------------------------------")
        port = str(readValuefromAppConfig("app.kapacitor.port"))
        verboseHandle.printConsoleInfo("Kapacitor will be installed on hosts : "+str(hostList))
        verboseHandle.printConsoleInfo("Kapacitor will be installed on port : "+str(port))
        verboseHandle.printConsoleInfo("Kapacitor configuration file : "+sourceInstallerDirectory+"/kapacitor/config/kapacitor.conf.template")
        verboseHandle.printConsoleInfo("Kapacitor installer : "+str(packageName))
        verboseHandle.printConsoleWarning("-------------------------------------------------------------")
        logger.info(" user: "+str(user))

    except Exception as e:
        handleException(e)
    logger.info("installUserAndTargetDirectory(): end")

def executeCommandForInstall():
    logger.info("executeCommandForInstall(): start")
    try:
        commandToExecute="scripts/monitors_alerts_services_kapacitor_install.sh"
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))#str(readValuefromAppConfig("app.setup.sourceInstaller"))
        additionalParam=sourceInstallerDirectory+' '+hostList+' '+port
        for host in hostList.split(','):
            logger.info("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user)+" sourceInstaller:"+sourceInstallerDirectory)
            with Spinner():
                outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
                verboseHandle.printConsoleInfo("kapacitor has been installed on host :"+str(host))
    except Exception as e:
        handleException(e)
    logger.info("executeCommandForInstall(): end")

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Monitors -> Alerts -> Services -> Kapacitor -> Install')
    try:
        installUserAndTargetDirectory()
        confirmInstall = str(userInputWrapper(Fore.YELLOW+"Are you sure want to install Kapacitor (y/n) [y]: "+Fore.RESET))
        if(len(str(confirmInstall))==0):
            confirmInstall='y'
        if(confirmInstall=='y'):
            #buildUploadInstallTarToServer()
            executeCommandForInstall()
    except Exception as e:
        handleException(e)