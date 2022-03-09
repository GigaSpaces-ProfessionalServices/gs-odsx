#!/usr/bin/env python3
import argparse
import os
import sys

import requests

from scripts.logManager import LogManager
from scripts.odsx_dataengine_list_cr8cdcpipelines_list import display_stream_list
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


def stopStream(args):
    deNodes = config_get_dataEngine_nodes()
    pipelineDict = display_stream_list(args)
    selectedOption = int(input("Enter your option: "))
    if (selectedOption != 99):
        configName = pipelineDict.get(selectedOption)
        response = requests.get(
            'http://' + deNodes[0].ip + ':2050/CR8/CM/configurations/stop/' + configName)
        logger.info(str(response.status_code))
        logger.info(str(response.text))
        if response.status_code == 200 and response.text.__contains__("has been killed"):
            verboseHandle.printConsoleInfo("Stopped online stream " + configName)
        else:
            verboseHandle.printConsoleError("Failed to stop stream " + configName)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Data Engine -> List -> CR8 CDC pipelines  -> Stop online stream')
    try:
        args = []
        args = myCheckArg()
        stopStream(args)
    except Exception as e:
        handleException(e)
