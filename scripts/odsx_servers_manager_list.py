#!/usr/bin/env python3
import os.path,  argparse, sys
import json
import logging.config
from concurrent.futures import ThreadPoolExecutor

from utils.ods_list import validateMetricsXmlInflux, validateMetricsXmlGrafana
from utils.ods_cluster_config import config_get_manager_node,isInstalledAndGetVersion
from scripts.logManager import LogManager
from utils.odsx_print_tabular_data import printTabular
from colorama import Fore
import socket, platform, requests
from utils.ods_validation import getSpaceServerStatus, port_check_config
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
            status = getSpaceServerStatus(os.getenv(node.ip))
            if(status=="ON"):
                managerHost = str(os.getenv(node.ip))
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

def printManagerList(node):
    installStatus='No'
    if (port_check_config(os.getenv(str(node.ip)),22)):
        status = getSpaceServerStatus(os.getenv(str(node.ip)))
    else:
        status="NOT REACHABLE"
    install = isInstalledAndGetVersion(os.getenv(str(node.ip)))
    logger.info("install : "+str(install))
    influx = validateMetricsXmlInflux(os.getenv(str(node.ip)))
    grafana = validateMetricsXmlGrafana(os.getenv(str(node.ip)))
    if(len(str(install))>8):
        installStatus='Yes'
    dataArray=[Fore.GREEN+os.getenv(str(node.ip))+Fore.RESET,
               Fore.GREEN+installStatus+Fore.RESET if(installStatus=='Yes') else Fore.RED+installStatus+Fore.RESET,
               Fore.GREEN+status+Fore.RESET if(status=='ON') else Fore.RED+status+Fore.RESET,
               Fore.GREEN+install+Fore.RESET if(installStatus=='Yes') else Fore.RED+'N/A'+Fore.RESET,
               Fore.GREEN+influx+Fore.RESET if(influx=='Yes') else Fore.RED+influx+Fore.RESET,
               Fore.GREEN+grafana+Fore.RESET if(grafana=='Yes') else Fore.RED+grafana+Fore.RESET]
    data.append(dataArray)

def listFileFromDirectory():
    logger.info("servers - manager - list")
    managerNodes = config_get_manager_node()
    managerHost = getManagerHost(managerNodes)
    logger.info("managerHost : "+str(managerHost))
    try:
        with Spinner():
            inputDirectory='backup'
            if(len(str(managerHost))>0):
                getGSInfo(managerHost)
            else:
                logger.info("Unable to retrive GS Info no manager status ON.")
                verboseHandle.printConsoleInfo("Unable to retrive GS Info no manager status ON.")
            logger.debug('Settings - Manager - List -listFileFromDirectory()')
            headers = [Fore.YELLOW+"Host"+Fore.RESET,
                       Fore.YELLOW+"Installed"+Fore.RESET,
                       Fore.YELLOW+"Status"+Fore.RESET,
                       Fore.YELLOW+"Version"+Fore.RESET,
                       Fore.YELLOW+"Influxdb"+Fore.RESET,
                       Fore.YELLOW+"Grafana"+Fore.RESET]
            global data
            data=[]
            managerNodes = config_get_manager_node()

            managerNodesLength=len(managerNodes)+1
            with ThreadPoolExecutor(managerNodesLength) as executor:
                for node in managerNodes:
                    executor.submit(printManagerList,node)

        printTabular(None,headers,data)
    except Exception as e:
        handleException(e)

def get_my_key(obj):
    return obj['timeStamp']

if __name__=="__main__" :
    verboseHandle.printConsoleWarning('Menu -> Servers -> Manager -> List')
    try:
        myCheckArg()
        listFileFromDirectory()
    except Exception as e:
        handleException(e)