#!/usr/bin/env python3
import os
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from scripts.odsx_space_createnewspace import listSpacesOnServer

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR


def listSpaceFromHosts(managerNodes):
    listSpacesOnServer(managerNodes)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Space -> List")
    managerNodes = config_get_manager_node()
    listSpaceFromHosts(managerNodes)