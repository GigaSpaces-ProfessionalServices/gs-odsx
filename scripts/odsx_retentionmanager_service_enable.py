#!/usr/bin/env python3
import argparse
import os
import sys

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_ssh import executeLocalCommandAndGetOutput
from colorama import Fore

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
serviceName = "retention-manager.service";

def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to start Retention Manager Service')
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

def startService(args):

    logger.info("startService()")
    
    confirmMsg = Fore.YELLOW + "Are you sure, you want to start Retention Manager service ? (Yes/No) [Yes]:" + Fore.RESET
    
    choice = str(input(confirmMsg))

    while(len(choice) > 0 and choice.casefold()!='yes' and choice.casefold()!='no'):
        verboseHandle.printConsoleError("Invalid input")
        choice = str(input(confirmMsg))

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
    verboseHandle.printConsoleInfo("Starting Retention Manager service")
    args = []
    args = myCheckArg()
    startService(args)
