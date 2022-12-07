#!/usr/bin/env python3

import os

import requests
from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_datavalidator_install_list import getDataValidationHost
from scripts.odsx_datavalidator_install_list import listDVServers
from scripts.spinner import Spinner
from utils.ods_app_config import set_value_in_property_file, readValuefromAppConfig
from utils.ods_cluster_config import config_get_dataValidation_nodes, config_remove_dataValidation_byNameIP
from utils.ods_ssh import connectExecuteSSH
from utils.odsx_keypress import userInputWithEscWrapper, userInputWrapper

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

def getDVServerHostList():
    nodeList = config_get_dataValidation_nodes()
    nodes=""
    for node in nodeList:
        #if(str(node.role).casefold() == 'server'):
        if(len(nodes)==0):
            nodes = os.getenv(node.ip)
        else:
            nodes = nodes+','+os.getenv(node.ip)
    return nodes

def removeInputUserAndHost():
    logger.info("removeInputUserAndHost():")
    try:
        global user
        global host
        user = str(userInputWrapper(Fore.YELLOW+"Enter user to connect to Data validation server [root]:"+Fore.RESET))
        if(len(str(user))==0):
            user="root"
        logger.info(" user: "+str(user))

    except Exception as e:
        handleException(e)

def proceedForIndividualRemove(host_dict_obj, nodes):
    logger.info("proceedForIndividualRemove :")
    hostNumer = str(userInputWrapper(Fore.YELLOW+"Enter serial number to remove : "+Fore.RESET))
    while(len(str(hostNumer))==0):
        hostNumer = str(userInputWrapper(Fore.YELLOW+"Enter serial number to remove : "+Fore.RESET))
    host = host_dict_obj.get(hostNumer)
    confirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to remove "+str(host)+" ? (y/n) [y]"+Fore.RESET))
    if(confirm=='y' or len(str(confirm))==0 ):
        logger.info("Individual host : "+str(host))
        commandToExecute="scripts/servers_datavalidation_remove.sh"
        outputShFile= connectExecuteSSH(host, user,commandToExecute,'')
        print(outputShFile)
        config_remove_dataValidation_byNameIP(host,host)
        hostAppConfig = str(readValuefromAppConfig("app.di.hosts")).replace('"','')
        logger.info("hostAppConfig :"+str(hostAppConfig))
        hostAppConfig = hostAppConfig.replace(host,'')
        logger.info("hostConfig after remove : "+str(hostAppConfig))
        set_value_in_property_file('app.di.hosts',hostAppConfig)
        verboseHandle.printConsoleInfo("Node has been removed :"+str(host))


def executeCommandForUnInstall():
    logger.info("executeCommandForUnInstall(): start")
    try:
        dataValidationNodes = config_get_dataValidation_nodes()
        dataValidationHost = getDataValidationHost(dataValidationNodes)
        logger.info("dataValidationHost : " + str(dataValidationHost))

        host_dict_obj = listDVServers()
        logger.info("host_dict_obj :"+str(host_dict_obj))
        nodes = getDVServerHostList()
        nodesCount = nodes.split(',')
        logger.info("nodesCount :"+str(len(nodesCount)))
        if(len(nodes)>0):
            removeType=''
            if(len(nodesCount)>1):
                removeType = str(userInputWithEscWrapper(Fore.YELLOW+"[1] Individual remove \n[Enter] To remove all \n[99] ESC : "))
            if(len(str(removeType))==0):
                confirmUninstall = str(userInputWithEscWrapper(Fore.YELLOW+"Are you sure want to remove Data validation servers ["+nodes+"] (y/n) [y]: "+Fore.RESET))
                if(len(str(confirmUninstall))==0):
                    confirmUninstall='y'
                logger.info("confirmUninstall :"+str(confirmUninstall))
                if(confirmUninstall=='y'):
                    commandToExecute="scripts/servers_datavalidation_remove.sh"
                    additionalParam=""
                    logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(nodes)+" User:"+str(user))
                    with Spinner():
                        for host in nodes.split(','):
                            if(dataValidationHost != ''):
                                response = requests.delete(
                                    "http://" + dataValidationHost + ":"+str(readValuefromAppConfig("app.dv.server.port"))+"/agent/remove/" + host)
                                logger.info(str(response.status_code))

                            outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
                            config_remove_dataValidation_byNameIP(host,host)
                            #set_value_in_property_file('app.di.hosts','')
                            verboseHandle.printConsoleWarning('');
                            verboseHandle.printConsoleInfo("Node has been removed :"+str(host))
            if(removeType=='1'):
                proceedForIndividualRemove(host_dict_obj,nodes)
            if(removeType=='99'):
                return
        else:
            logger.info("No server details found.")
            verboseHandle.printConsoleInfo("No server details found.")
    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataValidator -> Install -> Remove')
    try:
        removeInputUserAndHost()
        executeCommandForUnInstall()
    except Exception as e:
        handleException(e)
