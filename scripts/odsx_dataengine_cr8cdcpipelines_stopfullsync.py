#!/usr/bin/env python3
import argparse
import os
import sys

from scripts.logManager import LogManager
from scripts.odsx_dataengine_cr8cdcpipelines_startfullsync import display_stream_list
from utils.ods_cluster_config import config_get_dataEngine_nodes
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36, executeRemoteCommandAndGetOutput

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
    if selectedOption != 99:
        if selectedOption in pipelineDict:
            configName = pipelineDict.get(selectedOption)
            user = 'root'
            scriptUser = 'dbsh'
            cmd = "sudo -u " + scriptUser + " -H sh -c '/home/dbsh/cr8/latest_cr8/utils/CR8Sync.ctl stop " + configName + "'"
            output = executeRemoteCommandAndGetOutput(deNodes[0].ip, user, cmd)
            print(str(output))
            # cmd = "/home/dbsh/cr8/latest_cr8/utils/cr8CR8Sync.ctl stop " + configName
            # output = executeRemoteCommandAndGetOutputPython36(deNodes[0].ip, user, cmd)
            # verboseHandle.printConsoleInfo(str(output))
            if str(output).__contains__("has been killed"):
                verboseHandle.printConsoleInfo("Stopped full sync " + configName)
            else:
                verboseHandle.printConsoleError("Failed to stop full sync " + configName)
        else:
            verboseHandle.printConsoleError("Wrong option selected")


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Data Engine -> CR8 CDC pipelines  -> Stop Full sync')
    try:
        args = []
        args = myCheckArg()
        stopStream(args)
    except Exception as e:
        handleException(e)
