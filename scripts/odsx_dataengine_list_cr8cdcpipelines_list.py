#!/usr/bin/env python3
import argparse
import json
import os
import sys

import requests
from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_dataEngine_nodes
from utils.odsx_print_tabular_data import printTabularStream

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
        Fore.YELLOW + "Name" + Fore.RESET,
        Fore.YELLOW + "Status" + Fore.RESET
    ]
    data = []
    dataArray = []
    response = requests.get('http://' + deNodes[0].ip + ':2050/CR8/CM/configurations/getStatus',
                       headers={'Accept': 'application/json'})
    streams = json.loads(response.text)

    for stream in streams:
        try:
            dataArray = [stream["configurationName"],
                         stream["state"]]
            data.append(dataArray)
        except Exception as e:
            verboseHandle.printConsoleError("Error occurred")
            data.append(dataArray)
    printTabularStream(None, printHeaders, data)


def displayStaticOutput(stream, dt_stream, dataArray):
    if (str(stream.status).casefold() == 'running'):
        dataArray = [Fore.GREEN + str(stream.id),
                     stream.name,
                     Fore.YELLOW + stream.status + Fore.GREEN,
                     "N/A",
                     stream.description,
                     dt_stream,
                     stream.serverip,
                     stream.serverPathOfConfig]
        return dataArray
    elif (str(stream.status).casefold() == 'stopped'):
        dataArray = [Fore.GREEN + str(stream.id),
                     stream.name,
                     Fore.RED + stream.status + Fore.GREEN,
                     "N/A",
                     stream.description,
                     dt_stream,
                     stream.serverip,
                     stream.serverPathOfConfig]
        return dataArray


if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Data Engine -> List -> CR8 CDC pipelines  -> List")
    args = []
    args = myCheckArg()
    display_stream_list(args)
