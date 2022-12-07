#!/usr/bin/env python3
import os
import signal

from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_cleanup import signal_handler
from utils.odsx_keypress import userInputWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
serviceName = "retention-manager.service";
user = "root"

def removeService():
    logger.info("removeService() : start")

    confirmMsg = Fore.YELLOW + "Are you sure, you want to remove Retention Manager service ? (Yes/No) [Yes]:" + Fore.RESET
    
    choice = str(userInputWrapper(confirmMsg))

    while(len(choice) > 0 and choice.casefold()!='yes' and choice.casefold()!='no'):
        verboseHandle.printConsoleError("Invalid input")
        choice = str(userInputWrapper(confirmMsg))

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
    verboseHandle.printConsoleWarning("Menu -> Object -> RetentionManager -> Service -> Remove")
    signal.signal(signal.SIGINT, signal_handler)
    removeService()