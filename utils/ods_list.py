#!/usr/bin/env python3
# !/usr/bin/python

import os
from colorama import Fore

from utils.ods_cluster_config import config_get_grafana_list, config_get_influxdb_node
from utils.ods_validation import getTelnetStatus
from scripts.logManager import LogManager
from utils.ods_ssh import executeRemoteCommandAndGetOutputValuePython36, executeRemoteCommandAndGetOutput

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR

def getGrafanaServers():
    grafanaServers = config_get_grafana_list()
    for server in grafanaServers:
        return str(os.getenv(server.ip))

def getInfluxdbServers():
    influxdbServers = config_get_influxdb_node()
    for server in influxdbServers:
        return str(os.getenv(server.ip))


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

def validateMetricsXmlInfluxUrl(ip):
    logger.info("validateMetricsXmlInfluxUrl()")
    cmdToExecute = "xmllint --xpath 'string(/metrics-configuration/grafana/datasources/datasource/property[@name=\"url\"]/@value)' /dbagiga/gs_config/metrics.xml"
    logger.info("cmdToExecute : "+str(cmdToExecute))
    #output3 = executeRemoteCommandAndGetOutput(ip,"root",cmdToExecute)
    output3 = executeRemoteCommandAndGetOutputValuePython36(ip, 'root', cmdToExecute)
    output3=str(output3).replace('\n','')
    logger.info("output3"+str(output3))
    influxUrl="http://"+str(getInfluxdbServers())+":8086"
    if(str(output3)==str(influxUrl)):
        return "Yes"
    else:
        return "No"


def validateMetricsXmlInflux(ip):
    logger.info("validateMetricsXml()")
    cmdToExecute = "xmllint --xpath 'string(/metrics-configuration/reporters/reporter/property/@value)' /dbagiga/gs_config/metrics.xml"
    logger.info("cmdToExecute : "+str(cmdToExecute))
    output1 = executeRemoteCommandAndGetOutputValuePython36(ip,"root",cmdToExecute)
    output1=str(output1).replace('\n','')
    logger.info("output1"+str(output1))
    if str(output1)==str(getInfluxdbServers()):
        return validateMetricsXmlInfluxUrl(ip)
    else:
        return "No"

def validateMetricsXmlGrafana(ip):
    logger.info("validateMetricsXmlGrafana()")
    cmdToExecute = "xmllint --xpath 'string(/metrics-configuration/grafana/@url)' /dbagiga/gs_config/metrics.xml"
    logger.info("cmdToExecute : "+str(cmdToExecute))
    output2 = executeRemoteCommandAndGetOutputValuePython36(ip,"root",cmdToExecute)
    output2=str(output2).replace('\n','')
    grafanaUrl = "http://"+str(getGrafanaServers())+":3000"
    logger.info("output2"+str(output2))
    if(str(output2)==str(grafanaUrl)):
        return "Yes"
    else:
        return "No"