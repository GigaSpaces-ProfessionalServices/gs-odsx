#!/usr/bin/env python3
import argparse
import os
import sys

from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_datavalidator_install_list import listDVServers
from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_dataValidation_nodes
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36
from utils.odsx_keypress import userInputWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR

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


def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])

def getDVServerHostList():
    nodeList = config_get_dataValidation_nodes()
    nodes=""
    for node in nodeList:
        #if(str(node.role).casefold() == 'server'):
        if(len(nodes)==0):
            nodes = os.getenv(node.ip)
        else:
            nodes = nodes+','+os.getenv(node.ip)
    return nodes

def stopDataValidationService(args):
    try:
        listDVServers()
        nodes = getDVServerHostList()
        choice = str(userInputWrapper(Fore.YELLOW+"Are you sure, you want to stop data validation service for ["+str(nodes)+"] ? (y/n)"+Fore.RESET))
        if choice.casefold() == 'n':
            exit(0)
        for node in config_get_dataValidation_nodes():
            cmd = "systemctl stop odsxdatavalidation.service"
            logger.info("Getting status.. odsxdatavalidation:"+str(cmd))
            user = 'root'
            with Spinner():
                output = executeRemoteCommandAndGetOutputPython36(os.getenv(node.ip), user, cmd)
                if (output == 0):
                    verboseHandle.printConsoleInfo("Service data validation stop successfully on "+str(os.getenv(node.ip)))
                else:
                    verboseHandle.printConsoleError("Service data validation failed to stop")


    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> DataValidator -> Install -> Stop")
    args = []
    args = myCheckArg()
    stopDataValidationService(args)
