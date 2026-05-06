#!/usr/bin/env python3
import argparse
import os
import sys

from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_servers_di_list import listDIServers
from scripts.odsx_servers_di_start import getDIhostTypeDict
from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_dataIntegration_nodes, config_get_dataIntegrationiidr_nodes
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


def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])

def getDIServerHostList():
    nodeList = config_get_dataIntegration_nodes()
    nodes=""
    for node in nodeList:
        if(len(nodes)==0):
            nodes = os.getenv(node.ip)
        else:
            nodes = nodes+','+os.getenv(node.ip)
    return nodes


def stopSubscriptionManagerOnIIDR():
    logger.info("stopSubscriptionManagerOnIIDR()")
    user = 'root'
    nodeiidrList = config_get_dataIntegrationiidr_nodes()
    for node in nodeiidrList:
        iidrHost = os.getenv(node.ip)
        cmd = "sudo systemctl stop di-subscription-manager-iidr.service"
        logger.info("Stopping di-subscription-manager-iidr on " + str(iidrHost))
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(iidrHost, user, cmd)
            if output == 0:
                verboseHandle.printConsoleInfo("Service di-subscription-manager-iidr stopped successfully on " + str(iidrHost))
            else:
                verboseHandle.printConsoleError("Service di-subscription-manager-iidr failed to stop on " + str(iidrHost))


def stopZookeeperServiceByHost(host):
    logger.info("stopZookeeperServiceByHost()")
    cmd = "sudo systemctl stop odsxzookeeper.service"
    logger.info("Stopping odsxzookeeper on "+str(host)+": "+str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        if (output == 0):
            verboseHandle.printConsoleInfo("Service zookeeper stopped successfully on node "+str(host))
        else:
            verboseHandle.printConsoleError("Service zookeeper failed to stop on "+str(host))

def stopKafkaServiceByHost(host):
    logger.info("stopKafkaServiceByHost()")
    cmd = "sudo systemctl stop odsxkafka.service"
    logger.info("Stopping odsxkafka on "+str(host)+": "+str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        if (output == 0):
            verboseHandle.printConsoleInfo("Service kafka stopped successfully on node "+str(host))
        else:
            verboseHandle.printConsoleError("Service kafka failed to stop on "+str(host))


def stopTelegrafServiceByHost(host):
    logger.info("stopTelegrafServiceByHost()")
    cmd = "sudo systemctl stop telegraf"
    logger.info("Stopping telegraf on "+str(host)+": "+str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        if (output == 0):
            verboseHandle.printConsoleInfo("Service telegraf stopped successfully on "+str(host))
        else:
            verboseHandle.printConsoleError("Service telegraf failed to stop on "+str(host))

def stopDIMServices(host):
    logger.info("stopDIMServices()")
    # Stop order: di-transformations first, then di-manager, then di-mdm, then flink
    cmd = "sudo systemctl stop dih-admin.service;sleep 3;sudo systemctl stop di-transformations.service;sleep 3;sudo systemctl stop di-processor.service;sleep 3;sudo systemctl stop di-manager.service;sleep 3;sudo systemctl stop di-mdm.service;sleep 3;sudo systemctl stop di-flink-taskmanager.service;sudo systemctl stop di-flink-jobmanager.service"
    logger.info("Stopping DIM services on "+str(host)+": "+str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        if (output == 0):
            verboseHandle.printConsoleInfo("Services dih-admin/di-transformations/di-processor/di-manager/di-mdm/di-flink stopped successfully on "+str(host))
        else:
            verboseHandle.printConsoleError("Services dih-admin/di-transformations/di-processor/di-manager/di-mdm/di-flink failed to stop or not installed on "+str(host))

def stopKafkaService(args):
    logger.info("stopKafkaService()")
    try:
        if choiceOption == '1':
            hostNumber = str(userInputWrapper(Fore.YELLOW+"Enter host number to stop DI services : "+Fore.RESET))
            choice = str(userInputWrapper(Fore.YELLOW+"Are you sure want to stop DI services on "+str(host_dict_obj.get(hostNumber))+" ? (y/n) [y]: "+Fore.RESET))
            if len(choice)==0:
                choice='y'
            if choice =='y':
                host_type_dict_obj = getDIhostTypeDict()
                host = str(host_dict_obj.get(hostNumber))
                nodeType = host_type_dict_obj.get(host)
                di_nodes = list(config_get_dataIntegration_nodes())
                di_node1_host = os.getenv(di_nodes[0].ip) if di_nodes else None
                # Stop subscription manager on IIDR first, then DIM, then Kafka, then ZooKeeper
                if nodeType == "kafka Broker 1a" or (nodeListSize < 4 and host == di_node1_host):
                    stopSubscriptionManagerOnIIDR()
                    stopDIMServices(host)
                if nodeType != "Zookeeper Witness":
                    stopKafkaServiceByHost(host)
                if nodeType != "kafka Broker 1b" and nodeListSize==4:
                    stopZookeeperServiceByHost(host)
                elif nodeListSize<4:
                    stopZookeeperServiceByHost(host)
                #stopTelegrafServiceByHost(host)
            else:
                exit(0)
        if choiceOption == "":
            choice = str(userInputWrapper(Fore.YELLOW+"Are you sure want to stop DI services on "+str(nodes)+" ? (y/n) [y]: "+Fore.RESET))
            if choice.casefold() == 'n':
                exit(0)
            # Stop subscription manager on IIDR first, then DIM (node1 only), then Kafka, then ZooKeeper
            stopSubscriptionManagerOnIIDR()
            counter = 0
            for node in config_get_dataIntegration_nodes():
                counter += 1
                if node.type == "kafka Broker 1a" or (nodeListSize < 4 and counter == 1):
                    stopDIMServices(os.getenv(node.ip))
                    break
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
            #for node in config_get_dataIntegration_nodes():
            #stopTelegrafServiceByHost(os.getenv(node.ip))

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
    choiceOption = str(userInputWithEscWrapper(Fore.YELLOW+"Press [1] Individual stop\nPress [Enter] Stop current configuration.\nPress [99] For exit.:"+Fore.RESET))
    if choiceOption == "99":
        exit(0)
    stopKafkaService(args)

