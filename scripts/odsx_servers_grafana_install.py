#!/usr/bin/env python3

import os
import platform
from os import path
from colorama import Fore
from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_ssh import connectExecuteSSH
from utils.ods_scp import scp_upload
from utils.ods_cluster_config import config_add_grafana_node
from utils.ods_app_config import set_value_in_property_file, readValuefromAppConfig

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR


def installUserAndTargetDirectory():
    logger.info("installUserAndTargetDirectory():")
    try:
        global user
        global host
        host = str(input(Fore.YELLOW+"Enter host to install Grafana: "+Fore.RESET))
        while(len(str(host))==0):
            host = str(input(Fore.YELLOW+"Enter host to install Grafana: "+Fore.RESET))
        logger.info("Enter host to install Grafana: "+str(host))
        user = str(readValuefromAppConfig("app.server.user")).replace('"','')
        userinput = str(input(Fore.YELLOW+"Enter user to connect Grafana servers ["+user+"]:"+Fore.RESET))
        while(len(str(userinput))==0 and len(user)==0):
            userinput = str(input(Fore.YELLOW+"Enter user to connect Grafana servers ["+user+"]:"+Fore.RESET))
        user=userinput
        logger.info(" user: "+str(user))

    except Exception as e:
        logger.error("Exception in Grafana -> Install : installUserAndTargetDirectory() : "+str(e))
        verboseHandle.printConsoleError("Exception in Grafana -> Install : installUserAndTargetDirectory() : "+str(e))
    logger.info("installUserAndTargetDirectory(): end")

def buildUploadInstallTarToServer():
    logger.info("buildUploadInstallTarToServer(): start")
    try:
        cmd = 'tar -cvf install/install.tar install' # Creating .tar file on Pivot machine
        with Spinner():
            status = os.system(cmd)
            logger.info("Creating tar file status : "+str(status))
        with Spinner():
            logger.info("hostip ::"+str(host)+" user :"+str(user))
            scp_upload(host, user, 'install/install.tar', '')
    except Exception as e:
        logger.error("Exception in Grafana -> Install : buildUploadInstallTarToServer() : "+str(e))
        verboseHandle.printConsoleError("Exception in Grafana -> Install : buildUploadInstallTarToServer() : "+str(e))
    logger.info("buildUploadInstallTarToServer(): end")

def executeCommandForInstall():
    logger.info("executeCommandForInstall(): start")
    try:
        commandToExecute="scripts/servers_grafana_install.sh"
        additionalParam=""
        logger.info("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user))
        with Spinner():
            outputShFile= connectExecuteSSH(host, user,commandToExecute,'')
            config_add_grafana_node(host,host,'grafana','true')
            set_value_in_property_file('app.grafana.hosts',host)
            verboseHandle.printConsoleInfo("Node has been added :"+str(host))
    except Exception as e:
        logger.error("Exception in Grafana -> Install : executeCommandForInstall() : "+str(e))
        verboseHandle.printConsoleError("Exception in Grafana -> Install : executeCommandForInstall() : "+str(e))
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
        logger.error("Exception in Grafana -> Install : "+str(e))
        verboseHandle.printConsoleError("Exception in Grafana -> Install : "+str(e))