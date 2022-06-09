#!/usr/bin/env python3
import json
import os, socket
import subprocess,shlex

import requests
from colorama import Fore
from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import set_value_in_property_file, readValuefromAppConfig
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_scp import scp_upload
from utils.ods_ssh import connectExecuteSSH
from utils.ods_validation import getSpaceServerStatus
#from scripts.odsx_tieredstorage_deploy import displaySpaceHostWithNumber
#from scripts.odsx_servers_space_list import getGSCForHost
from requests.auth import HTTPBasicAuth
from utils.odsx_db2feeder_utilities import getPasswordByHost, getUsernameByHost
from utils.odsx_print_tabular_data import printTabular

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
clusterHosts = []

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR

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

def getManagerHost(managerNodes):
    managerHost=""
    try:
        logger.info("getManagerHost() : managerNodes :"+str(managerNodes))
        for node in managerNodes:
            status = getSpaceServerStatus(node.ip)
            if(status=="ON"):
                managerHost = node.ip
        return managerHost
    except Exception as e:
        handleException(e)

def getManagerServerHostList():
    nodeList = config_get_manager_node()
    nodes = ""
    for node in nodeList:
        # if(str(node.role).casefold() == 'server'):
        if (len(nodes) == 0):
            nodes = node.ip
        else:
            nodes = nodes + ',' + node.ip
    return nodes

class host_dictionary_obj(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

def get_gs_host_details(managerNodes):
    try:
        logger.info("get_gs_host_details() : managerNodes :"+str(managerNodes))
        for node in managerNodes:
            status = getSpaceServerStatus(node.ip)
            if(status=="ON"):
                managerHostConfig = node.ip;
        logger.info("managerHostConfig : "+str(managerHostConfig))
        #print(username+" : "+password)
        response = requests.get('http://'+managerHostConfig+':8090/v2/hosts', headers={'Accept': 'application/json'},auth = HTTPBasicAuth(username, password))
        logger.info("response status of host :"+str(managerHostConfig)+" status :"+str(response.status_code))
        jsonArray = json.loads(response.text)
        gs_servers_host_dictionary_obj = host_dictionary_obj()
        for data in jsonArray:
            gs_servers_host_dictionary_obj.add(str(data['name']),str(data['address']))
        logger.info("gs_servers_host_dictionary_obj : "+str(gs_servers_host_dictionary_obj))
        return gs_servers_host_dictionary_obj
    except Exception as e:
        handleException(e)

def getGSCForHost():
    logger.info("getGSCForHost")
    managerServerConfig = readValuefromAppConfig("app.manager.hosts")
    host_gsc_dict_obj =  obj_type_dictionary()
    host_gsc_mul_host_dict_obj =  obj_type_dictionary()
    managerServerConfigArr=[]
    if(str(managerServerConfig).__contains__(',')):  # if cluster manager configured
        managerServerConfig = str(managerServerConfig).replace('"','')
        managerServerConfigArr = managerServerConfig.split(',')
        logger.info("MangerServerConfigArray: "+str(managerServerConfigArr))
        host_gsc_dict_obj =  getGSCByManagerServerConfig(managerServerConfigArr[0], host_gsc_dict_obj)
    else:
        logger.info("managerServerConfig :"+str(managerServerConfig))
        host_gsc_dict_obj =  getGSCByManagerServerConfig(managerServerConfig, host_gsc_dict_obj)
    return host_gsc_dict_obj

def getGSCByManagerServerConfig(managerServerConfig, host_gsc_dict_obj):
    logger.info("getGSCByManagerServerConfig() : managerServerConfig :"+str(managerServerConfig)+" host_gsc_dict_obj :"+str(host_gsc_dict_obj))
    try:
        #print("Getting response for :"+managerServerConfig)
        response = requests.get(('http://'+managerServerConfig+':8090/v2/containers'), headers={'Accept': 'application/json'},auth = HTTPBasicAuth(username, password))
        output = response.content.decode("utf-8")
        logger.info("Json Response container:"+str(output))
        data = json.loads(output)
        for i in data :
            id=i["id"]
            id = str(id).replace('~'+str(i["pid"]), '')
            logger.info("id : "+str(id))
            if(host_gsc_dict_obj.__contains__(id)):
                host_gsc_dict_obj.add(id,host_gsc_dict_obj.get(id)+1)
            else:
                host_gsc_dict_obj.add(id,1)
        logger.info("GSC obj: "+str(host_gsc_dict_obj))
    except Exception as e:
        logger.error("Error while retrieving from REST :"+str(e))
    logger.info("host_gsc_dict_obj : "+str(host_gsc_dict_obj))
    return host_gsc_dict_obj


def displaySpaceHostWithNumber(managerNodes, spaceNodes):
    try:
        logger.info("displaySpaceHostWithNumber() managerNodes :"+str(managerNodes)+" spaceNodes :"+str(spaceNodes))
        gs_host_details_obj = get_gs_host_details(managerNodes)
        logger.info("gs_host_details_obj : "+str(gs_host_details_obj))
        counter = 0
        space_dict_obj = host_dictionary_obj()
        logger.info("space_dict_obj : "+str(space_dict_obj))
        for node in spaceNodes:
            if(gs_host_details_obj.__contains__(str(node.name)) or (str(node.name) in gs_host_details_obj.values())):
                space_dict_obj.add(str(counter+1),node.name)
                counter=counter+1
        logger.info("space_dict_obj : "+str(space_dict_obj))
        verboseHandle.printConsoleWarning("Space hosts lists")
        headers = [Fore.YELLOW+"No"+Fore.RESET,
                   Fore.YELLOW+"Host"+Fore.RESET]
        dataTable=[]
        for data in range (1,len(space_dict_obj)+1):
            dataArray = [Fore.GREEN+str(data)+Fore.RESET,
                         Fore.GREEN+str(space_dict_obj.get(str(data)))+Fore.RESET]
            dataTable.append(dataArray)
        printTabular(None,headers,dataTable)
        return space_dict_obj
    except Exception as e:
        handleException(e)


def getInputParam():
    logger.info("getInputParam()")
    locators = getManagerServerHostList()
    managerNodes = config_get_manager_node()
    spaceNodes = config_get_space_hosts()
    space_dict_obj = displaySpaceHostWithNumber(managerNodes,spaceNodes)
    logger.info("space_dict_obj : "+str(space_dict_obj))
    hostNumberToRebalance = str(input(Fore.YELLOW+"Enter host/IP number to rebalance : "+Fore.RESET))
    while(len(str(hostNumberToRebalance))==0):
        hostNumberToRebalance = str(input(Fore.YELLOW+"Enter host/IP number to rebalance : "+Fore.RESET))
    hostToRebalance = space_dict_obj.get(hostNumberToRebalance)

    zone = str(input(Fore.YELLOW+"Enter zone to rebalance [bll] : "+Fore.RESET))
    while(len(str(zone))==0):
        zone='bll'
    host_gsc_dict_obj = getGSCForHost()
    logger.info("host_gsc_dict_obj :"+str(host_gsc_dict_obj))
    logger.info("hostToRebalance :"+str(hostToRebalance))
    hostAddress = str(socket.gethostbyaddr(str(hostToRebalance))[0])
    logger.info("host_gsc_dict_obj : "+str(host_gsc_dict_obj))
    gscCount = str(host_gsc_dict_obj.get(hostAddress))
    logger.info("GSC for host "+hostAddress+" : "+str(gscCount))
    verboseHandle.printConsoleInfo("Gsc count ["+gscCount+"] to rebalance host ["+hostToRebalance+"] : "+Fore.RESET)

    currWorkingDir = format(os.getcwd())
    cmd = "scripts/utilities_rebalancingpolicy_apply.sh"+' '+locators+' '+hostToRebalance+' '+zone+' '+gscCount+' '+currWorkingDir
    status=''
    with Spinner():
        output = subprocess.check_output(cmd,shell=True)
        print(output)
        logger.info("Rebalancing log start : ")
        logger.info(str(output))
        logger.info("Rebalancing log end : ")

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Utilities -> Rebalancing -> Apply')
    try:
        nodeList = config_get_manager_node()
        if(len(str(nodeList))>0):
            appId = str(readValuefromAppConfig("app.space.security.appId")).replace('"','')
            safeId = str(readValuefromAppConfig("app.space.security.safeId")).replace('"','')
            objectId = str(readValuefromAppConfig("app.space.security.objectId")).replace('"','')
            logger.info("appId : "+appId+" safeID : "+safeId+" objectID : "+objectId)
            managerHost = getManagerHost(nodeList)
            username = "gs-admin"#str(getUsernameByHost(managerHost,appId,safeId,objectId))
            password = "gs-admin"#str(getPasswordByHost(managerHost,appId,safeId,objectId))
            getInputParam()
        else:
            logger.info("No manager host configuration found")
            verboseHandle.printConsoleInfo("No manager host configuration found")
    except Exception as e:
        handleException(e)
