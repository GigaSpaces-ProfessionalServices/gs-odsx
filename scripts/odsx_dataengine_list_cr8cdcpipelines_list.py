#!/usr/bin/env python3
import argparse
import json
import os
import sys

import requests
from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_dataEngine_nodes
from utils.ods_ssh import executeRemoteCommandAndGetOutput
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


def display_stream_list(args):
    deNodes = config_get_dataEngine_nodes()
    printHeaders = [
        Fore.YELLOW + "#" + Fore.RESET,
        Fore.YELLOW + "Name" + Fore.RESET,
        Fore.YELLOW + "getStatus" + Fore.RESET,
        Fore.YELLOW + "getFullSyncProgress Status" + Fore.RESET,
        Fore.YELLOW + "Stream status" + Fore.RESET
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
        response = requests.get('http://' + deNodes[0].ip + ':2050/CR8/CM/configurations/getFullSyncProgress/' + str(
            stream["configurationName"]))
        fullSyncData = json.loads(response.text)

        user = 'root'
        scriptUser = 'dbsh'
        cmd = "sudo -u " + scriptUser + " -H sh -c '/home/dbsh/cr8/latest_cr8/utils/CR8_Stream_ctl status " + str(
            stream["configurationName"]) + "'"
        with Spinner():
            streamStatus = executeRemoteCommandAndGetOutput(deNodes[0].ip, user, cmd)
        streamStatusJson = json.loads(str(streamStatus))

        counter = counter + 1
        # state = Fore.GREEN + "RUNNING" + Fore.RESET
        # if str(stream["state"]).upper() == "STOPPED":
        #    state = Fore.RED + "STOPPED" + Fore.RESET
        dataArray = [counter, stream["configurationName"], stream["state"], fullSyncData["status"],
                     streamStatusJson["streamStatus"]["state"]]
        pipelineDict.update({counter: stream["configurationName"]})
        data.append(dataArray)

    printTabular(None, printHeaders, data)
    return pipelineDict


if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Data Engine -> List -> CR8 CDC pipelines  -> List")
    args = []
    args = myCheckArg()
    display_stream_list(args)
