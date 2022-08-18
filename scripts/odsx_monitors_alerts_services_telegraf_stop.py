#!/usr/bin/env python3

import os
import sys

from colorama import Fore

from scripts.odsx_monitors_alerts_services_telegraf_list import listAllTelegrafServers
from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36

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

def stopTelegrafServiceByHost(host):
    logger.info("stopTelegrafServiceByHost()")
    cmd = "systemctl stop telegraf;sleep 3;"
    logger.info("Getting status.. telegraf :"+str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        if (output == 0):
            verboseHandle.printConsoleInfo("Service telegraf stopped successfully on "+str(host))
        else:
            verboseHandle.printConsoleError("Service telegraf failed to stop" +str(host))

def exitAndDisplay(isMenuDriven):
    logger.info("exitAndDisplay(isMenuDriven)")
    if(isMenuDriven=='m'):
        logger.info("exitAndDisplay(MenuDriven) ")
        os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_stop.py'+' '+isMenuDriven)
    else:
        cliArgumentsStr=''
        for arg in cliArguments:
            cliArgumentsStr+=arg
            cliArgumentsStr+=' '
        os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_stop.py'+' '+cliArgumentsStr)

if __name__ == '__main__':
    logger.info("Menu -> Monitors -> Alerts -> Service -> Telegraf -> Stop ")
    verboseHandle.printConsoleWarning('Menu -> Monitors -> Alerts -> Service -> Telegraf -> Stop')
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
        serverStopType = str(input(Fore.YELLOW+"press [1] if you want to stop individual server. \nPress [Enter] to stop all. \nPress [99] for exit.: "+Fore.RESET))
        logger.info("serverStopType:"+str(serverStopType))
        if(serverStopType=='1'):
            optionMainMenu = int(input("Enter your host number to stop: "))
            logger.info("Enter your host number to stop:"+str(optionMainMenu))
            if(optionMainMenu != 99):
                if len(streamDict) >= optionMainMenu:
                    host = streamDict.get(optionMainMenu)
                    choice = str(input(Fore.YELLOW+"Are you sure want to stop server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    while(len(str(choice))==0):
                        choice = str(input(Fore.YELLOW+"Are you sure want to stop server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    logger.info("choice :"+str(choice))
                    if(choice.casefold()=='no' or choice.casefold()=='n'):
                        if(isMenuDriven=='m'):
                            logger.info("menudriven")
                            os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_stop.py'+' '+isMenuDriven)
                        else:
                            exitAndDisplay(isMenuDriven)
                    elif(choice.casefold()=='yes' or choice.casefold()=='y'):
                        stopTelegrafServiceByHost(host)
        elif(serverStopType =='99'):
            logger.info("99 - Exist stop")
        else:
            confirm=''
            confirm = str(input(Fore.YELLOW+"Are you sure want to stop all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            while(len(str(confirm))==0):
                confirm = str(input(Fore.YELLOW+"Are you sure want to stop all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            logger.info("confirm :"+str(confirm))
            if(confirm=='yes' or confirm=='y'):
                for host in streamDict:
                 spaceHosts = stopTelegrafServiceByHost(streamDict.get(host))

            elif(confirm =='no' or confirm=='n'):
                if(isMenuDriven=='m'):
                    logger.info("menudriven")
                    os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_stop.py'+' '+isMenuDriven)
    except Exception as e:
        handleException(e)