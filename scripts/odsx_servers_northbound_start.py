#!/usr/bin/env python3
#!/usr/bin/python
import os, sys, argparse
import platform
from os import path
from colorama import Fore
from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_nb_list
from utils.ods_ssh import connectExecuteSSH,executeRemoteCommandAndGetOutputPython36
from utils.ods_app_config import readValuefromAppConfig

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
nbConfig = {}

class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR

def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    parser.add_argument('--host',
                        help='host ip',
                        required='True',
                        default='localhost')
    parser.add_argument('-u', '--user',
                        help='user name',
                        default='root')
    parser.add_argument('-dryrun', '--dryrun',
                        help='Dry run flag',
                        default='false', action='store_true')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])

def getNBServerHostList():
    nodeList = config_get_nb_list()
    nodes=""
    for node in nodeList:
        if(str(node.role).casefold().__contains__('applicative')):
            if(len(nodes)==0):
                nodes = node.ip
            else:
                nodes = nodes+','+node.ip
    return nodes

def getManagementHostList():
    logger.info("getManagementHostList()")
    nodeList = config_get_nb_list()
    nodes=""
    for node in nodeList:
        if(str(node.role).casefold().__contains__('management')):
            if(len(nodes)==0):
                nodes = node.ip
            else:
                nodes = nodes+','+node.ip
    return nodes

def getAgentHostList():
    logger.info("getAgentHostList()")
    nodeList = config_get_nb_list()
    nodes=""
    for node in nodeList:
        if(str(node.role).casefold().__contains__('agent')):
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
        #if(len(str(hostCLI))>0):
        #    host=hostCLI
        #logger.info("HOSTCLI: "+str(host))
        #user = str(input(Fore.YELLOW+"Enter user to connect to NB [root]:"+Fore.RESET))
        #if(len(str(user))==0):
        #    user="root"
        user = 'root'
        logger.info(" user: "+str(user))

    except Exception as e:
        logger.error("Exception in NB -> Start : startInputUserAndHost() : "+str(e))
        verboseHandle.printConsoleError("Exception in NB -> Start : startInputUserAndHost() : "+str(e))
    logger.info("startInputUserAndHost(): end")

def executeCommandForStart():
    logger.info("executeCommandForStart():")
    try:
        nodes = getNBServerHostList()
        if(len(nodes)>0):
            confirm = str(input(Fore.YELLOW+"Are you sure want to start NB applicative servers ["+nodes+"] (y/n) [y]: "+Fore.RESET))
            if(len(str(confirm))==0):
                confirm='y'
            logger.info("confirm :"+str(confirm))
            if(confirm=='y'):
                nodes = nodes.split(',')
                for host in nodes:
                    commandToExecute="scripts/servers_northbound_start.sh"
                    additionalParam=""
                    logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user))
                    with Spinner():
                        outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
                        logger.info("outputShFile"+str(outputShFile))
                        verboseHandle.printConsoleInfo("Node "+str(host)+" start command executed.")
        else:
            logger.info("No NB applicative server details found.")
            verboseHandle.printConsoleInfo("No NB applicative server details found.")
        #spaceHostsConfig = str(readValuefromAppConfig("app.space.hosts")).replace('"','')
        spaceHostsConfig = getAgentHostList()
        logger.info("spaceHostsConfig : "+str(spaceHostsConfig))
        if(len(spaceHostsConfig)>0):
            confirm = str(input(Fore.YELLOW+"Are you sure want to start NB Agent ["+spaceHostsConfig+"] (y/n) [y]: "+Fore.RESET))
            if(len(str(confirm))==0):
                confirm='y'
            logger.info("confirm :"+str(confirm))
            if(confirm=='y'):
                agentHosts = spaceHostsConfig.split(',')
                for host in agentHosts:
                    commandToExecute="scripts/servers_northbound_agent_start.sh"
                    additionalParam=""
                    logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user))
                    with Spinner():
                        outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
                        logger.info("outputShFile"+str(outputShFile))
                        verboseHandle.printConsoleInfo("Node "+str(host)+" start command executed.")
        else:
            logger.info("No NB Agent agent server details found.")
            verboseHandle.printConsoleInfo("No NB agent server details found.")
        nodesManagement = getManagementHostList()
        logger.info("nodesManagement :"+str(len(nodesManagement)))
        if(len(nodesManagement)>0):
            confirm = str(input(Fore.YELLOW+"Are you sure want to start NB Management servers ["+nodesManagement+"] (y/n) [y]: "+Fore.RESET))
            if(len(str(confirm))==0):
                confirm='y'
            logger.info("confirm :"+str(confirm))
            if(confirm=='y'):
                nodes = nodesManagement.split(',')
                for host in nodes:
                    commandToExecute="scripts/servers_northbound_start.sh"
                    additionalParam=""
                    logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user))
                    with Spinner():
                        outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
                        logger.info("outputShFile"+str(outputShFile))
                        verboseHandle.printConsoleInfo("Node "+str(host)+" start command executed.")
        else:
            logger.info("No NB management server details found.")
            verboseHandle.printConsoleInfo("No NB management server details found.")
    except Exception as e:
        logger.error("Exception in Northbound -> Start : executeCommandForStart() : "+str(e))
        verboseHandle.printConsoleError("Exception in Northbound -> Start : executeCommandForStart() : "+str(e))
    logger.info("executeCommandForStart(): end")

if __name__ == '__main__':
    logger.info("servers -> Northbound -> Start ")
    args = []
    menuDrivenFlag='m' # To differentiate between CLI and Menudriven Argument handling help section
    args.append(sys.argv[0])
    if len(sys.argv) > 1 and sys.argv[1] != menuDrivenFlag:
        arguments = myCheckArg(sys.argv[1:])
        #hostCLI = arguments.host
    try:
        startInputUserAndHost()
        executeCommandForStart()
    except Exception as e:
        logger.error("Exception in Nb -> Start : "+str(e))
        verboseHandle.printConsoleError("Exception in Nb -> Start : "+str(e))
    verboseHandle.printConsoleInfo("servers -> Northbound -> Start ")