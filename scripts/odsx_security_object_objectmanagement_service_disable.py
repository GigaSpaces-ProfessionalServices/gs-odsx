#!/usr/bin/env python3
import argparse
import os
import signal
import sys

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_cleanup import signal_handler
from utils.ods_ssh import executeLocalCommandAndGetOutput
from colorama import Fore

from utils.odsx_keypress import userInputWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
serviceName = 'object-management.service'

def checkServiceExists():
    logger.info("serviceExists()")
    cmd = "systemctl list-unit-files "+serviceName+" | wc -l"
    output = executeLocalCommandAndGetOutput(cmd)
    logger.info("serviceExists() : output =>"+str(output))
    if(output > 3):
        return 1
    else:
        return 0

def stopService():
    logger.info("stopService()")

    confirmMsg = Fore.YELLOW + "Are you sure, you want to stop Object Management service ? (Yes/No) [Yes] :"+Fore.RESET 

    choice = str(userInputWrapper(confirmMsg))

    while(len(choice) > 0 and choice.casefold()!='yes' and choice.casefold()!='no'):
        verboseHandle.printConsoleError("Invalid input")
        choice = str(input(confirmMsg))

    if choice.casefold() == 'no':
        exit(0)

    os.system('sudo systemctl daemon-reload')
    
    status = os.system('systemctl is-active --quiet '+serviceName)
    if(status!=0):
        verboseHandle.printConsoleError("Service is already stopped!")
        exit(0)

    with Spinner():
        executeLocalCommandAndGetOutput("sudo systemctl stop --quiet "+serviceName)
    status = os.system('systemctl is-active --quiet '+serviceName)
    if (status == 0):
        verboseHandle.printConsoleError("Service is failed to stop")
    else:
        verboseHandle.printConsoleInfo("Service is stopped successfully!!")

    


if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Object -> ObjectManagement -> Service -> Disable")
    signal.signal(signal.SIGINT, signal_handler)
    stopService()
