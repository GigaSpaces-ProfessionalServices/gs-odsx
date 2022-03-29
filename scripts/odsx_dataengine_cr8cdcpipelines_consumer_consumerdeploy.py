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


def proceedToCreateGSC():
    logger.info("proceedToCreateGSC()")
    # for host in managerNodes:
    #    scp_upload(str(host.ip),'root',dPipelineLocationSource,dPipelineLocationTarget)
    spaceNodes = config_get_space_hosts()
    for host in spaceNodes:
        # scp_upload(str(host.ip),'root',dPipelineLocationSource,dPipelineLocationTarget)
        # commandToExecute = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh container create --count="+str(numberOfGSC)+" --zone="+str(zoneGSC)+" --memory="+str(memoryGSC)+" --vm-option -Dspring.profiles.active=connector --vm-option -Dpipeline.config.location="+str(dPipelineLocationTarget)+" "+str(host.ip)
        commandToExecute = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh container create --count=" + str(
            numberOfGSC) + " --zone=" + str(zoneGSC) + " --memory=" + str(
            memoryGSC) + " " + str(host.ip)
        print(commandToExecute)
        logger.info(commandToExecute)
        with Spinner():
            output = executeRemoteCommandAndGetOutput(managerHost, 'root', commandToExecute)
            print(output)
            logger.info("Output:" + str(output))


def createGSCInputParam(managerHost, spaceNode, confirmCreateGSC):
    logger.info("createGSCInputParam()")
    global numberOfGSC
    global zoneGSC
    global memoryGSC
    global createGsc

    if confirmCreateGSC == "y" or confirmCreateGSC == "yes":
        createGsc = True
    else:
        createGsc = False
    if createGsc:
        numberOfGSC = str(input(Fore.YELLOW + "Enter number of GSCs per host [1] : " + Fore.RESET))
        while (len(str(numberOfGSC)) == 0):
            numberOfGSC = 1
        logger.info("numberOfGSC :" + str(numberOfGSC))

        zoneGSC = str(input(Fore.YELLOW + "Enter zone of GSC to create [consumer] : " + Fore.RESET))
        while (len(str(zoneGSC)) == 0):
            zoneGSC = 'consumer'
        logger.info("zoneGSC :" + str(zoneGSC))
        memoryGSC = str(input(Fore.YELLOW + "Enter memory of GSC [4g] : " + Fore.RESET))
        while (len(str(memoryGSC)) == 0):
            memoryGSC = '4g'
    else:
        zoneGSC = str(input(Fore.YELLOW + "Enter zone of GSC to deploy PU [consumer] : " + Fore.RESET))
        while (len(str(zoneGSC)) == 0):
            zoneGSC = 'consumer'
        logger.info("zoneGSC :" + str(zoneGSC))

def uploadFileRest(managerHostConfig):
    try:
        logger.info("uploadFileRest : managerHostConfig : " + str(managerHostConfig))
        pathOfSourcePU = resourcePath + "/" + resourceName

        logger.info("url : " + "curl -X PUT -F 'file=@" + str(
            pathOfSourcePU) + "' http://" + managerHostConfig + ":8090/v2/pus/resources")
        status = os.system(
            "curl -X PUT -F 'file=@" + str(pathOfSourcePU) + "' http://" + managerHostConfig + ":8090/v2/pus/resources")
        logger.info("status : " + str(status))
    except Exception as e:
        handleException(e)


def validateResponseGetDescription(responseCode):
    logger.info("validateResponse() " + str(responseCode))
    response = requests.get("http://" + managerHost + ":8090/v2/requests/" + str(responseCode))
    jsonData = json.loads(response.text)
    logger.info("response : " + str(jsonData))
    if (str(jsonData["status"]).__contains__("failed")):
        return "Status :" + str(jsonData["status"]) + " Description:" + str(jsonData["error"])
    else:
        return "Status :" + str(jsonData["status"]) + " Description:" + str(jsonData["description"])


def proceedToDeployPU(data):
    logger.info("proceedToDeployPU()")
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    logger.info("url : " + "http://" + managerHost + ":8090/v2/pus")

    response = requests.post("http://" + managerHost + ":8090/v2/pus", data=json.dumps(data), headers=headers)
    deployResponseCode = str(response.content.decode('utf-8'))
    print("deploy response_content : " + str(deployResponseCode))
    print("deploy status_code : " + str(response.status_code))
    logger.info("deployResponseCode :" + str(deployResponseCode))
    if (response.status_code == 202):
        verboseHandle.printConsoleInfo("Deployed successfully")
    else:
        logger.info("Unable to deploy :" + deployResponseCode)
        verboseHandle.printConsoleError("Unable to deploy : " + deployResponseCode)


def getDataPUREST():
    data = {
        "resource": "" + resourceName + "",
        "topology": {
            "instances": int(partition),
        },
        "sla": {
            "zones": [
                "" + zoneGSC + ""
            ],
        },
        "name": "" + processingUnitName + "",
        "maxInstancesPerMachine": int(maxInstancesPerMachine)
    }
    return data


def proceedToDeployPUInputParam(managerHost):
    logger.info("proceedToDeployPUInputParam()")
    global resourceName
    global processingUnitName
    global resourcePath

    resourceName = str(
        input(Fore.YELLOW + "Enter name of PU to deploy [cdc_tables-dih-consumer.war] :" + Fore.RESET))
    if (len(str(resourceName)) == 0):
        resourceName = 'cdc_tables-dih-consumer.war'
    logger.info("nameOfPU :" + str(resourceName))

    resourcePath = str(input(Fore.YELLOW + "Enter path of PU to deploy [/dbagiga] :" + Fore.RESET))
    if (len(str(resourcePath)) == 0):
        resourcePath = '/dbagiga'
    logger.info("nameOfPU :" + str(resourcePath))
    processingUnitName = str(input(Fore.YELLOW + "Enter Resource Name [consumer] : " + Fore.RESET))
    while (len(str(processingUnitName)) == 0):
        processingUnitName = 'consumer'
    logger.info("processingUnitName :" + str(processingUnitName))

    uploadFileRest(managerHost)

    global partition
    partition = '1'

    global maxInstancesPerMachine
    maxInstancesPerMachine = '1'
    logger.info("maxInstancePerVM Of PU :" + str(maxInstancesPerMachine))

    if createGsc:
        proceedToCreateGSC()
    proceedToDeployPU(getDataPUREST())


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Data Engine -> CR8 CDC pipelines -> Consumer -> Consumer Deploy')
    try:
        managerNodes = config_get_manager_node()
        logger.info("managerNodes: main" + str(managerNodes))
        if (len(str(managerNodes)) > 0):
            spaceNodes = config_get_space_hosts()
            logger.info("spaceNodes: main" + str(spaceNodes))
            managerHost = getManagerHost(managerNodes)
            # proceedToCreateStartDb2FeederFile("oar")
            logger.info("managerHost : main" + str(managerHost))
            if (len(str(managerHost)) > 0):
                # listSpacesOnServer(managerNodes)
                # listDeployed(managerHost)
                space_dict_obj = displaySpaceHostWithNumber(managerNodes, spaceNodes)
                if (len(space_dict_obj) > 0):
                    confirmCreateGSC = str(input(Fore.YELLOW + "Do you want to create GSC ? (y/n) [y] : "))
                    if (len(str(confirmCreateGSC)) == 0 or confirmCreateGSC == 'y'):
                        confirmCreateGSC = 'y'
                    createGSCInputParam(managerHost, spaceNodes, confirmCreateGSC)
                    proceedToDeployPUInputParam(managerHost)
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
