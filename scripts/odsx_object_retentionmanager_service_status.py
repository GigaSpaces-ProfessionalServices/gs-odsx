#!/usr/bin/env python3
import argparse
import os
import sys

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_ssh import executeLocalCommandAndGetOutput

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
serviceName = 'retention-manager.service'

def statusOfService():
    with Spinner():
        executeLocalCommandAndGetOutput("sudo systemctl is-active --quiet "+serviceName)
    status = os.system('systemctl is-active --quiet '+serviceName)
    if (status == 0):
        verboseHandle.printConsoleInfo("ACTIVE")
    else:
        verboseHandle.printConsoleError("NOT ACTIVE")


if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Object -> RetentionManager -> Service -> Status")
    statusOfService()
