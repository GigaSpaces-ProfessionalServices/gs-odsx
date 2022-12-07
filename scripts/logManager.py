#!/usr/bin/python3

import argparse
import logging
import logging.config
###########################################################################
# put below code in ~/.bashrc file to redirect all stderr to this function.
# From any script or program, when there is any print to stderr, it will
# print in RED color
#
# exec 9>&2
# exec 8> >(
#     while IFS='' read -r line || [ -n "$line" ]; do
#        echo -e "\033[31m${line}\033[0m"
#     done
# )
# function undirect(){ exec 2>&9; }
# function redirect(){ exec 2>&8; }
# trap "redirect;" DEBUG
# PROMPT_COMMAND='undirect;'
###########################################################################
import os.path

from colorama import init, Fore

LOGGING_CONFIG = 'config/logging.conf'
logging.config.fileConfig(LOGGING_CONFIG)

class LogManager():  # Custom completer
    verboseFlag = False
    scriptName = "osdxLogger"
    logger = logging.getLogger("osdxLogger")

    def __init__(self, script=None, verboseFlag=False) -> None:
        init(autoreset=True)
        if script != None:
            self.scriptName = script.split(".")[0]

        self.logger = logging.getLogger(self.scriptName)
        if verboseFlag == True:
            self.logger.setLevel(logging.DEBUG)
            self.verboseFlag = verboseFlag

    def setVerboseFlag(self, verboseFlag=True):
        if verboseFlag == True:
            self.logger.setLevel(logging.DEBUG)
            self.logger.info("Verbose mode enabled")
        else:
            self.logger.setLevel(logging.INFO)
            self.logger.info("Verbose mode disabled")

        self.verboseFlag = verboseFlag

    def checkArg(self, parser=None):
        if parser == None:
            parser = argparse.ArgumentParser(description='basic argparse')
        parser.add_argument('-v', '--verbose',
                            help='verbose', action='store_true')

        return parser.parse_args()

    def checkAndEnableVerbose(self, parser=None, argsParam=None):
        args = self.checkArg(parser)
        self.verboseFlag = args.verbose
        if args.verbose == True:
            self.logger.setLevel(logging.DEBUG)
            self.logger.info("Verbose mode enabled")
        return args

    def printConsoleDebug(self, msg):
        if self.verboseFlag == True:
            print(Fore.BLUE + msg)

    def printConsoleInfo(self, msg):
        print(Fore.GREEN + msg)

    def printConsoleWarning(self, msg):
        print(Fore.YELLOW + msg)

    def printConsoleError(self, msg):
        print(Fore.RED + msg)


if __name__ == '__main__':
#    logManager = LogManager(os.path.basename(__file__), True)
    logManager = LogManager(os.path.basename(__file__))

    logManager.setVerboseFlag()

    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    #logManager.checkAndEnableVerbose(None, sys.argv[1:])

    logManager.logger.debug("This is debug")
    logManager.logger.info("This is info")
    logManager.logger.warning("This is warning")
    logManager.logger.error("This is error")
    
    logManager.printConsoleDebug("This is debug on console")
    logManager.printConsoleInfo("This is info on console")
    logManager.printConsoleWarning("This is warning on console")
    logManager.printConsoleError("This is error on console")
