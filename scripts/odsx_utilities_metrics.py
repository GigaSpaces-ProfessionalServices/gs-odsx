#!/usr/bin/env python3
import os

from scripts.logManager import LogManager
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36
from utils.odsx_keypress import userInputWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR
#!/usr/bin/env python3
import os
from scripts.logManager import LogManager
from utils.ods_app_config import getYamlFilePathInsideFolder, readValuefromAppConfig
from scripts.spinner import Spinner
from colorama import Fore
from scripts.odsx_servers_grafana_stop import getGrafanaServerHostList
from scripts.odsx_servers_influxdb_stop import getInfluxdbServerHostList
from utils.ods_cluster_config import getManagerHostFromEnv, config_get_space_hosts, config_get_manager_node
from scripts.odsx_servers_space_install import getSpaceHostFromEnv

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

def getSpaceHostFromEnv():
    logger.info("getSpaceHostFromEnv()")
    hosts = ''
    spaceNodes = config_get_space_hosts()
    for node in spaceNodes:
        hosts+=str(os.getenv(str(node.ip)))+','
    hosts=hosts[:-1]
    return hosts

def getManagerHostFromEnv():
    logger.info("getManagerHostFromEnv()")
    hosts = ''
    managerNodes = config_get_manager_node()
    for node in managerNodes:
        hosts+=str(os.getenv(str(node.ip)))+','
    hosts=hosts[:-1]
    return hosts

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

def configureLicenseManagerAndSpace():
    managerHosts = getManagerHostFromEnv()
    spaceHosts = getSpaceHostFromEnv()
    sourceGSmetrics = str(getYamlFilePathInsideFolder(".gs.config.metrics.metricsxml"))
    dbaGigaPath=str(readValuefromAppConfig("app.giga.path"))
    targetGSmetrics = dbaGigaPath+"gs_config/metrics.xml"
    verboseHandle.printConsoleWarning("-------------------Summary-----------------")
    verboseHandle.printConsoleInfo("metrics.xml.template source file :"+str(sourceGSmetrics))
    verboseHandle.printConsoleInfo("metrics.xml target : "+str(targetGSmetrics))
    verboseHandle.printConsoleInfo("Manager hosts : "+managerHosts)
    verboseHandle.printConsoleInfo("Space hosts : "+spaceHosts)
    verboseHandle.printConsoleInfo("Influxdb hosts : "+getInfluxdbServerHostList())
    verboseHandle.printConsoleInfo("Grafana hosts : "+getGrafanaServerHostList())
    verboseHandle.printConsoleWarning("-------------------------------------------")
    #licenseConfig='"\\"{}\\""'.format(licenseConfig)
    confirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to proceed ? (y/n) [y] : "+Fore.RESET))
    if confirm=='y' or confirm=='':
        #commandToExecute = "sed -i '/export GS_LICENSE*/c\export GS_LICENSE=\""+licenseConfig+"\"'  /dbagiga/gigaspaces-smart-ods/bin/setenv-overrides.sh"

        commandToExecute = "cp "+sourceGSmetrics+" "+targetGSmetrics
        logger.info("commandToExecute:"+commandToExecute)

        for host in managerHosts.split(','):
            executeRemoteCommandAndGetOutputPython36(host, 'root', commandToExecute)
            configureMetricsXML(host)
            verboseHandle.printConsoleInfo("metrics.xml configured for host:"+host)

        for host in spaceHosts.split(','):
            executeRemoteCommandAndGetOutputPython36(host, 'root', commandToExecute)
            configureMetricsXML(host)
            verboseHandle.printConsoleInfo("metrics.xml configured for host:"+host)

if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Utilities -> Metrics")
    logger.info("Utilities - Metrics")
    try:
        configureLicenseManagerAndSpace()
    except Exception as e:
        handleException(e)
