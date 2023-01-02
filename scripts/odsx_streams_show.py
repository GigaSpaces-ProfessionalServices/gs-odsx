#!/usr/bin/env python3
import argparse
import json
import os
import sys

from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_cdc_streams
from utils.ods_ssh import executeRemoteCommandAndGetOutput

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    parser.add_argument('-id', '--streamid',
                        help='Stream Id',
                        default='1')
    parser.add_argument('-u', '--username',
                        help='Server User name',
                        default='ec2-user')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])


def display_stream_json_data(args=None):
    verboseHandle.printConsoleWarning('Servers -> Streams -> Show')
    streams = config_get_cdc_streams()
    if args.m is not None:
        verboseHandle.printConsoleWarning("Please choose an option from below :")
    streamDict = {}
    counter = 0
    for stream in streams:
        counter = counter + 1
        if args.m == None:
            streamDict.update({stream.id: stream})
        else:
            streamDict.update({counter: stream})
            verboseHandle.printConsoleInfo(
                str(counter) + ". " + stream.id + " (" + stream.name + ")")

    optionMainMenu = None
    if args.m == None:
        optionMainMenu = args.streamid
    else:
        from utils.odsx_keypress import userInputWrapper
        optionMainMenu = int(userInputWrapper("Enter your option: "))
    if streamDict.get(optionMainMenu) is None:
        verboseHandle.printConsoleError("please select valid id")
        exit(0)

    stream = streamDict.get(optionMainMenu)
    userName = None
    if args.m == None:
        userName = args.username
    else:
        from utils.odsx_keypress import userInputWrapper
        userName = str(userInputWrapper("username [ec2-user] : "))
    if userName == "":
        userName = "ec2-user"
    out = executeRemoteCommandAndGetOutput(stream.serverip, userName,
                                           "cat " + stream.serverPathOfConfig)
    # print(out)
    jsonout = json.loads(out)
    verboseHandle.printConsoleWarning("-------------------------------------------")
    verboseHandle.printConsoleInfo("Name : " + jsonout["name"])
    verboseHandle.printConsoleInfo("Last Modified : " + jsonout["lastModified"])
    verboseHandle.printConsoleInfo("Stream Type : " + jsonout["streamType"])
    verboseHandle.printConsoleInfo("Source Db Type : " + jsonout["basicProperties"]["source"]["dBType"])
    verboseHandle.printConsoleInfo("Target Db Type : " + jsonout["basicProperties"]["target"]["dBType"])
    verboseHandle.printConsoleInfo("Target Db Type : " + jsonout["basicProperties"]["target"]["jmsType"])
    verboseHandle.printConsoleInfo(
        "Sys Base Fetch Mode : " + jsonout["advancedProperties"]["logReader"]["sybaseFetchMode"])
    verboseHandle.printConsoleInfo("Fetcher Mode : " + jsonout["advancedProperties"]["fetcher"]["mode"])
    verboseHandle.printConsoleInfo("Start Date : " + jsonout["advancedProperties"]["fetcher"]["startDate"])
    verboseHandle.printConsoleInfo("Applier Mode : " + jsonout["advancedProperties"]["applier"]["mode"])
    verboseHandle.printConsoleInfo("Applier Journal Type : " + jsonout["advancedProperties"]["applier"]["journalType"])
    verboseHandle.printConsoleWarning("-------------------------------------------")


if __name__ == '__main__':
    args = myCheckArg()
    display_stream_json_data(args)
