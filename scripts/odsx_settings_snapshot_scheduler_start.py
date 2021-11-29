#!/usr/bin/env python3
import sys
import argparse
import os
from scripts.logManager import LogManager
from utils.ods_scheduler_status import startScheduler
from utils.ods_scheduler_status import getSchedulerStatus
from colorama import Fore

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR

def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])


def start_scheduler():
    verboseHandle.printConsoleWarning("Settings -> Snapshot -> Scheduler -> Start")
    startScheduler()
    status = getSchedulerStatus()
    if(status.casefold()=='running'):
        print('Scheduler Status :'+Fore.GREEN+ status+Fore.RESET)
    elif(status.casefold()=='stopped'):
        print('Scheduler Status :'+Fore.RED+ status+Fore.RESET)

if __name__ == '__main__':
    args = []
    args = myCheckArg()
    print(args)
    start_scheduler()
