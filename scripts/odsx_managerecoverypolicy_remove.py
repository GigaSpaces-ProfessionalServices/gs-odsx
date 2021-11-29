#!/usr/bin/env python3
import os

from scripts.logManager import LogManager

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

if __name__ == '__main__':
    verboseHandle.printConsoleInfo("Remove Policy")