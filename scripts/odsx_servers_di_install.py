#!/usr/bin/env python3

import os
import platform
from os import path
from colorama import Fore
from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_ssh import connectExecuteSSH
from utils.ods_scp import scp_upload
from utils.ods_cluster_config import config_add_dataIntegration_node
from utils.ods_app_config import set_value_in_property_file

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

class host_type_dictionary(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

def getDIServerTypeInstall():
    logger.info("getDIServerTypeInstall()")
    serverType = str(input(Fore.YELLOW+"[1] Single\n[2] Cluster\n[99] Exit : "+Fore.RESET))
    while(len(serverType)==0):
        serverType = str(input(Fore.YELLOW+"[1] Single\n[2] Cluster\n[99] Exit : "+Fore.RESET))
    return serverType

def installSingle():
    logger.info("installSingle():")
    try:
        global user
        host = str(input(Fore.YELLOW+"Enter host to install DI: "+Fore.RESET))
        while(len(str(host))==0):
            host = str(input(Fore.YELLOW+"Enter host to install DI: "+Fore.RESET))
        logger.info("Enter host to install Grafana: "+str(host))
        user = str(input(Fore.YELLOW+"Enter user to connect DI servers [root]:"+Fore.RESET))
        if(len(str(user))==0):
            user="root"
        logger.info(" user: "+str(user))

        confirmInstall = str(input(Fore.YELLOW+"Are you sure want to install DI servers (y/n) [y]: "+Fore.RESET))
        if(len(str(confirmInstall))==0):
            confirmInstall='y'
        if(confirmInstall=='y'):
            buildUploadInstallTarToServer(host)
            executeCommandForInstall(host,'SingleNode')

    except Exception as e:
        handleException(e)

def installCluster():
    logger.info("installCluster()")
    global clusterHosts
    global user
    clusterHosts=[]
    masterHost  = str(input(Fore.YELLOW+"Enter Masterhost  :"+Fore.RESET))
    while(len(masterHost)==0):
        masterHost  = str(input(Fore.YELLOW+"Enter Masterhost  :"+Fore.RESET))
    logger.info("masterHost : "+str(masterHost))
    standByHost = str(input(Fore.YELLOW+"Enter StandbyHost :"+Fore.RESET))
    while(len(standByHost)==0):
        standByHost = str(input(Fore.YELLOW+"Enter StandbyHost :"+Fore.RESET))
    logger.info("standByHost : "+str(standByHost))
    witnessHost = str(input(Fore.YELLOW+"Enter WitnessHost :"+Fore.RESET))
    while(len(witnessHost)==0):
        witnessHost = str(input(Fore.YELLOW+"Enter WitnessHost :"+Fore.RESET))
    logger.info("witnessHost :"+str(witnessHost))
    user = str(input(Fore.YELLOW+"Enter user to connect DI servers [root]:"+Fore.RESET))
    if(len(str(user))==0):
        user="root"
    logger.info(" user: "+str(user))

    clusterHosts.append(masterHost)
    clusterHosts.append(standByHost)
    clusterHosts.append(witnessHost)
    host_type_dictionary_obj = host_type_dictionary()
    host_type_dictionary_obj.add(masterHost,'Master')
    host_type_dictionary_obj.add(standByHost,'Standby')
    host_type_dictionary_obj.add(witnessHost,'Witness')
    logger.info("clusterHosts : "+str(clusterHosts))
    logger.info("host_type_dictionary_obj : "+str(host_type_dictionary_obj))
    confirmInstall = str(input(Fore.YELLOW+"Are you sure want to install DI servers on "+str(clusterHosts)+" (y/n) [y]: "+Fore.RESET))
    if(len(str(confirmInstall))==0):
        confirmInstall='y'
    if(confirmInstall=='y'):
        for host in clusterHosts:
            logger.info("proceeding for host : "+str(host))
            buildUploadInstallTarToServer(host)
            executeCommandForInstall(host,host_type_dictionary_obj.get(host))


def buildUploadInstallTarToServer(host):
    logger.info("buildUploadInstallTarToServer(): start host :" +str(host))
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

def executeCommandForInstall(host,type):
    logger.info("executeCommandForInstall(): start host : "+str(host) +" type : "+str(type))
    try:
        commandToExecute="scripts/servers_di_install.sh"
        additionalParam=""
        logger.info("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user))
        with Spinner():
            outputShFile= connectExecuteSSH(host, user,commandToExecute,'')
            config_add_dataIntegration_node(host, host, "dataIntegration", "true", type)
            set_value_in_property_file('app.di.hosts',host)
            verboseHandle.printConsoleInfo("Node has been added :"+str(host))
    except Exception as e:
        logger.error("Exception in Grafana -> Install : executeCommandForInstall() : "+str(e))
        verboseHandle.printConsoleError("Exception in Grafana -> Install : executeCommandForInstall() : "+str(e))
    logger.info("executeCommandForInstall(): end")


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> DI -> Install')
    try:
        diServerType = getDIServerTypeInstall()
        logger.info("diServerInstallType : "+str(diServerType))
        if(diServerType!='99'):
            if(diServerType=='1'):
                installSingle()
            if(diServerType=='2'):
                installCluster()
    except Exception as e:
        handleException(e)