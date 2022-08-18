#!/usr/bin/env python3

import os

from colorama import Fore

from scripts.odsx_monitors_alerts_service_telegraf_list import listAllTelegrafServers
from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36, connectExecuteSSH

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

def reloadInputUserAndHost(host):
    logger.info("executeCommandForInstall(): start")
    try:
        commandToExecute="scripts/monitors_alerts_service_telegraf_restart.sh"
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))#str(readValuefromAppConfig("app.setup.sourceInstaller"))
        additionalParam=sourceInstallerDirectory
        logger.info("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user)+" sourceInstaller:"+sourceInstallerDirectory)
        with Spinner():
            outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
            verboseHandle.printConsoleInfo("Telegraf  has been reload"
                                           " on host :"+str(host))
    except Exception as e:
        handleException(e)
    logger.info("executeCommandForInstall(): end")
def exitAndDisplay(isMenuDriven):
    logger.info("exitAndDisplay(isMenuDriven)")
    if(isMenuDriven=='m'):
        logger.info("exitAndDisplay(MenuDriven) ")
        os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_restart.py'+' '+isMenuDriven)
    else:
        cliArgumentsStr=''
        for arg in cliArguments:
            cliArgumentsStr+=arg
            cliArgumentsStr+=' '
        os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_restart.py'+' '+cliArgumentsStr)

if __name__ == '__main__':
    logger.info("Menu -> Monitors -> Alerts -> Service -> Telegraf -> Restart ")
    verboseHandle.printConsoleWarning('Menu -> Monitors -> Alerts -> Service -> Telegraf -> Restart')
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
        serverRestartType = str(input(Fore.YELLOW+"press [1] if you want to restart individual server. \nPress [Enter] to restart all. \nPress [99] for exit.: "+Fore.RESET))
        logger.info("serverRestartType:"+str(serverRestartType))
        if(serverRestartType=='1'):
            optionMainMenu = int(input("Enter your host number to restart: "))
            logger.info("Enter your host number to restart:"+str(optionMainMenu))
            spaceRestart1 = streamDict.get(optionMainMenu)
            if(optionMainMenu != 99):
                if len(streamDict) >= optionMainMenu:
                    host = streamDict.get(optionMainMenu)
                    choice = str(input(Fore.YELLOW+"Are you sure want to restart server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    while(len(str(choice))==0):
                        choice = str(input(Fore.YELLOW+"Are you sure want to restart server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    logger.info("choice :"+str(choice))
                    if(choice.casefold()=='no' or choice.casefold()=='n'):
                        if(isMenuDriven=='m'):
                            logger.info("menudriven")
                            os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_restart.py'+' '+isMenuDriven)
                        else:
                            exitAndDisplay(isMenuDriven)
                    elif(choice.casefold()=='yes' or choice.casefold()=='y'):
                        reloadInputUserAndHost(host)
        elif(serverRestartType =='99'):
            logger.info("99 - Exist restart")
        else:
            confirm=''
            confirm = str(input(Fore.YELLOW+"Are you sure want to restart all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            while(len(str(confirm))==0):
                confirm = str(input(Fore.YELLOW+"Are you sure want to restart all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            logger.info("confirm :"+str(confirm))

            if(confirm=='yes' or confirm=='y'):
                for host in streamDict:
                    spaceHosts = reloadInputUserAndHost(streamDict.get(host))

            elif(confirm =='no' or confirm=='n'):
                if(isMenuDriven=='m'):
                    logger.info("menudriven")
                    os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_restart.py'+' '+isMenuDriven)
    except Exception as e:
        logger.error("Invalid argument space remove :"+str(e))
        verboseHandle.printConsoleError("Invalid argument")


