import argparse
import os
import sys

from scripts.logManager import LogManager

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


def check_arg(args=None):
    parser = argparse.ArgumentParser(description='Script to check snapshot retention')
    parser.add_argument('--maxretention',
                        help='Max no of snapshot retention to keep')
    parser.add_argument('--retentiontime',
                        help='retention time')
    parser.add_argument('m', nargs='?')
    verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])
    return parser.parse_args(args)


def update_app_config_file(linePatternToReplace, inputMsg, passedArg):
    file_name = "config/app.config"
    lines = open(file_name, 'r').readlines()
    lineNo = -1
    for line in lines:
        lineNo = lineNo + 1
        if line.startswith("#"):
            continue
        elif line.__contains__(linePatternToReplace):
            break
    previousValue = ""
    if passedArg is None:
        previousValue = lines[lineNo].replace("\n", "").replace(linePatternToReplace + "=",
                                                                "")
        from utils.odsx_keypress import userInputWrapper
        selectedValue = str(userInputWrapper(
            inputMsg + " [current '" + previousValue + "'] : "))
    else:
        selectedValue = passedArg

    if selectedValue != "" and lines[lineNo].replace("\n", "").replace(linePatternToReplace + "=",
                                                                       "") != selectedValue:
        lines[lineNo] = ""
        lines[lineNo] = linePatternToReplace + "=" + selectedValue + "\n"
        logger.info("Updated value from '" + previousValue + "' to '" + selectedValue + "'")
        verboseHandle.printConsoleInfo(
            "Updated value from '" + previousValue + "' to '" + selectedValue + "'")

    out = open(file_name, 'w')
    out.writelines(lines)
    out.close()


def snapshot_retention_modify(args):
    if args.maxretention is None and args.retentiontime is None:
        verboseHandle.printConsoleWarning(
            "Please provide a value for the following, or click ENTER to accept the [default value]")
    update_app_config_file("cluster.config.snapshot.time", "retention time", args.retentiontime)
    update_app_config_file("cluster.config.snapshot.maxbackup", "max number of backups to keep ", args.maxretention)


if __name__ == "__main__":
    args = check_arg(sys.argv[1:])
    snapshot_retention_modify(args)
