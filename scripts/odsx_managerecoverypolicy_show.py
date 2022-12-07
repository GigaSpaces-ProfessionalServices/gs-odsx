#!/usr/bin/env python3
import argparse
import os
import sys

from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_policyConfigurations
from utils.odsx_keypress import userInputWithEscWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])


def show_policy_info(args):
    policyConfigurations = config_get_policyConfigurations()
    policyDict = {}
    policyAssociatedDict = {}
    counter = 0
    print("Select a policy to show details")
    for policy in policyConfigurations.policies:
        counter = counter + 1
        print("[" + str(counter) + "] " + policy.name + " [" + policy.description + "]")
        policyDict.update({counter: policy})

    for policyAssociated in policyConfigurations.policyAssociations:
        policyAssociatedDict.update({policyAssociated.policy: policyAssociated})

    print("[99] " + "ESC")
    choice = str(userInputWithEscWrapper("Enter your option: "))
    if len(choice) == 0 or int(choice) > len(policyDict) or int(choice) == 99:
        if int(choice) != 99:
            verboseHandle.printConsoleError("Invalid input")
        exit(0)

    selectedValue = policyDict.get(int(choice))
    if selectedValue == "":
        verboseHandle.printConsoleError("Invalid input")
        exit(0)

    # data.append(selectedValue.description)
    # data.append(selectedValue.type)
    # data.append(selectedValue.definition)
    # data.append(selectedValue.parameters.waitIntervalAfterServerDown)
    # data.append(selectedValue.parameters.waitIntervalForContainerCheckAfterServerUp)
    # data.append(selectedValue.parameters.waitIntervalForDeletionAfterDemote)
    #  data.append('Not Active')

    verboseHandle.printConsoleWarning("Name : " + Fore.CYAN + selectedValue.name)
    verboseHandle.printConsoleWarning("Description : " + Fore.CYAN + selectedValue.description)
    verboseHandle.printConsoleWarning("Type : " + Fore.CYAN + selectedValue.type)
    verboseHandle.printConsoleWarning("Definition : " + Fore.CYAN + selectedValue.definition)
    verboseHandle.printConsoleWarning(
        "Wait Interval after Server Down : " + Fore.CYAN + str(selectedValue.parameters.waitIntervalAfterServerDown))
    verboseHandle.printConsoleWarning("Wait Interval for Container check after Server Up : " + Fore.CYAN + str(
        selectedValue.parameters.waitIntervalForContainerCheckAfterServerUp))
    verboseHandle.printConsoleWarning("Wait Interval for Deletion after Demote : " + Fore.CYAN + str(
        selectedValue.parameters.waitIntervalForDeletionAfterDemote))

    #status = executeLocalCommandAndGetOutput("sudo systemctl is-active --quiet odsxrecovery.service")
    status = os.system('systemctl is-active --quiet odsxrecovery.service')
    if (status == 0):
        verboseHandle.printConsoleWarning("Status : " + Fore.GREEN + 'Active')
    else:
        verboseHandle.printConsoleWarning("Status : " + Fore.RED + 'Not Active')
    if policyAssociatedDict.get(selectedValue.name):
        selectedValue = policyAssociatedDict.get(selectedValue.name)
        verboseHandle.printConsoleWarning("Target Node Type : " + Fore.CYAN + selectedValue.targetNodeType)
        verboseHandle.printConsoleWarning("Nodes : " + Fore.CYAN + str(selectedValue.nodes))
        verboseHandle.printConsoleWarning("GSC Count : " + Fore.CYAN + str(selectedValue.gsc.count))
        verboseHandle.printConsoleWarning("Zones : " + Fore.CYAN + str(selectedValue.gsc.zones))


#        for selectedValueGsc in list(selectedValue.gsc):
#            verboseHandle.printConsoleWarning("GSC Count : " + Fore.CYAN + str(selectedValueGsc.count))
#            verboseHandle.printConsoleWarning("Zones : " + Fore.CYAN + str(selectedValueGsc.zones))


if __name__ == '__main__':
    args = []
    args = myCheckArg()
    show_policy_info(args)
