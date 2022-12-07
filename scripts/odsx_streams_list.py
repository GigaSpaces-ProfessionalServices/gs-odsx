#!/usr/bin/env python3
import argparse
import json
import os
import sys
from datetime import datetime

from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_cdc_streams
from utils.ods_ssh import executeRemoteCommandAndGetOutput
from utils.ods_validation import isValidHost
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
    streams = config_get_cdc_streams()
    #if args.m is not None:
    verboseHandle.printConsoleWarning("MENU -> STREAMS -> List\n")
    headers=[Fore.YELLOW+"ID"+Fore.RESET,
             Fore.YELLOW+"Name"+Fore.RESET,
             Fore.YELLOW+"Status"+Fore.RESET,
             Fore.YELLOW+"StreamType"+Fore.RESET,
             Fore.YELLOW+"Description"+Fore.RESET,
             Fore.YELLOW+"CreationDate"+Fore.RESET,
             Fore.YELLOW+"ServerIP"+Fore.RESET,
             Fore.YELLOW+"ServerJsonConfigPath"+Fore.RESET]
    data=[]
    dataArray=[]
    for stream in streams:
        dt_string = stream.creationDate
        dt_time_obj = datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")
        dt_stream = dt_time_obj.strftime('%Y-%m-%d')
        if(isValidHost(stream.serverip)):
            try:
                out = executeRemoteCommandAndGetOutput(stream.serverip, "ec2-user",
                                                       "cat " + stream.serverPathOfConfig)

                jsonout = json.loads(out)
                if (str(stream.status).casefold() == 'running'):
                    dataArray=[Fore.GREEN+stream.id,
                              stream.name,
                              Fore.YELLOW + stream.status+Fore.GREEN,
                              jsonout["basicProperties"]["source"]["dBType"],
                              stream.description,
                              dt_stream,
                              stream.serverip,
                              stream.serverPathOfConfig]
                    data.append(dataArray)
                elif (str(stream.status).casefold() == 'stopped'):
                    dataArray=[Fore.GREEN+stream.id,
                              stream.name,
                              Fore.RED + stream.status+Fore.GREEN,
                              jsonout["basicProperties"]["source"]["dBType"],
                              stream.description,
                              dt_stream,
                              stream.serverip,
                              stream.serverPathOfConfig]
                    data.append(dataArray)
            except Exception as e:
                dataArray =displayStaticOutput(stream,dt_stream,dataArray)
                data.append(dataArray)
        else:
            dataArray =displayStaticOutput(stream,dt_stream,dataArray)
            data.append(dataArray)
    printTabularStream(None,headers,data)


def displayStaticOutput(stream,dt_stream,dataArray):
    if (str(stream.status).casefold() == 'running'):
        dataArray=[Fore.GREEN+str(stream.id),
                  stream.name ,
                  Fore.YELLOW + stream.status+Fore.GREEN,
                   "N/A",
                   stream.description,
                   dt_stream,
                   stream.serverip,
                  stream.serverPathOfConfig]
        return dataArray
    elif (str(stream.status).casefold() == 'stopped'):
        dataArray=[Fore.GREEN+str(stream.id),
                  stream.name ,
                  Fore.RED +stream.status +Fore.GREEN,
                  "N/A" ,
                  stream.description ,
                  dt_stream ,
                  stream.serverip ,
                  stream.serverPathOfConfig]
        return dataArray
if __name__ == '__main__':
    args = []
    args = myCheckArg()
    display_stream_list(args)
