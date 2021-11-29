#!/usr/bin/env python3

import argparse
import os
import sys

from scripts.logManager import LogManager

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


def check_arg(args=None):
    parser = argparse.ArgumentParser(description='Script to check snapshot retention')
    parser.add_argument('--retentionlocation',
                        help='Location to keep backup for snapshots')
    parser.add_argument('m', nargs='?')
    verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])
    return parser.parse_args(args)


def update_app_config_file(linePatternToReplace, inputMsg, args):
    file_name = "config/app.config"
    lines = open(file_name, 'r').readlines()
    lineNo = -1
    for line in lines:
        lineNo = lineNo + 1
        if line.startswith("#"):
            continue
        elif line.startswith(linePatternToReplace):
            break
    previousValue = ""
    if args.retentionlocation is None:
        previousValue = lines[lineNo].replace("\n", "").replace(linePatternToReplace + "=",
                                                                "")
        selectedValue = str(input(
            inputMsg + " [current '" + previousValue + "'] : "))
    else:
        selectedValue = args.retentionlocation

    if selectedValue != "" and lines[lineNo].replace("\n", "").replace(linePatternToReplace + "=",
                                                                       "") != args.retentionlocation:
        lines[lineNo] = ""
        lines[lineNo] = linePatternToReplace + "=" + selectedValue + "\n"
        logger.info("Updated value from '" + previousValue + "' to '" + selectedValue + "'")
        verboseHandle.printConsoleInfo(
            "Updated value from '" + previousValue + "' to '" + selectedValue + "'")
    out = open(file_name, 'w')
    out.writelines(lines)
    out.close()
    return selectedValue


def snapshot_retention_location_modify(args):
    if args.retentionlocation is None:
        verboseHandle.printConsoleWarning(
            "Please provide a value for the following, or click ENTER to accept the [default value]")
    selectLocation = update_app_config_file("cluster.config.snapshot.backup.path", "backup location", args)
    if selectLocation != "":
        if os.path.exists(selectLocation):
            logger.debug("path exist")
        else:
            os.makedirs(selectLocation)
            logger.debug("path not exist created directory ")


if __name__ == "__main__":
    args = check_arg(sys.argv[1:])
    snapshot_retention_location_modify(args)
