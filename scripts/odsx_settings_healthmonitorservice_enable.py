#!/usr/bin/env python3
import argparse
import os
import sys

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_ssh import executeLocalCommandAndGetOutput

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])


def startHealthmonitorService(args):
    verboseHandle.printConsoleWarning("Are you sure, you want to start monitor service ? [Yes][No][Cancel]")
    from utils.odsx_keypress import userInputWrapper
    choice = str(userInputWrapper(""))
    if choice.casefold() == 'no':
        exit(0)
    with Spinner():
        executeLocalCommandAndGetOutput("sudo systemctl start --quiet odsxhealthcheck.service")
    status = os.system('systemctl is-active --quiet odsxhealthcheck.service')
    if (status == 0):
        verboseHandle.printConsoleInfo("Service started successfully")
    else:
        verboseHandle.printConsoleError("Service failed to start")


if __name__ == '__main__':
    verboseHandle.printConsoleInfo("Starting monitor service")
    args = []
    args = myCheckArg()
    startHealthmonitorService(args)
