#!/usr/bin/env python3

import json
import os

import requests
from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_dataIntegration_nodes
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_ssh import executeRemoteCommandAndGetOutput
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_print_tabular_data import printTabular

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
clusterHosts = []
confirmCreateGSC = ''


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


class host_dictionary_obj(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value


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


def getBootstrapAddress(hostConfig):
    logger.info("getBootstrapAddress()")
    bootstrapAddress = ''
    for host in hostConfig.split(','):
        bootstrapAddress = bootstrapAddress + host + ':9092,'
    bootstrapAddress = bootstrapAddress[:-1]
    logger.info("getBootstrapAddress : " + str(bootstrapAddress))
    return bootstrapAddress


def getManagerHost(managerNodes):
    managerHost = ""
    try:
        logger.info("getManagerHost() : managerNodes :" + str(managerNodes))
        for node in managerNodes:
            status = getSpaceServerStatus(node.ip)
            if (status == "ON"):
                managerHost = node.ip
        return managerHost
    except Exception as e:
        handleException(e)


def listDeployed(managerHost):
    global gs_space_dictionary_obj
    try:
        logger.info("managerHost :" + str(managerHost))
        response = requests.get("http://" + str(managerHost) + ":8090/v2/pus/")
        logger.info("response status of host :" + str(managerHost) + " status :" + str(
            response.status_code) + " Content: " + str(response.content))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Resources on cluster:")
        headers = [Fore.YELLOW + "Sr No." + Fore.RESET,
                   Fore.YELLOW + "Name" + Fore.RESET,
                   Fore.YELLOW + "Resource" + Fore.RESET,
                   Fore.YELLOW + "Zone" + Fore.RESET,
                   Fore.YELLOW + "processingUnitType" + Fore.RESET,
                   Fore.YELLOW + "Status" + Fore.RESET
                   ]
        gs_space_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_dictionary_obj : " + str(gs_space_dictionary_obj))
        counter = 0
        dataTable = []
        for data in jsonArray:
            dataArray = [Fore.GREEN + str(counter + 1) + Fore.RESET,
                         Fore.GREEN + data["name"] + Fore.RESET,
                         Fore.GREEN + data["resource"] + Fore.RESET,
                         Fore.GREEN + str(data["sla"]["zones"]) + Fore.RESET,
                         Fore.GREEN + data["processingUnitType"] + Fore.RESET,
                         Fore.GREEN + data["status"] + Fore.RESET
                         ]
            gs_space_dictionary_obj.add(str(counter + 1), str(data["name"]))
            counter = counter + 1
            dataTable.append(dataArray)
        printTabular(None, headers, dataTable)
        return gs_space_dictionary_obj
    except Exception as e:
        handleException(e)


def listSpacesOnServer(managerNodes):
    try:
        logger.info("listSpacesOnServer : managerNodes :" + str(managerNodes))
        managerHost = ''
        for node in managerNodes:
            status = getSpaceServerStatus(node.ip)
            logger.info("Ip :" + str(node.ip) + "Status : " + str(status))
            if (status == "ON"):
                managerHost = node.ip;
        logger.info("managerHost :" + managerHost)
        response = requests.get("http://" + managerHost + ":8090/v2/spaces")
        logger.info("response status of host :" + str(managerHost) + " status :" + str(response.status_code))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Existing spaces on cluster:")
        headers = [Fore.YELLOW + "Sr No." + Fore.RESET,
                   Fore.YELLOW + "Name" + Fore.RESET,
                   Fore.YELLOW + "PU Name" + Fore.RESET
                   ]
        gs_space_host_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_host_dictionary_obj : " + str(gs_space_host_dictionary_obj))
        counter = 0
        dataTable = []
        for data in jsonArray:
            dataArray = [Fore.GREEN + str(counter + 1) + Fore.RESET,
                         Fore.GREEN + data["name"] + Fore.RESET,
                         Fore.GREEN + data["processingUnitName"] + Fore.RESET
                         ]
            gs_space_host_dictionary_obj.add(str(counter + 1), str(data["name"]))
            counter = counter + 1
            dataTable.append(dataArray)
        # printTabular(None,headers,dataTable)
        return gs_space_host_dictionary_obj
    except Exception as e:
        handleException(e)

def proceedToKillResource(managerHost):
    logger.info("proceedToUndeployResource()")
    resourceName = str(
        input(Fore.YELLOW + "Enter name of zone kill [consumer] :" + Fore.RESET))
    if (len(str(resourceName)) == 0):
        resourceName = 'consumer'
    logger.info("resourceName :" + str(resourceName))

    # for host in spaceNodes:
    commandToExecute = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh container kill --zones " + str(
        resourceName)
    print(commandToExecute)
    logger.info(commandToExecute)
    with Spinner():
        output = executeRemoteCommandAndGetOutput(managerHost, 'root', commandToExecute)
        print(output)
        logger.info("Output:" + str(output))

def proceedToUndeployResource(managerHost):
    logger.info("proceedToUndeployResource()")
    resourceName = str(
        input(Fore.YELLOW + "Enter name of resource to undeploy [consumer] :" + Fore.RESET))
    if (len(str(resourceName)) == 0):
        resourceName = 'consumer'
    logger.info("resourceName :" + str(resourceName))

    # for host in spaceNodes:
    commandToExecute = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh service undeploy --drain-mode=ATTEMPT " + str(
        resourceName)
    print(commandToExecute)
    logger.info(commandToExecute)
    with Spinner():
        try:
            output = executeRemoteCommandAndGetOutput(managerHost, 'root', commandToExecute)
            print(output)
            logger.info("Output:" + str(output))
        except:
            verboseHandle.printConsoleError("Something went wrong.")


def get_gs_host_details(managerNodes):
    try:
        logger.info("get_gs_host_details() : managerNodes :" + str(managerNodes))
        for node in managerNodes:
            status = getSpaceServerStatus(node.ip)
            if (status == "ON"):
                managerHostConfig = node.ip;
        logger.info("managerHostConfig : " + str(managerHostConfig))
        response = requests.get('http://' + managerHostConfig + ':8090/v2/hosts',
                                headers={'Accept': 'application/json'})
        logger.info("response status of host :" + str(managerHostConfig) + " status :" + str(response.status_code))
        jsonArray = json.loads(response.text)
        gs_servers_host_dictionary_obj = host_dictionary_obj()
        for data in jsonArray:
            gs_servers_host_dictionary_obj.add(str(data['name']), str(data['address']))
        logger.info("gs_servers_host_dictionary_obj : " + str(gs_servers_host_dictionary_obj))
        return gs_servers_host_dictionary_obj
    except Exception as e:
        handleException(e)


def displaySpaceHostWithNumber(managerNodes, spaceNodes):
    try:
        logger.info(
            "displaySpaceHostWithNumber() managerNodes :" + str(managerNodes) + " spaceNodes :" + str(spaceNodes))
        gs_host_details_obj = get_gs_host_details(managerNodes)
        logger.info("gs_host_details_obj : " + str(gs_host_details_obj))
        counter = 0
        space_dict_obj = host_dictionary_obj()
        logger.info("space_dict_obj : " + str(space_dict_obj))
        for node in spaceNodes:
            print(node.name)
            if (gs_host_details_obj.__contains__(str(node.name)) or (str(node.name) in gs_host_details_obj.values())):
                space_dict_obj.add(str(counter + 1), node.name)
                counter = counter + 1
        logger.info("space_dict_obj : " + str(space_dict_obj))
        # verboseHandle.printConsoleWarning("Space hosts lists")
        headers = [Fore.YELLOW + "No" + Fore.RESET,
                   Fore.YELLOW + "Host" + Fore.RESET]
        dataTable = []
        for data in range(1, len(space_dict_obj) + 1):
            dataArray = [Fore.GREEN + str(data) + Fore.RESET,
                         Fore.GREEN + str(space_dict_obj.get(str(data))) + Fore.RESET]
            dataTable.append(dataArray)
        # printTabular(None,headers,dataTable)
        return space_dict_obj
    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Data Engine -> CR8 CDC pipelines -> Consumer -> Consumer Undeploy')
    try:
        managerNodes = config_get_manager_node()
        logger.info("managerNodes: main" + str(managerNodes))
        if (len(str(managerNodes)) > 0):
            spaceNodes = config_get_space_hosts()
            logger.info("spaceNodes: main" + str(spaceNodes))
            managerHost = getManagerHost(managerNodes)
            logger.info("managerHost : main" + str(managerHost))
            if (len(str(managerHost)) > 0):
                space_dict_obj = displaySpaceHostWithNumber(managerNodes, spaceNodes)
                if (len(space_dict_obj) > 0):
                    proceedToUndeployResource(managerHost)
                    proceedToKillResource(managerHost)
                else:
                    logger.info("Please check space server.")
                    verboseHandle.printConsoleInfo("Please check space server.")
            else:
                logger.info("Please check manager server status.")
                verboseHandle.printConsoleInfo("Please check manager server status.")
        else:
            logger.info("No Manager configuration found please check.")
            verboseHandle.printConsoleInfo("No Manager configuration found please check.")
    except Exception as e:
        handleException(e)
