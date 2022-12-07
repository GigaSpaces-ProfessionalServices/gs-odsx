#!/usr/bin/env python3
# !/usr/bin/python
# to remove space

import argparse
import os
import sys

from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_grafana_list, config_get_influxdb_node
from utils.ods_list import getGrafanaServerDetails, getInfluxdbServerDetails
from utils.odsx_print_tabular_data import printTabular

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
    parser.add_argument('-dryrun', '--dryrun',
                        help='Dry run flag',
                        default='false', action='store_true')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])

def listGrafana():
    logger.debug("listing Grafana servers")
    grafanaServers = config_get_grafana_list()
    influxdbServers = config_get_influxdb_node()
    verboseHandle.printConsoleWarning("Menu -> Servers -> Grafana -> List\n")
    headers = [Fore.YELLOW+"IP"+Fore.RESET,
               Fore.YELLOW+"Host"+Fore.RESET,
               Fore.YELLOW+"Role"+Fore.RESET,
               Fore.YELLOW+"Installed"+Fore.RESET,
               Fore.YELLOW+"Status"+Fore.RESET]
    data=[]
    dataArray = getGrafanaServerDetails(grafanaServers)
    # To display Influxdb information in Grafana list
    influxdbDataArray = getInfluxdbServerDetails(influxdbServers)
    if(len(dataArray)>0):
        data.append(dataArray)
    if(len(influxdbDataArray)>0):
        data.append(influxdbDataArray)

    printTabular(None,headers,data)
if __name__ == '__main__':
    try:
        args = []
        menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
        args.append(sys.argv[0])
        myCheckArg()
        with Spinner():
            listGrafana()
    except Exception as e:
        handleException(e)
