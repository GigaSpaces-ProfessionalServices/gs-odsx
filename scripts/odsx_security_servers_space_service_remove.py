#!/usr/bin/env python3

import os

from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_security_servers_space_install import getSpaceHostFromEnv
from scripts.odsx_security_servers_space_service_list import listspaceServersCachePolicyService
from scripts.spinner import Spinner
from utils.ods_ssh import connectExecuteSSH
from utils.odsx_keypress import userInputWrapper

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


def removeInputUserAndHost():
    logger.info("removeInputUserAndHost():")
    try:
        global user
        global host
        # user = str(userInputWrapper(Fore.YELLOW+"Enter user to connect to DI server [root]:"+Fore.RESET))
        # if(len(str(user))==0):
        user = "root"
        logger.info(" user: " + str(user))

    except Exception as e:
        handleException(e)


def executeCommandForUnInstall():
    logger.info("executeCommandForUnInstall(): start")
    try:
        host_dict_obj = listspaceServersCachePolicyService()
        logger.info("host_dict_obj :" + str(host_dict_obj))
        nodes = getSpaceHostFromEnv()
        nodesCount = nodes.split(',')
        logger.info("nodesCount :" + str(len(nodesCount)))
        if (len(nodes) > 0):
            confirmUninstall = str(userInputWrapper(
                Fore.YELLOW + "Are you sure want to remove space-update-cache-policy from space servers [" + nodes + "] (y/n) [y]: " + Fore.RESET))
            if (len(str(confirmUninstall)) == 0):
                confirmUninstall = 'y'
            logger.info("confirmUninstall :" + str(confirmUninstall))
            if (confirmUninstall == 'y'):
                commandToExecute = "scripts/space_server_cache_policy_service_remove.sh"
                with Spinner():
                    for host in nodes.split(','):
                        print(host)
                        outputShFile = connectExecuteSSH(host, user, commandToExecute, "")
                        print(outputShFile)
                        verboseHandle.printConsoleInfo("Node has been removed :" + str(host))

        else:
            logger.info("No server details found.")
            verboseHandle.printConsoleInfo("No server details found.")
    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> Space -> Service -> Remove')
    try:
        removeInputUserAndHost()
        executeCommandForUnInstall()
    except Exception as e:
        handleException(e)
