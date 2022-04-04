#!/usr/bin/env python3
import argparse
import os
import sys

from utils.ods_scp import scp_upload
from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_ssh import executeLocalCommandAndGetOutput
from colorama import Fore


verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
serviceName = "catalogue-service.service";

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
    parser = argparse.ArgumentParser(description='Script to remove Catalogue service')
    parser.add_argument('m', nargs='?')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])

def removeService():
    logger.info("removeService() started")

    confirmMsg = Fore.YELLOW + "Are you sure, you want to remove Catalogue service ? (Yes/No) [Yes]:" + Fore.RESET
    
    choice = str(input(confirmMsg))

    while(len(choice) > 0 and choice.casefold()!='yes' and choice.casefold()!='no'):
        verboseHandle.printConsoleError("Invalid input")
        choice = str(input(confirmMsg))

    if choice.casefold() == 'no':
        exit(0)


    commandToExecute = "scripts/settings_catalogueService_remove.sh"
    logger.info("Command "+commandToExecute)
    
    try:
        os.system(commandToExecute)
        logger.info("removeService() completed")
    except Exception as e:
        logger.error("error occurred in removeService()")

if __name__ == '__main__':
    verboseHandle.printConsoleInfo("Removing Catalogue service")
    args = []
    args = myCheckArg()
    removeService()
