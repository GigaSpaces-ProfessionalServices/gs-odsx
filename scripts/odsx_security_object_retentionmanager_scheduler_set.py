#!/usr/bin/env python3
import argparse
import os
import signal
import sys

from utils.ods_cleanup import signal_handler
from utils.ods_scp import scp_upload
from scripts.logManager import LogManager
from scripts.spinner import Spinner
from colorama import Fore
from utils.ods_scp import scp_upload
from utils.ods_cluster_config import config_get_manager_node
from utils.ods_app_config import set_value_in_property_file, readValuefromAppConfig, getYamlFilePathInsideFolder
from utils.odsx_retentionmanager_utilities import isTimeFormat, setupOrReloadService,getManagerHost

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

    confirmMsg = Fore.YELLOW + "Are you sure, you want to update scheduler interval for retenion manager ? (Yes/No):" + Fore.RESET
    schedulerConfInput = Fore.YELLOW + "Please select scheduler configuration from below options \n [1]-Regular Interval\n [2]-Specific time in a day\n [99]-Exit : " + Fore.RESET
    
    schedulerConf = str(input(schedulerConfInput))
    while(len(schedulerConf) == 0 or (str(schedulerConf)!='1') and str(schedulerConf)!='2'  and str(schedulerConf)!='99'):
        schedulerConf = str(input(schedulerConfInput))
    
    schedulerIntervalInput = ""
    if schedulerConf=="99":
        exit(0)
    if(schedulerConf=='1'):
        schedulerIntervalInput = Fore.YELLOW + "Enter scheduler interval in minutes [10]: " + Fore.RESET
    if(schedulerConf=='2'):
        schedulerIntervalInput = Fore.YELLOW + "Enter time to run scheduler in HH:MM (24 hours) format [10:00]: " + Fore.RESET

    schedulerInterval = str(input(schedulerIntervalInput))
    if(schedulerConf=='1'):
        if(len(str(schedulerInterval))==0):
            schedulerInterval='10'
        
        isIntervalNum = str(schedulerInterval).isnumeric()
        while(isIntervalNum==False):
            verboseHandle.printConsoleError("Please enter valid number")
            schedulerInterval = str(input(schedulerIntervalInput))
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
            schedulerInterval = str(input(schedulerIntervalInput))
            if(len(str(schedulerInterval))==0):
                schedulerInterval = '10:10'
                isTimeInput= True
            else:
                isTimeInput = isTimeFormat(schedulerInterval)
        

    choice = str(input(confirmMsg))
    while(len(choice) == 0):
        choice = str(input(confirmMsg))

    while(choice.casefold()!='yes' and choice.casefold()!='no' and choice.casefold()!='y' and choice.casefold()!='n'):
        verboseHandle.printConsoleError("Invalid input")
        choice = str(input(confirmMsg))


    if(choice.casefold() == 'no' or choice.casefold() == 'n'):
        exit(0)

    
    spaceName = readValuefromAppConfig(app_config_space_key)
    dbLocation = readValuefromAppConfig(app_retentionmanager_sqlite_dbfile)
    #print(str(intervalInMilliSecs))
    retentionJar = str(getYamlFilePathInsideFolder(".gs.jars.retention.retentionjar"))
    setupOrReloadService(spaceName,schedulerInterval,managerServer,dbLocation,retentionJar)
    verboseHandle.printConsoleInfo("Scheduler interval set successfull!")
    logger.info("setScheduleInterval() : end")




if __name__ == '__main__':
    verboseHandle.printConsoleWarning("MENU -> Object -> Retention Manager -> Scheduler -> Set")
    signal.signal(signal.SIGINT, signal_handler)
    setScheduleInterval()
    
