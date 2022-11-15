#!/usr/bin/env python3

import os
import platform
from os import path
from colorama import Fore
from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_ssh import connectExecuteSSH, executeRemoteCommandAndGetOutputValuePython36, \
    executeRemoteCommandAndGetOutputPython36, executeRemoteCommandAndGetOutput
from utils.ods_scp import scp_upload
from utils.ods_cluster_config import config_get_grafana_node
from utils.ods_app_config import set_value_in_property_file, readValuefromAppConfig
from utils.odsx_print_tabular_data import printTabular

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR

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

def isInstalledAndGetVersionKapacitor(host):
    logger.info("isInstalledAndGetVersion")
    commandToExecute='ls /usr/lib/systemd/system/kapacitor*'
    outputShFile = executeRemoteCommandAndGetOutputPython36(host, 'root', commandToExecute)
    #print(outputShFile)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    return str(outputShFile)


def getStatusOfKapacitor(host):
    logger.info("getStatusOfKapacitor()")
    with Spinner():
        user="root"
        cmd="systemctl status kapacitor"
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        logger.info("output1 : "+str(output))
        if(output!=0):
            return "OFF"
        else:
            return "ON"

def listCustomMetrics():
    logger.info("listKapacitor()")
    try:
        headers = [Fore.YELLOW+"Id"+Fore.RESET,
                   Fore.YELLOW+"Name"+Fore.RESET,
                   Fore.YELLOW+"Role"+Fore.RESET,
                   Fore.YELLOW+"Source path"+Fore.RESET,
                   Fore.YELLOW+"Dest path"+Fore.RESET]
        data=[]
        dataArray=[]
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
        installStatus='No'
        # For GC
        sourcePath= sourceInstallerDirectory+"/telegraf/scripts/"
        destPath=str(readValuefromAppConfig("app.alert.telegraf.custommetrics"))
        dir_list=""
        count=1;
        with Spinner():
            if os.path.isdir(sourcePath):
                dir_list = os.listdir(sourcePath)
                for dir in dir_list:
                    sourcePath= sourceInstallerDirectory+"/telegraf/scripts/"+str(dir)
                    if os.path.isdir(sourcePath):
                        file_list = os.listdir(sourcePath)
                        for file in file_list:
                            dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                                       Fore.GREEN+str(file)+Fore.RESET,
                                       Fore.GREEN+str(dir)+Fore.RESET,
                                       Fore.GREEN+str(sourcePath)+Fore.RESET,
                                       Fore.GREEN+str(destPath)+Fore.RESET]
                            count=count+1
                            data.append(dataArray)
        printTabular(None,headers,data)
    except Exception as e:
        handleException(e)

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Monitors -> Alerts -> Custom metrics -> GC')
    try:
        listCustomMetrics()
    except Exception as e:
        handleException(e)