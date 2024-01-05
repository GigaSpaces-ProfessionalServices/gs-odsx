#!/usr/bin/env python3
import argparse
import os
import sys
import sqlite3
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_dataIntegration_nodes, config_get_dataValidation_nodes
from utils.ods_ssh import executeRemoteShCommandAndGetOutput, executeRemoteCommandAndGetOutputPython36
from scripts.spinner import Spinner
from scripts.odsx_datavalidator_install_list import listDVAgents, listDVServers, getConsolidatedStatus, \
    isServiceInstalled
from utils.odsx_keypress import userInputWithEscWrapper, userInputWrapper

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
        output = getConsolidatedStatus(os.getenv(node.ip))
        if (output == 0):
            continue
        #if(str(node.role).casefold() == 'server'):
        if(len(nodes)==0):
            nodes = os.getenv(node.ip)
        else:
            nodes = nodes+','+os.getenv(node.ip)
    return nodes

def startDataValidationService(args):
    try:
        host_dict_obj = listDVServers()
        #listDVAgents()
        serverStartType = str(userInputWithEscWrapper(Fore.YELLOW+"press [1] if you want to start individual server. \nPress [Enter] to start all servers. \nPress [99] for exit.: "+Fore.RESET))
        if(serverStartType=='1'):
            optionMainMenu = int(userInputWrapper("Enter host Sr Number to start: "))
            if len(host_dict_obj) >= optionMainMenu:
                hostToStart = host_dict_obj.get(str(optionMainMenu))
                hostType = hostToStart[1]
                hostToStart = hostToStart[0]
                # start individual
                if len(str(isServiceInstalled(hostToStart,hostType)))>0:
                    cmd = "systemctl start odsxdatavalidation"+hostType+".service"
                    logger.info("Getting status.. odsxdatavalidation"+hostType+":"+str(cmd))
                    user = 'root'
                    with Spinner():
                        output = executeRemoteCommandAndGetOutputPython36(hostToStart, user, cmd)
                        if (output == 0):
                            verboseHandle.printConsoleInfo("Service data validation started successfully on "+str(hostToStart))
                        else:
                            verboseHandle.printConsoleError("Service data validation failed to start on "+str(hostToStart))
                else:
                    verboseHandle.printConsoleError("No service installed for host:"+str(hostToStart))
        elif(serverStartType =='99'):
            logger.info("99 - Exist start")
        else:
            confirm=''
            confirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to start all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            while(len(str(confirm))==0):
                confirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to start all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            logger.info("confirm :"+str(confirm))
            if(confirm=='yes' or confirm=='y'): # Start all
                for node in config_get_dataValidation_nodes():
                    output = getConsolidatedStatus(os.getenv(node.ip),str(node.type))
                    if (output == 0):
                        continue
                    if len(str(isServiceInstalled(os.getenv(node.ip), str(node.type))))>0:
                        cmd = "systemctl start odsxdatavalidation"+str(node.type)+".service"
                        logger.info("Getting status.. odsxdatavalidation"+str(node.type)+":"+str(cmd))
                        user = 'root'
                        with Spinner():
                            output = executeRemoteCommandAndGetOutputPython36(os.getenv(node.ip), user, cmd)
                            if (output == 0):
                                verboseHandle.printConsoleInfo("Service data validation started successfully on "+str(os.getenv(node.ip)))
                            else:
                                verboseHandle.printConsoleError("Service data validation failed to start on "+str(os.getenv(node.ip)))
                    else:
                        verboseHandle.printConsoleError("No service installed for host:"+str(os.getenv(node.ip)))
            else:
                exit(0)

    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> DataValidator -> Install -> Start")
    args = []
    args = myCheckArg()
    startDataValidationService(args)