#!/usr/bin/env python3
import os
from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_ssh import connectExecuteSSH
from scripts.spinner import Spinner
from colorama import Fore

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR


def configureHoststoMetricsxml(grafanaHosts, influxdbHosts, host):
    commandToExecute="scripts/utilities_metrics.sh"
    additionalParam = grafanaHosts+' '+influxdbHosts
    verboseHandle.printConsoleInfo("Configuring metrics.xmsl for host:"+host)
    logger.info("Configuring metrics.xmsl for host:"+host)
    with Spinner():
        outputShFile= connectExecuteSSH(host, 'root',commandToExecute,additionalParam)
    logger.info("Configuring metrics.xml for host:"+host+" completed.")
    verboseHandle.printConsoleInfo("Configuring metrics.xml for host:"+host+" completed.")

def validateGrafanaInfluxdb():
    logger.info("validateGrafanaInfluxdb()")
    grafanaHosts = str(readValuefromAppConfig("app.grafana.hosts")).replace('"','')
    influxdbHosts = str(readValuefromAppConfig("app.influxdb.hosts")).replace('"','')
    managerHostConfig = str(readValuefromAppConfig("app.manager.hosts")).replace('"','')
    managerHosts = managerHostConfig.split(',')
    spaceHostConfig = str(readValuefromAppConfig("app.space.hosts")).replace('"','')
    spaceHosts = spaceHostConfig.split(',')
    if(len(grafanaHosts)==0):
        verboseHandle.printConsoleInfo("Grafana host not found.")
    if(len(influxdbHosts)==0):
        verboseHandle.printConsoleInfo("Influxdb host not found.")
    if(len(managerHosts)==0):
        verboseHandle.printConsoleInfo("Manager host not found.")
    logger.info("grafanahosts :"+str(grafanaHosts)+" influxdbhosts:"+str(influxdbHosts))

    if(len(grafanaHosts)>0 and len(influxdbHosts)>0 and len(managerHosts)>0):
        logger.info("Manager configuration")
        verboseHandle.printConsoleInfo("Grafana host :"+grafanaHosts)
        verboseHandle.printConsoleInfo("Influxdb host :"+influxdbHosts)
        confirmManagerHostConfig = str(input(Fore.YELLOW+"Do you want to configure for manager hosts ? ["+managerHostConfig+"] (y/n) [y] : "+Fore.RESET))
        if(len(confirmManagerHostConfig)==0):
            confirmManagerHostConfig='y'
        logger.info("confirmManagerHostConfig :"+str(confirmManagerHostConfig))
        if(confirmManagerHostConfig=='y'):
            for host in managerHosts:
                configureHoststoMetricsxml(grafanaHosts,influxdbHosts,host)
    if(len(grafanaHosts)>0 and len(influxdbHosts)>0 and len(spaceHosts)>0):
        logger.info("Space configuration")
        confirmSpaceHostConfig = str(input(Fore.YELLOW+"Do you want to configure for space hosts ? ["+spaceHostConfig+"] (y/n) [y] : "+Fore.RESET))
        if(len(confirmSpaceHostConfig)==0):
            confirmSpaceHostConfig='y'
        if(confirmSpaceHostConfig=='y'):
            for host in spaceHosts:
                configureHoststoMetricsxml(grafanaHosts,influxdbHosts,host)

if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Utilities -> Metrics")
    logger.info("Utilities - Metrics")
    verboseHandle.printConsoleInfo("Validating Grafana and Influxdb hosts.")
    try:
        validateGrafanaInfluxdb()
    except Exception as e:
        logger.error("Exception in Utilities - Metrics."+str(e))
        verboseHandle.printConsoleError(str(e))