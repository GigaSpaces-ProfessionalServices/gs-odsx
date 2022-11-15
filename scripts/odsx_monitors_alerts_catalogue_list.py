#!/usr/bin/env python3
import glob
import os
import platform
from os import path
from colorama import Fore

from scripts.odsx_monitors_alerts_services_kapacitor_list import getStatusOfKapacitor
from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_ssh import connectExecuteSSH, executeRemoteCommandAndGetOutputPython36, \
    executeRemoteCommandAndGetOutputValuePython36
from utils.ods_scp import scp_upload
from utils.ods_cluster_config import config_get_grafana_node
from utils.ods_app_config import set_value_in_property_file, readValuefromAppConfig

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

def listCatalogue():
    host = os.getenv("pivot1")
    status=getStatusOfKapacitor(host)
    if status=="ON":
        commandToExecute='kapacitor list tasks'
        logger.info("commandToExecute :"+str(commandToExecute))
        outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
        print(Fore.GREEN+str(outputShFile)+Fore.RESET)
        logger.info("outputShFile :"+str(outputShFile))
    else:
        verboseHandle.printConsoleInfo("Kapacitor status is off. Please start kapacitor on host."+str(host))

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Monitors -> Alerts -> Catalogue -> List')
    try:
        listCatalogue()
    except Exception as e:
        handleException(e)