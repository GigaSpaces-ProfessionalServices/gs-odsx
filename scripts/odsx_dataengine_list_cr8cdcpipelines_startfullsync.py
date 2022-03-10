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


def display_stream_list(args):
    deNodes = config_get_dataEngine_nodes()
    printHeaders = [
        Fore.YELLOW + "#" + Fore.RESET,
        Fore.YELLOW + "Name" + Fore.RESET,
        Fore.YELLOW + "Status" + Fore.RESET,
        Fore.YELLOW + "Rows Completed" + Fore.RESET,
        Fore.YELLOW + "Time Completed" + Fore.RESET,
        Fore.YELLOW + "Work Completed (%)" + Fore.RESET,
        Fore.YELLOW + "Progress Update Time" + Fore.RESET
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
        # print(stream)
        response = requests.get('http://' + deNodes[0].ip + ':2050/CR8/CM/configurations/getFullSyncProgress/' + str(
            stream["configurationName"]))
        streamSyncData = json.loads(response.text)
        print(str(streamSyncData))
        counter = counter + 1
        state = Fore.GREEN + "RUNNING" + Fore.RESET
        if str(stream["state"]).upper() == "STOPPED":
            state = Fore.RED + "STOPPED" + Fore.RESET
        dataArray = [counter, stream["configurationName"],
                     state, streamSyncData["rowsCompleted"], streamSyncData["timeCompleted"],
                     streamSyncData["pctWorkCompleted"], streamSyncData["progressUpdateTime"]]
        pipelineDict.update({counter: stream["configurationName"]})
        data.append(dataArray)

    printTabular(None, printHeaders, data)
    return pipelineDict


def startStream(args):
    deNodes = config_get_dataEngine_nodes()
    pipelineDict = display_stream_list(args)
    selectedOption = int(input("Enter your option: "))
    if (selectedOption != 99):
        configName = pipelineDict.get(selectedOption)
        user = 'root'
        scriptUser = 'dbsh'
        cmd = "sudo -u " + scriptUser + " -H sh -c '/home/dbsh/cr8/latest_cr8/utils/CR8Sync.ctl start " + configName + "'"
        with Spinner():
            output = executeRemoteCommandAndGetOutput(deNodes[0].ip, user, cmd)
        # cmd = "/home/dbsh/cr8/latest_cr8/utils/cr8CR8Sync.ctl start " + configName
        # output = executeRemoteCommandAndGetOutputPython36(deNodes[0].ip, user, cmd)
        # verboseHandle.printConsoleInfo(str(output))
        if str(output).__contains__("start"):
            verboseHandle.printConsoleInfo("Started full sync " + configName)
        else:
            verboseHandle.printConsoleError("Failed to start full sync " + configName)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Data Engine -> List -> CR8 CDC pipelines  -> Start Full sync')
    try:
        args = []
        args = myCheckArg()
        startStream(args)
    except Exception as e:
        handleException(e)
