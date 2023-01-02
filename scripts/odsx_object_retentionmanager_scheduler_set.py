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


def setScheduleInterval():
    managerServer = getManagerHost()
    #print("defaultManagerServer=>"+str(defaultManagerServer))
    logger.info("setScheduleInterval() : start")

    confirmMsg = Fore.YELLOW + "Are you sure, you want to update scheduler interval for retention manager ? (Yes/No):" + Fore.RESET
    schedulerConfInput = Fore.YELLOW + "Please select scheduler configuration from below options \n [1]-Regular Interval\n [2]-Specific time in a day\n [99]-Exit : " + Fore.RESET
    
    schedulerConf = str(userInputWithEscWrapper(schedulerConfInput))
    while(len(schedulerConf) == 0 or (str(schedulerConf)!='1') and str(schedulerConf)!='2'  and str(schedulerConf)!='99'):
        schedulerConf = str(userInputWithEscWrapper(schedulerConfInput))
    
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
        

    choice = str(userInputWrapper(confirmMsg))
    while(len(choice) == 0):
        choice = str(userInputWrapper(confirmMsg))

    while(choice.casefold()!='yes' and choice.casefold()!='no' and choice.casefold()!='y' and choice.casefold()!='n'):
        verboseHandle.printConsoleError("Invalid input")
        choice = str(userInputWrapper(confirmMsg))


    if(choice.casefold() == 'no' or choice.casefold() == 'n'):
        exit(0)

    
    spaceName = readValuefromAppConfig(app_config_space_key)
    dbLocation = readValuefromAppConfig(app_retentionmanager_sqlite_dbfile)
    #print(str(intervalInMilliSecs))
    retentionJar = str(getYamlFilePathInsideFolder(".object.jars.retention.retentionjar"))
    setupOrReloadService(spaceName,schedulerInterval,managerServer,dbLocation,retentionJar)
    verboseHandle.printConsoleInfo("Scheduler interval set successfull!")
    logger.info("setScheduleInterval() : end")




if __name__ == '__main__':
    verboseHandle.printConsoleWarning("MENU -> Object -> Retention Manager -> Scheduler -> Set")
    signal.signal(signal.SIGINT, signal_handler)
    setScheduleInterval()
    
