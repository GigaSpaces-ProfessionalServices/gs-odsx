#!/usr/bin/env python3

import os

from scripts.odsx_monitors_alerts_services_telegraf_list import listAllTelegrafServers, getStatusOfTelegraf
from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36
from colorama import Fore

from utils.odsx_keypress import userInputWithEscWrapper

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

def startInputUserAndHost(host):
    logger.info("startTelegrafServiceByHost()")
    cmd = "systemctl start telegraf;sleep 3;"
    logger.info("Getting status.. telegraf :"+str(cmd))
    user = 'root'
    try:
        with Spinner():
            if(getStatusOfTelegraf(host) != 0):
                output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
                if (output == 0):
                    verboseHandle.printConsoleInfo("Service telegraf started successfully on "+host)
                else:
                    verboseHandle.printConsoleError("Service telegraf failed to start on "+host)
            else:
                print("Telegraf Already started on host : "+ host)
    except Exception as e:
       handleException(e)
       logger.info("executeCommandForInstall(): end")

def exitAndDisplay(isMenuDriven):
    logger.info("exitAndDisplay(isMenuDriven)")
    if(isMenuDriven=='m'):
        logger.info("exitAndDisplay(MenuDriven) ")
        os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_start.py'+' '+isMenuDriven)
    else:
        cliArgumentsStr=''
        for arg in cliArguments:
            cliArgumentsStr+=arg
            cliArgumentsStr+=' '
        os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_start.py'+' '+cliArgumentsStr)

if __name__ == '__main__':

      logger.info("Menu -> Monitors -> Alerts -> Service -> Telegraf -> Start ")
      verboseHandle.printConsoleWarning('Menu -> Monitors -> Alerts -> Service -> Telegraf -> Start')
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
        serverStartType = str(userInputWithEscWrapper(Fore.YELLOW+"press [1] if you want to start individual server. \nPress [Enter] to start all. \nPress [99] for exit.: "+Fore.RESET))
        logger.info("serverStartType:"+str(serverStartType))
        if(serverStartType=='1'):
            optionMainMenu = int(input("Enter your host number to start: "))
            logger.info("Enter your host number to start:"+str(optionMainMenu))
            spaceStart1 = streamDict.get(optionMainMenu)
            if(optionMainMenu != 99):
                if len(streamDict) >= optionMainMenu:
                    host = streamDict.get(optionMainMenu)
                    choice = str(input(Fore.YELLOW+"Are you sure want to start server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    while(len(str(choice))==0):
                        choice = str(input(Fore.YELLOW+"Are you sure want to start server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    logger.info("choice :"+str(choice))
                    if(choice.casefold()=='no' or choice.casefold()=='n'):
                        if(isMenuDriven=='m'):
                            logger.info("menudriven")
                            os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_start.py'+' '+isMenuDriven)
                        else:
                            exitAndDisplay(isMenuDriven)
                    elif(choice.casefold()=='yes' or choice.casefold()=='y'):
                        startInputUserAndHost(host)
        elif(serverStartType =='99'):
            logger.info("99 - Exist start")
        else:
            confirm=''
            confirm = str(input(Fore.YELLOW+"Are you sure want to start all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            while(len(str(confirm))==0):
                confirm = str(input(Fore.YELLOW+"Are you sure want to start all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            logger.info("confirm :"+str(confirm))

            if(confirm=='yes' or confirm=='y'):
                for host in streamDict:
                 spaceHosts = startInputUserAndHost(streamDict.get(host))

            elif(confirm =='no' or confirm=='n'):
                if(isMenuDriven=='m'):
                    logger.info("menudriven")
                    os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_start.py'+' '+isMenuDriven)

      except Exception as e:
          handleException(e)

