#!/usr/bin/env python3

import os

from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_servers_di_list import listDIServers
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_dataEngine_nodes, config_remove_dataEngine_byNameIP, \
    isInstalledAdabasService
from utils.ods_ssh import connectExecuteSSH, executeRemoteCommandAndGetOutputPython36
from utils.odsx_keypress import userInputWithEscWrapper, userInputWrapper
from utils.odsx_print_tabular_data import printTabular

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

def getDEServerHostList():
    nodeList = config_get_dataEngine_nodes()
    nodes = ""
    for node in nodeList:
        # if(str(node.role).casefold() == 'server'):
        if node.role == "mq-connector":
            if (len(nodes) == 0):
                nodes = os.getenv(node.ip)
            else:
                nodes = nodes + ',' + os.getenv(node.ip)
    return nodes

def removeInputUserAndHost():
    logger.info("removeInputUserAndHost():")
    try:
        global user
        global host
        #user = str(userInputWrapper(Fore.YELLOW+"Enter user to connect to DI server [root]:"+Fore.RESET))
        #if(len(str(user))==0):
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
        commandToExecute="scripts/security_mq-connector_adabasservice_remove.sh"
        dbaGigaLogPath=str(readValuefromAppConfig("app.gigalog.path"))
        outputShFile= connectExecuteSSH(host, user,commandToExecute,dbaGigaLogPath)
        print(outputShFile)
        config_remove_dataEngine_byNameIP(host,host)
       # hostAppConfig = str(readValuefromAppConfig("app.di.hosts")).replace('"','')
       # logger.info("hostAppConfig :"+str(hostAppConfig))
       # hostAppConfig = hostAppConfig.replace(host,'')
       # logger.info("hostConfig after remove : "+str(hostAppConfig))
       # set_value_in_property_file('app.di.hosts',hostAppConfig)
        verboseHandle.printConsoleInfo("Node has been removed :"+str(host))

class obj_type_dictionary(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

def getAdabusServiceStatus(node):
    logger.info("getConsolidatedStatus() : " + str(os.getenv(node.ip)))
    cmdList = ["systemctl status odsxadabas"]
    for cmd in cmdList:
        logger.info("cmd :" + str(cmd) + " host :" + str(os.getenv(node.ip)))
        logger.info("Getting status.. :" + str(cmd))
        user = 'root'
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(os.getenv(node.ip), user, cmd)
            logger.info("output1 : " + str(output))
            if (output != 0):
                # verboseHandle.printConsoleInfo(" Service :"+str(cmd)+" not started.")
                logger.info(" Service :" + str(cmd) + " not started." + str(os.getenv(node.ip)))
            return output

def listDIServers():
    logger.info("listDEServers()")
    host_dict_obj = obj_type_dictionary()
    dEServers = config_get_dataEngine_nodes("config/cluster.config")
    headers = [Fore.YELLOW + "Sr Num" + Fore.RESET,
               Fore.YELLOW + "Ip" + Fore.RESET,
               Fore.YELLOW + "Host" + Fore.RESET,
               Fore.YELLOW + "Installed" + Fore.RESET,
               Fore.YELLOW + "Status" + Fore.RESET]
    data = []
    counter = 1
    for node in dEServers:
        if node.role == "mq-connector":
            installStatus='No'
            host_dict_obj.add(str(counter), str(node.ip))
            status = getAdabusServiceStatus(node)
            install = isInstalledAdabasService(str(os.getenv(node.ip)))
            logger.info("install : "+str(install))
            if(len(str(install))>0):
                installStatus='Yes'
            dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                         Fore.GREEN + os.getenv(node.ip) + Fore.RESET,
                         Fore.GREEN + os.getenv(node.name) + Fore.RESET,
                         Fore.GREEN+installStatus+Fore.RESET if(installStatus=='Yes') else Fore.RED+installStatus+Fore.RESET,
                         Fore.GREEN+"ON"+Fore.RESET if(status == 0) else Fore.RED+"OFF"+Fore.RESET
                         ]
            data.append(dataArray)
            counter = counter + 1
    printTabular(None, headers, data)
    return host_dict_obj

def executeCommandForUnInstall():
    logger.info("executeCommandForUnInstall(): start")
    try:
        host_dict_obj = listDIServers()
        logger.info("host_dict_obj :"+str(host_dict_obj))
        nodes = getDEServerHostList()
        nodesCount = nodes.split(',')
        logger.info("nodesCount :"+str(len(nodesCount)))
        if(len(nodes)>0):
            removeType=''
            if(len(nodesCount)>1):
                removeType = str(userInputWithEscWrapper(Fore.YELLOW+"[1] Individual remove \n[Enter] To remove all \n[99] ESC : "))
            if(len(str(removeType))==0):
                confirmUninstall = str(userInputWrapper(Fore.YELLOW+"Are you sure want to remove Adabas service ["+nodes+"] (y/n) [y]: "+Fore.RESET))
                if(len(str(confirmUninstall))==0):
                    confirmUninstall='y'
                logger.info("confirmUninstall :"+str(confirmUninstall))
                if(confirmUninstall=='y'):
                    commandToExecute="scripts/security_mq-connector_adabasservice_remove.sh"
                    dbaGigaLogPath=str(readValuefromAppConfig("app.gigalog.path"))
                    additionalParam=dbaGigaLogPath
                    logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(nodes)+" User:"+str(user))
                    with Spinner():
                        for host in nodes.split(','):
                            print(host)
                            outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
                            print(outputShFile)
                            #config_remove_dataEngine_byNameIP(host,host)
                            #set_value_in_property_file('app.di.hosts','')
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
    verboseHandle.printConsoleWarning("Menu -> MQ Connector -> Adabas Service -> Remove")
    try:
        removeInputUserAndHost()
        executeCommandForUnInstall()
    except Exception as e:
        handleException(e)
