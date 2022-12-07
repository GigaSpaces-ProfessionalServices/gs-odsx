#!/usr/bin/env python3

import os
import os.path

from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_monitors_alerts_services_telegraf_list import listAllTelegrafServers
from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_space_node
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36
from utils.odsx_keypress import userInputWithEscWrapper, userInputWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
nbConfig = {}
telegrafHostList=[]

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

def getTelegrafServerHostList():
    nodes = os.getenv("pivot1")
    return nodes

def removeInputUserAndHost():
    logger.info("removeInputUserAndHost():")
    try:
        global user
        global host
        user = str(userInputWrapper(Fore.YELLOW+"Enter user to connect to Telegraf [root]:"+Fore.RESET))
        if(len(str(user))==0):
            user="root"
        logger.info(" user: "+str(user))

    except Exception as e:
        handleException(e)
    logger.info("removeInputUserAndHost(): end")

def executeCommandForUnInstall(host):
    logger.info("executeCommandForUnInstall(): remove")
    try:
        cmd = "systemctl stop telegraf;sleep 5;yum -y remove telegraf;systemctl daemon-reload;"
        logger.info("Getting status.. telegraf :"+str(cmd))
        user = 'root'
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
            if (output == 0):
                verboseHandle.printConsoleInfo("Telegraf removed successfully on "+str(host))
            else:
                verboseHandle.printConsoleError("Telegraf removed failed on "+str(host))
    except Exception as e:
        handleException(e)
    logger.info("executeCommandForUnInstall(): end")

def executeCommandForAgentRemovePath():
    nodelist = getSpaceServerList()
    for node in nodelist.split(','):
        path = '/etc/telegraf/'
        isdir = os.path.isdir(path)
        if(isdir):
         agentCommandForRemove(node)
        else:
          print("Northbound not exist on space : "+node)

def getSpaceServerList():
    logger.info("getSpaceServerList()")
    nodeList = config_get_space_node()
    nodes = ""
    print(nodeList)
    for node in nodeList:
        if (len(nodeList) == 1):
            nodes = os.getenv(node.ip)
        else:
            nodes = nodes + ',' + os.getenv(node.ip)
    if nodes[0]==',':
        nodes=nodes[1:]
    return nodes

def agentCommandForRemove(host):
    logger.info("executeCommandForInstall(): remove")
    # nodeListSize = len(str((getSpaceServerList())).split(','))
    #
    # try:
    #     commandToExecute="scripts/monitors_alerts_service_telegraf_remove.sh"
    #     sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))#str(readValuefromAppConfig("app.setup.sourceInstaller"))
    #     additionalParam=sourceInstallerDirectory
    #     # for host in hostList.split(','):
    #     logger.info("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user)+" sourceInstaller:"+sourceInstallerDirectory)
    #     with Spinner():
    #         outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
    #         verboseHandle.printConsoleInfo("Telegraf  has been Removed from host :"+str(host))
    # except Exception as e:
    #     handleException(e)
    logger.info("executeCommandForInstall(): end")

def exitAndDisplay(isMenuDriven):
    logger.info("exitAndDisplay(isMenuDriven)")
    if(isMenuDriven=='m'):
        logger.info("exitAndDisplay(MenuDriven) ")
        os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_remove.py'+' '+isMenuDriven)
    else:
        cliArgumentsStr=''
        for arg in cliArguments:
            cliArgumentsStr+=arg
            cliArgumentsStr+=' '
        os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_remove.py'+' '+cliArgumentsStr)

if __name__ == '__main__':
    logger.info("Menu -> Monitors -> Alerts -> Service -> Telegraf -> Remove ")
    verboseHandle.printConsoleWarning('Menu -> Monitors -> Alerts -> Service -> Telegraf -> Remove')
    try:
        streamResumeStream=''
        optionMainMenu=''
        choice=''
        cliArguments=''
        isMenuDriven=''
        managerRemove=''
        user='root'
        logger.info("user :"+str(user))
        streamDict = listAllTelegrafServers()
        serverRemoveType = str(userInputWithEscWrapper(Fore.YELLOW+"press [1] if you want to remove individual server. \nPress [Enter] to remove all. \nPress [99] for exit.: "+Fore.RESET))
        logger.info("serverRemoveType:"+str(serverRemoveType))
        if(serverRemoveType=='1'):
            optionMainMenu = int(userInputWrapper("Enter your host number to remove: "))
            logger.info("Enter your host number to remove:"+str(optionMainMenu))
            if(optionMainMenu != 99):
                if len(streamDict) >= optionMainMenu:
                    host = streamDict.get(optionMainMenu)
                    choice = str(userInputWrapper(Fore.YELLOW+"Are you sure want to remove server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    while(len(str(choice))==0):
                        choice = str(userInputWrapper(Fore.YELLOW+"Are you sure want to remove server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    logger.info("choice :"+str(choice))
                    if(choice.casefold()=='no' or choice.casefold()=='n'):
                        if(isMenuDriven=='m'):
                            logger.info("menudriven")
                            os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_remove.py'+' '+isMenuDriven)
                        else:
                            exitAndDisplay(isMenuDriven)
                    elif(choice.casefold()=='yes' or choice.casefold()=='y'):
                        executeCommandForUnInstall(host)
        elif(serverRemoveType =='99'):
            logger.info("99 - Exist remove")
        else:
            confirm=''
            confirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to remove all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            while(len(str(confirm))==0):
                confirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to remove all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            logger.info("confirm :"+str(confirm))

            if(confirm=='yes' or confirm=='y'):
                for host in telegrafHostList:
                    executeCommandForUnInstall(streamDict.get(host))

            elif(confirm =='no' or confirm=='n'):
                if(isMenuDriven=='m'):
                    logger.info("menudriven")
                    os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_remove.py'+' '+isMenuDriven)

    except Exception as e:
        handleException(e)

