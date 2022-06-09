#!/usr/bin/env python3
import argparse
import os
import sys

from scripts.logManager import LogManager
from scripts.odsx_servers_di_start import getDIhostTypeDict
from utils.ods_cluster_config import config_get_dataIntegration_nodes
from utils.ods_ssh import executeRemoteShCommandAndGetOutput, executeRemoteCommandAndGetOutputPython36
from scripts.spinner import Spinner
from colorama import Fore
from scripts.odsx_servers_di_list import listDIServers

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
            nodes = os.getenv(node.ip)
        else:
            nodes = nodes+','+os.getenv(node.ip)
    return nodes


def stopZookeeperServiceByHost(host):
    logger.info("stopZookeeperServiceByHost()")
    cmd = "systemctl stop odsxzookeeper.service; sleep 5;"
    logger.info("Getting status.. :"+str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        if (output == 0):
            verboseHandle.printConsoleInfo("Service zookeeper stopped successfully on node "+str(host))
        else:
            verboseHandle.printConsoleError("Service zookeeper failed to stop.")
    pass

def stopKafkaServiceByHost(host):
    logger.info("stopKafkaServiceByHost()")
    cmd = "systemctl stop odsxkafka.service; sleep 5;"
    logger.info("Getting status.. :"+str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        if (output == 0):
            verboseHandle.printConsoleInfo("Service kafka stopped successfully on node "+str(host))
        else:
            verboseHandle.printConsoleError("Service kafka failed to stop.")
    pass


def stopTelegrafServiceByHost(host):
    logger.info("stopTelegrafServiceByHost()")
    cmd = "systemctl stop telegraf"
    logger.info("Getting status.. telegraf :"+str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        if (output == 0):
            verboseHandle.printConsoleInfo("Service telegraf stopped successfully on "+str(host))
        else:
            verboseHandle.printConsoleError("Service telegraf failed to stop"+str(host))

def stopKafkaService(args):
    logger.info("stopKafkaService()")
    try:
        if choiceOption == '1':
            hostNumber = str(input(Fore.YELLOW+"Enter host number to stop kafka service : "+Fore.RESET))
            choice = str(input(Fore.YELLOW+"Are you sure want to stop kafka service on "+str(host_dict_obj.get(hostNumber))+" ? (y/n) [y]: "+Fore.RESET))
            if len(choice)==0:
                choice='y'
            if choice =='y':
                host_type_dict_obj = getDIhostTypeDict()
                nodeType = host_type_dict_obj.get(str(host_dict_obj.get(hostNumber)))
                if nodeType != "kafka Broker 1b" and nodeListSize==4:
                    stopZookeeperServiceByHost(str(host_dict_obj.get(hostNumber)))
                elif nodeListSize<4:
                    stopZookeeperServiceByHost(str(host_dict_obj.get(hostNumber)))
                if nodeType != "Zookeeper Witness":
                    stopKafkaServiceByHost(str(host_dict_obj.get(hostNumber)))
                elif nodeListSize<4:
                    stopKafkaService(str(host_dict_obj.get(hostNumber)))
                stopTelegrafServiceByHost(str(host_dict_obj.get(hostNumber)))
            else:
                exit(0)
        if choiceOption == "":
            choice = str(input(Fore.YELLOW+"Are you sure want to stop kafka service on "+str(nodes)+" ? (y/n) [y]: "+Fore.RESET))
            if choice.casefold() == 'n':
                exit(0)
            for node in config_get_dataIntegration_nodes():
                if node.type != "Zookeeper Witness" and nodeListSize==4:
                    stopKafkaServiceByHost(os.getenv(node.ip))
                elif nodeListSize<4:
                    stopKafkaServiceByHost(os.getenv(node.ip))
            for node in config_get_dataIntegration_nodes():
                if node.type != "kafka Broker 1b" and nodeListSize==4:
                    stopZookeeperServiceByHost(os.getenv(node.ip))
                elif nodeListSize<4:
                    stopZookeeperServiceByHost(os.getenv(node.ip))
            for node in config_get_dataIntegration_nodes():
                stopTelegrafServiceByHost(os.getenv(node.ip))

    except Exception as e:
        handleException(e)

if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Servers -> DI -> Stop")
    args = []
    args = myCheckArg()
    global choiceOption
    global host_dict_obj
    global nodeListSize
    nodeListSize = len(str((getDIServerHostList())).split(','))
    host_dict_obj = listDIServers()
    nodes = getDIServerHostList()
    verboseHandle.printConsoleWarning("Current configurations ["+str(nodes)+"]")
    choiceOption = str(input(Fore.YELLOW+"Press [1] Individual stop\nPress [Enter] Stop current configuration.\nPress [99] For exit.:"+Fore.RESET))
    if choiceOption == "99":
        exit(0)
    stopKafkaService(args)
