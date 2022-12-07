#!/usr/bin/env python3

import os

from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36
from utils.odsx_keypress import userInputWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR

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

def stopKapacitorServiceByHost(host):
    logger.info("stopKapacitorServiceByHost()")
    cmd = "systemctl stop kapacitor.service;sleep 5; "
    logger.info("Getting status.. kapacitor :"+str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        if (output == 0):
            verboseHandle.printConsoleInfo("Service Kapacitor stopped successfully on "+str(host))
        else:
            verboseHandle.printConsoleError("Service Kapacitor failed to stop on "+str(host))


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Monitors -> Alerts -> Services -> Kapacitor -> Stop')
    try:
        host = os.getenv("pivot1")
        confirmInstall = str(userInputWrapper(Fore.YELLOW+"Are you sure want to stop Kapacitor (y/n) [y]: "+Fore.RESET))
        if(len(str(confirmInstall))==0):
            confirmInstall='y'
        if(confirmInstall=='y'):
           stopKapacitorServiceByHost(host)
    except Exception as e:
        handleException(e)