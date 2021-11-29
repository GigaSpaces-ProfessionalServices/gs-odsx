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

def stopInputUserAndHost():
    logger.info("stopInputUserAndHost():")
    try:
        global user
        global host
        user = str(input(Fore.YELLOW+"Enter user to connect to Influxdb [root]:"+Fore.RESET))
        if(len(str(user))==0):
            user="root"
        logger.info(" user: "+str(user))

    except Exception as e:
        logger.error("Exception in Influxdb -> Stop : stopInputUserAndHost() : "+str(e))
        verboseHandle.printConsoleError("Exception in Influxdb -> Stop : stopInputUserAndHost() : "+str(e))
    logger.info("stopInputUserAndHost(): end")

def executeCommandForStop():
    logger.info("executeCommandForStop(): stop")
    try:
        nodes = getInfluxdbServerHostList()
        if(len(nodes)>0):
            confirm = str(input(Fore.YELLOW+"Are you sure want to stop Influxdb servers ["+nodes+"] (y/n) [y]: "+Fore.RESET))
            if(len(str(confirm))==0):
                confirm='y'
            logger.info("confirm :"+str(confirm))
            if(confirm=='y'):
                commandToExecute="scripts/servers_influxdb_stop.sh"
                additionalParam=""
                logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(nodes)+" User:"+str(user))
                with Spinner():
                    outputShFile= connectExecuteSSH(nodes, user,commandToExecute,additionalParam)
                    verboseHandle.printConsoleInfo("Node "+str(nodes)+" stop Influxdb service command executed.")
        else:
            logger.info("No server details found.")
            verboseHandle.printConsoleInfo("No server details found.")
    except Exception as e:
        logger.error("Exception in Influxdb -> Stop : executeCommandForStop() : "+str(e))
        verboseHandle.printConsoleError("Exception in Influxdb -> Stop : executeCommandForStop() : "+str(e))
    logger.info("executeCommandForStop(): end")

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> Influxdb -> Stop')
    try:
        stopInputUserAndHost()
        executeCommandForStop()
    except Exception as e:
        logger.error("Exception in Influxdb -> Stop : "+str(e))
        verboseHandle.printConsoleError("Exception in Influxdb -> Stop : "+str(e))