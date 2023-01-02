#!/usr/bin/env python3
import sys

import argparse
import os

from scripts.logManager import LogManager
from utils.ods_ssh import executeLocalCommandAndGetOutput

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])


def list_wan_gateway_info(args):
    from utils.odsx_keypress import userInputWrapper
    selectedValue = str(
        userInputWrapper("Enter wan space locators ['127.0.1.1:4166,127.0.1.1:4266'] : "))
    if selectedValue == "":
        selectedValue = "127.0.1.1:4166,127.0.1.1:4266"
        # selectedValue = "localhost:4174"
    out = executeLocalCommandAndGetOutput(
        "java -jar wan_gateway/wangateway-util.jar -locators " + selectedValue + " -menu spacelist")
    #verboseHandle.printConsoleInfo(out)
    return out

if __name__ == '__main__':
    args = []
    args = myCheckArg()
    list_wan_gateway_info(args)
