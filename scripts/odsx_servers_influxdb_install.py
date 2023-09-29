#!/usr/bin/env python3

import os

from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_influxdb_node
from utils.ods_scp import scp_upload
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

def getInfluxdbHostFromEnv():
    logger.info("getinfluxdbHostFromEnv()")
    hosts = ''
    influxdbNodes = config_get_influxdb_node()
    for node in influxdbNodes:
        hosts+=str(os.getenv(str(node.ip)))+','
    hosts=hosts[:-1]
    return hosts

def installUserAndTargetDirectory():
    logger.info("installUserAndTargetDirectory():")
    try:
        global user
        global host
        global targetDirectory
        host = getInfluxdbHostFromEnv()
        '''
        = str(userInputWrapper(Fore.YELLOW+"Enter host to install Influxdb: "+Fore.RESET))
        while(len(str(host))==0):
            host = str(userInputWrapper(Fore.YELLOW+"Enter host to install Influxdb: "+Fore.RESET))
        logger.info("Enter host to install Grafana: "+str(host))
        user = str(userInputWrapper(Fore.YELLOW+"Enter user to connect Influxdb servers [root]:"+Fore.RESET))
        if(len(str(user))==0):
        '''
        user="root"
        logger.info(" user: "+str(user))
        targetDirectory = str(userInputWrapper(Fore.YELLOW+"Enter data directory Influxdb server [/dbagigainfluxdata]:"+Fore.RESET))
        if(len(targetDirectory)==0):
            targetDirectory='/dbagigainfluxdata'
        logger.info("targetDirectory : "+str(targetDirectory))

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
        with Spinner():
            logger.info("hostip ::"+str(host)+" user :"+str(user))
            scp_upload(host, user, 'install/install.tar', '')
    except Exception as e:
        handleException(e)
    logger.info("buildUploadInstallTarToServer(): end")

def executeCommandForInstall():
    logger.info("executeCommandForInstall(): start")
    try:
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))#str(readValuefromAppConfig("app.setup.sourceInstaller"))
        commandToExecute="scripts/servers_influxdb_install.sh"
        additionalParam=targetDirectory+' '+sourceInstallerDirectory
        logger.info("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user)+"sourceInstallerDire :"+sourceInstallerDirectory)
        with Spinner():
            outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
            #config_add_influxdb_node(host,host,'influxdb')
            #set_value_in_property_file('app.influxdb.hosts',host)
            verboseHandle.printConsoleInfo("Influxdb has been installed on host :"+str(host))
    except Exception as e:
        handleException(e)
    logger.info("executeCommandForInstall(): end")

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> Influxdb -> Install')
    try:
        installUserAndTargetDirectory()
        confirmInstall = str(userInputWrapper(Fore.YELLOW+"Are you sure want to install Influxdb servers on host "+str(host)+" (y/n) [y]: "+Fore.RESET))
        if(len(str(confirmInstall))==0):
            confirmInstall='y'
        if(confirmInstall=='y'):
            buildUploadInstallTarToServer()
            executeCommandForInstall()
    except Exception as e:
        handleException(e)