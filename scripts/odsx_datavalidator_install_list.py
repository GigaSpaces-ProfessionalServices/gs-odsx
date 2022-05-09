import argparse, subprocess
import os
import sys
import sqlite3

from utils.ods_validation import getSpaceServerStatus, getDataValidationServerStatus
from utils.odsx_print_tabular_data import printTabular
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_dataIntegration_nodes, config_get_dataValidation_nodes
from colorama import Fore
from scripts.spinner import Spinner
from utils.ods_ssh import executeRemoteCommandAndGetOutput, executeRemoteCommandAndGetOutputPython36

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


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


class obj_type_dictionary(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value


class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR


def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    parser.add_argument('-dryrun', '--dryrun',
                        help='Dry run flag',
                        default='false', action='store_true')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])


def getConsolidatedStatus(ip):
    output = ''
    logger.info("getConsolidatedStatus() : " + str(ip))
    cmdList = ["systemctl status odsxdatavalidation"]
    for cmd in cmdList:
        logger.info("cmd :" + str(cmd) + " host :" + str(ip))
        logger.info("Getting status.. :" + str(cmd))
        user = 'root'
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(ip, user, cmd)
            logger.info("output1 : " + str(output))
            if (output != 0):
                # verboseHandle.printConsoleInfo(" Service :"+str(cmd)+" not started.")
                logger.info(" Service :" + str(cmd) + " not started." + str(ip))
                return output
    return output


def listDVServers():
    logger.info("listDVServers()")
    host_dict_obj = obj_type_dictionary()
    dVServers = config_get_dataValidation_nodes()
    headers = [Fore.YELLOW + "Sr Num" + Fore.RESET,
               Fore.YELLOW + "Host Ip" + Fore.RESET,
               Fore.YELLOW + "Type" + Fore.RESET,
               Fore.YELLOW + "Role" + Fore.RESET,
               Fore.YELLOW + "Status" + Fore.RESET]
    data = []
    counter = 1
    for node in dVServers:
        host_dict_obj.add(str(counter), str(node.ip))
        output = getConsolidatedStatus(node.ip)
        if (output == 0):
            dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                         Fore.GREEN + node.ip + Fore.RESET,
                         Fore.GREEN + node.type + Fore.RESET,
                         Fore.GREEN + node.role + Fore.RESET,
                         Fore.GREEN + "ON" + Fore.RESET]
        else:
            dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                         Fore.GREEN + node.ip + Fore.RESET,
                         Fore.GREEN + node.type + Fore.RESET,
                         Fore.GREEN + node.role + Fore.RESET,
                         Fore.RED + "OFF" + Fore.RESET]
        data.append(dataArray)
        counter = counter + 1
    printTabular(None, headers, data)
    return host_dict_obj

def listDVAgents():
    headers = [Fore.YELLOW + "Sr Num" + Fore.RESET,
           Fore.YELLOW + "Name" + Fore.RESET,
           Fore.YELLOW + "Type" + Fore.RESET,
           Fore.YELLOW + "Role" + Fore.RESET,
           Fore.YELLOW + "Status" + Fore.RESET]
    data = []
    counter = 1

    dbPath = "datavalidator.db"
    con = sqlite3.connect(dbPath)
    cur = con.cursor()
    cur.execute("SELECT * FROM agents")
    rows = cur.fetchall()
    for row in rows:
        output = getConsolidatedStatus(row[1])
        if (output == 0):
            dataArray = [Fore.GREEN + str(row[0]) + Fore.RESET,
                         Fore.GREEN + row[1] + Fore.RESET,
                         Fore.GREEN + 'Data Validation' + Fore.RESET,
                         Fore.GREEN + 'Agent' + Fore.RESET,
                         Fore.GREEN + "ON" + Fore.RESET]
        else:
            dataArray = [Fore.GREEN + str(row[0]) + Fore.RESET,
                         Fore.GREEN + row[1] + Fore.RESET,
                         Fore.GREEN + 'Data Validation' + Fore.RESET,
                         Fore.GREEN + 'Agent' + Fore.RESET,
                         Fore.RED + "OFF" + Fore.RESET]
        data.append(dataArray)
        counter = counter + 1
    printTabular(None, headers, data)

def getDataValidationHost(dataValidationNodes):
    logger.info("getDataValidationHost()")
    dataValidationHost = ""
    status = ""
    try:
        logger.info("getDataValidationHost() : dataValidationNodes :" + str(dataValidationNodes))
        for node in dataValidationNodes:
            if(node.role == 'Server'):
                status = getDataValidationServerStatus(node.ip,"7890")
                if (status == "ON"):
                    dataValidationHost = node.ip
        return dataValidationHost
    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataValidator -> Install -> List')
    try:
        args = []
        menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
        args.append(sys.argv[0])
        myCheckArg()
        listDVServers()
        #listDVAgents()
    except Exception as e:
        handleException(e)
