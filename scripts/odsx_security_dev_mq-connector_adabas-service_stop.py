#!/usr/bin/env python3
import argparse
import os
import sys

from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_servers_di_list import listDIServers
from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_dataIntegration_nodes, config_get_dataEngine_nodes
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36
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
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])


def getDEServerHostList():
    nodeList = config_get_dataEngine_nodes()
    nodes = ""
    for node in nodeList:
        # if(str(node.role).casefold() == 'server'):
        if node.role == "mq-connector":
            if (len(nodes) == 0):
                nodes = node.ip
            else:
                nodes = nodes + ',' + node.ip
    return nodes


def getAdabusServiceStatus(node):
    logger.info("getConsolidatedStatus() : " + str(node.ip))
    cmdList = ["systemctl status odsxadabas"]
    for cmd in cmdList:
        logger.info("cmd :" + str(cmd) + " host :" + str(node.ip))
        logger.info("Getting status.. :" + str(cmd))
        user = 'root'
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(node.ip, user, cmd)
            logger.info("output1 : " + str(output))
            if (output != 0):
                # verboseHandle.printConsoleInfo(" Service :"+str(cmd)+" not started.")
                logger.info(" Service :" + str(cmd) + " not started." + str(node.ip))
            return output


class obj_type_dictionary(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value


def listDEServers():
    logger.info("listDEServers()")
    host_dict_obj = obj_type_dictionary()
    dEServers = config_get_dataEngine_nodes("config/cluster.config")
    headers = [Fore.YELLOW + "Sr Num" + Fore.RESET,
               Fore.YELLOW + "Ip" + Fore.RESET,
               Fore.YELLOW + "Host" + Fore.RESET,
               Fore.YELLOW + "Status" + Fore.RESET]
    data = []
    counter = 1
    global adbas_host_dict
    adbas_host_dict = obj_type_dictionary()
    for node in dEServers:
        if node.role == "mq-connector":
            host_dict_obj.add(str(counter), str(node.ip))
            status = getAdabusServiceStatus(node)
            if (status == 0):
                dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                             Fore.GREEN + node.ip + Fore.RESET,
                             Fore.GREEN + node.name + Fore.RESET,
                             Fore.GREEN + "ON" + Fore.RESET]
            else:
                dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                             Fore.GREEN + node.ip + Fore.RESET,
                             Fore.GREEN + node.name + Fore.RESET,
                             Fore.RED + "OFF" + Fore.RESET]
            data.append(dataArray)
            adbas_host_dict.add(str(counter),str(node.ip))
            counter = counter + 1
    printTabular(None, headers, data)
    return host_dict_obj

def executeService(host):
    cmd = "systemctl stop odsxadabas.service"
    logger.info("Getting status.. odsxadabas:" + str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        if (output == 0):
            verboseHandle.printConsoleInfo("Service odsxadabas stopped successfully on " + str(host))
        else:
            verboseHandle.printConsoleError("Service odsxadabas failed to stop on " + str(host))

def stopAdabusService(args):
    try:
        listDEServers()
        inputChoice = str(input(Fore.YELLOW+"[1] For individual stop \n[Enter] For stop all servers \n[99] For exit \nEnter your choice : "+Fore.RESET))
        if(inputChoice=='1'):
            hostNumber = str(input(Fore.YELLOW+"Enter host number to stop : "+Fore.RESET))
            while(len(str(hostNumber))==0):
                hostNumber = str(input(Fore.YELLOW+"Enter host number to stop : "+Fore.RESET))
            host = adbas_host_dict.get(hostNumber)
            executeService(host)
        elif(len(str(inputChoice))==0):
            nodes = getDEServerHostList()
            choice = str(input(Fore.YELLOW + "Are you sure, you want to stop adabus service for [" + str(
                nodes) + "] ? (y/n) [y]: " + Fore.RESET))
            if choice.casefold() == 'n':
                exit(0)
            for node in config_get_dataIntegration_nodes():
                executeService(str(node.ip))
        elif(inputChoice=='99'):
            return
    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Security -> Dev -> MQ Connector -> Adabas Service -> Stop")
    args = []
    args = myCheckArg()
    stopAdabusService(args)
