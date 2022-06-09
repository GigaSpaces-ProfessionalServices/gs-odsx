import argparse
import os
import subprocess
import sys

from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_dataIntegration_nodes
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36
from utils.odsx_print_tabular_data import printTabular

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
dIServers = config_get_dataIntegration_nodes("config/cluster.config")


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


def getKafkaStatus(node):
    logger.info("getConsolidatedStatus() : " + str(node.ip))
    cmdList = ["systemctl status odsxkafka"]
    for cmd in cmdList:
        logger.info("cmd :" + str(cmd) + " host :" + str(node.ip))
        logger.info("Getting status.. :" + str(cmd))
        user = 'root'
        if len(dIServers) > 3 and (node.type == "Zookeeper Witness" and cmd == "systemctl status odsxkafka"):
            output = "NA"
            return output
        if len(dIServers) > 3 and (node.type == "kafka Broker 1b" and cmd == "systemctl status odsxzookeeper"):
            output = "NA"
            return output
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(node.ip, user, cmd)
            logger.info("output1 : " + str(output))
            if (output != 0):
                # verboseHandle.printConsoleInfo(" Service :"+str(cmd)+" not started.")
                logger.info(" Service :" + str(cmd) + " not started." + str(node.ip))
                output = "OFF"
            else:
                output = "ON"
            return output


def getZookeeperStatus(node):
    logger.info("getConsolidatedStatus() : " + str(node.ip))
    cmdList = ["systemctl status odsxzookeeper"]
    for cmd in cmdList:
        logger.info("cmd :" + str(cmd) + " host :" + str(node.ip))
        logger.info("Getting status.. :" + str(cmd))
        user = 'root'
        if len(dIServers) > 3 and (node.type == "Zookeeper Witness" and cmd == "systemctl status odsxkafka"):
            output = "NA"
            return output
        if len(dIServers) > 3 and (node.type == "kafka Broker 1b" and cmd == "systemctl status odsxzookeeper"):
            output = "NA"
            return output
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(node.ip, user, cmd)
            logger.info("output1 : " + str(output))
            if (output != 0):
                # verboseHandle.printConsoleInfo(" Service :"+str(cmd)+" not started.")
                logger.info(" Service :" + str(cmd) + " not started." + str(node.ip))
                output = "OFF"
            else:
                output = "ON"
            return output


def getConsolidatedStatus(node):
    output = ''
    logger.info("getConsolidatedStatus() : " + str(node.ip))
    cmdList = ["systemctl status odsxkafka", "systemctl status odsxzookeeper", "systemctl status telegraf"]
    for cmd in cmdList:
        logger.info("cmd :" + str(cmd) + " host :" + str(node.ip))
        if len(dIServers) > 3 and ((str(node.type) == 'kafka Broker 1b' and cmd == 'systemctl status odsxzookeeper') or (
                str(node.type) == 'Zookeeper Witness' and cmd == 'systemctl status odsxkafka')):
            output = 0
        #       elif (str(node.type) == 'Zookeeper Witness' and cmd == 'systemctl status odsxkafka'):
        #           output = 0
        else:
            logger.info("Getting status.. :" + str(cmd))
            user = 'root'
            with Spinner():
                output = executeRemoteCommandAndGetOutputPython36(node.ip, user, cmd)
                logger.info("output1 : " + str(output))
                if (output != 0):
                    # verboseHandle.printConsoleInfo(" Service :"+str(cmd)+" not started.")
                    logger.info(" Service :" + str(cmd) + " not started." + str(node.ip))
                    output = "OFF"
                    return output
    output = "ON"
    return output


def roleOfCurrentNode(ip):
    logger.info("isCurrentNodeLeaderNode(ip) " + str(ip))
    cmd = "echo srvr | nc " + ip + " 2181"
    # print(cmd)
    output = subprocess.getoutput(cmd)
    # print(output)
    logger.info("output " + str(output))
    if (str(output).__contains__('Mode: leader')):
        return "Leader"
  #  elif (str(output).__contains__('Mode: follower')):
  #      return "Follower"
    else:
        return "Follower"


def listDIServers():
    logger.info("listDIServers()")
    host_dict_obj = obj_type_dictionary()
    dIServers = config_get_dataIntegration_nodes("config/cluster.config")
    headers = [Fore.YELLOW + "Sr Num" + Fore.RESET,
               Fore.YELLOW + "Name" + Fore.RESET,
               Fore.YELLOW + "Type" + Fore.RESET,
               Fore.YELLOW + "Role" + Fore.RESET,
               Fore.YELLOW + "Status" + Fore.RESET,
               Fore.YELLOW + "Kafka Status" + Fore.RESET,
               Fore.YELLOW + "Zookeeper Status" + Fore.RESET,
               Fore.YELLOW + "DIRole" + Fore.RESET]
    data = []
    counter = 1
    for node in dIServers:
        host_dict_obj.add(str(counter), str(node.ip))
        output = getConsolidatedStatus(node)
        kafkaOutput = getKafkaStatus(node)
        zkOutput = getZookeeperStatus(node)
        role = roleOfCurrentNode(node.ip)
        # print(node.ip)
        # print(kafkaOutput)
        # print(zkOutput)
        # print(output)
        # print("======")
        if (kafkaOutput == "ON" or kafkaOutput == "NA") and (zkOutput == "ON" or zkOutput == "NA") and output == "ON":
            dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                         Fore.GREEN + node.name + Fore.RESET,
                         Fore.GREEN + node.type + Fore.RESET,
                         Fore.GREEN + node.role + Fore.RESET,
                         Fore.GREEN + output + Fore.RESET,
                         Fore.GREEN + kafkaOutput + Fore.RESET,
                         Fore.GREEN + zkOutput + Fore.RESET,
                         Fore.GREEN + str(role) + Fore.RESET]
        elif (kafkaOutput == "ON" or kafkaOutput == "NA") and (zkOutput == "ON" or zkOutput == "NA") and output != "ON":
            dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                         Fore.GREEN + node.name + Fore.RESET,
                         Fore.GREEN + node.type + Fore.RESET,
                         Fore.GREEN + node.role + Fore.RESET,
                         Fore.RED + output + Fore.RESET,
                         Fore.GREEN + kafkaOutput + Fore.RESET,
                         Fore.GREEN + zkOutput + Fore.RESET,
                         Fore.GREEN + str(role) + Fore.RESET]
        elif (kafkaOutput == "OFF" and zkOutput != "OFF" and output != "ON"):
            dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                         Fore.GREEN + node.name + Fore.RESET,
                         Fore.GREEN + node.type + Fore.RESET,
                         Fore.GREEN + node.role + Fore.RESET,
                         Fore.RED + output + Fore.RESET,
                         Fore.RED + kafkaOutput + Fore.RESET,
                         Fore.GREEN + zkOutput + Fore.RESET,
                         Fore.GREEN + str(role) + Fore.RESET]
        elif (kafkaOutput != "OFF" and zkOutput == "OFF" and output != "ON"):
            dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                         Fore.GREEN + node.name + Fore.RESET,
                         Fore.GREEN + node.type + Fore.RESET,
                         Fore.GREEN + node.role + Fore.RESET,
                         Fore.RED + output + Fore.RESET,
                         Fore.GREEN + kafkaOutput + Fore.RESET,
                         Fore.RED + zkOutput + Fore.RESET,
                         Fore.GREEN + str(role) + Fore.RESET]
        else:
            dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                         Fore.GREEN + node.name + Fore.RESET,
                         Fore.GREEN + node.type + Fore.RESET,
                         Fore.GREEN + node.role + Fore.RESET,
                         Fore.RED + output + Fore.RESET,
                         Fore.RED + kafkaOutput + Fore.RESET,
                         Fore.RED + zkOutput + Fore.RESET,
                         Fore.GREEN + str(role) + Fore.RESET]
        data.append(dataArray)
        counter = counter + 1
    printTabular(None, headers, data)
    return host_dict_obj


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> DI -> List')
    try:
        args = []
        menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
        args.append(sys.argv[0])
        myCheckArg()
        listDIServers()
    except Exception as e:
        handleException(e)
