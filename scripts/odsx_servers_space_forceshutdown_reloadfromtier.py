#!/usr/bin/env python3

import argparse
from logging import exception
import os
import re
from shutil import ExecError
import pexpect
import sys
from utils.ods_app_config import getYamlFilePathInsideFolder, readValuefromAppConfig
from utils.odsx_print_tabular_data import printTabular
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_manager_node, config_get_nb_list, config_get_space_hosts_list
from colorama import Fore
from utils.ods_validation import getSpaceServerStatus
from scripts.spinner import Spinner
from utils.ods_ssh import executeRemoteCommandAndGetOutput 
import requests, json

from utils.odsx_space_shutdown_reload_utilities import checkSpacePrimaryStatus, deployFeeders, getManagerHost, startSpaceServers

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
user='root'
class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR
    BLUE = '\033[94m'
    BOLD = '\033[1m'

def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    parser.add_argument('-dryrun', '--dryrun',
                        help='Dry run flag',
                        default='false', action='store_true')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])

def handleException(e):
    logger.info("handleException()")
    trace = []
    tb = e.__traceback__
    while tb is not None:
        trace.append({
            "filename": tb.tb_frame.f_code.co_filename,
            "name": tb.tb_frame.f_code.co_name,
            "lineno": tb.tb_lineno
        })
        tb = tb.tb_next
    logger.error(str({
        'type': type(e).__name__,
        'message': str(e),
        'trace': trace
    }))
    verboseHandle.printConsoleError((str({
        'type': type(e).__name__,
        'message': str(e),
        'trace': trace
    })))


def reloadSpaces():
    logger.info("reloadSpaces() : start")
    global managerHost

    
    managerHost = getManagerHost()
    startSpaceServers(user)

    #python_code = __import__('odsx_dataengine_db2-feeder_install-deploy')
    #python_code.installFeeder(True)
    #os.system("python3 scripts/odsx_dataengine_db2-feeder_install-deploy.py")
    checkSpacePrimaryStatus(managerHost)
    deployFeeders()
    """
    isSpaceIntact = checkSpaceStatus()
    if(isSpaceIntact == True):
        deployFeeders()
    
   
    """
    
    logger.info("reloadSpaces() : end")
    #except Exception as e:
    #    logger.error("error occurred in shutdownServers()")

if __name__ == '__main__':
    args = []
    menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
    args.append(sys.argv[0])
    myCheckArg()
    #with Spinner():
    reloadSpaces()
