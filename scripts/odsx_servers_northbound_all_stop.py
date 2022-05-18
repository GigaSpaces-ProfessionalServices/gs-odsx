#!/usr/bin/env python3
#!/usr/bin/python
import os
import platform
from os import path
from colorama import Fore
from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_nb_list
from utils.ods_ssh import connectExecuteSSH
from utils.ods_app_config import readValuefromAppConfig

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
nbConfig = {}

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

def getNBServerHostList():
    logger.info("getNBServerHostList()")
    nodeList = config_get_nb_list()
    nodes=""
    for node in nodeList:
        if(str(node.role).casefold().__contains__('applicative')):
            if(len(nodes)==0):
                nodes = os.getenv(node.ip)
            else:
                nodes = nodes+','+os.getenv(node.ip)
    return nodes

def getManagementHostList():
    logger.info("getManagementHostList()")
    nodeList = config_get_nb_list()
    nodes=""
    for node in nodeList:
        if(str(node.role).casefold().__contains__('management')):
            if(len(nodes)==0):
                nodes = os.getenv(node.ip)
            else:
                nodes = nodes+','+os.getenv(node.ip)
    return nodes

def getAgentHostList():
    logger.info("getAgentHostList()")
    nodeList = config_get_nb_list()
    nodes=""
    for node in nodeList:
        if(str(node.role).casefold().__contains__('agent')):
            if(len(nodes)==0):
                nodes = os.getenv(node.ip)
            else:
                nodes = nodes+','+os.getenv(node.ip)
    return nodes

def stopInputUserAndHost():
    logger.info("stoptInputUserAndHost():")
    try:
        global user
        global host
        #user = str(input(Fore.YELLOW+"Enter user to connect to NB [root]:"+Fore.RESET))
        #if(len(str(user))==0):
        #    user="root"
        user = 'root'
        logger.info(" user: "+str(user))

    except Exception as e:
        handleException(e)
    logger.info("stoptInputUserAndHost(): end")

def executeCommandForStop():
    logger.info("executeCommandForStop():")
    try:
        nodes = getNBServerHostList()
        if(len(nodes)>0):
            print(Fore.YELLOW+"NB applicative servers going to stop ["+nodes+"] "+Fore.RESET)
        spaceHostsConfig = getAgentHostList()
        logger.info("spaceHostsConfig : "+str(spaceHostsConfig))
        if(len(spaceHostsConfig)>0):
            print(Fore.YELLOW+"NB Agent servers going to stop["+spaceHostsConfig+"] "+Fore.RESET)
        nodesManagement = getManagementHostList()
        if(len(nodesManagement)>0):
            print(Fore.YELLOW+"NB management servers going to stop ["+nodesManagement+"]"+Fore.RESET)
        confirm = str(input(Fore.YELLOW+"Are you sure want to proceed ? (y/n) [y]: "+Fore.RESET))
        if(len(str(confirm))==0):
            confirm='y'
        if confirm.casefold() == 'y':
            if(len(nodes)>0):
                #confirm = str(input(Fore.YELLOW+"Are you sure want to stop NB applicative servers ["+nodes+"] (y/n) [y]: "+Fore.RESET))
                #if(len(str(confirm))==0):
                confirm='y'
                logger.info("NB servers confirm :"+str(confirm))
                if(confirm=='y'):
                    nodes = nodes.split(',')
                    for host in nodes:
                        commandToExecute="scripts/servers_northbound_stop.sh"
                        additionalParam=""
                        logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user))
                        with Spinner():
                            outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
                            logger.info("outputShFile"+str(outputShFile))
                            verboseHandle.printConsoleInfo("Node "+str(host)+" stop command executed.")
            else:
                logger.info("No NB Agent applicative server details found.")
                verboseHandle.printConsoleInfo("No NB applicative server details found.")
            #spaceHostsConfig = str(readValuefromAppConfig("app.space.hosts")).replace('"','')
            spaceHostsConfig = getAgentHostList()
            logger.info("spaceHostsConfig : "+str(spaceHostsConfig))
            if(len(spaceHostsConfig)>0):
                #confirm = str(input(Fore.YELLOW+"Are you sure want to stop NB Agent ["+spaceHostsConfig+"] (y/n) [y]: "+Fore.RESET))
                #if(len(str(confirm))==0):
                confirm='y'
                logger.info("stop NB Agent confirm :"+str(confirm))
                if(confirm=='y'):
                    agentHosts = spaceHostsConfig.split(',')
                    for host in agentHosts:
                        commandToExecute="scripts/servers_northbound_agent_stop.sh"
                        additionalParam=""
                        logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user))
                        with Spinner():
                            outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
                            logger.info("outputShFile"+str(outputShFile))
                            verboseHandle.printConsoleInfo("Node "+str(host)+" stop command executed.")
            else:
                logger.info("No NB Agent server details found.")
                verboseHandle.printConsoleInfo("No NB Agent server details found.")
            nodesManagement = getManagementHostList()
            if(len(nodesManagement)>0):
                #confirm = str(input(Fore.YELLOW+"Are you sure want to stop NB management servers ["+nodesManagement+"] (y/n) [y]: "+Fore.RESET))
                #if(len(str(confirm))==0):
                confirm='y'
                logger.info("stop management servers confirm :"+str(confirm))
                if(confirm=='y'):
                    nodes = nodesManagement.split(',')
                    for host in nodes:
                        logger.info("host :"+str(host))
                        commandToExecute="scripts/servers_northbound_stop.sh"
                        additionalParam=""
                        logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user))
                        with Spinner():
                            outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
                            logger.info("outputShFile"+str(outputShFile))
                            verboseHandle.printConsoleInfo("Node "+str(host)+" stop command executed.")
            else:
                logger.info("No NB management server details found.")
                verboseHandle.printConsoleInfo("No NB management server details found.")
    except Exception as e:
        handleException(e)
    logger.info("executeCommandForStop(): end")

if __name__ == '__main__':
    logger.info("servers -> Northbound -> Stop ")
    verboseHandle.printConsoleInfo("Menu -> servers -> Northbound -> All -> Stop ")
    try:
        stopInputUserAndHost()
        executeCommandForStop()
    except Exception as e:
        handleException(e)
