#!/usr/bin/env python3
import argparse
import datetime
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
        Fore.YELLOW + "isRunning" + Fore.RESET,
        Fore.YELLOW + "State" + Fore.RESET,
        Fore.YELLOW + "State Timestamp" + Fore.RESET,
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
        user = 'root'
        scriptUser = 'dbsh'
        cmd = "sudo -u " + scriptUser + " -H sh -c '/home/dbsh/cr8/latest_cr8/utils/CR8_Stream_ctl status " + str(
            stream["configurationName"]) + "'"
        with Spinner():
            response = executeRemoteCommandAndGetOutput(deNodes[0].ip, user, cmd)
        streamSyncData = json.loads(str(response))
        print(str(streamSyncData))
        dateTime = ""
        if streamSyncData["streamStatus"]["stateTimeStamp"] != "":
            epochTimeresponse = requests.get(
                'http://' + deNodes[0].ip + ':2050/CR8/utils/getDateTimeFromEpoch/' + streamSyncData["streamStatus"][
                    "stateTimeStamp"])
            dateTime = str(epochTimeresponse.text)
        counter = counter + 1
        dataArray = [counter, streamSyncData["streamStatus"]["name"],
                     streamSyncData["isRunning"], streamSyncData["streamStatus"]["state"], dateTime]
        pipelineDict.update({counter: stream["configurationName"]})
        datetime1 = datetime.datetime.fromtimestamp(streamSyncData["streamStatus"]["stateTimeStamp"])
        print(datetime1)

        data.append(dataArray)

    printTabular(None, printHeaders, data)
    return pipelineDict


def startStream(args):
    deNodes = config_get_dataEngine_nodes()
    pipelineDict = display_stream_list(args)
    selectedOption = int(input("Enter your option: "))
    if (selectedOption != 99):
        configName = pipelineDict.get(selectedOption)
        response = requests.get(
            'http://' + deNodes[0].ip + ':2050/CR8/CM/configurations/start/' + configName)
        logger.info(str(response.status_code))
        print(str(response.status_code))
        logger.info(str(response.text))
        print(str(response.text))
        if response.status_code == 200 and response.text.__contains__("started"):
            verboseHandle.printConsoleInfo("Started online stream " + configName)
        else:
            verboseHandle.printConsoleError("Failed to start stream " + configName)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Data Engine -> List -> CR8 CDC pipelines  -> Start online stream')
    try:
        args = []
        args = myCheckArg()
        startStream(args)
    except Exception as e:
        handleException(e)
