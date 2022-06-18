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

def getGrafanaHostFromEnv():
    logger.info("getManagerHostFromEnv()")
    hosts = ''
    grafanaNodes = config_get_grafana_node()
    for node in grafanaNodes:
        hosts+=str(os.getenv(str(node.ip)))+','
    hosts=hosts[:-1]
    return hosts

def installUserAndTargetDirectory():
    logger.info("installUserAndTargetDirectory():")
    try:
        global user
        global hostList
        '''
        host = str(input(Fore.YELLOW+"Enter host to install Grafana: "+Fore.RESET))
        while(len(str(host))==0):
            host = str(input(Fore.YELLOW+"Enter host to install Grafana: "+Fore.RESET))
        logger.info("Enter host to install Grafana: "+str(host))
        user = str(input(Fore.YELLOW+"Enter user to connect Grafana servers [root]:"+Fore.RESET))
        if(len(str(user))==0):
        '''
        user="root"
        hostList = getGrafanaHostFromEnv()
        verboseHandle.printConsoleInfo("Garafana server will be installed on hosts : "+str(hostList))
        logger.info(" user: "+str(user))

    except Exception as e:
        handleException(e)
    logger.info("installUserAndTargetDirectory(): end")

def buildUploadInstallTarToServer():
    logger.info("buildUploadInstallTarToServer(): start")
    try:
        cmd = 'tar -cvf install/install.tar install' # Creating .tar file on Pivot machine
        with Spinner():
            status = os.system(cmd)
            logger.info("Creating tar file status : "+str(status))
        for host in hostList.split(','):
            with Spinner():
                logger.info("hostip ::"+str(host)+" user :"+str(user))
                scp_upload(host, user, 'install/install.tar', '')
    except Exception as e:
        handleException(e)
    logger.info("buildUploadInstallTarToServer(): end")

def executeCommandForInstall():
    logger.info("executeCommandForInstall(): start")
    try:
        commandToExecute="scripts/servers_grafana_install.sh"
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))#str(readValuefromAppConfig("app.setup.sourceInstaller"))
        additionalParam=sourceInstallerDirectory
        for host in hostList.split(','):
            logger.info("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user)+" sourceInstaller:"+sourceInstallerDirectory)
            with Spinner():
                outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
                verboseHandle.printConsoleInfo("Grafana has been installed on host :"+str(host))
    except Exception as e:
        handleException(e)
    logger.info("executeCommandForInstall(): end")

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> Grafana -> Install')
    try:
        installUserAndTargetDirectory()
        confirmInstall = str(input(Fore.YELLOW+"Are you sure want to install Grafana servers (y/n) [y]: "+Fore.RESET))
        if(len(str(confirmInstall))==0):
            confirmInstall='y'
        if(confirmInstall=='y'):
            buildUploadInstallTarToServer()
            executeCommandForInstall()
    except Exception as e:
        handleException(e)