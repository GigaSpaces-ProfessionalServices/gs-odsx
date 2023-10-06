#!/usr/bin/env python3
# !/usr/bin/python

import os
from colorama import Fore

from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_grafana_list, config_get_influxdb_node, config_get_manager_node
from utils.ods_validation import getTelnetStatus
from scripts.logManager import LogManager
from utils.ods_ssh import executeRemoteCommandAndGetOutputValuePython36, executeRemoteCommandAndGetOutput, \
    executeRemoteCommandAndGetOutputPython36, executeLocalCommandAndGetOutput

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR

class obj_type_dictionary(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

def getGrafanaServers():
    grafanaServers = config_get_grafana_list()
    for server in grafanaServers:
        return str(os.getenv(server.ip))

def getInfluxdbServers():
    influxdbServers = config_get_influxdb_node()
    for server in influxdbServers:
        return str(os.getenv(server.ip))

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
    dbaGigaPath=str(readValuefromAppConfig("app.giga.path"))
    cmdToExecute = "xmllint --xpath 'string(/metrics-configuration/grafana/datasources/datasource/property[@name=\"url\"]/@value)' "+dbaGigaPath+"gs_config/metrics.xml"
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


def getManagerHostFromEnv():
    logger.info("getManagerHostFromEnv()")
    hosts = ''
    managerNodes = config_get_manager_node()
    for node in managerNodes:
        hosts+=str(os.getenv(str(node.ip)))+','
    hosts=hosts[:-1]
    return hosts


def validateMetricsXmlInflux(ip):
    logger.info("validateMetricsXml()")
    dbaGigaPath=str(readValuefromAppConfig("app.giga.path"))
    cmdToExecute = "xmllint --xpath 'string(/metrics-configuration/reporters/reporter/property/@value)' "+dbaGigaPath+"gs_config/metrics.xml"
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
    dbaGigaPath=str(readValuefromAppConfig("app.giga.path"))
    cmdToExecute = "xmllint --xpath 'string(/metrics-configuration/grafana/@url)' "+dbaGigaPath+"gs_config/metrics.xml"
    logger.info("cmdToExecute : "+str(cmdToExecute))
    output2 = executeRemoteCommandAndGetOutputValuePython36(ip,"root",cmdToExecute)
    output2=str(output2).replace('\n','')
    grafanaUrl = "http://"+str(getGrafanaServers())+":3000"
    logger.info("output2"+str(output2))
    if(str(output2)==str(grafanaUrl)):
        return "Yes"
    else:
        return "No"

def validateRPMS():
    logger.info("validateRPM()")
    try:
        installerArray = []
        cmd = "pwd"
        home = executeLocalCommandAndGetOutput(cmd)
        home = getPlainOutput(home)
        logger.info("home dir : " + str(home))
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
        cmd = 'find ' + str(sourceInstallerDirectory) + '/jdk/ -name *.rpm -printf "%f\n"'  # Checking .rpm file on Pivot machine
        javaRpm = executeLocalCommandAndGetOutput(cmd)
        javaRpm = getPlainOutput(javaRpm)
        logger.info("javaRpm found :" + str(javaRpm))

        cmd = 'find ' + str(sourceInstallerDirectory)  + '/unzip/ -name *.rpm -printf "%f\n"'  # Checking .rpm file on Pivot machine
        unZip = executeLocalCommandAndGetOutput(cmd)
        unZip = getPlainOutput(unZip)
        logger.info("unZip found :" + str(unZip))

        cmd = 'find ' + str(sourceInstallerDirectory) + '/gs/ -name *.zip -printf "%f\n"'  # Checking .zip file on Pivot machine
        gsZip = executeLocalCommandAndGetOutput(cmd)
        gsZip = getPlainOutput(gsZip)
        logger.info("Gigaspace Zip found :" + str(gsZip))

        di_installer_dict = obj_type_dictionary()
        di_installer_dict.add('Java', javaRpm)
        di_installer_dict.add('unZip', unZip)
        di_installer_dict.add('gsZip', gsZip)

        for name, installer in di_installer_dict.items():
            if (len(str(installer)) == 0):
                verboseHandle.printConsoleInfo(
                    "Pre-requisite installer " + str(home) + "/install/" + str(name) + " not found")
                return False
        return True
    except Exception as e:
        handleException(e)

def getPlainOutput(input):
    input = str(input).replace('\\n','').replace("b'","").replace("'","").replace('"','')
    return input


def configureMetricsXML(host):
    logger.info("configureMetricsXML()")
    try:
        dbaGigaPath=str(readValuefromAppConfig("app.giga.path"))
        cmd = 'sed -i "s|grafana1:3000|'+os.getenv("grafana1")+':3000|g" '+dbaGigaPath+'gs_config/metrics.xml;sed -i "s|influxdb1:8086|'+os.getenv("influxdb1")+':8086|g" '+dbaGigaPath+'gs_config/metrics.xml;sed -i "s|value=\\"influxdb1\\"|value=\\"'+os.getenv("influxdb1")+'\\"|g" '+dbaGigaPath+'gs_config/metrics.xml'
        logger.info(cmd)
        user = 'root'
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
    except Exception as e:
        handleException(e)