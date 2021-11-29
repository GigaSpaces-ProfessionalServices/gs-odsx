#!/usr/bin/env python3

import os
import platform
from os import path
from colorama import Fore
from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_ssh import connectExecuteSSH
from utils.ods_cluster_config import config_remove_grafana_byNameIP, config_get_grafana_list
from utils.ods_app_config import set_value_in_property_file

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
nbConfig = {}

class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR

def getGrafanaServerHostList():
    nodeList = config_get_grafana_list()
    nodes=""
    for node in nodeList:
        #if(str(node.role).casefold() == 'server'):
        if(len(nodes)==0):
            nodes = node.ip
        else:
            nodes = nodes+','+node.ip
    return nodes

def removeInputUserAndHost():
    logger.info("removeInputUserAndHost():")
    try:
        global user
        global host
        user = str(input(Fore.YELLOW+"Enter user to connect to Grafana [root]:"+Fore.RESET))
        if(len(str(user))==0):
            user="root"
        logger.info(" user: "+str(user))

    except Exception as e:
        logger.error("Exception in Grafana -> Remove : removeInputUserAndHost() : "+str(e))
        verboseHandle.printConsoleError("Exception in Grafana -> Remove : removeInputUserAndHost() : "+str(e))
    logger.info("removeInputUserAndHost(): end")

def executeCommandForUnInstall():
    logger.info("executeCommandForUnInstall(): start")
    try:
        nodes = getGrafanaServerHostList()
        if(len(nodes)>0):
            confirmUninstall = str(input(Fore.YELLOW+"Are you sure want to remove Grafana servers ["+nodes+"] (y/n) [y]: "+Fore.RESET))
            if(len(str(confirmUninstall))==0):
                confirmUninstall='y'
            logger.info("confirmUninstall :"+str(confirmUninstall))
            if(confirmUninstall=='y'):
                commandToExecute="scripts/servers_grafana_remove.sh"
                additionalParam=""
                logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(nodes)+" User:"+str(user))
                with Spinner():
                    outputShFile= connectExecuteSSH(nodes, user,commandToExecute,additionalParam)
                    config_remove_grafana_byNameIP(nodes,nodes)
                    set_value_in_property_file('app.grafana.hosts','')
                    verboseHandle.printConsoleInfo("Node has been removed :"+str(nodes))
        else:
            logger.info("No server details found.")
            verboseHandle.printConsoleInfo("No server details found.")
    except Exception as e:
        logger.error("Exception in Grafana -> remove : executeCommandForUnInstall() : "+str(e))
        verboseHandle.printConsoleError("Exception in Grafana -> Remove : executeCommandForUnInstall() : "+str(e))
    logger.info("executeCommandForUnInstall(): end")

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> Grafana -> Remove')
    try:
        removeInputUserAndHost()
        executeCommandForUnInstall()
    except Exception as e:
        logger.error("Exception in Grafana -> Remove : "+str(e))
        verboseHandle.printConsoleError("Exception in Grafana -> Remove : "+str(e))