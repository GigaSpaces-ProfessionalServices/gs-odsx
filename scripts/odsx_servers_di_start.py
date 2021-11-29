#!/usr/bin/env python3
import argparse
import os
import sys
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_dataIntegration_nodes
from utils.ods_ssh import executeRemoteShCommandAndGetOutput, executeRemoteCommandAndGetOutputPython36
from scripts.spinner import Spinner

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

def getDIServerHostList():
    nodeList = config_get_dataIntegration_nodes()
    nodes=""
    for node in nodeList:
        #if(str(node.role).casefold() == 'server'):
        if(len(nodes)==0):
            nodes = node.ip
        else:
            nodes = nodes+','+node.ip
    return nodes

def startKafkaService(args):
    try:
        nodes = getDIServerHostList()
        choice = str(input(Fore.YELLOW+"Are you sure, you want to start kafka service for ["+str(nodes)+"] ? (y/n)"+Fore.RESET))
        if choice.casefold() == 'n':
            exit(0)
        for node in config_get_dataIntegration_nodes():
            cmd = "systemctl start odsxkafka.service"
            logger.info("Getting status.. :"+str(cmd))
            user = 'root'
            with Spinner():
                output = executeRemoteCommandAndGetOutputPython36(node.ip, user, cmd)
                if (output == 0):
                    verboseHandle.printConsoleInfo("Service started successfully on "+str(node.ip))
                else:
                    verboseHandle.printConsoleError("Service failed to start")
    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Servers -> DI -> Start")
    args = []
    args = myCheckArg()
    startKafkaService(args)
