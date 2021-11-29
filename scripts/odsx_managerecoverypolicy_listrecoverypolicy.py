#!/usr/bin/env python3
import argparse
import os
import sys

from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_policyConfigurations
from utils.ods_ssh import executeLocalCommandAndGetOutput
from utils.odsx_print_tabular_data import printTabular

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


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


def getRecoveryPolicyDetails(policy):
    dataArray = []
    # for policy in policyConfigurations.policies:
    #status = executeLocalCommandAndGetOutput("sudo systemctl is-active --quiet odsxrecovery.service")
    status = os.system('systemctl is-active --quiet odsxrecovery.service')
    #print(status)  # will return 0 for active else inactive.
    # status = 'Not Active'
    if (status == 0):
        dataArray = [Fore.GREEN + policy.name + Fore.RESET,
                     Fore.GREEN + policy.description + Fore.RESET,
                     Fore.GREEN + policy.type + Fore.RESET,
                     Fore.GREEN + str(policy.parameters.waitIntervalAfterServerDown) + Fore.RESET,
                     Fore.GREEN + 'Active' + Fore.RESET]
    else:
        dataArray = [Fore.GREEN + policy.name + Fore.RESET,
                     Fore.GREEN + policy.description + Fore.RESET,
                     Fore.GREEN + policy.type + Fore.RESET,
                     Fore.GREEN + str(policy.parameters.waitIntervalAfterServerDown) + Fore.RESET,
                     Fore.RED + 'Not Active' + Fore.RESET]
    return dataArray


def listPolicies():
    logger.debug("listing Grafana servers")
    logger.debug("listing Grafana servers")
    policyConfigurations = config_get_policyConfigurations()

    verboseHandle.printConsoleWarning("Menu -> Manage Recovery Policy -> List recovery policy\n")
    headers = [Fore.YELLOW + "Name" + Fore.RESET,
               Fore.YELLOW + "Description" + Fore.RESET,
               Fore.YELLOW + "Type" + Fore.RESET,
               Fore.YELLOW + "Wait Time After ServerDown (s)" + Fore.RESET,
               Fore.YELLOW + "Status" + Fore.RESET]
    data = []
    for policy in policyConfigurations.policies:
        data.append(getRecoveryPolicyDetails(policy))

    printTabular(None, headers, data)


if __name__ == '__main__':
    args = []
    menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
    args.append(sys.argv[0])
    myCheckArg()
    listPolicies()
