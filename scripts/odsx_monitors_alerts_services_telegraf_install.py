#!/usr/bin/env python3

import os

from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_monitors_alerts_services_telegraf_list import listAllTelegrafServers
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_space_node, config_get_manager_node
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

def getManagerHostFromEnv():
    logger.info("getManagerHostFromEnv()")
    hosts = ''
    managerNodes = config_get_manager_node()
    for node in managerNodes:
        hosts+=str(os.getenv(str(node.ip)))+','
    hosts=hosts[:-1]
    return hosts

def executeCommandForInstall(host):
    logger.info("executeCommandForInstall(): start")
    try:
        commandToExecute="scripts/monitors_alerts_service_telegraf_install.sh"
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))#str(readValuefromAppConfig("app.setup.sourceInstaller"))
        additionalParam=sourceInstallerDirectory+' '+getManagerHostFromEnv()
        logger.info("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+host+" User:"+str(user)+" sourceInstaller:"+sourceInstallerDirectory)
        with Spinner():
                outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
                verboseHandle.printConsoleInfo("Telegraf  has been installed on host :"+host)
    except Exception as e:
        handleException(e)
    logger.info("executeCommandForInstall(): end")

def agentCommandForInstall(host):
    logger.info("executeCommandForInstall(): start")
    try:
        commandToExecute="scripts/monitors_alerts_service_telegraf_agent_install.sh"
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))#str(readValuefromAppConfig("app.setup.sourceInstaller"))
        additionalParam=sourceInstallerDirectory
        logger.info("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user)+" sourceInstaller:"+sourceInstallerDirectory)
        with Spinner():
            outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
            verboseHandle.printConsoleInfo("Telegraf  has been installed on host :"+str(host))
    except Exception as e:
        handleException(e)
    logger.info("executeCommandForInstall(): end")

def executeCommandForAgentPathCopy():
    nodelist = getSpaceServerList()
    for node in nodelist.split(','):
        agentCommandForInstall(node)

def getSpaceServerList():
    nodeList = config_get_space_node()
    nodes = ""
    for node in nodeList:
        if (len(nodeList) == 1):
            nodes = os.getenv(node.ip)
        else:
            nodes = nodes + ',' + os.getenv(node.ip)
    if nodes[0]==',':
        nodes=nodes[1:]
    return nodes

def exitAndDisplay(isMenuDriven):
    logger.info("exitAndDisplay(isMenuDriven)")
    if(isMenuDriven=='m'):
        logger.info("exitAndDisplay(MenuDriven) ")
        os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_install.py'+' '+isMenuDriven)
    else:
        cliArgumentsStr=''
        for arg in cliArguments:
            cliArgumentsStr+=arg
            cliArgumentsStr+=' '
        os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_install.py'+' '+cliArgumentsStr)

def summaryInstall(host):
    #To Display Summary ::
    telegrafSpaceScriptFiles =[]
    telegrafPivotScriptFiles =[]
    telegrafSpaceConfigFiles =[]
    telegrafPivotConfigFiles =[]
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    rpmPath=sourceInstallerDirectory+"/telegraf"

    #for file in glob.glob(rpmPath+"/*.rpm"):
    #    rpmFile=file
    rpmFile = [f for f in os.listdir(str(rpmPath)+"/") if f.endswith('.rpm')]
    telegrafSourcePath = [rpmPath+"/scripts/space/", rpmPath+"/scripts/pivot/"]
    telegrafTartgetPath = str(readValuefromAppConfig("app.alert.telegraf.custommetrics"))
    telegrafConfSourcePath = [rpmPath+"/config/space/", rpmPath+"/config/pivot/"]
    telegrafConfTartgetPath = "/etc/telegraf/telegraf.conf"

    for scriptSpace in os.listdir(rpmPath+"/scripts/space/"):
        telegrafSpaceScriptFiles.append(scriptSpace)

    for scriptPivot in os.listdir(rpmPath+"/scripts/pivot/"):
        telegrafPivotScriptFiles.append(scriptPivot)

    for configSpace in os.listdir(rpmPath+"/config/space/"):
        telegrafSpaceConfigFiles.append(configSpace)

    for configPivot in os.listdir(rpmPath+"/config/pivot/"):
        telegrafPivotConfigFiles.append(configPivot)

    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleWarning("***Summary***")
    print(Fore.GREEN+"1. "+
          Fore.GREEN+"Telegraf Version = "+
          Fore.GREEN+str(rpmFile)+Fore.RESET)
    print(Fore.GREEN+"2. "+
          Fore.GREEN+"Scripts pivot files = "+
          Fore.GREEN+str(telegrafPivotScriptFiles)+Fore.RESET)
    print(Fore.GREEN+"3. "+
          Fore.GREEN+"Scripts space files = "+
          Fore.GREEN+str(telegrafSpaceScriptFiles)+Fore.RESET)
    print(Fore.GREEN+"4. "+
          Fore.GREEN+"Script source path = "+
          Fore.GREEN+str(telegrafSourcePath)+Fore.RESET)
    print(Fore.GREEN+"5. "+
          Fore.GREEN+"Script target path = "+
          Fore.GREEN+str(telegrafTartgetPath)+Fore.RESET)
    print(Fore.GREEN+"6. "+
          Fore.GREEN+"Configuration pivot files = "+
          Fore.GREEN+str(telegrafPivotConfigFiles)+Fore.RESET)
    print(Fore.GREEN+"7. "+
          Fore.GREEN+"Configuration space files = "+
          Fore.GREEN+str(telegrafSpaceConfigFiles)+Fore.RESET)
    print(Fore.GREEN+"8. "+
          Fore.GREEN+"Configuration source path = "+
          Fore.GREEN+str(telegrafConfSourcePath)+Fore.RESET)
    print(Fore.GREEN+"9. "+
          Fore.GREEN+"Configuration target path = "+Fore.RESET,
          Fore.GREEN+telegrafConfTartgetPath+Fore.RESET)
    if(host != 0):
        print(Fore.GREEN+"10. "+
              Fore.GREEN+"Host = "+
              Fore.GREEN+str(host)+Fore.RESET)
    verboseHandle.printConsoleWarning("------------------------------------------------------------")

if __name__ == '__main__':
    logger.info("Menu -> Monitors -> Alerts -> Service -> Telegraf -> Install ")
    verboseHandle.printConsoleWarning('Menu -> Monitors -> Alerts -> Service -> Telegraf -> Install')
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
        serverInstallType = str(userInputWithEscWrapper(Fore.YELLOW+"press [1] if you want to install individual server. \nPress [Enter] to install all. \nPress [99] for exit.: "+Fore.RESET))
        logger.info("serverInstallType:"+str(serverInstallType))
        if(serverInstallType=='1'):
            optionMainMenu = int(userInputWrapper("Enter your host number to install: "))
            logger.info("Enter your host number to install:"+str(optionMainMenu))
            if(optionMainMenu != 99):
                if len(streamDict) >= optionMainMenu:
                    host = streamDict.get(optionMainMenu)
                    summaryInstall(host)
                    choice = str(userInputWrapper(Fore.YELLOW+"Are you sure want to install server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    while(len(str(choice))==0):
                        choice = str(userInputWrapper(Fore.YELLOW+"Are you sure want to install server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    logger.info("choice :"+str(choice))
                    if(choice.casefold()=='no' or choice.casefold()=='n'):
                        if(isMenuDriven=='m'):
                            logger.info("menudriven")
                            os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_install.py'+' '+isMenuDriven)
                        else:
                            exitAndDisplay(isMenuDriven)
                    elif(choice.casefold()=='yes' or choice.casefold()=='y'):
                        if(os.getenv("pivot1")==host):
                           executeCommandForInstall(host)
                           executeCommandForAgentPathCopy()
                        else:
                            executeCommandForInstall(host)

        elif(serverInstallType =='99'):
            logger.info("99 - Exist install")
        else:
            confirm=''
            confirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to install all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            while(len(str(confirm))==0):
                confirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to install all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            logger.info("confirm :"+str(confirm))
            if(confirm=='yes' or confirm=='y'):
                for host in streamDict:
                    if(os.getenv("pivot1")==streamDict.get(host)):
                      executeCommandForInstall(streamDict.get(host))
                      executeCommandForAgentPathCopy()
                    else:
                      executeCommandForInstall(streamDict.get(host))

            elif(confirm =='no' or confirm=='n'):
                if(isMenuDriven=='m'):
                    logger.info("menudriven")
                    os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_install.py'+' '+isMenuDriven)
    except Exception as e:
        handleException(e)