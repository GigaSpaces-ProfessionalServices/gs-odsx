#!/usr/bin/env python3
import os

from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_ssh import executeRemoteCommandAndGetOutput

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR


def handleException(e):
    logger.info("handleException()")
    trace = []
    tb = e.__traceback__
    while tb is not None:
        trace.append({
            "filename": tb.tb_frame.f_code.co_filename,
            "name": tb.tb_frame.f_code.co_name,
            "lineno": tb.tb_lineno
        })
        tb = tb.tb_next
    logger.error(str({
        'type': type(e).__name__,
        'message': str(e),
        'trace': trace
    }))
    verboseHandle.printConsoleError((str({
        'type': type(e).__name__,
        'message': str(e),
        'trace': trace
    })))

def executeCommandForInstall(user):
    logger.info("executeCommandForInstall(): start")
    try:
        dbaGigaDir=str(readValuefromAppConfig("app.giga.path"))
        path = str(readValuefromAppConfig("app.utilities.checkmanagersync.file")).replace("/dbagiga/",dbaGigaDir)
        with Spinner():
          host= os.getenv("pivot1")
          output= executeRemoteCommandAndGetOutput(host,user,path)
          print(output)
    except Exception as e:
        handleException(e)
    logger.info("executeCommandForInstall(): end")

if __name__ == '__main__':
    logger.info("Menu -> Utilities -> Check Manager Sync")
    verboseHandle.printConsoleWarning('Menu -> Utilities -> Check Manager Sync')
    try:
        user = 'root'
        logger.info("user :" + str(user))
        executeCommandForInstall(user)
    except Exception as e:
        handleException(e)
