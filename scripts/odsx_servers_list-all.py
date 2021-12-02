#!/usr/bin/env python3

import os.path,  argparse, sys, subprocess
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_manager_node
from colorama import Fore
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_print_tabular_data import printTabular
from utils.ods_cluster_config import config_get_space_hosts,config_get_nb_list,config_get_grafana_list,config_get_influxdb_node, config_get_dataIntegration_nodes
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36,executeRemoteCommandAndGetOutput
from utils.ods_validation import getTelnetStatus
from scripts.spinner import Spinner

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR

class host_dictionary(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value


def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])

def getStatusOfHost(host_nic_dict_obj,server):
    logger.info("getStatusOfHost(host_nic_dict_obj,server) :")
    status = host_nic_dict_obj.get(server.ip)
    logger.info("status of "+str(server)+" "+str(status))
    if(status=="3"):
        status="OFF"
    elif(status=="0"):
        status="ON"
    else:
        logger.info("Host Not reachable.. :"+str(server))
        status="OFF"
    logger.info("Final Status :"+str(status))
    return status

def getStatusOfSpaceHost(serverHost):
    commandToExecute = "ps -ef | grep GSA"
    with Spinner():
        output = executeRemoteCommandAndGetOutput(serverHost, 'root', commandToExecute)
    if(str(output).__contains__('services=GSA')):
        return "ON"
    else:
        return "OFF"


def getStatusOfNBHost(server):
    if(str(server.role).__contains__('agent')):
        cmd = "systemctl status consul.service"
    if(str(server.role).__contains__('applicative')):
        cmd = 'systemctl status northbound.target'
    if(server.role =='management'):
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

def getConsolidatedStatus(node):
    output=''
    logger.info("getConsolidatedStatus() : "+str(node.ip))
    cmdList = [ "systemctl status odsxkafka" , "systemctl status odsxzookeeper", "systemctl status odsxcr8", "systemctl status telegraf"]
    for cmd in cmdList:
        logger.info("cmd :"+str(cmd))
        logger.info("Getting status.. :"+str(cmd))
        user = 'root'
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(node.ip, user, cmd)
            logger.info("output1 : "+str(output))
            if(output!=0):
                #verboseHandle.printConsoleInfo(" Service :"+str(cmd)+" not started.")
                logger.info(" Service :"+str(cmd)+" not started.")
                return output
    return output

def listAllServers():
    logger.info("Manager server list :")
    headers = [Fore.YELLOW+"Sr No"+Fore.RESET,
               Fore.YELLOW+"Type of host"+Fore.RESET,
               Fore.YELLOW+"IP"+Fore.RESET,
               Fore.YELLOW+"Status"+Fore.RESET]
    data=[]
    managerNodes = config_get_manager_node()
    count = 0
    for node in managerNodes:
        count = count+1
        status = getSpaceServerStatus(node.ip)
        if(status=="ON"):
            dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                       Fore.GREEN+"Manager"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+status+Fore.RESET,
                       ]
        else:
            dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                       Fore.GREEN+"Manager"+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.RED+status+Fore.RESET]
        data.append(dataArray)
    logger.info("Space server list.")
    spaceServers = config_get_space_hosts()
    host_dict_obj = host_dictionary()
    for server in spaceServers:
        cmd = 'systemctl is-active gs.service'
        user='root'
        output = executeRemoteCommandAndGetOutputPython36(server.ip, user, cmd)
        logger.info("executeRemoteCommandAndGetOutputPython36 : output:"+str(output))
        host_dict_obj.add(server.ip,str(output))
    logger.info("host_dict_obj :"+str(host_dict_obj))

    for server in spaceServers:
        count = count+1
        logger.info(server.ip)
        #status = getStatusOfHost(host_dict_obj,server)
        status = getStatusOfSpaceHost(server.ip)
        logger.info(status)
        if(status=="ON"):
            dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                       Fore.GREEN+"Space"+Fore.RESET,
                       Fore.GREEN+server.ip+Fore.RESET,
                       Fore.GREEN+str(status)+Fore.RESET,
                       ]
        else:
            dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                       Fore.GREEN+"Space"+Fore.RESET,
                       Fore.GREEN+server.ip+Fore.RESET,
                       Fore.RED+str(status)+Fore.RESET
                       ]
        data.append(dataArray)
    #cdcServers = config_cdc_list()
    logger.info("NB servers list")
    nbServers = config_get_nb_list()
    for server in nbServers:
        count = count+1
        status = getStatusOfNBHost(server)
        if(status=='ON'):
            dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                       Fore.GREEN+"Northbound "+server.role+Fore.RESET,
                       Fore.GREEN+server.ip+Fore.RESET,
                       Fore.GREEN+"ON"+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                       Fore.GREEN+"Northbound "+server.role+Fore.RESET,
                       Fore.GREEN+server.ip+Fore.RESET,
                       Fore.GREEN+"OFF"+Fore.RESET]
        data.append(dataArray)

    logger.info("Grafana server list.")
    grafanaServers = config_get_grafana_list()
    for server in grafanaServers:
        count = count+1
        status = getTelnetStatus(server.ip,3000)
        if(status=='ON'):
            dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                       Fore.GREEN+"Grafana"+Fore.RESET,
                       Fore.GREEN+server.ip+Fore.RESET,
                       Fore.GREEN+status+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                       Fore.GREEN+"Grafana"+Fore.RESET,
                       Fore.GREEN+server.ip+Fore.RESET,
                       Fore.RED+status+Fore.RESET]
        data.append(dataArray)

    logger.info("Influxdb servers list")
    influxdbServers = config_get_influxdb_node()
    for server in influxdbServers:
        status = getTelnetStatus(server.ip,8086)
        if(status=='ON'):
            dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                       Fore.GREEN+"Influxdb"+Fore.RESET,
                       Fore.GREEN+server.ip+Fore.RESET,
                       Fore.GREEN+status+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                       Fore.GREEN+"Influxdb"+Fore.RESET,
                       Fore.GREEN+server.ip+Fore.RESET,
                       Fore.RED+status+Fore.RESET]
        data.append(dataArray)

    logger.info("DI servers list")
    dIServers = config_get_dataIntegration_nodes()
    headers = [Fore.YELLOW+"Sr Num"+Fore.RESET,
               Fore.YELLOW+"Name"+Fore.RESET,
               Fore.YELLOW+"Type"+Fore.RESET,
               Fore.YELLOW+"Resume Mode"+Fore.RESET,
               Fore.YELLOW+"Role"+Fore.RESET,
               Fore.YELLOW+"Status"+Fore.RESET,
               Fore.YELLOW+"DIRole"+Fore.RESET]
    data=[]
    counter=1
    for node in dIServers:
        host_dict_obj.add(str(counter),str(node.ip))
        output = getConsolidatedStatus(node)
        if(output==0):
            dataArray=[Fore.GREEN+str(counter)+Fore.RESET,
                       Fore.GREEN+node.name+Fore.RESET,
                       Fore.GREEN+node.type+Fore.RESET,
                       Fore.GREEN+node.resumeMode+Fore.RESET,
                       Fore.GREEN+node.role+Fore.RESET,
                       Fore.GREEN+"ON"+Fore.RESET,
                       Fore.GREEN+""+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+str(counter)+Fore.RESET,
                       Fore.GREEN+node.name+Fore.RESET,
                       Fore.GREEN+node.type+Fore.RESET,
                       Fore.GREEN+node.resumeMode+Fore.RESET,
                       Fore.GREEN+node.role+Fore.RESET,
                       Fore.RED+"OFF"+Fore.RESET,
                       Fore.GREEN+""+Fore.RESET]
        data.append(dataArray)
        counter=counter+1
    printTabular(None,headers,data)

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> List-All')
    try:
        listAllServers()
    except Exception as e:
        logger.error("Exception in Servers->List-all"+str(e))
        verboseHandle.printConsoleError("Exception in Servers->List-all"+str(e))
