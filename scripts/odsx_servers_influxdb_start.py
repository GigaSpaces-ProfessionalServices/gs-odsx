#!/usr/bin/env python3

import os
import platform
from os import path
from colorama import Fore
from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_ssh import connectExecuteSSH
from utils.ods_cluster_config import config_get_influxdb_node

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
nbConfig = {}

class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR

def getInfluxdbServerHostList():
    nodeList = config_get_influxdb_node()
    nodes=""
    for node in nodeList:
        #if(str(node.role).casefold() == 'server'):
        if(len(nodes)==0):
            nodes = node.ip
        else:
            nodes = nodes+','+node.ip
    return nodes

def startInputUserAndHost():
    logger.info("startInputUserAndHost():")
    try:
        global user
        global host
        user = str(input(Fore.YELLOW+"Enter user to connect to Influxdb [root]:"+Fore.RESET))
        if(len(str(user))==0):
            user="root"
        logger.info(" user: "+str(user))

    except Exception as e:
        logger.error("Exception in Influxdb -> Start : startInputUserAndHost() : "+str(e))
        verboseHandle.printConsoleError("Exception in Influxdb -> Start : startInputUserAndHost() : "+str(e))
    logger.info("startInputUserAndHost(): end")

def executeCommandForStart():
    logger.info("executeCommandForStart(): start")
    try:
        nodes = getInfluxdbServerHostList()
        if(len(nodes)>0):
            confirm = str(input(Fore.YELLOW+"Are you sure want to start Influxdb servers ["+nodes+"] (y/n) [y]: "+Fore.RESET))
            if(len(str(confirm))==0):
                confirm='y'
            logger.info("confirm :"+str(confirm))
            if(confirm=='y'):
                commandToExecute="scripts/servers_influxdb_start.sh"
                additionalParam=""
                logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(nodes)+" User:"+str(user))
                with Spinner():
                    outputShFile= connectExecuteSSH(nodes, user,commandToExecute,additionalParam)
                    verboseHandle.printConsoleInfo("Node "+str(nodes)+" start command executed.")
        else:
            logger.info("No server details found.")
            verboseHandle.printConsoleInfo("No server details found.")
    except Exception as e:
        logger.error("Exception in Influxdb -> Start : executeCommandForStart() : "+str(e))
        verboseHandle.printConsoleError("Exception in Influxdb -> Start : executeCommandForStart() : "+str(e))
    logger.info("executeCommandForStart(): end")

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> Influxdb -> Start')
    try:
        startInputUserAndHost()
        executeCommandForStart()
    except Exception as e:
        logger.error("Exception in Influxdb -> Start : "+str(e))
        verboseHandle.printConsoleError("Exception in Influxdb -> Start : "+str(e))