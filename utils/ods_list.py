#!/usr/bin/env python3
# !/usr/bin/python

import os
import socket
from colorama import Fore

from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_grafana_list, config_get_influxdb_node, config_get_manager_node
from utils.ods_validation import getTelnetStatus
from scripts.logManager import LogManager
from utils.ods_ssh import executeRemoteCommandAndGetOutputValuePython36, executeRemoteCommandAndGetOutput, \
    executeRemoteCommandAndGetOutputPython36, executeLocalCommandAndGetOutput, get_ssh_user
from utils.ods_app_config import readValuefromAppConfig

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

dbaGigaPath=readValuefromAppConfig("app.giga.path")

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
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, get_ssh_user(), commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    if len(str(outputShFile)) ==0:
        commandToExecute='ls ~/.config/systemd/user/grafana*'
        logger.info("commandToExecute :"+str(commandToExecute))
        outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, get_ssh_user(), commandToExecute)
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
    commandToExecute='rpm -q influxdb && ls /usr/lib/systemd/system/influxdb.service'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, get_ssh_user(), commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    return str(outputShFile)

def isInstalledIIDRAccessServer(host):
    logger.info("isInstalledIIDRAccessServer")
    commandToExecute='ls /data/gs_software/iidr/as*'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, get_ssh_user(), commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    return str(outputShFile)

def isInstalledIIDRKafkaAgent(host):
    logger.info("isInstalledIIDRKafkaAgent")
    commandToExecute='ls /data/gs_software/iidr/kafka*'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, get_ssh_user(), commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    return str(outputShFile)

def isInstalledIIDROracleAgent(host):
    logger.info("isInstalledIIDROracleAgent")
    commandToExecute='ls /data/gs_software/iidr/oracle*'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, get_ssh_user(), commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    return str(outputShFile)

def isInstalledIIDRSubscriptionManager(host):
    logger.info("isInstalledIIDRSubscriptionManager")
    commandToExecute='ls $HOME/di-subscription-manager/latest-di-subscription-manager*'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, get_ssh_user(), commandToExecute)
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
    cmdToExecute = "xmllint --xpath 'string(/metrics-configuration/grafana/datasources/datasource/property[@name=\"url\"]/@value)' "+dbaGigaPath+"/gs_config/metrics.xml"
    logger.info("cmdToExecute : "+str(cmdToExecute))
    #output3 = executeRemoteCommandAndGetOutput(ip,get_ssh_user(),cmdToExecute)
    output3 = executeRemoteCommandAndGetOutputValuePython36(ip, get_ssh_user(), cmdToExecute)
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
    cmdToExecute = "xmllint --xpath 'string(/metrics-configuration/reporters/reporter/property/@value)' "+ dbaGigaPath +"/gs_config/metrics.xml"
    logger.info("cmdToExecute : "+str(cmdToExecute))
    output1 = executeRemoteCommandAndGetOutputValuePython36(ip,get_ssh_user(),cmdToExecute)
    output1=str(output1).replace('\n','')
    logger.info("output1"+str(output1))
    if str(output1)==str(getInfluxdbServers()):
        return validateMetricsXmlInfluxUrl(ip)
    else:
        return "No"

def validateMetricsXmlGrafana(ip):
    logger.info("validateMetricsXmlGrafana()")
    cmdToExecute = "xmllint --xpath 'string(/metrics-configuration/grafana/@url)' "+ dbaGigaPath +"/gs_config/metrics.xml"
    logger.info("cmdToExecute : "+str(cmdToExecute))
    output2 = executeRemoteCommandAndGetOutputValuePython36(ip,get_ssh_user(),cmdToExecute)
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
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
        cmd = 'find ' + str(sourceInstallerDirectory) + '/gs/ -name *.zip -printf "%f\n"'  # Checking .zip file on Pivot machine
        gsZip = executeLocalCommandAndGetOutput(cmd)
        gsZip = getPlainOutput(gsZip)
        logger.info("Gigaspace Zip found :" + str(gsZip))

        if len(str(gsZip)) == 0:
            verboseHandle.printConsoleInfo(
                "Pre-requisite installer " + str(sourceInstallerDirectory) + "/gs/*.zip not found")
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
        cmd = 'sed -i "s|grafana1:3000|'+os.getenv("grafana1")+':3000|g" '+ dbaGigaPath +'/gs_config/metrics.xml;sed -i "s|influxdb1:8086|'+os.getenv("influxdb1")+':8086|g" '+ dbaGigaPath +'/gs_config/metrics.xml;sed -i "s|value=\\"influxdb1\\"|value=\\"'+os.getenv("influxdb1")+'\\"|g" '+ dbaGigaPath +'/gs_config/metrics.xml'
        logger.info(cmd)
        user = get_ssh_user()
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
    except Exception as e:
        handleException(e)

# --- GigaSpaces 17.3.0+ : metrics.properties replaces metrics.xml ------------
# From 17.3.0 the distribution ships no metrics.xml at all, and
# MetricsConfigLoader reads "<com.gs.home>/config/metrics/metrics.properties".
# It resolves that path from -Dcom.gs.home and returns BEFORE looking at
# -Dcom.gigaspaces.metrics.config, so the XML written by configureMetricsXML()
# above is silently ignored on those versions. configureMetricsXML is kept for
# pre-17.3 clusters, which still read it.

METRICS_PROPERTIES_REL_PATH = "/gigaspaces-smart-ods/config/metrics/metrics.properties"

def getGsMetricsPropertiesPath():
    """Absolute path of the metrics.properties the platform actually reads."""
    return dbaGigaPath + METRICS_PROPERTIES_REL_PATH

def getPrometheusServers():
    """Host running Prometheus / the OTLP receiver.

    host.yaml has no dedicated 'prometheus' category on most environments, so
    fall back to the pivot, which is where the receiver is normally run.
    """
    for key in ("prometheus1", "pivot1"):
        value = os.getenv(key)
        if value and value != "None":
            return str(value)
    return None

def configureMetricsProperties(host):
    """Substitute this environment's endpoints into metrics.properties on host."""
    logger.info("configureMetricsProperties()")
    try:
        target = getGsMetricsPropertiesPath()
        replacements = []
        prometheusHost = getPrometheusServers()
        if prometheusHost:
            replacements.append(("prometheus1:9090", prometheusHost + ":9090"))
        else:
            verboseHandle.printConsoleWarning(
                "No 'prometheus' or 'pivot' host in host.yaml - leaving the OTLP "
                "placeholder unresolved in " + target)
        influxdbHost = os.getenv("influxdb1")
        if influxdbHost and influxdbHost != "None":
            replacements.append(("influxdb1:8086", str(influxdbHost) + ":8086"))
        grafanaHost = os.getenv("grafana1")
        if grafanaHost and grafanaHost != "None":
            replacements.append(("grafana1:3000", str(grafanaHost) + ":3000"))
        gigaLogPath = readValuefromAppConfig("app.gigalog.path")
        if gigaLogPath and gigaLogPath != "None":
            replacements.append(("@GIGALOGPATH@", str(gigaLogPath)))
        else:
            verboseHandle.printConsoleWarning(
                "app.gigalog.path is not set - leaving the file-tap placeholder "
                "unresolved in " + target)
        if not replacements:
            return
        cmd = ';'.join('sed -i "s|' + old + '|' + new + '|g" ' + target
                       for old, new in replacements)
        logger.info(cmd)
        with Spinner():
            executeRemoteCommandAndGetOutputPython36(host, get_ssh_user(), cmd)
    except Exception as e:
        handleException(e)

def validateMetricsPropertiesOtlp(ip):
    """Return "Yes" when metrics.properties on ip enables OTLP to our Prometheus."""
    logger.info("validateMetricsPropertiesOtlp()")
    try:
        target = getGsMetricsPropertiesPath()
        cmd = ("grep -E '^[[:space:]]*metrics\\.(registries|otlp\\.url)[[:space:]]*=' "
               + target + " 2>/dev/null")
        logger.info("cmdToExecute : " + str(cmd))
        output = executeRemoteCommandAndGetOutputValuePython36(ip, get_ssh_user(), cmd)
        output = getPlainOutput(output)
        logger.info("output : " + str(output))
        prometheusHost = getPrometheusServers()
        if "otlp" in output and prometheusHost and prometheusHost in output:
            return "Yes"
        return "No"
    except Exception as e:
        handleException(e)
        return "No"

def addGscCountForContainer(host_gsc_dict_obj, containerHostname):
    # The manager reports each container under its own machine's hostname
    # (e.g. an EC2 internal FQDN), which may differ from the name this machine
    # resolves for that host. Count it under every candidate key - full
    # hostname, short hostname and forward-resolved IP - so a lookup by any
    # of them succeeds.
    logger.info("addGscCountForContainer() : containerHostname :"+str(containerHostname))
    keys = {str(containerHostname), str(containerHostname).split('.')[0]}
    try:
        keys.add(socket.gethostbyname(str(containerHostname)))
    except OSError as e:
        logger.info("Could not resolve container hostname "+str(containerHostname)+" : "+str(e))
    for key in keys:
        if key in host_gsc_dict_obj:
            host_gsc_dict_obj[key] = host_gsc_dict_obj[key]+1
        else:
            host_gsc_dict_obj[key] = 1
    return host_gsc_dict_obj

def getGscCountForHost(host_gsc_dict_obj, host):
    logger.info("getGscCountForHost() : host :"+str(host))
    gsc = host_gsc_dict_obj.get(str(host))
    if gsc is None:
        # Fall back to reverse DNS (full then short name) for setups where the
        # container hostname could not be forward-resolved to this host's IP.
        try:
            reverseName = str(socket.gethostbyaddr(str(host)).__getitem__(0))
            gsc = host_gsc_dict_obj.get(reverseName)
            if gsc is None:
                gsc = host_gsc_dict_obj.get(reverseName.split('.')[0])
        except OSError as e:
            logger.info("Could not reverse-resolve host "+str(host)+" : "+str(e))
    logger.info("GSC count for host "+str(host)+" : "+str(gsc))
    return gsc