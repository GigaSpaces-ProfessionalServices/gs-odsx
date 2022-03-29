#!/usr/bin/env python3
import argparse
import json
import os
import sys

import requests
from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_dataEngine_nodes, config_get_manager_node, \
    config_get_dataIntegration_nodes
from utils.ods_ssh import executeRemoteCommandAndGetOutputValuePython36
from utils.ods_validation import getSpaceServerStatus
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
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])

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

def getManagerHost(managerNodes):
    managerHost=""
    try:
        logger.info("getManagerHost() : managerNodes :"+str(managerNodes))
        for node in managerNodes:
            status = getSpaceServerStatus(node.ip)
            if(status=="ON"):
                managerHost = node.ip
        return managerHost
    except Exception as e:
        handleException(e)

def display_stream_list(args):
    deNodes = config_get_dataEngine_nodes()
    managerNodes = config_get_manager_node()
    diNodes = config_get_dataIntegration_nodes()
    printHeaders = [
        Fore.YELLOW + "#" + Fore.RESET,
        Fore.YELLOW + "pipeline name (topic)" + Fore.RESET,
        Fore.YELLOW + "Consumer Status" + Fore.RESET,
        Fore.YELLOW + "messages in topic (count)" + Fore.RESET,
        # Fore.YELLOW + "getStatus" + Fore.RESET,
        Fore.YELLOW + "full sync fetch to Kafka status" + Fore.RESET,
        Fore.YELLOW + "online stream fetch to Kafka status" + Fore.RESET
    ]
    data = []
    pipelineDict = {}
    global streams
    try:
        response = requests.get('http://' + deNodes[0].ip + ':2050/CR8/CM/configurations/getStatus',
                                headers={'Accept': 'application/json'})
        streams = json.loads(response.text)
    except Exception as e:
        verboseHandle.printConsoleError("Error occurred")
        with open('/home/jay/work/gigaspace/bofLeumi/intellij-ide/gs-odsx/config/stream-response-test.json',
                  'r') as myfile:
            data1 = myfile.read()
        # parse file
        streams = json.loads(data1)
    counter = 0
    for stream in streams:
        # response = requests.get('http://' + deNodes[0].ip + ':2050/CR8/CM/configurations/getFullSyncProgress/' + str(
        #    stream["configurationName"]))
        # fullSyncData = json.loads(response.text)

        user = 'root'
        scriptUser = 'dbsh'
        fullSyncCmd = "sudo -u " + scriptUser + " -H sh -c '/home/dbsh/cr8/latest_cr8/utils/CR8Sync.ctl status " + str(
            stream["configurationName"]) + "'"

        cmd = "sudo -u " + scriptUser + " -H sh -c '/home/dbsh/cr8/latest_cr8/utils/CR8_Stream_ctl.sh status " + str(
            stream["configurationName"]) + "'"

        topicCountCmd = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$KAFKAPATH/bin/kafka-run-class.sh kafka.tools.GetOffsetShell --broker-list "+diNodes[0].ip+":9092 --topic " + str(
            stream["configurationName"]) +" | awk -F  \":\" '{sum += $3} END {print sum}'"
        with Spinner():
            streamStatus = executeRemoteCommandAndGetOutputValuePython36(deNodes[0].ip, user, cmd)
            fullSyncStatus = executeRemoteCommandAndGetOutputValuePython36(deNodes[0].ip, user, fullSyncCmd)
            topicCountResponse = executeRemoteCommandAndGetOutputValuePython36(diNodes[0].ip, user, topicCountCmd)

            managerNode = getManagerHost(managerNodes)
            responseManager = requests.get('http://' + managerNode + ':8090/v2/data-pipelines/'+stream["configurationName"]+'/consumer/status',
                                           headers={'Accept': 'application/json'})
            jsonResponseManager = json.loads(response.text)

        streamStatus = streamStatus.split("\n", 1)[1]
        if streamStatus != "":
            streamStatusJson = json.loads(str(streamStatus))
            streamStatus = streamStatusJson["streamStatus"]["state"]
        else:
            streamStatus = ""

        fullSyncStatusDisplay = "STOPPED"
        if fullSyncStatus.__contains__("is running"):
            fullSyncStatusDisplay = "RUNNING"
            fullSyncStatusDisplay = Fore.GREEN + fullSyncStatusDisplay + Fore.RESET
        elif fullSyncStatusDisplay == "STOPPED":
            fullSyncStatusDisplay = Fore.YELLOW + fullSyncStatusDisplay + Fore.RESET
        elif streamStatus == "CLEANED":
            fullSyncStatusDisplay = Fore.WHITE + fullSyncStatusDisplay + Fore.RESET

        if streamStatus == "STARTED":
            streamStatus = "RUNNING"
            streamStatus = Fore.GREEN + streamStatus + Fore.RESET
        elif streamStatus == "STOPPED":
            streamStatus = Fore.YELLOW + streamStatus + Fore.RESET
        elif streamStatus == "CLEANED":
            streamStatus = Fore.WHITE + streamStatus + Fore.RESET

        counter = counter + 1
        # state = Fore.GREEN + "RUNNING" + Fore.RESET
        # if str(stream["state"]).upper() == "STOPPED":
        #    state = Fore.RED + "STOPPED" + Fore.RESET
        dataArray = [counter, stream["configurationName"],
                     jsonResponseManager["status"],
                     str(topicCountResponse),
                     #    stream["state"],
                     #    stream["state"],
                     fullSyncStatusDisplay,
                     streamStatus]
        pipelineDict.update({counter: stream["configurationName"]})
        data.append(dataArray)
    data.append(dataArray)
    printTabular(None, printHeaders, data)
    return pipelineDict


if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Data Engine -> CR8 pipelines -> CDC -> List")
    args = []
    args = myCheckArg()
    display_stream_list(args)
