#!/usr/bin/env python3

import os.path

import json
import requests
import subprocess
from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_manager_node, config_get_space_hosts, config_get_nb_list, \
    config_get_grafana_list, config_get_influxdb_node
from utils.ods_ssh import executeRemoteCommandAndGetOutput, executeRemoteCommandAndGetOutputPython36
from utils.ods_validation import getSpaceServerStatus
from utils.ods_validation import isValidHost, getTelnetStatus
from utils.odsx_print_tabular_data import printTabular

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR

class host_dictionary_obj(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

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

def getManagerServerDataArray(managerNodes, gs_servers_host_dictionary_obj,dataTable):
    logger.info("getManagerServerDataArray()")
    for node in managerNodes:
        logger.info("node.ip"+str(node.ip))
        status = getSpaceServerStatus(node.ip)
        if(gs_servers_host_dictionary_obj.__contains__(str(node.ip)) and status=="ON"):
            status="ON"
        else:
            status="OFF"
        logger.info("status :"+str(status))
        if(status=="ON"):
            elapseTime = getElapseTime(node.ip)
            dataArray=[Fore.GREEN+"Agent up"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Manager"+Fore.RESET,
                       Fore.GREEN+elapseTime+Fore.RESET,
                       Fore.GREEN+"PASS"+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+"Agent up"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Manager"+Fore.RESET,
                       Fore.RED+"-"+Fore.RESET,
                       Fore.RED+"FAIL"+Fore.RESET]
        dataTable.append(dataArray)
    return dataTable

def getSpaceServerDataArray(spaceServers, gs_servers_host_dictionary_obj,dataTable):
    logger.info("getSpaceServerDataArray()")
    for node in spaceServers:
        logger.info("node.ip "+str(node.ip))
        status = "OFF"
        if(gs_servers_host_dictionary_obj.__contains__(str(node.ip))):
            status="ON"
        else:
            status="OFF"
        logger.info("status :"+str(status))
        if(status=="ON"):
            elapseTime = getElapseTime(str(node.ip))
            dataArray=[Fore.GREEN+"Agent up"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Space"+Fore.RESET,
                       Fore.GREEN+elapseTime+Fore.RESET,
                       Fore.GREEN+"PASS"+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+"Agent up"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Space"+Fore.RESET,
                       Fore.RED+"-"+Fore.RESET,
                       Fore.RED+"FAIL"+Fore.RESET]
        dataTable.append(dataArray)
    return dataTable


def get_gs_host_details(managerNodes):
    logger.info("get_gs_host_details()")
    managerHost=''
    for node in managerNodes:
        status = getSpaceServerStatus(node.ip)
        if(status=="ON"):
            managerHost = node.ip;
    if(len(managerHost)>0):
        response = requests.get('http://'+managerHost+':8090/v2/hosts', headers={'Accept': 'application/json'})
        logger.info("response.status_code :"+str(response.status_code))
        jsonArray = json.loads(response.text)
        gs_servers_host_dictionary_obj = host_dictionary_obj()
        for data in jsonArray:
            gs_servers_host_dictionary_obj.add(str(data['address']),str(data['address']))
        return gs_servers_host_dictionary_obj
    return ""

def isCurrentNodeLeaderNode(ip):
    logger.info("isCurrentNodeLeaderNode(ip) "+str(ip))
    cmd = "echo srvr | nc "+ip+" 2181"
    output = subprocess.getoutput(cmd)
    logger.info("output "+str(output))
    return (str(output).__contains__('Mode: leader'))

def getGSM_up_host_details(managerNodes,dataTable):
    logger.info("getGSM_up_host_details()")
    gs_servers_host_dictionary_obj = host_dictionary_obj()
    for node in managerNodes:
        logger.info("node.ip "+str(node.ip))
        leaderNode=''
        isLeaderNode = isCurrentNodeLeaderNode(node.ip)
        if(isLeaderNode):
            leaderNode='Leader'
        serverStatus = getSpaceServerStatus(node.ip)
        if(serverStatus=="ON"):
            response = requests.get('http://'+str(node.ip)+':8090/v2/info', headers={'Accept': 'application/json'})
            jsonArray = json.loads(response.text)
            if(len(str(jsonArray['lookupGroups']))>0):
                dataArray=[Fore.GREEN+"GSM up"+Fore.RESET,
                           Fore.GREEN+node.ip+Fore.RESET,
                           Fore.GREEN+"Manager"+" "+leaderNode+Fore.RESET,
                           Fore.GREEN+"-"+Fore.RESET,
                           Fore.GREEN+"PASS"+Fore.RESET]
            else:
                dataArray=[Fore.GREEN+"GSM up"+Fore.RESET,
                           Fore.GREEN+node.ip+Fore.RESET,
                           Fore.GREEN+"Manager"+" "+leaderNode+Fore.RESET,
                           Fore.RED+"-"+Fore.RESET,
                           Fore.RED+"FAIL"+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+"GSM up"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Manager"+" "+leaderNode+Fore.RESET,
                       Fore.RED+"-"+Fore.RESET,
                       Fore.RED+"FAIL"+Fore.RESET]
        dataTable.append(dataArray)
    return dataTable

def getWebUIStatus(managerNodes, dataTable):
    logger.info("getWebUIStatus()")
    for node in managerNodes:
        logger.info("node.ip "+str(node.ip))
        status = getSpaceServerStatus(node.ip)
        logger.info("node.ip status:"+str(status))
        if(status=="ON"):
            dataArray=[Fore.GREEN+"WebUI up"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Manager"+Fore.RESET,
                       Fore.GREEN+"-"+Fore.RESET,
                       Fore.GREEN+"PASS"+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+"WebUI up"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Manager"+Fore.RESET,
                       Fore.RED+"-"+Fore.RESET,
                       Fore.RED+"FAIL"+Fore.RESET]
        dataTable.append(dataArray)
    return dataTable

def getOpsManagerStatus(managerNodes, dataTable):
    logger.info("getOpsManagerStatus()")
    for node in managerNodes:
        logger.info("node.ip "+str(node.ip))
        cmd = "curl -Is http://"+node.ip+":8090 | head -1"
        output = subprocess.getoutput(cmd)
        logger.info(" output : "+str(output))
        if(str(output).__contains__('200')):
            dataArray=[Fore.GREEN+"Ops Manager up"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Manager"+Fore.RESET,
                       Fore.GREEN+"-"+Fore.RESET,
                       Fore.GREEN+"PASS"+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+"Ops Manager up"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Manager"+Fore.RESET,
                       Fore.RED+"-"+Fore.RESET,
                       Fore.RED+"FAIL"+Fore.RESET]
        dataTable.append(dataArray)
    return dataTable

def getRESTResponsive(managerNodes, dataTable):
    logger.info("getRESTResponsive()")
    for node in managerNodes:
        logger.info("node.ip "+str(node.ip))
        cmd = "curl -Is http://"+node.ip+":8090/v2/index.html | head -1"
        output = subprocess.getoutput(cmd)
        logger.info("output :"+str(output))
        if(str(output).__contains__('200')):
            dataArray=[Fore.GREEN+"REST responsive"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Manager"+Fore.RESET,
                       Fore.GREEN+"-"+Fore.RESET,
                       Fore.GREEN+"PASS"+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+"REST responsive"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Manager"+Fore.RESET,
                       Fore.RED+"-"+Fore.RESET,
                       Fore.RED+"FAIL"+Fore.RESET]
        dataTable.append(dataArray)
    return dataTable

def getElapseTime(ip):
    logger.info("getElapseTime(ip) : "+str(ip))
    commandToExecute = "pidof java"
    output = executeRemoteCommandAndGetOutput(ip, 'root', commandToExecute)
    pidStrArray = str(output).split(' ')
    commandToExecute = "ps -p "+pidStrArray[0]+" -o etime"
    output = executeRemoteCommandAndGetOutput(ip, 'root', commandToExecute)
    elapseTime = str(output).replace('    ','').replace('ELAPSED','').replace('   ','').replace('\n','')
    return elapseTime

def getUpTimeManagerStatus(managerNodes, dataTable):
    logger.info("getUpTimeManagerStatus()")
    for node in managerNodes:
        logger.info("node.ip "+str(node.ip))
        status = getSpaceServerStatus(node.ip)
        if(status=='ON'):
            elapseTime = getElapseTime(node.ip)
            if(len(str(elapseTime))>0):
                dataArray=[Fore.GREEN+"Up time"+Fore.RESET,
                           Fore.GREEN+node.ip+Fore.RESET,
                           Fore.GREEN+"Manager"+Fore.RESET,
                           Fore.GREEN+elapseTime+Fore.RESET,
                           Fore.GREEN+"PASS"+Fore.RESET]
            else:
                dataArray=[Fore.GREEN+"Up time"+Fore.RESET,
                           Fore.GREEN+node.ip+Fore.RESET,
                           Fore.GREEN+"Manager"+Fore.RESET,
                           Fore.RED+"-"+Fore.RESET,
                           Fore.RED+"FAIL"+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+"Up time"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Manager"+Fore.RESET,
                       Fore.RED+"-"+Fore.RESET,
                       Fore.RED+"FAIL"+Fore.RESET]
        dataTable.append(dataArray)
    return dataTable

def getStatusOfNBHost(server):
    if(str(server.role).__contains__('agent')):
        cmd = "systemctl status consul.service"
    if(str(server.role).__contains__('server') or str(server.role).__contains__('management')):
        cmd = 'systemctl status northbound.target'
    logger.info("Getting status.. :"+str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(server.ip, user, cmd)
    logger.info(cmd+" :"+str(output))
    if(output ==0):
        return "ON"
    else:
        return "OFF"

def getUpTimeForServiceByServiceName(node,serviceName):
    logger.info("getUpTimeForServiceByServiceName()")
    host=node.ip
    if(isValidHost(host)):
        logger.info("host :"+host)
        commandToExecute = "systemctl status "+serviceName
        elaplsedTime = ''
        elaplsedTimehr=''
        elaplsedTimeMin=''
        elaplsedTimeSec=''
        try:
            status = getStatusOfNBHost(node)
            logger.info("getStatusOfNBHost : status "+str(status))
            if(status=='ON'):
                output = executeRemoteCommandAndGetOutput(host, 'root', commandToExecute)
                outputStr = str(output)
                startStrElapseTime = str(output).rfind('UTC;')+4
                endStrElapseTime = str(output).rfind('ago')
                elaplsedTime = outputStr[startStrElapseTime:endStrElapseTime]
                #print(outputStr[startStrElapseTime:endStrElapseTime])
                if(len(str(elaplsedTime))>0):
                    if(elaplsedTime.__contains__('h')):
                        elaplsedTimehr = elaplsedTime[0:elaplsedTime.rfind('h')].replace(' ','')
                        elaplsedTime = elaplsedTime[elaplsedTime.rfind('h')+1:]
                        if(len(elaplsedTimehr)==1):
                            elaplsedTimehr = '0'+elaplsedTimehr
                    else:
                        elaplsedTimehr = '00'
                    if(elaplsedTime.__contains__('min')):
                        elaplsedTimeMin = elaplsedTime[0:elaplsedTime.rfind('min')].replace(' ','')
                        elaplsedTime = elaplsedTime[elaplsedTime.rfind('min')+3:]
                        if(len(elaplsedTimeMin)==1):
                            elaplsedTimeMin = '0'+elaplsedTimeMin
                    else:
                        elaplsedTimeMin = '00'
                    if(elaplsedTime.__contains__('s')):
                        elaplsedTimeSec = elaplsedTime[0:elaplsedTime.rfind('s')].replace(' ','')
                        if(len(elaplsedTimeSec)==1):
                            elaplsedTimeSec = '0'+elaplsedTimeSec
                    else:
                        elaplsedTimeSec='00'
                elaplsedTime = elaplsedTimehr+":"+elaplsedTimeMin+":"+elaplsedTimeSec

        except Exception as e:
            print("")
        #print(elaplsedTime)
    else:
        logger.info("Invalid host or IP: "+host)
        verboseHandle.printConsoleInfo("Invalid host or IP: "+host)
    return elaplsedTime

def getUpTimeSpaceStatus(spaceServers,gs_servers_host_dictionary_obj, dataTable):
    logger.info("getUpTimeSpaceStatus()")
    for node in spaceServers:
        logger.info("node.ip :"+str(node.ip))
        status = "OFF"
        if(gs_servers_host_dictionary_obj.__contains__(str(node.ip))):
            status="ON"
        else:
            status="OFF"
        logger.info("status :"+str(status))
        if(status=='ON'):
            elapseTime = getElapseTime(node.ip)
            if(len(str(elapseTime))>0):
                dataArray=[Fore.GREEN+"Up time"+Fore.RESET,
                           Fore.GREEN+node.ip+Fore.RESET,
                           Fore.GREEN+"Space"+Fore.RESET,
                           Fore.GREEN+elapseTime+Fore.RESET,
                           Fore.GREEN+"PASS"+Fore.RESET]
            else:
                dataArray=[Fore.GREEN+"Up time"+Fore.RESET,
                           Fore.GREEN+node.ip+Fore.RESET,
                           Fore.GREEN+"Space"+Fore.RESET,
                           Fore.RED+"-"+Fore.RESET,
                           Fore.RED+"FAIL"+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+"Up time"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Space"+Fore.RESET,
                       Fore.RED+"-"+Fore.RESET,
                       Fore.RED+"FAIL"+Fore.RESET]
        dataTable.append(dataArray)
    return dataTable

def getUpTimeNorthboundStatus(northboundServer, dataTable):
    logger.info("getUpTimeNorthboundStatus()")
    for node in northboundServer:
        logger.info("node.ip :"+str(node.ip))
        if(str(node.role).__contains__('agent')):
            elapseTime = getUpTimeForServiceByServiceName(node,'consul.service')
        if(str(node.role).__contains__('server')):
            elapseTime = getUpTimeForServiceByServiceName(node,'northbound.target')
        if(node.role=='management'):
            elapseTime = getUpTimeForServiceByServiceName(node,'northbound.target')
        if(len(str(elapseTime))>0):
            dataArray=[Fore.GREEN+"Up time"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Northbound "+node.role+Fore.RESET,
                       Fore.GREEN+elapseTime+Fore.RESET,
                       Fore.GREEN+"PASS"+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+"Up time"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Northbound "+node.role+Fore.RESET,
                       Fore.RED+"-"+Fore.RESET,
                       Fore.RED+"FAIL"+Fore.RESET]
        dataTable.append(dataArray)

    return dataTable

def getUsageOfRoot(ip):
    logger.info("getUsageOfRoot(ip) "+str(ip))
    commandToExecute = "df / | awk 'END{ print $(NF-1) }'"
    output = executeRemoteCommandAndGetOutput(ip, 'root', commandToExecute)
    logger.info("output :"+str(output))
    return str(output).replace('\n','')

def getUsageOfWork(ip):
    logger.info("getUsageOfWork(ip) :"+str(ip))
    commandToExecute = "df /dbagigawork/ | awk 'END{ print $(NF-1) }'"
    output = executeRemoteCommandAndGetOutput(ip, 'root', commandToExecute)
    logger.info("output :"+str(output))
    return str(output).replace('\n','')

def getPercentageOfRootForManagerAndSpaces(managerNodes,dataTable,spaceServers,gs_servers_host_dictionary_obj):
    logger.info("getPercentageOfRootForManagerAndSpaces()")
    for node in managerNodes:
        logger.info("node.ip :"+str(node.ip))
        status = getSpaceServerStatus(node.ip)
        logger.info("manager status : "+str(status))
        if(status=='ON'):
            usage = getUsageOfRoot(node.ip)
            usageWork = getUsageOfWork(node.ip)
            dataArray=[Fore.GREEN+"% of root, work"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Manager"+Fore.RESET,
                       Fore.GREEN+usage+','+usageWork+Fore.RESET,
                       Fore.GREEN+"PASS"+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+"% of root, work"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Manager"+Fore.RESET,
                       Fore.RED+"-"+Fore.RESET,
                       Fore.RED+"FAIL"+Fore.RESET]
        dataTable.append(dataArray)

    for node in spaceServers:
        logger.info("node.ip space "+str(node.ip))
        status = "OFF"
        if(gs_servers_host_dictionary_obj.__contains__(str(node.ip))):
            status="ON"
        else:
            status="OFF"
        logger.info("space status : "+str(status))
        if(status=='ON'):
            usage = getUsageOfRoot(node.ip)
            usageWork = getUsageOfWork(node.ip)
            dataArray=[Fore.GREEN+"% of root, work"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Space"+Fore.RESET,
                       Fore.GREEN+usage+','+usageWork+Fore.RESET,
                       Fore.GREEN+"PASS"+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+"% of root, work"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Space"+Fore.RESET,
                       Fore.RED+"-"+Fore.RESET,
                       Fore.RED+"FAIL"+Fore.RESET]
        dataTable.append(dataArray)
    return dataTable


def getUsageOfRAM(managerNodes,ip):
    logger.info("getUsageOfRAM(managerNodes,ip)")
    host = ip
    managerHost=''
    for node in managerNodes:
        status = getSpaceServerStatus(node.ip)
        if(status=="ON"):
            managerHost = node.ip
    logger.info("URL : http://"+str(managerHost)+":8090/v2/hosts/"+str(host)+"/statistics/os")
    response = requests.get("http://"+managerHost+":8090/v2/hosts/"+host+"/statistics/os", headers={'Accept': 'application/json'})
    logger.info(response.status_code)
    logger.info(response.content)
    jsonArray = json.loads(response.text)
    logger.info("str(round(jsonArray['physicalMemoryUsedPerc'],2)) : "+str(round(jsonArray['physicalMemoryUsedPerc'],2)))
    return str(round(jsonArray['physicalMemoryUsedPerc'],2))

def getRAMUtilizationForManagerAndSpace(managerNodes, dataTable, spaceServers, gs_servers_host_dictionary_obj):
    logger.info("getRAMUtilizationForManagerAndSpace()")
    for node in managerNodes:
        logger.info("manager node.ip "+str(node.ip))
        status = getSpaceServerStatus(node.ip)
        logger.info("manager status "+str(status))
        if(status=='ON'):
            usage = getUsageOfRAM(managerNodes,node.ip)
            dataArray=[Fore.GREEN+"RAM utilization"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Manager"+Fore.RESET,
                       Fore.GREEN+usage+"%"+Fore.RESET,
                       Fore.GREEN+"PASS"+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+"RAM utilization"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Manager"+Fore.RESET,
                       Fore.RED+"-"+Fore.RESET,
                       Fore.RED+"FAIL"+Fore.RESET]
        dataTable.append(dataArray)

    for node in spaceServers:
        logger.info("space node.ip "+str(node.ip))
        status = "OFF"
        if(gs_servers_host_dictionary_obj.__contains__(str(node.ip))):
            status="ON"
        else:
            status="OFF"
        logger.info("space status "+str(status))
        if(status=='ON'):
            usage = getUsageOfRAM(managerNodes,node.ip)
            dataArray=[Fore.GREEN+"RAM utilization"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Space"+Fore.RESET,
                       Fore.GREEN+usage+"%"+Fore.RESET,
                       Fore.GREEN+"PASS"+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+"RAM utilization"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Space"+Fore.RESET,
                       Fore.RED+"-"+Fore.RESET,
                       Fore.RED+"FAIL"+Fore.RESET]
        dataTable.append(dataArray)
    return dataTable

def getStatusOfFileBeat(server):
    logger.info("getStatusOfFileBeat() :"+str(server.ip))
    cmd = "systemctl is-active filebeat.service"
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(server.ip, user, cmd)
    logger.info(cmd+" :"+str(output))
    if(output ==0):
        return "ON"
    else:
        return "OFF"

def getFileBeatServiceStatus(managerNodes, dataTable, spaceServers, gs_servers_host_dictionary_obj, northboundServer):
    logger.info("getFileBeatServiceStatus()")
    for node in managerNodes:
        logger.info("manager node.ip "+str(node.ip))
        status = getStatusOfFileBeat(node)
        logger.info("space status : "+str(status))
        if(status=='ON'):
            dataArray=[Fore.GREEN+"Filebeat status"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Manager"+Fore.RESET,
                       Fore.GREEN+"-"+Fore.RESET,
                       Fore.GREEN+"PASS"+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+"Filebeat status"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Manager"+Fore.RESET,
                       Fore.RED+"-"+Fore.RESET,
                       Fore.RED+"FAIL"+Fore.RESET]
        dataTable.append(dataArray)

    for node in spaceServers:
        logger.info("space node.ip "+str(node.ip))
        status = "OFF"
        if(gs_servers_host_dictionary_obj.__contains__(str(node.ip))):
            status="ON"
        else:
            status="OFF"
        logger.info("space status : "+str(status))
        if(status=='ON'):
            nbstatus = getStatusOfFileBeat(node)
            if(nbstatus=='ON'):
                dataArray=[Fore.GREEN+"Filebeat status"+Fore.RESET,
                           Fore.GREEN+node.ip+Fore.RESET,
                           Fore.GREEN+"Space"+Fore.RESET,
                           Fore.GREEN+"-"+Fore.RESET,
                           Fore.GREEN+"PASS"+Fore.RESET]
            else:
                dataArray=[Fore.GREEN+"Filebeat status"+Fore.RESET,
                           Fore.GREEN+node.ip+Fore.RESET,
                           Fore.GREEN+"Space"+Fore.RESET,
                           Fore.RED+"-"+Fore.RESET,
                           Fore.RED+"FAIL"+Fore.RESET]
        dataTable.append(dataArray)

    for node in northboundServer:
        logger.info("northbound node.ip "+str(node.ip))
        status = getStatusOfFileBeat(node)
        logger.info("northbound status : "+str(status))
        if(status=='ON'):
            dataArray=[Fore.GREEN+"Filebeat status"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Northbound "+node.role+Fore.RESET,
                       Fore.GREEN+"-"+Fore.RESET,
                       Fore.GREEN+"PASS"+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+"Filebeat status"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Northbound "+node.role+Fore.RESET,
                       Fore.RED+"-"+Fore.RESET,
                       Fore.RED+"FAIL"+Fore.RESET]
        dataTable.append(dataArray)
    grafanaServers = config_get_grafana_list()
    for node in grafanaServers:
        logger.info("grafana node.ip "+str(node.ip))
        status = getTelnetStatus(node.ip,3000)
        logger.info("grafana status : "+str(status))
        if(status=='ON'):
            status = getStatusOfFileBeat(node)
            if(status=='ON'):
                dataArray=[Fore.GREEN+"Filebeat status"+Fore.RESET,
                           Fore.GREEN+node.ip+Fore.RESET,
                           Fore.GREEN+"Grafana"+Fore.RESET,
                           Fore.GREEN+"-"+Fore.RESET,
                           Fore.GREEN+"PASS"+Fore.RESET]
            else:
                dataArray=[Fore.GREEN+"Filebeat status"+Fore.RESET,
                           Fore.GREEN+node.ip+Fore.RESET,
                           Fore.GREEN+"Grafana"+Fore.RESET,
                           Fore.RED+"-"+Fore.RESET,
                           Fore.RED+"FAIL"+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+"Filebeat status"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Grafana"+Fore.RESET,
                       Fore.RED+"-"+Fore.RESET,
                       Fore.RED+"FAIL"+Fore.RESET]
        dataTable.append(dataArray)
    influxdbServers = config_get_influxdb_node()
    for node in influxdbServers:
        status = getTelnetStatus(node.ip,8086)
        if(status=='ON'):
            status = getStatusOfFileBeat(node)
            if(status=='ON'):
                dataArray=[Fore.GREEN+"Filebeat status"+Fore.RESET,
                           Fore.GREEN+node.ip+Fore.RESET,
                           Fore.GREEN+"Influxdb"+Fore.RESET,
                           Fore.GREEN+"-"+Fore.RESET,
                           Fore.GREEN+"PASS"+Fore.RESET]
            else:
                dataArray=[Fore.GREEN+"Filebeat status"+Fore.RESET,
                           Fore.GREEN+node.ip+Fore.RESET,
                           Fore.GREEN+"Influxdb"+Fore.RESET,
                           Fore.RED+"-"+Fore.RESET,
                           Fore.RED+"FAIL"+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+"Filebeat status"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+"Influxdb"+Fore.RESET,
                       Fore.RED+"-"+Fore.RESET,
                       Fore.RED+"FAIL"+Fore.RESET]
        dataTable.append(dataArray)

    return dataTable
def doValidate():
    headers = [Fore.YELLOW+"Validator Name"+Fore.RESET,
               Fore.YELLOW+"Host"+Fore.RESET,
               Fore.YELLOW+"Type"+Fore.RESET,
               Fore.YELLOW+"Details"+Fore.RESET,
               Fore.YELLOW+"Result"+Fore.RESET
               ]
    dataTable=[]

    managerNodes = config_get_manager_node()
    spaceServers = config_get_space_hosts()
    northboundServer = config_get_nb_list()
    gs_servers_host_dictionary_obj = get_gs_host_details(managerNodes)

    dataTable = getManagerServerDataArray(managerNodes, gs_servers_host_dictionary_obj,dataTable)
    dataTable = getSpaceServerDataArray(spaceServers,gs_servers_host_dictionary_obj,dataTable)
    dataTable = getGSM_up_host_details(managerNodes,dataTable)
    dataTable = getWebUIStatus(managerNodes,dataTable)
    dataTable = getOpsManagerStatus(managerNodes,dataTable)
    dataTable = getRESTResponsive(managerNodes,dataTable)
    #dataTable = getUpTimeManagerStatus(managerNodes,dataTable)
    #dataTable = getUpTimeSpaceStatus(spaceServers,gs_servers_host_dictionary_obj,dataTable)
    dataTable = getUpTimeNorthboundStatus(northboundServer,dataTable)
    dataTable = getPercentageOfRootForManagerAndSpaces(managerNodes,dataTable,spaceServers,gs_servers_host_dictionary_obj)
    dataTable = getRAMUtilizationForManagerAndSpace(managerNodes,dataTable,spaceServers,gs_servers_host_dictionary_obj)
    dataTable = getFileBeatServiceStatus(managerNodes,dataTable,spaceServers,gs_servers_host_dictionary_obj,northboundServer)

    printTabular(None,headers,dataTable)

if __name__ == '__main__':
    logger.info("odsx - validators")
    verboseHandle.printConsoleWarning('Menu -> Validators')
    try:
        with Spinner():
            doValidate()
    except Exception as e:
        logger.error("Exception in Menu->Validators"+str(e))
        verboseHandle.printConsoleError("Exception in Menu->Validators"+str(e))
        handleException(e)
