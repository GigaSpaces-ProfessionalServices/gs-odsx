#!/usr/bin/env python3
import os
import signal

from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig, getYamlFilePathInsideFolder
from utils.ods_cleanup import signal_handler
from utils.odsx_keypress import userInputWithEscWrapper, userInputWrapper
from utils.odsx_retentionmanager_utilities import isTimeFormat, setupOrReloadService, getManagerHost

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
serviceName = "retention-manager.service"
user = "root"
app_config_interval_key = 'app.retentionmanager.scheduler.interval'
app_config_time_key = 'app.retentionmanager.scheduler.time'
app_config_space_key = 'app.retentionmanager.space'
app_retentionmanager_sqlite_dbfile = 'app.retentionmanager.sqlite.dbfile'

def setupService():
    global defaultManagerServer
    defaultManagerServer = getManagerHost()
    #print("defaultManagerServer=>"+str(defaultManagerServer))
    logger.info("setupService() : start")

    defaultSpaceName = readValuefromAppConfig(app_config_space_key)
    if(len(str(defaultSpaceName))==0 or str(defaultSpaceName)=='""'):
        defaultSpaceName = 'bll'

    #managerServerInput = Fore.YELLOW + "Enter manager serverhost ["+defaultManagerServer+"] :" + Fore.RESET
    #spaceNameInput = Fore.YELLOW + "Enter space name ["+defaultSpaceName+"] :" + Fore.RESET
    schedulerConfInput = Fore.YELLOW + "Please select scheduler configuration from below options \n [1]-Regular Interval\n [2]-Specific time in a day\n [99]-Exit: " + Fore.RESET
    
    #managerServer = str(userInputWrapper(managerServerInput))
    #if(len(managerServer) == 0):
    managerServer=defaultManagerServer

    #spaceName = str(userInputWrapper(spaceNameInput))
    #if(len(spaceName) == 0):
    spaceName=defaultSpaceName
   
    schedulerConf = str(userInputWithEscWrapper(schedulerConfInput))
    while(len(schedulerConf) == 0 or (str(schedulerConf)!='1') and str(schedulerConf)!='2' and str(schedulerConf)!='99'):
        schedulerConf = str(userInputWrapper(schedulerConfInput))

    schedulerIntervalInput = ""
    if schedulerConf=="99":
        exit(0)
    if(schedulerConf=='1'):
        schedulerIntervalInput = Fore.YELLOW + "Enter scheduler interval in minutes [10]: " + Fore.RESET
    if(schedulerConf=='2'):
        schedulerIntervalInput = Fore.YELLOW + "Enter time to run scheduler in HH:MM (24 hours) format [10:00]: " + Fore.RESET

    schedulerInterval = str(userInputWrapper(schedulerIntervalInput))
    if(schedulerConf=='1'):
        if(len(str(schedulerInterval))==0):
            schedulerInterval='10'
        
        isIntervalNum = str(schedulerInterval).isnumeric()
        while(isIntervalNum==False):
            verboseHandle.printConsoleError("Please enter valid number")
            schedulerInterval = str(userInputWrapper(schedulerIntervalInput))
            if(len(str(schedulerInterval))==0):
                schedulerInterval = '10'
                isIntervalNum= True
            else:
                isIntervalNum = str(schedulerInterval).isnumeric()
    if(schedulerConf=='2'): 
        if(len(str(schedulerInterval))==0):
            schedulerInterval='10:00'
     
        isTimeInput = isTimeFormat(schedulerInterval)
        while(isTimeInput==False):
            verboseHandle.printConsoleError("Please enter valid time format (HH:MM)")
            schedulerInterval = str(userInputWrapper(schedulerIntervalInput))
            if(len(str(schedulerInterval))==0):
                schedulerInterval = '10:10'
                isTimeInput= True
            else:
                isTimeInput = isTimeFormat(schedulerInterval)

    displaySummary(managerServer,spaceName,schedulerInterval)

    confirmMsg = Fore.YELLOW + "Are you sure, you want to setup Retention Manager service ? (Yes/No) [yes]:" + Fore.RESET
    choice = str(userInputWrapper(confirmMsg))
    while(len(choice) == 0):
        choice = 'y'

    while(choice.casefold()!='yes' and choice.casefold()!='no' and choice.casefold()!='y' and choice.casefold()!='n'):
        verboseHandle.printConsoleError("Invalid input")
        choice = str(userInputWrapper(confirmMsg))

    if (choice.casefold() == 'no' or choice.casefold()=='n'):
        logger.info("Exiting without registering policy")
        exit(0)

    #set_value_in_property_file(app_config_space_key,str(spaceName))

    dbLocation = readValuefromAppConfig(app_retentionmanager_sqlite_dbfile)
    setupOrReloadService(spaceName,schedulerInterval,managerServer,dbLocation,retentionJar)
    verboseHandle.printConsoleInfo("Retention Manager Service setup successfully!")


def displaySummary(managerServer,spaceName,schedulerInterval):
    global retentionJar
    retentionJar = str(getYamlFilePathInsideFolder(".object.jars.retention.retentionjar"))
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleWarning("***Summary***")
    print(Fore.GREEN+"1. "+
            Fore.GREEN+"Manager Server = "+
            Fore.GREEN+managerServer+Fore.RESET)
    print(Fore.GREEN+"2. "+
            Fore.GREEN+"Space Name = "+
            Fore.GREEN+spaceName+Fore.RESET)
    print(Fore.GREEN+"3. "+
            Fore.GREEN+"Scheduler Interval= "+
            Fore.GREEN+str(schedulerInterval)+Fore.RESET)
    print(Fore.GREEN+"4. "+
          Fore.GREEN+"Retention jar= "+
          Fore.GREEN+str(retentionJar)+Fore.RESET)
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
   
   
if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Object -> RetentionManager -> Service -> Setup")
    signal.signal(signal.SIGINT, signal_handler)
    setupService()
    
