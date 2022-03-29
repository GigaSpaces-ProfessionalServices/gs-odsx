#!/usr/bin/env python3
import argparse
import json
import os
import sys

import requests

from scripts.logManager import LogManager
from scripts.odsx_dataengine_cr8cdcpipelines_cdc_list import display_stream_list
from utils.ods_cluster_config import config_get_dataEngine_nodes

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


def show_details(args):
    deNodes = config_get_dataEngine_nodes("config/cluster.config")
    pipelineDict = display_stream_list(args)
    selectedOption = int(input("Enter your option: "))
    streamConfig = ""
    if (selectedOption != 99):
        if selectedOption in pipelineDict:
            configName = pipelineDict.get(selectedOption)
            print(configName)
            try:
                response = requests.get(
                    'http://' + deNodes[0].ip + ':2050/CR8/CM/configurations/getConfigurations/' + configName,
                    headers={'Accept': 'application/json'})
                streamConfig = json.loads(response.text)
            except Exception as e:
                verboseHandle.printConsoleError("Error occurred")
                with open(
                        '/home/jay/work/gigaspace/bofLeumi/intellij-ide/gs-odsx/config/stream-response-single-test.json',
                        'r') as myfile:
                    data1 = myfile.read()
                # parse file
                streamConfig = json.loads(data1)

            verboseHandle.printConsoleWarning("-------------------------------------------")
            verboseHandle.printConsoleInfo("Source : ")
            verboseHandle.printConsoleInfo("Name : " + streamConfig["name"])
            verboseHandle.printConsoleInfo("DB Type : " + streamConfig["basicProperties"]["source"]["dBType"])
            verboseHandle.printConsoleInfo("Host : " + streamConfig["basicProperties"]["source"]["host"])
            verboseHandle.printConsoleInfo("Port : " + streamConfig["basicProperties"]["source"]["port"])
            verboseHandle.printConsoleInfo("Service Name : " + streamConfig["basicProperties"]["source"]["serviceName"])
            verboseHandle.printConsoleInfo("Username : " + streamConfig["basicProperties"]["source"]["username"])
            verboseHandle.printConsoleInfo("Destination : ")
            verboseHandle.printConsoleInfo("DB Type : " + streamConfig["basicProperties"]["target"]["dBType"])
            verboseHandle.printConsoleInfo("Host : " + streamConfig["basicProperties"]["target"]["host"])
            verboseHandle.printConsoleInfo("Kafka Topic : " + streamConfig["basicProperties"]["target"]["kafkaTopic"])
            verboseHandle.printConsoleWarning("-------------------------------------------")
        else:
            verboseHandle.printConsoleError("Wrong option selected")

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Data Engine -> CR8 CDC pipelines  -> CDC -> Show')
    try:
        args = []
        args = myCheckArg()
        show_details(args)
    except Exception as e:
        handleException(e)
