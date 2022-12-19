#!/usr/bin/env python3
import argparse
import os
import sys

from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_servers_di_list import listDIServers
from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_dataIntegration_nodes
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36
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

class obj_type_dictionary(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

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
            nodes = nodes+','+str(os.getenv(node.ip))
    return nodes

def getDIhostTypeDict():
    global host_type_dict_obj
    host_type_dict_obj = obj_type_dictionary()
    nodeList = config_get_dataIntegration_nodes()
    nodes=""
    for node in nodeList:
        #if(str(node.role).casefold() == 'server'):
        host_type_dict_obj.add(os.getenv(node.ip),node.type)

    return host_type_dict_obj

def startZookeeperServiceByHost(host):
        cmd = "rm -rf /var/log/kafka/*;sleep 5; systemctl start odsxzookeeper.service"
        logger.info("Getting status.. odsxzookeeper:"+str(cmd))
        user = 'root'
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
            if (output == 0):
                verboseHandle.printConsoleInfo("Service zookeeper started successfully on "+str(host))
            else:
                verboseHandle.printConsoleError("Service zookeeper failed to start on "+str(host))


def startKafkaServiceByHost(host):
    logger.info("startKafkaServiceByHost()")
    cmd = "rm -rf /var/log/kafka/*;sleep 5; systemctl start odsxkafka.service;/dbagiga/di-flink/latest-flink/bin/start-cluster.sh;systemctl start di-flink-taskmanager.service;systemctl start di-flink-jobmanager.service"
    logger.info("Getting status.. odsxkafka :"+str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        if (output == 0):
            verboseHandle.printConsoleInfo("Service kafka started successfully on "+str(host))
        else:
            verboseHandle.printConsoleError("Service kafka failed to start on "+str(host))


def startTelegrafServiceByHost(host):
    logger.info("startTelegrafServiceByHost()")
    cmd = "systemctl start telegraf"
    logger.info("Getting status.. telegraf :"+str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        if (output == 0):
            verboseHandle.printConsoleInfo("Service telegraf started successfully on "+str(host))
        else:
            verboseHandle.printConsoleError("Service telegraf failed to start on "+str(host))


def startDIMServices(host):
    logger.info("startTelegrafServiceByHost()")
    cmd = "systemctl start di-manager;sleep 3;systemctl start di-mdm;sleep 3;"
    logger.info("Getting status.. telegraf :"+str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        if (output == 0):
            verboseHandle.printConsoleInfo("Services di-manager/di-mdm/di-flink started successfully on "+str(host))
        else:
            verboseHandle.printConsoleError("Service di-manager/di-mdm/di-flink telegraf failed to start on "+str(host))


def startKafkaService(args):
    try:

        if choiceOption == '1':
            hostNumber = str(userInputWrapper(Fore.YELLOW+"Enter host number to start kafka service : "+Fore.RESET))
            choice = str(userInputWrapper(Fore.YELLOW+"Are you sure want to start kafka service on "+str(host_dict_obj.get(hostNumber))+" ? (y/n) [y]: "+Fore.RESET))
            if len(choice)==0:
                choice='y'
            if choice =='y':
                getDIhostTypeDict()
                nodeType = host_type_dict_obj.get(str(host_dict_obj.get(hostNumber)))
                if nodeType != "kafka Broker 1b" and nodeListSize==4:
                    startZookeeperServiceByHost(str(host_dict_obj.get(hostNumber)))
                elif nodeListSize<4:
                    startZookeeperServiceByHost(str(host_dict_obj.get(hostNumber)))
                if nodeType != "Zookeeper Witness":
                    startKafkaServiceByHost(str(host_dict_obj.get(hostNumber)))
                elif nodeListSize<4:
                    startKafkaService(str(host_dict_obj.get(hostNumber)))
                startTelegrafServiceByHost(str(host_dict_obj.get(hostNumber)))
                startDIMServices(str(host_dict_obj.get(hostNumber)))
            else:
                exit(0)

        if choiceOption == "":
            choice = str(userInputWrapper(Fore.YELLOW+"Are you sure want to start kafka service on "+str(nodes)+" ? (y/n) [y]: "+Fore.RESET))
            if choice.casefold() == 'n':
                exit(0)
            #print(nodeListSize)
            for node in config_get_dataIntegration_nodes():
                if node.type != "kafka Broker 1b" and nodeListSize==4:
                    startZookeeperServiceByHost(os.getenv(node.ip))
                elif nodeListSize<4:
                    startZookeeperServiceByHost(os.getenv(node.ip))
            for node in config_get_dataIntegration_nodes():
                if node.type != "Zookeeper Witness":
                    startKafkaServiceByHost(os.getenv(node.ip))
                elif nodeListSize<4:
                    startKafkaService(os.getenv(node.ip))
            for node in config_get_dataIntegration_nodes():
                startTelegrafServiceByHost(os.getenv(node.ip))
                startDIMServices(os.getenv(node.ip))
    except Exception as e:
        handleException(e)

if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Servers -> DI -> Start")
    args = []
    args = myCheckArg()
    global choiceOption
    global host_dict_obj
    nodeListSize = len(str((getDIServerHostList())).split(','))
    host_dict_obj = listDIServers()
    nodes = getDIServerHostList()
    verboseHandle.printConsoleWarning("Current configurations ["+str(nodes)+"]")
    choiceOption = str(userInputWithEscWrapper(Fore.YELLOW+"Press [1] Individual start\nPress [Enter] Start current configuration.\nPress [99] For exit.:"+Fore.RESET))
    if choiceOption == "99":
        exit(0)
    startKafkaService(args)
