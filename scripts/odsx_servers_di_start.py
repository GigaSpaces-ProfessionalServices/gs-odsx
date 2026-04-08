#!/usr/bin/env python3
import argparse
import os
import sys

from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_servers_di_list import listDIServers
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig
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
        if(len(nodes)==0):
            nodes = os.getenv(node.ip)
        else:
            nodes = nodes+','+str(os.getenv(node.ip))
    return nodes

def getDIhostTypeDict():
    global host_type_dict_obj
    host_type_dict_obj = obj_type_dictionary()
    nodeList = config_get_dataIntegration_nodes()
    for node in nodeList:
        host_type_dict_obj.add(os.getenv(node.ip),node.type)
    return host_type_dict_obj

def startZookeeperServiceByHost(host):
    logger.info("startZookeeperServiceByHost()")
    cmd = " systemctl start odsxzookeeper.service"
    logger.info("Starting odsxzookeeper on "+str(host)+": "+str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        if (output == 0):
            verboseHandle.printConsoleInfo("Service zookeeper started successfully on "+str(host))
        else:
            verboseHandle.printConsoleError("Service zookeeper failed to start on "+str(host))


def startKafkaServiceByHost(host):
    logger.info("startKafkaServiceByHost()")
    user = 'root'
    # KRaft: format storage if not already done (meta.properties absent = not formatted)
    gigapath = "/dbagiga"
    gigasharepath = "/dbagigashare"
    kafka_data = str(readValuefromAppConfig("app.di.base.kafka.data")).rstrip('/')
    kafka_bin = gigapath + "/kafka_latest/bin/kafka-storage.sh"
    kafka_cfg = gigapath + "/kafka_latest/config/server.properties"
    cluster_id_file = gigasharepath + "/current/kafka-cluster-id"
    format_cmd = ("[ -f " + kafka_data + "/meta.properties ] || " +
                  kafka_bin + " format -t $(cat " + cluster_id_file + ") -c " + kafka_cfg)
    verboseHandle.printConsoleInfo("Format command: "+str(format_cmd))
    logger.info("Ensuring KRaft storage is formatted on "+str(host))
    with Spinner():
        executeRemoteCommandAndGetOutputPython36(host, user, format_cmd)
    cmd = " systemctl start odsxkafka.service"
    logger.info("Starting odsxkafka on "+str(host)+": "+str(cmd))
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        if (output == 0):
            verboseHandle.printConsoleInfo("Service kafka started successfully on "+str(host))
        else:
            verboseHandle.printConsoleError("Service kafka failed to start on "+str(host))


def startTelegrafServiceByHost(host):
    logger.info("startTelegrafServiceByHost()")
    cmd = " systemctl start telegraf"
    logger.info("Starting telegraf on "+str(host)+": "+str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        if (output == 0):
            verboseHandle.printConsoleInfo("Service telegraf started successfully on "+str(host))
        else:
            verboseHandle.printConsoleError("Service telegraf failed to start on "+str(host))


def startSubscriptionManagerOnIIDR():
    logger.info("startSubscriptionManagerOnIIDR()")
    user = 'root'
    nodeiidrList = config_get_dataIntegrationiidr_nodes()
    for node in nodeiidrList:
        iidrHost = os.getenv(node.ip)
        cmd = "systemctl start di-subscription-manager-iidr.service"
        logger.info("Starting di-subscription-manager-iidr on " + str(iidrHost))
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(iidrHost, user, cmd)
            if output == 0:
                verboseHandle.printConsoleInfo("Service di-subscription-manager-iidr started successfully on " + str(iidrHost))
            else:
                verboseHandle.printConsoleError("Service di-subscription-manager-iidr failed to start on " + str(iidrHost))


def startDIMServices(host):
    logger.info("startDIMServices()")
    # Start order: flink first, then di-mdm (needs ZK), then di-manager (needs di-mdm), then di-transformations (needs di-mdm + di-manager)
    cmd = " systemctl start di-flink-jobmanager.service; systemctl start di-flink-taskmanager.service;sleep 3; systemctl start di-mdm.service;sleep 5; systemctl start di-manager.service;sleep 3; systemctl start di-transformations.service;sleep 3; systemctl start dih-admin.service"
    logger.info("Starting DIM services on "+str(host)+": "+str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        if (output == 0):
            verboseHandle.printConsoleInfo("Services di-flink/di-mdm/di-manager/di-transformations/dih-admin started successfully on "+str(host))
        else:
            verboseHandle.printConsoleError("Services di-flink/di-mdm/di-manager/di-transformations/dih-admin failed to start on "+str(host))


def startKafkaService(args):
    try:
        if choiceOption == '1':
            hostNumber = str(userInputWrapper(Fore.YELLOW+"Enter host number to start DI services : "+Fore.RESET))
            choice = str(userInputWrapper(Fore.YELLOW+"Are you sure want to start DI services on "+str(host_dict_obj.get(hostNumber))+" ? (y/n) [y]: "+Fore.RESET))
            if len(choice)==0:
                choice='y'
            if choice =='y':
                getDIhostTypeDict()
                host = str(host_dict_obj.get(hostNumber))
                nodeType = host_type_dict_obj.get(host)
                if nodeType != "kafka Broker 1b" and nodeListSize==4:
                    startZookeeperServiceByHost(host)
                elif nodeListSize<4:
                    startZookeeperServiceByHost(host)
                if nodeType != "Zookeeper Witness":
                    startKafkaServiceByHost(host)
                #startTelegrafServiceByHost(host)
                if nodeType == "kafka Broker 1a" or nodeListSize < 4:
                    startDIMServices(host)
                    startSubscriptionManagerOnIIDR()
            else:
                exit(0)

        if choiceOption == "":
            choice = str(userInputWrapper(Fore.YELLOW+"Are you sure want to start DI services on "+str(nodes)+" ? (y/n) [y]: "+Fore.RESET))
            if choice.casefold() == 'n':
                exit(0)
            # Start ZooKeeper on all nodes first
            for node in config_get_dataIntegration_nodes():
                if node.type != "kafka Broker 1b" and nodeListSize==4:
                    startZookeeperServiceByHost(os.getenv(node.ip))
                elif nodeListSize<4:
                    startZookeeperServiceByHost(os.getenv(node.ip))
            # Then start Kafka on broker nodes
            for node in config_get_dataIntegration_nodes():
                if node.type != "Zookeeper Witness":
                    startKafkaServiceByHost(os.getenv(node.ip))
            # Then start DIM services (only on node 1 / kafka Broker 1a), then subscription manager on IIDR host
            for node in config_get_dataIntegration_nodes():
                #startTelegrafServiceByHost(os.getenv(node.ip))
                if node.type == "kafka Broker 1a" or nodeListSize < 4:
                    startDIMServices(os.getenv(node.ip))
            startSubscriptionManagerOnIIDR()
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
