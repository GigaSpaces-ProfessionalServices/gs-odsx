#!/usr/bin/env python3
# !/usr/bin/python

import os
from colorama import Fore
from utils.ods_validation import getTelnetStatus
from scripts.logManager import LogManager
from utils.ods_ssh import executeRemoteCommandAndGetOutputValuePython36

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR

def isInstalledAndGetVersionGrafana(host):
    logger.info("isInstalledAndGetVersion")
    commandToExecute='ls /usr/lib/systemd/system/grafana*'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    if len(str(outputShFile)) ==0:
        commandToExecute='ls /etc/systemd/system/grafana*'
        logger.info("commandToExecute :"+str(commandToExecute))
        outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
        outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    return str(outputShFile)

def getGrafanaServerDetails(grafanaServers):
    logger.info("getGrafanaServerDetails()")
    dataArray=[]
    for server in grafanaServers:
        installStatus='No'
        host = str(os.getenv(server.ip))
        status = getTelnetStatus(host,3000)
        install = isInstalledAndGetVersionGrafana(str(host))
        logger.info("install : "+str(install))
        if(len(str(install))>0):
            installStatus='Yes'
        dataArray=[Fore.GREEN+host+Fore.RESET,
                   Fore.GREEN+host+Fore.RESET,
                   Fore.GREEN+server.role+Fore.RESET,
                   Fore.GREEN+installStatus+Fore.RESET if(installStatus=='Yes') else Fore.RED+installStatus+Fore.RESET,
                   Fore.GREEN+status+Fore.RESET if(status=='ON') else Fore.RED+status+Fore.RESET]
    return dataArray

def isInstalledAndGetVersionInflux(host):
    logger.info("isInstalledAndGetVersion")
    commandToExecute='ls /etc/systemd/system/influx*'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    return str(outputShFile)

def getInfluxdbServerDetails(influxdbServers):
    logger.info("getInfluxdbServerDetails()")
    dataArray=[]
    for server in influxdbServers:
        host = str(os.getenv(server.ip))
        installStatus='No'
        install = isInstalledAndGetVersionInflux(str(host))
        logger.info("install : "+str(install))
        if(len(str(install))>0):
            installStatus='Yes'
        status = getTelnetStatus(host,8086)
        dataArray=[Fore.GREEN+host+Fore.RESET,
                   Fore.GREEN+host+Fore.RESET,
                   Fore.GREEN+server.role+Fore.RESET,
                   Fore.GREEN+installStatus+Fore.RESET if(installStatus=='Yes') else Fore.RED+installStatus+Fore.RESET,
                   Fore.GREEN+status+Fore.RESET if(status=='ON') else Fore.RED+status+Fore.RESET,]
    return dataArray
