#!/usr/bin/env python3
import os

from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import getGrafanaServerHostList
from utils.ods_ssh import connectExecuteSSH
from utils.odsx_keypress import userInputWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
nbConfig = {}
telegrafHostList=[]
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

def reloadSpaceboardServiceByHost():
    logger.info("reloadSpaceboardServiceByHost()")
    cmd = "cp "
    logger.info("Getting status.. telegraf :"+str(cmd))
    user = 'root'
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))#str(readValuefromAppConfig("app.setup.sourceInstaller"))
    # filename = Path(abc)
    # filename = os.path.basename(additionalParam+'/gs_config.yaml')
    nodes = getGrafanaServerHostList()
    if(os.path.exists(sourceInstallerDirectory+'grafana/gs_config.yaml')):
        filename = "gs_config.yaml"
    else:
        filename = ""
    gsConfigSpaceboardTarget = str(readValuefromAppConfig("app.grafana.provisioning.dashboards.target"))
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))#str(readValuefromAppConfig("app.setup.sourceInstaller"))
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleWarning("***Summary***")
    print(Fore.GREEN+"1. "+
          Fore.GREEN+"Grafana dashboard files  = "+sourceInstallerDirectory+"/grafana/dashboards/"+
          Fore.GREEN+str(filename)+Fore.RESET)
    verboseHandle.printConsoleInfo("2. Target path : "+str(gsConfigSpaceboardTarget))
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    if(len(nodes)>0):
        confirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to reload grafana servers ["+nodes+"] (y/n) [y]: "+Fore.RESET))
        if(len(str(confirm))==0):
            confirm='y'
        logger.info("confirm :"+str(confirm))
        if(confirm=='y'):
            commandToExecute="scripts/monitors_spaceboard_reload.sh"
            sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))#str(readValuefromAppConfig("app.setup.sourceInstaller"))
            additionalParam=sourceInstallerDirectory+' '+str(gsConfigSpaceboardTarget)
            logger.info("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+nodes+" User:"+str(user)+" sourceInstaller:"+sourceInstallerDirectory)
            with Spinner():
                output= connectExecuteSSH(nodes, user,commandToExecute,additionalParam)
                if (output == 0):
                    verboseHandle.printConsoleInfo("Grafana Service Reloaded successfully on "+str(nodes))
                else:
                    verboseHandle.printConsoleInfo("Grafana Service Reloaded successfully on "+str(nodes))
            return "Yes"

if __name__ == '__main__':
    logger.info("Menu -> Monitors -> Spaceboard -> Reload ")
    verboseHandle.printConsoleWarning("Menu -> Monitors -> Spaceboard -> Reload ")
    try:
        #listGrafana()
        reloadSpaceboardServiceByHost()
    except Exception as e:
        logger.error("Invalid argument :"+str(e))
        verboseHandle.printConsoleError("Invalid argument")
