#!/usr/bin/env python3

import os
import platform
from os import path
from colorama import Fore

from scripts.odsx_monitors_alerts_services_kapacitor_list import getStatusOfKapacitor
from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_ssh import connectExecuteSSH, executeRemoteCommandAndGetOutputPython36
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

def reloadedKapacitorServiceByHost(host):
    logger.info("reloadedKapacitorServiceByHost()")
    cmd = "systemctl stop kapacitor.service;sleep 5;systemctl start kapacitor.service;sleep 2;"
    logger.info("Getting status.. kapacitor :"+str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        if (output == 0):
            verboseHandle.printConsoleInfo("Service Kapacitor restarted successfully on "+str(host))
        else:
            verboseHandle.printConsoleError("Service Kapacitor failed to reloaded on "+str(host))


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Monitors -> Alerts -> Services -> Kapacitor -> Restart')
    try:
        host = os.getenv("pivot1")
        status=getStatusOfKapacitor(host)
        if status=="ON":
            confirmInstall = str(input(Fore.YELLOW+"Are you sure want to restart Kapacitor (y/n) [y]: "+Fore.RESET))
            if(len(str(confirmInstall))==0):
                confirmInstall='y'
            if(confirmInstall=='y'):
                reloadedKapacitorServiceByHost(host)
        else:
            verboseHandle.printConsoleInfo("Kapacitor status is off. Please start kapacitor on host."+str(host))
    except Exception as e:
        handleException(e)