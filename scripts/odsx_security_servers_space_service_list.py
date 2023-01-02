import argparse
import os
import sys

from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_space_node
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36
from utils.odsx_print_tabular_data import printTabular

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


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


def getSpaceUpdateCachePolicyStatus(node):
    logger.info("getSpaceUpdateCachePolicyStatus() : " + str(os.getenv(node.ip)))
    cmdList = ["systemctl status space-update-cache-policy"]
    for cmd in cmdList:
        logger.info("cmd :" + str(cmd) + " host :" + str(os.getenv(node.ip)))
        logger.info("Getting status.. :" + str(cmd))
        user = 'root'
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(os.getenv(node.ip), user, cmd)
            logger.info("output1 : " + str(output))
            if (output != 0):
                logger.info(" Service :" + str(cmd) + " not started." + str(os.getenv(node.ip)))
                return Fore.RED + "OFF" + Fore.RESET
            return Fore.GREEN + "ON" + Fore.RESET


def listspaceServersCachePolicyService():
    logger.info("listspaceServers()")
    host_dict_obj = obj_type_dictionary()
    spaceServers = config_get_space_node("config/cluster.config")
    headers = [Fore.YELLOW + "Id" + Fore.RESET,
               Fore.YELLOW + "Host" + Fore.RESET,
               Fore.YELLOW + "Status" + Fore.RESET
               ]
    data = []
    counter = 1
    for node in spaceServers:
        host_dict_obj.add(str(counter), str(os.getenv(node.ip)))
        output = getSpaceUpdateCachePolicyStatus(node)
        dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                     Fore.GREEN + os.getenv(node.name) + Fore.RESET,
                     output]
        data.append(dataArray)
        counter = counter + 1
    printTabular(None, headers, data)
    return host_dict_obj


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> Space -> Service -> List')
    try:
        args = []
        menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
        args.append(sys.argv[0])
        myCheckArg()
        listspaceServersCachePolicyService()
    except Exception as e:
        handleException(e)
