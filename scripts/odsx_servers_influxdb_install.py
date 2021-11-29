#!/usr/bin/env python3

import os
import platform
from os import path
from colorama import Fore
from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_ssh import connectExecuteSSH
from utils.ods_scp import scp_upload
from utils.ods_cluster_config import config_add_influxdb_node
from utils.ods_app_config import set_value_in_property_file

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
        global targetDirectory
        host = str(input(Fore.YELLOW+"Enter host to install Influxdb: "+Fore.RESET))
        while(len(str(host))==0):
            host = str(input(Fore.YELLOW+"Enter host to install Influxdb: "+Fore.RESET))
        logger.info("Enter host to install Grafana: "+str(host))
        user = str(input(Fore.YELLOW+"Enter user to connect Influxdb servers [root]:"+Fore.RESET))
        if(len(str(user))==0):
            user="root"
        logger.info(" user: "+str(user))
        targetDirectory = str(input(Fore.YELLOW+"Enter data directory Influxdb server [/dbagigainflaxdata]:"+Fore.RESET))
        if(len(targetDirectory)==0):
            targetDirectory='/dbagigainflaxdata'
        logger.info("targetDirectory : "+str(targetDirectory))

    except Exception as e:
        logger.error("Exception in Influxdb -> Install : installUserAndTargetDirectory() : "+str(e))
        verboseHandle.printConsoleError("Exception in Influxdb -> Install : installUserAndTargetDirectory() : "+str(e))
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
        logger.error("Exception in Influxdb -> Install : buildUploadInstallTarToServer() : "+str(e))
        verboseHandle.printConsoleError("Exception in Influxdb -> Install : buildUploadInstallTarToServer() : "+str(e))
    logger.info("buildUploadInstallTarToServer(): end")

def executeCommandForInstall():
    logger.info("executeCommandForInstall(): start")
    try:
        commandToExecute="scripts/servers_influxdb_install.sh"
        additionalParam=targetDirectory
        logger.info("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user))
        with Spinner():
            outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
            config_add_influxdb_node(host,host,'influxdb','true')
            set_value_in_property_file('app.influxdb.hosts',host)
            verboseHandle.printConsoleInfo("Node has been added :"+str(host))
    except Exception as e:
        logger.error("Exception in Influxdb -> Install : executeCommandForInstall() : "+str(e))
        verboseHandle.printConsoleError("Exception in Influxdb -> Install : executeCommandForInstall() : "+str(e))
    logger.info("executeCommandForInstall(): end")

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> Influxdb -> Install')
    try:
        installUserAndTargetDirectory()
        confirmInstall = str(input(Fore.YELLOW+"Are you sure want to install Influxdb servers (y/n) [y]: "+Fore.RESET))
        if(len(str(confirmInstall))==0):
            confirmInstall='y'
        if(confirmInstall=='y'):
            buildUploadInstallTarToServer()
            executeCommandForInstall()
    except Exception as e:
        logger.error("Exception in Influxdb -> Install : "+str(e))
        verboseHandle.printConsoleError("Exception in Influxdb -> Install : "+str(e))