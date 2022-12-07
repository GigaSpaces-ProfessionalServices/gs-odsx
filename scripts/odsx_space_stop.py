# to quiesce space
import argparse
import os
import sys

import requests

from scripts import ods_server_request_status
from scripts.logManager import LogManager
from utils.odsx_keypress import userInputWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


def check_arg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('-spacename', '--spacename',
                        help='Space Name',
                        # required='True',
                        default='demo')
    parser.add_argument('-host', '--host',
                        help='host name/ip',
                        default='localhost')
    parser.add_argument('-dryrun', '--dryrun',
                        help='Dry run flag',
                        default='false', action='store_true')
    parser.add_argument('m', nargs='?')
    verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])
    return parser.parse_args(args)


# curl -X POST --header 'Content-Type: application/json' --header 'Accept: text/plain' 'http://localhost:8090/v2/pus/demo/quiesce'


def _url(host="localhost", port="8090", spaceName="demo"):
    return 'http://' + host + ':' + port + '/v2/pus/' + spaceName + "/quiesce"


def quiesceSpace(space_name, host, dryRun):
    if dryRun != "false":
        verboseHandle.printConsoleInfo("The request to stop space is successfully sent to server with Dry run mode ON.")
        return 202

    response = requests.post(_url(host, '8090', space_name), headers={'Accept': 'text/plain'})
    logger.debug(response.text)
    if response.status_code == 202:
        verboseHandle.printConsoleInfo("The request to stop space is successfully sent to server.")
        verboseHandle.printConsoleInfo("Request id: " + str(response.json()))
        if ods_server_request_status.getRequestStatus(str(response.json()), host,
                                                      verboseHandle.verboseFlag) == "Request processed successfully":
            verboseHandle.printConsoleInfo("Request processed successfully")
    elif response.status_code == 404:
        verboseHandle.printConsoleError("The requested space does not exist.")
    else:
        verboseHandle.printConsoleError("Error! Please try again.")
    return response.status_code


if __name__ == '__main__':
    args = check_arg(sys.argv[1:])
    if args.m == "m":
        tmpHost = str(userInputWrapper("host ip: "))
        if tmpHost != "" or tmpHost is not None:
            args.host = tmpHost

    quiesceSpace(args.spacename, args.host, args.dryrun)
