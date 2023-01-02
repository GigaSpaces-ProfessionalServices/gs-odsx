#!/usr/bin/env python3
import argparse
import os
import signal
import sys

from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_cleanup import signal_handler
from utils.ods_cluster_config import config_get_grafana_list, config_get_nb_list
from utils.ods_ssh import connectExecuteSSH, executeRemoteCommandAndGetOutput

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
serviceName = "catalogue-service.service";
user = "root"
def getGrafanaServerHostList():
    nodeList = config_get_grafana_list()
    nodes=""
    for node in nodeList:
        if(len(nodes)==0):
            nodes = os.getenv(node.ip)
        else:
            nodes = nodes+','+os.getenv(node.ip)
    return nodes

def getNBServerHostList():
    nodeList = config_get_nb_list()
    nodes=""
    for node in nodeList:
        if(str(node.role).casefold().__contains__('applicative')):
            if(len(nodes)==0):
                nodes = os.getenv(node.ip)
            else:
                nodes = nodes+','+os.getenv(node.ip)
    return nodes


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
    parser = argparse.ArgumentParser(description='Script to remove Catalogue service')
    parser.add_argument('m', nargs='?')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])

def removeService():
    logger.info("removeService() : start")

    confirmMsg = Fore.YELLOW + "Are you sure, you want to remove Catalogue service ? (Yes/No) [Yes]:" + Fore.RESET

    from utils.odsx_keypress import userInputWrapper
    choice = str(userInputWrapper(confirmMsg))

    while(len(choice) > 0 and choice.casefold()!='yes' and choice.casefold()!='no'):
        verboseHandle.printConsoleError("Invalid input")
        from utils.odsx_keypress import userInputWrapper
        choice = str(userInputWrapper(confirmMsg))

    if choice.casefold() == 'no':
        exit(0)


    commandToExecute = "scripts/settings_catalogueService_remove.sh"
    logger.info("Command "+commandToExecute)
    
    try:
        os.system(commandToExecute)
        logger.info("removeService() : end")
    except Exception as e:
        logger.error("error occurred in removeService()")

def removeGrafanaDashboard():
    logger.info("removeGrafanaDashboard() : start")
    verboseHandle.printConsoleInfo("Removing Catalogue dashboard from grafana...")
    global grafanaHosts
    grafanaHosts = getGrafanaServerHostList()
    grafanaHostList = grafanaHosts.split(",")

    for host in grafanaHostList:
        try:
            jsonDelete = executeRemoteCommandAndGetOutput(host,user,"rm -f /usr/share/grafana/conf/provisioning/dashboards/catalogue.json")
            yamlDelete = executeRemoteCommandAndGetOutput(host,user,"rm -f /etc/grafana/provisioning/dashboards/catalogue.yaml")
        except Exception as e:
            logger.error("Exception in removing catalogue dashboard in grafana : removeGrafanaDashboard() :"+str(e))
            verboseHandle.printConsoleError("Exception in removing catalogue dashboard in grafana: removeGrafanaDashboard() : "+str(e))

    restartGrafana()
    verboseHandle.printConsoleInfo("Catalogue dashboard removed successfully...")
    logger.info("removeGrafanaDashboard() : end")
    return

def restartGrafana():
    logger.info("restartGrafana() : start")
    verboseHandle.printConsoleInfo("Restarting Grafana service..")
   
    try:
    
        if(len(grafanaHosts)>0):
            
            commandToExecute="scripts/restartGrafana.sh"
            additionalParam=""
            logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(grafanaHosts)+" User:"+str(user))
            with Spinner():
                outputShFile= connectExecuteSSH(grafanaHosts, user,commandToExecute,additionalParam)
                verboseHandle.printConsoleInfo("Host "+str(grafanaHosts)+" restart grafana service command executed.")
        else:
            logger.info("No server details found.")
            verboseHandle.printConsoleInfo("No server details found.")
    except Exception as e:
        logger.error("Exception in Grafana -> Restart : restartGrafana() : "+str(e))
        verboseHandle.printConsoleError("Exception in Grafana -> Stop : restartGrafana() : "+str(e))
    
    logger.info("restartGrafana(): end")

    verboseHandle.printConsoleInfo("Grafana Restarted successfully!")

if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Settings -> CatalogueService -> Remove")
    args = []
    args = myCheckArg()
    signal.signal(signal.SIGINT, signal_handler)
    removeService()
    removeGrafanaDashboard()
