#!/usr/bin/env python3
import argparse
import os
import sys

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_ssh import executeLocalCommandAndGetOutput

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
serviceName = 'catalogue-service.service'


def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to get status of Catalogue service')
    parser.add_argument('m', nargs='?')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])


def statusOfCatalogueService(args):
    with Spinner():
        executeLocalCommandAndGetOutput("sudo systemctl is-active --quiet "+serviceName)
    status = os.system('systemctl is-active --quiet '+serviceName)
    if (status == 0):
        verboseHandle.printConsoleInfo("ACTIVE")
    else:
        verboseHandle.printConsoleError("NOT ACTIVE")


if __name__ == '__main__':
    verboseHandle.printConsoleInfo("Status of Catalogue service")
    args = []
    args = myCheckArg()
    statusOfCatalogueService(args)
