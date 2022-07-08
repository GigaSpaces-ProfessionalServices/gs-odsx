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
from utils.ods_app_config import set_value_in_property_file, readValuefromAppConfig

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
serviceName = "retention-manager.service"
user = "root"
app_config_interval_key = 'app.retentionmanager.scheduler.interval'
app_config_time_key = 'app.retentionmanager.scheduler.time'
app_config_space_key = 'app.retentionmanager.space'

def showScheduleInterval():
    logger.info("showScheduleInterval() : start")


    interval = readValuefromAppConfig(app_config_interval_key)
    #verboseHandle.printConsoleInfo("Scheduler interval is set to -> "+str(interval))
    if(len(str(interval))==0 or str(interval)=='""'):
        interval = readValuefromAppConfig(app_config_time_key)
        print(Fore.GREEN + "Scheduler interval is set to run at " + Fore.RESET + str(interval) +" every day")
    else:
        print(Fore.GREEN + "Scheduler interval is set to : " + Fore.RESET + str(int(interval)) +" minutes")
    
    logger.info("showScheduleInterval() : end")
   
    
    

if __name__ == '__main__':
    verboseHandle.printConsoleWarning("MENU -> Object -> Retention Manager -> Scheduler -> Show")
    signal.signal(signal.SIGINT, signal_handler)
    showScheduleInterval()
    
