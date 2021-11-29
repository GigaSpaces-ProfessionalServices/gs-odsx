#!/usr/bin/env python3

import os
import platform
from os import path
from colorama import Fore
from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_ssh import connectExecuteSSH
from utils.ods_cluster_config import config_get_dataIntegration_nodes, config_remove_dataIntegration_byNameIP
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

def getDIServerHostList():
    nodeList = config_get_dataIntegration_nodes()
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
        user = str(input(Fore.YELLOW+"Enter user to connect to DI server [root]:"+Fore.RESET))
        if(len(str(user))==0):
            user="root"
        logger.info(" user: "+str(user))

    except Exception as e:
        handleException(e)

def executeCommandForUnInstall():
    logger.info("executeCommandForUnInstall(): start")
    try:
        nodes = getDIServerHostList()
        if(len(nodes)>0):
            confirmUninstall = str(input(Fore.YELLOW+"Are you sure want to remove DI servers ["+nodes+"] (y/n) [y]: "+Fore.RESET))
            if(len(str(confirmUninstall))==0):
                confirmUninstall='y'
            logger.info("confirmUninstall :"+str(confirmUninstall))
            if(confirmUninstall=='y'):
                commandToExecute="scripts/servers_di_remove.sh"
                additionalParam=""
                logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(nodes)+" User:"+str(user))
                with Spinner():
                    for host in nodes.split(','):
                        print(host)
                        outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
                        print(outputShFile)
                        config_remove_dataIntegration_byNameIP(host,host)
                        set_value_in_property_file('app.di.hosts','')
                        verboseHandle.printConsoleInfo("Node has been removed :"+str(host))
        else:
            logger.info("No server details found.")
            verboseHandle.printConsoleInfo("No server details found.")
    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> DI -> Remove')
    try:
        removeInputUserAndHost()
        executeCommandForUnInstall()
    except Exception as e:
        handleException(e)
