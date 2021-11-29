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


def statusOfHealthmonitorService(args):
    with Spinner():
        executeLocalCommandAndGetOutput("sudo systemctl is-active --quiet odsxhealthcheck.service")
    status = os.system('systemctl is-active --quiet odsxhealthcheck.service')
    if (status == 0):
        verboseHandle.printConsoleInfo("active")
    else:
        verboseHandle.printConsoleError("not active")


if __name__ == '__main__':
    verboseHandle.printConsoleInfo("status of monitor service")
    args = []
    args = myCheckArg()
    statusOfHealthmonitorService(args)
