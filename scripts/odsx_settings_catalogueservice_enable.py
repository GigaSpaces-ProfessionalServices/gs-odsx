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

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
serviceName = "catalogue-service.service";

def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to start Catalogue Service')
    parser.add_argument('m', nargs='?')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])

def checkServiceExists():
    logger.info("serviceExists()")
    cmd = "systemctl list-unit-files "+serviceName+" | wc -l"
    verboseHandle.printConsoleError(cmd)
    output = os.system(cmd)
    logger.info("serviceExists() : output =>"+str(output))
    verboseHandle.printConsoleInfo("serviceExists() : output =>"+str(output))
    if(int(output) > 3):
        return 1
    else:
        return 0

def startCatalogueService(args):

    logger.info("startCatalogueService()")
    
    confirmMsg = Fore.YELLOW + "Are you sure, you want to start Catalogue service ? (Yes/No) [Yes]:" + Fore.RESET

    from utils.odsx_keypress import userInputWrapper
    choice = str(userInputWrapper(confirmMsg))

    while(len(choice) > 0 and choice.casefold()!='yes' and choice.casefold()!='no'):
        verboseHandle.printConsoleError("Invalid input")
        from utils.odsx_keypress import userInputWrapper
        choice = str(userInputWrapper(confirmMsg))

    if choice.casefold() == 'no':
        exit(0)

    os.system('sudo systemctl daemon-reload')

    status = os.system('systemctl is-active --quiet '+serviceName)
    
    if(status==0):
        verboseHandle.printConsoleError("Service is already started!")
        exit(0)

    with Spinner():
        executeLocalCommandAndGetOutput("sudo systemctl start --quiet "+serviceName)
    status = os.system('systemctl is-active --quiet '+serviceName)
    if (status == 0):
        verboseHandle.printConsoleInfo("Service is started successfully!!")
    else:
        verboseHandle.printConsoleError("Service is failed to start")


if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Settings -> CatalogueService -> Enable")
    args = []
    args = myCheckArg()
    signal.signal(signal.SIGINT, signal_handler)
    startCatalogueService(args)
