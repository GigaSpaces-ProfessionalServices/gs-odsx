#!/usr/bin/env python3

import os
import platform
from os import path
from colorama import Fore
from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_ssh import connectExecuteSSH
from utils.ods_scp import scp_upload
from utils.ods_cluster_config import config_get_grafana_node
from utils.ods_app_config import set_value_in_property_file, readValuefromAppConfig
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

def rpmExitsOrNot():
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    rpmPath=sourceInstallerDirectory+"/kapacitor/"
    rpmFile = [f for f in os.listdir(str(rpmPath)+"/") if f.endswith('.rpm')]
    files = [i for i in rpmFile if i.lower().startswith(("jq","kapacitor"))]
    if(len(files) == 2 ):
        return "Yes"
    else:
        return "No"

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
        rpmStatus = rpmExitsOrNot()
        if(rpmStatus == "Yes"):
            if(len(str(confirmInstall))==0):
                confirmInstall='y'
                if(confirmInstall=='y'):
                    #buildUploadInstallTarToServer()
                    executeCommandForInstall()
        else:
            verboseHandle.printConsoleError(" jq or kapacitor rpm File not exists")
    except Exception as e:
        handleException(e)