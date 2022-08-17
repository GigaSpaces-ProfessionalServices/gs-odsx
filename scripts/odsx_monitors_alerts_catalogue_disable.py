#!/usr/bin/env python3
import glob
import os
import platform
from os import path
from colorama import Fore

from scripts.odsx_monitors_alerts_catalogue_list import listCatalogue
from scripts.odsx_monitors_alerts_services_kapacitor_list import getStatusOfKapacitor
from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_ssh import connectExecuteSSH, executeRemoteCommandAndGetOutputPython36, \
    executeRemoteCommandAndGetOutputValuePython36
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

class obj_type_dictionary(dict):
    # __init__ function
    def __init__(self):
        self = dict()
    # Function to add key:value
    def add(self, key, value):
        self[key] = value

def disableKapacitorServiceByHost(alertName):
    logger.info("stopKapacitorServiceByHost()")
    verboseHandle.printConsoleInfo("Enabling alert :"+alertName)
    cmd = "kapacitor disable "+str(alertName)
    logger.info("Getting status.. kapacitor :"+str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        if (output == 0):
            verboseHandle.printConsoleInfo("Alert "+str(alertName)+" disabled.")
        else:
            verboseHandle.printConsoleError("Alert "+str(alertName)+" unable to disabled.")


def getListAndSelect():
    listCatalogue()
    global sourceDB2FeederShFilePath
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    sourceDB2FeederShFilePath = str(sourceInstallerDirectory+".kapacitor.alerts.").replace('.','/')
    status=getStatusOfKapacitor(host)
    headers = [Fore.YELLOW+"Id"+Fore.RESET,
               Fore.YELLOW+"Alert name"+Fore.RESET
               ]
    data=[]
    dataArray=[]
    alertDict = obj_type_dictionary()
    if status=="ON":
        directory = os.getcwd()
        os.chdir(sourceDB2FeederShFilePath)
        count=1
        for file in glob.glob("*.tick"):
            os.chdir(directory)
            aliasName = str(file).replace(".tick","")
            alertDict.add(count,aliasName)
            dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                       Fore.GREEN+aliasName+Fore.RESET]
            count=count+1
            data.append(dataArray)
        printTabular(None,headers,data)
    else:
        verboseHandle.printConsoleError("Kapacitor status is off. Please start kapacitor on host."+str(host))
    return alertDict

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Monitors -> Alerts -> Services -> Kapacitor -> Disable')
    try:
        host = os.getenv("pivot1")
        alertDict = getListAndSelect()
        if len(alertDict)>0 :
            choice = str(input(Fore.YELLOW+"[1] For individual \n[Enter] For all \n[99] For exit. : "+Fore.RESET))
            if choice=='99':
                quit()
            if choice=='1':
                alertNumber = str(input(Fore.YELLOW+"Enter alert id you want to disable : "+Fore.RESET))
                while(len(alertNumber)==0):
                    alertNumber = str(input(Fore.YELLOW+"Enter alert id you want to disable : "+Fore.RESET))
                alertName = alertDict.get(int(alertNumber))
                confirmInstall = str(input(Fore.YELLOW+"Are you sure want to disable alert ["+alertName+"] (y/n) [y]: "+Fore.RESET))
                if(len(str(confirmInstall))==0):
                    confirmInstall='y'
                if(confirmInstall=='y'):
                    disableKapacitorServiceByHost(alertName)
            if choice=="":
                confirmInstall = str(input(Fore.YELLOW+"Are you sure want to disable alert (y/n) [y]: "+Fore.RESET))
                if(len(str(confirmInstall))==0):
                    confirmInstall='y'
                if(confirmInstall=='y'):
                    for id in range(1,len(alertDict)+1):
                        alertName = alertDict.get(id)
                        disableKapacitorServiceByHost(alertName)
    except Exception as e:
        handleException(e)