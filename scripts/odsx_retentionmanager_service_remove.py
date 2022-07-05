#!/usr/bin/env python3
import argparse
import os
import sys
from utils.ods_cluster_config import config_get_grafana_list,config_get_nb_list
from utils.ods_ssh import connectExecuteSSH, executeRemoteCommandAndGetOutput, executeLocalCommandAndGetOutput
from utils.ods_scp import scp_upload
from scripts.logManager import LogManager
from scripts.spinner import Spinner
from colorama import Fore


verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
serviceName = "retention-manager.service";
user = "root"

def removeService():
    logger.info("removeService() : start")

    confirmMsg = Fore.YELLOW + "Are you sure, you want to remove Retention Manager service ? (Yes/No) [Yes]:" + Fore.RESET
    
    choice = str(input(confirmMsg))

    while(len(choice) > 0 and choice.casefold()!='yes' and choice.casefold()!='no'):
        verboseHandle.printConsoleError("Invalid input")
        choice = str(input(confirmMsg))

    if choice.casefold() == 'no':
        exit(0)


    commandToExecute = "scripts/retentionmanager_service_remove.sh"
    logger.info("Command "+commandToExecute)
    
    try:
        os.system(commandToExecute)
        logger.info("removeService() : end")
    except Exception as e:
        logger.error("error occurred in removeService()")

if __name__ == '__main__':
    verboseHandle.printConsoleInfo("Removing Retention Manager service")
    
    removeService()