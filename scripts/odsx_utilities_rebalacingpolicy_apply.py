#!/usr/bin/env python3

import os, socket
import signal
import subprocess,shlex
from colorama import Fore
from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import set_value_in_property_file
from utils.ods_cleanup import signal_handler
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_scp import scp_upload
from utils.ods_ssh import connectExecuteSSH
from utils.ods_validation import getSpaceServerStatus
from scripts.odsx_tieredstorage_deploy import displaySpaceHostWithNumber
from scripts.odsx_servers_space_list import getGSCForHost

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
clusterHosts = []

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

def getManagerHost(managerNodes):
    managerHost=""
    try:
        logger.info("getManagerHost() : managerNodes :"+str(managerNodes))
        for node in managerNodes:
            status = getSpaceServerStatus(os.getenv(node.ip))
            if(status=="ON"):
                managerHost = os.getenv(node.ip)
        return managerHost
    except Exception as e:
        handleException(e)

def getManagerServerHostList():
    nodeList = config_get_manager_node()
    nodes = ""
    for node in nodeList:
        # if(str(node.role).casefold() == 'server'):
        if (len(nodes) == 0):
            nodes = os.getenv(node.ip)
        else:
            nodes = nodes + ',' + os.getenv(node.ip)
    return nodes


def getInputParam():
    logger.info("getInputParam()")
    locators = getManagerServerHostList()
    managerNodes = config_get_manager_node()
    spaceNodes = config_get_space_hosts()
    space_dict_obj = displaySpaceHostWithNumber(managerNodes,spaceNodes)
    logger.info("space_dict_obj : "+str(space_dict_obj))
    hostNumberToRebalance = str(input(Fore.YELLOW+"Enter host/IP number to rebalance : "+Fore.RESET))
    while(len(str(hostNumberToRebalance))==0):
        hostNumberToRebalance = str(input(Fore.YELLOW+"Enter host/IP number to rebalance : "+Fore.RESET))
    hostToRebalance = space_dict_obj.get(hostNumberToRebalance)

    zone = str(input(Fore.YELLOW+"Enter zone to rebalance [bll] : "+Fore.RESET))
    while(len(str(zone))==0):
        zone='bll'
    host_gsc_dict_obj = getGSCForHost()
    logger.info("host_gsc_dict_obj :"+str(host_gsc_dict_obj))
    logger.info("hostToRebalance :"+str(hostToRebalance))
    hostAddress = str(socket.gethostbyaddr(str(hostToRebalance))[0])

    gscCount = str(host_gsc_dict_obj.get(hostAddress))
    logger.info("GSC for host "+hostAddress+" : "+str(gscCount))
    verboseHandle.printConsoleInfo("Gsc count ["+gscCount+"] to rebalance host ["+hostToRebalance+"] : "+Fore.RESET)

    currWorkingDir = format(os.getcwd())
    cmd = "scripts/utilities_rebalancingpolicy_apply.sh"+' '+locators+' '+hostToRebalance+' '+zone+' '+gscCount+' '+currWorkingDir
    status=''
    with Spinner():
        output = subprocess.check_output(cmd,shell=True)
        print(output)
        logger.info("Rebalancing log start : ")
        logger.info(str(output))
        logger.info("Rebalancing log end : ")

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Utilities -> Rebalancing -> Apply')
    signal.signal(signal.SIGINT, signal_handler)
    try:
        nodeList = config_get_manager_node()
        if(len(str(nodeList))>0):
            getInputParam()
        else:
            logger.info("No manager host configuration found")
            verboseHandle.printConsoleInfo("No manager host configuration found")
    except Exception as e:
        handleException(e)
