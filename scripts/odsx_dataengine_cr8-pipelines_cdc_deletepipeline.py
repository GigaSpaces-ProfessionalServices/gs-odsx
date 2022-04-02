#!/usr/bin/env python3
import argparse
import importlib
import os
import sys

from scripts.logManager import LogManager

cdclist = importlib.import_module("odsx_dataengine_cr8-pipelines_cdc_list")
from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_dataEngine_nodes
from utils.ods_ssh import executeRemoteCommandAndGetOutput

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


def deletePipeline(args):
    deNodes = config_get_dataEngine_nodes()
    pipelineDict = cdclist.display_stream_list(args)
    selectedOption = int(input("Enter your option: "))
    if selectedOption != 99:
        if selectedOption in pipelineDict:
            configName = pipelineDict.get(selectedOption)
            user = 'root'
            scriptUser = 'dbsh'
            getClustercmd = "sudo -u " + scriptUser + " -H sh -c 'cat /home/dbsh/cr8/latest_cr8/etc/CR8Cluster.cfg"

            with Spinner():
                output = executeRemoteCommandAndGetOutput(deNodes[0].ip, user, getClustercmd)
                clusterName = ""
                for str in output.split("\n"):
                    if str.startswith("cr8ClusterName"):
                        clusterName = str.split("=")[1]
                        print("clusterName :" + clusterName)
                cmd = "sudo -u " + scriptUser + " -H sh -c '/home/dbsh/cr8/latest_cr8/utils/CR8_utils.sh  -deleteZkNode /dbsh/cr8/" + clusterName + "/configurations/" + configName
                output = executeRemoteCommandAndGetOutput(deNodes[0].ip, user, cmd)
                print(str(output))
            # jsonout = json.loads(output)
            # logger.info("output" + str(jsonout))
            # response = requests.post(
            #    'http://' + deNodes[0].ip + ':2050/CR8/CM/configurations/validateConfigurations/' + configName,
            #    data=json.dumps(jsonout),
            #    headers={'Accept': 'application/json'})
            # logger.info(str(response.status_code))
            # logger.info(str(response.text))
        else:
            verboseHandle.printConsoleError("Wrong option selected")


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Data Engine -> CR8 pipelines -> CDC -> Delete Pipeline')
    try:
        args = []
        args = myCheckArg()
        deletePipeline(args)
    except Exception as e:
        handleException(e)