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
    nodes = ""
    for node in nodeList:
        # if(str(node.role).casefold() == 'server'):
        if (len(nodes) == 0):
            nodes = node.ip
        else:
            nodes = nodes + ',' + node.ip
    return nodes


def stopKafkaService(args):
    try:
        host_dict_obj = listDIServers()
        stopType = str(input(Fore.YELLOW + "[1] Single server stop \n[Enter] To stop on all servers \n[99] ESC : "))
        nodes = getDIServerHostList()
        singleHostIp = ''
        if (stopType == '99'):
            exit(0)
        if (stopType == '1'):
            hostNumer = str(input(Fore.YELLOW + "Enter serial number to stop : " + Fore.RESET))
            while (len(str(hostNumer)) == 0):
                hostNumer = str(input(Fore.YELLOW + "Enter serial number to stop : " + Fore.RESET))
            host = host_dict_obj.get(hostNumer)
            nodes = host
            singleHostIp = host
        choice = str(input(
            Fore.YELLOW + "Are you sure, you want to stop kafka services for [" + str(
                nodes) + "]? (y/n) [y]" + Fore.RESET))
        if choice.casefold() == 'n':
            exit(0)
        for node in config_get_dataIntegration_nodes():
            if (stopType == '1' and singleHostIp == node.ip) or (
                    singleHostIp == "" and len(host_dict_obj) <= 3) or (
                    singleHostIp == "" and len(host_dict_obj) > 3 and node.type != "Zookeeper Witness"):
                cmd = "systemctl stop odsxkafka.service; sleep 5;"
                logger.info("Getting status.. :" + str(cmd))
                user = 'root'
                with Spinner():
                    output = executeRemoteCommandAndGetOutputPython36(node.ip, user, cmd)
                    if (output == 0):
                        verboseHandle.printConsoleInfo("Service kafka stopped successfully on node " + str(node.ip))
                    else:
                        verboseHandle.printConsoleError("Service kafka failed to stop.")
        for node in config_get_dataIntegration_nodes():
            if (stopType == '1' and singleHostIp == node.ip) or (
                    singleHostIp == "" and len(host_dict_obj) <= 3) or (
                    singleHostIp == "" and len(host_dict_obj) > 3 and node.type != "kafka Broker 1b"):
                cmd = "systemctl stop odsxzookeeper.service; sleep 5;"
                logger.info("Getting status.. :" + str(cmd))
                user = 'root'
                with Spinner():
                    output = executeRemoteCommandAndGetOutputPython36(node.ip, user, cmd)
                    if (output == 0):
                        verboseHandle.printConsoleInfo("Service zookeeper stopped successfully on node " + str(node.ip))
                    else:
                        verboseHandle.printConsoleError("Service zookeeper failed to stop.")
        # for node in config_get_dataIntegration_nodes():
        #    cmd = "systemctl stop odsxcr8.service; sleep 5;"
        #    logger.info("Getting status odsxcr8.. :"+str(cmd))
        #    user = 'root'
        #    if(str(node.type)!='Witness'):
        #        with Spinner():
        #            output = executeRemoteCommandAndGetOutputPython36(node.ip, user, cmd)
        #            if (output == 0):
        #                verboseHandle.printConsoleInfo("Service CR8 stopped successfully on node "+str(node.ip))
        #            else:
        #                verboseHandle.printConsoleError("Service CR8 failed to stop.")
        for node in config_get_dataIntegration_nodes():
            if (stopType == '1' and singleHostIp == node.ip) or (
                    singleHostIp == ""):
                cmd = "systemctl stop telegraf"
                logger.info("Getting status.. telegraf :" + str(cmd))
                user = 'root'
                with Spinner():
                    output = executeRemoteCommandAndGetOutputPython36(node.ip, user, cmd)
                    if (output == 0):
                        verboseHandle.printConsoleInfo("Service telegraf stopped successfully on " + str(node.ip))
                    else:
                        verboseHandle.printConsoleError("Service telegraf failed to stop")
    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Servers -> DI -> Stop")
    args = []
    args = myCheckArg()
    stopKafkaService(args)
