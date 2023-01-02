#!/usr/bin/env python3
import argparse
import os
import sys

from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_security_servers_space_service_list import listspaceServersCachePolicyService
from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_space_node, \
    getSpaceHostFromEnv
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


def startSpaceUpdatePolicyServiceByHost(host):
    logger.info("startSpaceUpdatePolicyServiceByHost()")
    cmd = "systemctl start space-update-cache-policy.service"
    logger.info("Getting status.. space-update-cache-policy.service :" + str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        if (output == 0):
            verboseHandle.printConsoleInfo("Service space-update-cache-policy started successfully on " + str(host))
        else:
            verboseHandle.printConsoleError("Service space-update-cache-policy failed to start on " + str(host))


def startCachePolicyService(args):
    try:

        if choiceOption == '1':
            hostNumber = str(userInputWrapper(
                Fore.YELLOW + "Enter host number to start space-update-cache-policy service : " + Fore.RESET))
            choice = str(userInputWrapper(
                Fore.YELLOW + "Are you sure want to start space-update-cache-policy service on " + str(
                    host_dict_obj.get(hostNumber)) + " ? (y/n) [y]: " + Fore.RESET))
            if len(choice) == 0:
                choice = 'y'
            if choice == 'y':
                startSpaceUpdatePolicyServiceByHost(str(host_dict_obj.get(hostNumber)))
            else:
                exit(0)

        if choiceOption == "":
            choice = str(userInputWrapper(
                Fore.YELLOW + "Are you sure want to start space-update-cache-policy service on " + str(
                    getSpaceHostFromEnv()) + " ? (y/n) [y]: " + Fore.RESET))
            if choice.casefold() == 'n':
                exit(0)
            for node in config_get_space_node():
                startSpaceUpdatePolicyServiceByHost(os.getenv(node.ip))

    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Servers -> Space -> Service -> Start")
    args = []
    args = myCheckArg()
    global choiceOption
    global host_dict_obj
    host_dict_obj = listspaceServersCachePolicyService()
    choiceOption = str(userInputWithEscWrapper(
        Fore.YELLOW + "Press [1] Individual start\nPress [Enter] Start current configuration.\nPress [99] For exit.:" + Fore.RESET))
    if choiceOption == "99":
        exit(0)
    startCachePolicyService(args)
