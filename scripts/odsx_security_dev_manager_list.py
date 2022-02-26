#!/usr/bin/env python3
import os.path,  argparse, sys
import json
import logging.config
from utils.ods_cluster_config import config_get_manager_node
from scripts.logManager import LogManager
from utils.odsx_print_tabular_data import printTabular
from colorama import Fore
import socket, platform, requests
from utils.ods_validation import getSpaceServerStatus
from scripts.spinner import Spinner

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

def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])

def getManagerHost(managerNodes):
    logger.info("getManagerHost()")
    managerHost=""
    status=""
    try:
        logger.info("getManagerHost() : managerNodes :"+str(managerNodes))
        for node in managerNodes:
            status = getSpaceServerStatus(node.ip)
            if(status=="ON"):
                managerHost = node.ip
        return managerHost
    except Exception as e:
        handleException(e)


def getGSInfo(managerHost):
    logger.info("getGSInfo() ")
    global version
    global build
    global revision

    logger.info("url : "+str('http://'+str(managerHost)+':8090/v2/info'))
    response = requests.get(('http://'+str(managerHost)+':8090/v2/info'), headers={'Accept': 'application/json'})
    output = response.content.decode("utf-8")
    logger.info("Json Response container:"+str(output))
    jsonArray = json.loads(response.text)
    print()
    verboseHandle.printConsoleWarning("Version  : "+str(jsonArray["version"]))
    verboseHandle.printConsoleWarning("Build    : "+str(jsonArray["build"]))
    verboseHandle.printConsoleWarning("Revision : "+str(jsonArray["revision"]))
    print()

def listFileFromDirectory():
    logger.debug("security - manager - list")
    logger.info("security - manager - list")
    managerNodes = config_get_manager_node()
    managerHost = getManagerHost(managerNodes)
    logger.info("managerHost : "+str(managerHost))
    try:
        inputDirectory='backup'
        if(len(str(managerHost))>0):
            getGSInfo(managerHost)
        else:
            logger.info("Unable to retrive GS Info no manager status ON.")
            verboseHandle.printConsoleInfo("Unable to retrive GS Info no manager status ON.")
        logger.debug('Settings - Manager - List -listFileFromDirectory()')
        headers = [Fore.YELLOW+"Manager Name"+Fore.RESET,
                   Fore.YELLOW+"IP"+Fore.RESET,
                   Fore.YELLOW+"Role"+Fore.RESET,
                   Fore.YELLOW+"Resume Mode"+Fore.RESET,
                   Fore.YELLOW+"Status"+Fore.RESET]
        data=[]
        managerNodes = config_get_manager_node()
        for node in managerNodes:
            status = getSpaceServerStatus(node.ip)
            if(status=="ON"):
                dataArray=[Fore.GREEN+node.name+Fore.RESET,
                           Fore.GREEN+node.ip+Fore.RESET,
                           Fore.GREEN+node.role+Fore.RESET,
                           Fore.GREEN+node.resumeMode+Fore.RESET,
                           Fore.GREEN+status+Fore.RESET]
            else:
                dataArray=[Fore.GREEN+node.name+Fore.RESET,
                           Fore.GREEN+node.ip+Fore.RESET,
                           Fore.GREEN+node.role+Fore.RESET,
                           Fore.GREEN+node.resumeMode+Fore.RESET,
                           Fore.RED+status+Fore.RESET]
            data.append(dataArray)

        printTabular(None,headers,data)
    except Exception as e:
        logger.error("Exception while listing manager"+str(e))

def get_my_key(obj):
    return obj['timeStamp']

if __name__=="__main__" :
    verboseHandle.printConsoleWarning('Menu -> Security -> Dev -> Manager -> List')
    myCheckArg()
    with Spinner():
        listFileFromDirectory()
