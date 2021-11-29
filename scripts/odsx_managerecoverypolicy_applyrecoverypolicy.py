#!/usr/bin/env python3
import argparse
import json
import os
import sys

import requests

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_policyConfigurations, get_spaces_servers, config_add_policy_association, \
    config_get_manager_node
from utils.ods_ssh import executeLocalCommandAndGetOutput

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


class GscInfoPerHost:
    def __init__(self, zoneName, gscCount, gscMaxMemory, emptyGscCount):
        self.zoneName = zoneName
        self.gscCount = gscCount
        self.gscMaxMemory = gscMaxMemory
        self.emptyGscCount = emptyGscCount


class HostGscInfo:
    def __init__(self, hostname, gscInfoPerHost, freeMemory):
        self.hostname = hostname
        self.gscInfoPerHost = gscInfoPerHost
        self.freeMemory = freeMemory


def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])


def dataContainerREST(host, zone, memory):
    data = {
        "vmArguments": [
            "-Xms" + str(memory) + " -Xmx" + str(memory)
        ],
        "memory": memory,
        "zone": zone,
        "host": host
    }
    # response = requests.post("http://54.154.72.190:8090/v2/spaces?name=space&partitions=1&backups=true")
    return data


def applySimpleSpaceRecoveryPolicy():
    if len(config_get_manager_node()) > 0:
        managerHost = config_get_manager_node()[0].ip
        # http://localhost:8090/v2/hosts
        response = requests.get('http://' + managerHost + ':8090/v2/hosts', headers={'Accept': 'application/json'})
        hostInfoDict = {}
        for host in response.json():
            print("host name : " + host['address'])
            # http://localhost:8090/v2/hosts/jay-laptop/containers
            response = requests.get('http://' + managerHost + ':8090/v2/hosts/' + host['address'] + '/containers',
                                    headers={'Accept': 'application/json'})
            zoneinfoDict = {}
            zoneContainerCount = {}
            for hostContainer in response.json():
                if len(hostContainer['zones']) > 0:
                    print("zone : " + hostContainer['zones'][0])
                if len(hostContainer['instances']) == 0:
                    print("empty gsc " + hostContainer['id'])

                # http://localhost:8090/v2/containers/jay-laptop~44619/details/jvm
                response = requests.get(
                    'http://' + managerHost + ':8090/v2/containers/' + hostContainer['id'] + '/details/jvm',
                    headers={'Accept': 'application/json'})
                hostContainerJvmInfo = response.json();
                print(
                    hostContainer['id'] + " GSC Memory in bytes : " + str(hostContainerJvmInfo['memoryHeapMaxInBytes']))
                print(hostContainer['id'] + " GSC Memory in mb : " + str(
                    hostContainerJvmInfo['memoryHeapMaxInBytes'] / 1024 / 1024))
                zoneName = ""
                if len(hostContainer['zones']) > 0:
                    zoneName = hostContainer['zones'][0]
                if len(zoneinfoDict) > 0 and zoneinfoDict.get(zoneName) is not None:
                    gscCount = zoneinfoDict[zoneName].gscCount
                    emptyGscCount = zoneinfoDict[zoneName].emptyGscCount
                    if len(hostContainer['instances']) == 0:
                        emptyGscCount = zoneinfoDict[zoneName].emptyGscCount + 1
                    else:
                        gscCount = zoneinfoDict[zoneName].gscCount + 1
                    zoneinfoDict.pop(zoneName)
                    zoneinfoDict[zoneName] = GscInfoPerHost(zoneName, gscCount,
                                                            hostContainerJvmInfo['memoryHeapMaxInBytes'], emptyGscCount)
                else:
                    emptyGscCount = 0
                    gscWithPU = 1
                    if len(hostContainer['instances']) == 0:
                        emptyGscCount = 1
                        gscWithPU = 0
                    zoneinfoDict[zoneName] = GscInfoPerHost(zoneName, 1,
                                                            hostContainerJvmInfo['memoryHeapMaxInBytes'], emptyGscCount)

            # http://localhost:8090/v2/hosts/jay-laptop/statistics/os
            response = requests.get('http://' + managerHost + ':8090/v2/hosts/' + host['address'] + '/statistics/os',
                                    headers={'Accept': 'application/json'})
            hostInfo = response.json()

            response = requests.get('http://' + managerHost + ':8090/v2/info',
                                    headers={'Accept': 'application/json'})
            managerServers = response.json()['managers']

            hostInfoDict[host['address']] = HostGscInfo(host['address'], list(zoneinfoDict.values()),
                                                        hostInfo['actualFreePhysicalMemorySizeInBytes'])
            print("free memory in bytes : " + str(hostInfo['actualFreePhysicalMemorySizeInBytes']))
            print("free memory in gb : " + str(hostInfo['actualFreePhysicalMemorySizeInBytes'] / 1024 / 1024 / 1024))
            print(">used memory in bytes : " + str(hostInfo['actualMemoryUsed']))
            print(">used memory in gb : " + str(hostInfo['actualMemoryUsed'] / 1024 / 1024 / 1024))

        print("\n")
        for index, (key, value) in enumerate(hostInfoDict.items()):
            print(">>>>>Host : " + key + ", index : " + str(index))
            for gscInfo in value.gscInfoPerHost:
                print("zone : '" + gscInfo.zoneName + "', empty gsc count : " + str(gscInfo.emptyGscCount))
                print("zone : '" + gscInfo.zoneName + "', gsc count containing PU : " + str(
                    gscInfo.gscCount))
                if gscInfo.gscCount > gscInfo.emptyGscCount:
                    verboseHandle.printConsoleWarning(
                        "zone : '" + gscInfo.zoneName + "', spare gsc to be created on other host: " + str(
                            gscInfo.gscCount - gscInfo.emptyGscCount))
                    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

                    gscCountTobeCreated = gscInfo.gscCount - gscInfo.emptyGscCount
                    for i in range(1, gscInfo.gscCount - gscInfo.emptyGscCount + 1):
                        # TODO check if empty gsc with zone exist in other host. If exist then subrtact count
                        for subindex, (subkey, subvalue) in enumerate(hostInfoDict.items()):
                            if subkey != key and gscCountTobeCreated > 0:
                                response = requests.get(
                                    'http://' + managerHost + ':8090/v2/hosts/' + subkey + '/containers',
                                    headers={'Accept': 'application/json'})
                                for hostContainer in response.json():
                                    tmpZoneName = ""
                                    if len(hostContainer['zones']) > 0:
                                        tmpZoneName = hostContainer['zones'][0]
                                    if tmpZoneName == gscInfo.zoneName and len(hostContainer['instances']) == 0:
                                        verboseHandle.printConsoleWarning("empty gsc found on host " + subkey)
                                        gscCountTobeCreated = gscCountTobeCreated - 1

                        for subindex, (subkey, subvalue) in enumerate(hostInfoDict.items()):
                            if gscCountTobeCreated > 0:
                                if subkey not in managerServers:
                                    if subkey != key:

                                        response = requests.get(
                                            'http://' + managerHost + ':8090/v2/hosts/' + subkey + '/statistics/os',
                                            headers={'Accept': 'application/json'})
                                        hostInfo = response.json()
                                        if hostInfo['actualFreePhysicalMemorySizeInBytes'] > gscInfo.gscMaxMemory:
                                            data = dataContainerREST(subkey, gscInfo.zoneName, gscInfo.gscMaxMemory)
                                            response = requests.post("http://" + managerHost + ":8090/v2/containers",
                                                                     data=json.dumps(data), headers=headers)
                                            if response.status_code == 202:
                                                gscCountTobeCreated = gscCountTobeCreated - 1
                                                verboseHandle.printConsoleInfo(
                                                    "GSC " + str(i) + " created on host :" + str(host))
                                        else:
                                            verboseHandle.printConsoleWarning(
                                                "Not enough memory on host " + subkey + ", trying different server ...")
                                    else:
                                        verboseHandle.printConsoleWarning(
                                            "Same host " + subkey + " so not creating gsc")
                                else:
                                    verboseHandle.printConsoleWarning(
                                        "Manager host found " + subkey + ", not creating gsc")
                            else:
                                verboseHandle.printConsoleWarning("All required gsc created")
                                break

                else:
                    verboseHandle.printConsoleInfo(
                        "zone : '" + gscInfo.zoneName + "', spare gsc not required to be created")

    else:
        logger.error("No manager found")
        verboseHandle.printConsoleWarning("No manager found")


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
    choice = str(input("Enter your option: "))
    if len(choice) == 0 or int(choice) > len(policyDict) or int(choice) == 99:
        if int(choice) != 99:
            verboseHandle.printConsoleError("Invalid input")
        exit(0)

    selectedValue = policyDict.get(int(choice))
    if selectedValue == "":
        verboseHandle.printConsoleError("Invalid input")
        exit(0)

    verboseHandle.printConsoleWarning("Are you sure want to apply policy ? [Yes][No][Cancel]")
    choice = str(input(""))
    if choice.casefold() == 'no':
        exit(0)

    if selectedValue.name == "spaceRecoveryPolicy" or selectedValue.name == "simpleSpaceRecoveryPolicy":
        # get space servers from config
        nodes = []
        zones = []
        for spaceserver in get_spaces_servers().host:
            nodes.append(spaceserver.ip)
        # get zones and gsc count for each zone

        if len(config_get_manager_node()) > 0:
            managerHost = config_get_manager_node()[0].ip

            response = requests.get('http://' + managerHost + ':8090/v2/containers',
                                    headers={'Accept': 'application/json'})
            gscCount = 0
            for key in response.json():
                gscCount = gscCount + 1
                for zone in key["zones"]:
                    zones.append(zone)
            if len(nodes) == 0:
                verboseHandle.printConsoleError("No space server found")
            else:
                if selectedValue.name == "simpleSpaceRecoveryPolicy":
                    applySimpleSpaceRecoveryPolicy()
                else:
                    gscCount = int(gscCount / len(nodes))
                    config_add_policy_association("space", nodes, selectedValue.name, gscCount, list(set(zones)))
        else:
            logger.error("No manager found")
        if selectedValue.name != "simpleSpaceRecoveryPolicy":
            with Spinner():
                executeLocalCommandAndGetOutput("sudo systemctl restart --quiet odsxrecovery.service")
        verboseHandle.printConsoleInfo("Done")


if __name__ == '__main__':
    verboseHandle.printConsoleInfo("Apply Policy")
    args = []
    args = myCheckArg()
    show_policy_info(args)
