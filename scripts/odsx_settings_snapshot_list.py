#!/usr/bin/env python3
import argparse
import os.path
import sys
from utils.odsx_print_tabular_data import printTabular
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import get_cluster_obj

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


def listFileFromDirectory():
    logger.debug("Showing snapshots current version and backups")
    # if(inputDirectory==''):
    inputDirectory = readValuefromAppConfig("cluster.config.snapshot.backup.path", verboseHandle.verboseFlag)
    verboseHandle.printConsoleWarning('Settings -> Backup -> List')
    print('\n')
    headers = [Fore.YELLOW+"Filename"+Fore.RESET,
               Fore.YELLOW+"Version"+Fore.RESET,
               Fore.YELLOW+"TimeStamp"+Fore.RESET
               ]
    data=[]
    config_data = get_cluster_obj(verbose=verboseHandle.verboseFlag)
    dataArrayCurrent=[Fore.GREEN+"cluster.config"+Fore.RESET,Fore.GREEN+config_data.cluster.configVersion+"Current"+Fore.RESET,Fore.GREEN+ config_data.cluster.timestamp+Fore.RESET]
    data.append(dataArrayCurrent)
    for filename in os.listdir(inputDirectory):
        config_data = get_cluster_obj(os.path.join(inputDirectory, filename))
        dataArray=[Fore.GREEN+filename+Fore.RESET,
                   Fore.GREEN+config_data.cluster.configVersion+Fore.RESET,
                   Fore.GREEN+config_data.cluster.timestamp+Fore.RESET
                   ]
        data.append(dataArray)
    printTabular(None,headers,data)

if __name__ == "__main__":
    myCheckArg()
    listFileFromDirectory()
