#!/usr/bin/env python3

import argparse
import os.path
import signal
import sys

from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_servers_di_list import isInstalledNot
from scripts.odsx_servers_northbound_all_list import isInstalledAndGetVersion
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cleanup import signal_handler
from utils.ods_cluster_config import config_get_manager_node, config_get_iidrAccessServer_node, \
    config_get_iidrKafkaAgent_node, config_get_iidrOracleAgent_node, config_get_dataIntegrationSubscriptionManager_node
from utils.ods_cluster_config import config_get_space_hosts, config_get_nb_list, config_get_grafana_list, \
    config_get_influxdb_node, config_get_dataIntegration_nodes, config_get_dataIntegrationiidr_nodes, \
    config_get_service_hosts
from utils.ods_list import isInstalledAndGetVersionGrafana, isInstalledAndGetVersionInflux, isInstalledIIDRAccessServer, \
                            isInstalledIIDROracleAgent, isInstalledIIDRKafkaAgent, isInstalledIIDRSubscriptionManager
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36, executeRemoteCommandAndGetOutput, \
    executeRemoteCommandAndGetOutputValuePython36
from utils.ods_validation import getSpaceServerStatus
from utils.ods_validation import getTelnetStatus
from utils.odsx_print_tabular_data import printTabular

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
    cmd=''
    if(str(server.role).__contains__('agent')):
        cmd = "systemctl status consul.service"
    if(str(server.role).__contains__('applicative')):
        cmd = 'systemctl status northbound.target'
    if(str(server.role).__contains__('management')):
        cmd = 'systemctl status northbound.target'
    logger.info("Getting status.. :"+str(cmd))
    user = 'root'
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(os.getenv(server.ip), user, cmd)
    logger.info(cmd+" :"+str(output))
    if(output ==0):
        return "ON"
    else:
        return "OFF"

def getConsolidatedStatus(node,role):
    output=''
    user='root'
    cmdList=[]
    logger.info("getConsolidatedStatus() : "+str(os.getenv(node.ip)))
    cmdKafka1b = [ "systemctl status odsxkafka", "systemctl status telegraf"]
    cmdZookeeperWitness2 = [  "systemctl status odsxzookeeper", "systemctl status telegraf"]
    cmdList3 = [ "systemctl status odsxkafka" , "systemctl status odsxzookeeper", "systemctl status telegraf"]
    if role.__contains__("kafka Broker 1b"):
        cmdList = cmdKafka1b
    elif role.__contains__("Zookeeper Witness"):
        cmdList = cmdZookeeperWitness2
    else :
        cmdList = cmdList3
    logger.info(str(os.getenv(node.ip)+" : "+str(role)+" : "+str(cmdList)))
    #print(os.getenv(node.ip),role,cmdList)
    with Spinner():
        for cmd in cmdList:
            output = executeRemoteCommandAndGetOutputPython36(os.getenv(node.ip), user, cmd)
            logger.info("output1 : "+str(output))
            #print(output)
            if(output!=0):
                #verboseHandle.printConsoleInfo(" Service :"+str(cmd)+" not started.")
                logger.info(" Service :"+str(cmd)+" not started.")
                return output
    return output

def isInstalledAndGetVersionManagerSpace(host):
    logger.info("isInstalledAndGetVersion")
    #commandToExecute="ls -la /dbagiga | grep \"\->\" | awk \'{print $11}\'"
    commandToExecute='cd /dbagiga;cd -P gigaspaces-smart-ods;echo ""$(basename $(pwd))'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
    outputShFile=str(outputShFile).replace('\n','').replace('/dbagiga/','')
    logger.info("outputShFile :"+str(outputShFile))
    return str(outputShFile)

def listAllServers():
    logger.info("Manager server list :")
    headers = [Fore.YELLOW+"Sr No"+Fore.RESET,
               Fore.YELLOW+"Type of host"+Fore.RESET,
               Fore.YELLOW+"IP"+Fore.RESET,
               Fore.YELLOW+"Installed"+Fore.RESET,
               Fore.YELLOW+"Status"+Fore.RESET]
    data=[]
    managerNodes = config_get_manager_node()
    count = 0
    for node in managerNodes:
        count = count+1
        status = getSpaceServerStatus(os.getenv(node.ip))
        installStatus='No'
        install = isInstalledAndGetVersionManagerSpace(os.getenv(str(node.ip)))
        logger.info("install : "+str(install))
        if(len(str(install))>8):
            installStatus='Yes'
        dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                   Fore.GREEN+"Manager"+Fore.RESET,
                   Fore.GREEN+os.getenv(node.ip)+Fore.RESET,
                   Fore.GREEN+installStatus+Fore.RESET if(installStatus=='Yes') else Fore.RED+installStatus+Fore.RESET,
                   Fore.GREEN+status+Fore.RESET if(status=='ON') else Fore.RED+status+Fore.RESET]
        data.append(dataArray)
    logger.info("Space server list.")
    spaceServers = config_get_space_hosts()
    host_dict_obj = host_dictionary()
    for server in spaceServers:
        cmd = 'systemctl is-active gs.service'
        user='root'
        output = executeRemoteCommandAndGetOutputPython36(os.getenv(server.ip), user, cmd)
        logger.info("executeRemoteCommandAndGetOutputPython36 : output:"+str(output))
        host_dict_obj.add(os.getenv(server.ip),str(output))
    logger.info("host_dict_obj :"+str(host_dict_obj))

    for server in spaceServers:
        count = count+1
        logger.info(os.getenv(server.ip))
        #status = getStatusOfHost(host_dict_obj,server)
        status = getStatusOfSpaceHost(os.getenv(server.ip))
        logger.info("status"+str(status))
        installStatus='No'
        install = isInstalledAndGetVersionManagerSpace(os.getenv(str(server.ip)))
        logger.info("install : "+str(install))
        logger.info("install : "+str(install))
        if(len(str(install))>8):
            installStatus='Yes'
        dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                   Fore.GREEN+"Space"+Fore.RESET,
                   Fore.GREEN+os.getenv(server.ip)+Fore.RESET,
                   Fore.GREEN+installStatus+Fore.RESET if(installStatus=='Yes') else Fore.RED+installStatus+Fore.RESET,
                   Fore.GREEN+status+Fore.RESET if(status=='ON') else Fore.RED+status+Fore.RESET
                   ]
        data.append(dataArray)

    logger.info("Service server list.")
    serviceServers = config_get_service_hosts()
    for server in serviceServers:
        count = count+1
        logger.info(os.getenv(server.ip))
        status = getStatusOfSpaceHost(os.getenv(server.ip))
        logger.info("status"+str(status))
        installStatus='No'
        install = isInstalledAndGetVersionManagerSpace(os.getenv(str(server.ip)))
        logger.info("install : "+str(install))
        if(len(str(install))>8):
            installStatus='Yes'
        dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                   Fore.GREEN+"Service"+Fore.RESET,
                   Fore.GREEN+os.getenv(server.ip)+Fore.RESET,
                   Fore.GREEN+installStatus+Fore.RESET if(installStatus=='Yes') else Fore.RED+installStatus+Fore.RESET,
                   Fore.GREEN+status+Fore.RESET if(status=='ON') else Fore.RED+status+Fore.RESET
                   ]
        data.append(dataArray)
    #cdcServers = config_cdc_list()
    logger.info("NB servers list")
    nbServers = config_get_nb_list()
    for server in nbServers:
        host = str(os.getenv(server.ip))
        count = count+1
        if os.getenv(server.ip) is not None:
            status = getStatusOfNBHost(server)
            installStatus='No'
            install = isInstalledAndGetVersion(str(host))
            logger.info("install : "+str(install))
            if(len(str(install))>0):
                installStatus='Yes'
                dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                       Fore.GREEN+"Northbound "+server.role+Fore.RESET,
                       Fore.GREEN+str(os.getenv(server.ip))+Fore.RESET,
                       Fore.GREEN+installStatus+Fore.RESET if(installStatus=='Yes') else Fore.RED+installStatus+Fore.RESET,
                       Fore.GREEN+status+Fore.RESET if(status=='ON') else Fore.RED+status+Fore.RESET]
                data.append(dataArray)
        else:
            logger.info("server.ip -> " + str(server.ip) + ", HOST NONE")

    logger.info("Grafana server list.")
    grafanaServers = config_get_grafana_list()
    for server in grafanaServers:
        count = count+1
        status = getTelnetStatus(os.getenv(server.ip),3000)
        installStatus='No'
        host = str(os.getenv(server.ip))
        install = isInstalledAndGetVersionGrafana(str(host))
        logger.info("install : "+str(install))
        if(len(str(install))>0):
            installStatus='Yes'
        dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                   Fore.GREEN+"Grafana"+Fore.RESET,
                   Fore.GREEN+os.getenv(server.ip)+Fore.RESET,
                   Fore.GREEN+installStatus+Fore.RESET if(installStatus=='Yes') else Fore.RED+installStatus+Fore.RESET,
                   Fore.GREEN+status+Fore.RESET if(status=='ON') else Fore.RED+status+Fore.RESET]

        data.append(dataArray)

    logger.info("Influxdb servers list")
    influxdbServers = config_get_influxdb_node()
    for server in influxdbServers:
        count=count+1
        status = getTelnetStatus(os.getenv(server.ip),8086)
        host = str(os.getenv(server.ip))
        installStatus='No'
        install = isInstalledAndGetVersionInflux(str(host))
        logger.info("install : "+str(install))
        if(len(str(install))>0):
            installStatus='Yes'
        dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                   Fore.GREEN+"Influxdb"+Fore.RESET,
                   Fore.GREEN+os.getenv(server.ip)+Fore.RESET,
                   Fore.GREEN+installStatus+Fore.RESET if(installStatus=='Yes') else Fore.RED+installStatus+Fore.RESET,
                   Fore.GREEN+status+Fore.RESET if(status=='ON') else Fore.RED+status+Fore.RESET,]
        data.append(dataArray)

    get_iidrAccessServerServers = config_get_iidrAccessServer_node()
    for server in get_iidrAccessServerServers:
        count=count+1
        host = str(os.getenv(server.ip))

        IIDRAccessServerPort = readValuefromAppConfig("app.iidr.Access.Server.Port")
        IIDRAccessServerStatus = getTelnetStatus(os.getenv(server.ip),IIDRAccessServerPort)
        IIDRAccessServerInstallStatus='No'
        IIDRAccessServerInstall = isInstalledIIDRAccessServer(str(host))
        logger.info("IIDRAccessServerInstall : "+str(IIDRAccessServerInstall))
        if(len(str(IIDRAccessServerInstall))>0):
            IIDRAccessServerInstallStatus='Yes'

        IIDRAccessServerdataArray=[Fore.GREEN+str(count)+Fore.RESET,
                                       Fore.GREEN+"IIDR Access Server"+Fore.RESET,
                                       Fore.GREEN+os.getenv(server.ip)+Fore.RESET,
                                       Fore.GREEN+IIDRAccessServerInstallStatus+Fore.RESET if(IIDRAccessServerInstallStatus=='Yes') else Fore.RED+IIDRAccessServerInstallStatus+Fore.RESET,
                                       Fore.GREEN+IIDRAccessServerStatus+Fore.RESET if(IIDRAccessServerStatus=='ON') else Fore.RED+IIDRAccessServerStatus+Fore.RESET,]
        data.append(IIDRAccessServerdataArray)


    get_iidrKafkaAgentServers = config_get_iidrKafkaAgent_node()
    for server in get_iidrKafkaAgentServers:
        count=count+1
        host = str(os.getenv(server.ip))

        IIDRKafkaAgentPort = readValuefromAppConfig("app.iidr.Kafka.Agent.Port")
        IIDRKafkaAgentStatus = getTelnetStatus(os.getenv(server.ip),IIDRKafkaAgentPort)
        IIDRKafkaAgentInstallStatus='No'
        IIDRKafkaAgentInstall = isInstalledIIDRKafkaAgent(str(host))
        logger.info("IIDRKafkaAgentInstall : "+str(IIDRKafkaAgentInstall))
        if(len(str(IIDRKafkaAgentInstall))>0):
            IIDRKafkaAgentInstallStatus='Yes'

        IIDRKafkaAgentdataArray=[Fore.GREEN+str(count)+Fore.RESET,
                                     Fore.GREEN+"IIDR Kafka Agent"+Fore.RESET,
                                     Fore.GREEN+os.getenv(server.ip)+Fore.RESET,
                                     Fore.GREEN+IIDRKafkaAgentInstallStatus+Fore.RESET if(IIDRKafkaAgentInstallStatus=='Yes') else Fore.RED+IIDRKafkaAgentInstallStatus+Fore.RESET,
                                     Fore.GREEN+IIDRKafkaAgentStatus+Fore.RESET if(IIDRKafkaAgentStatus=='ON') else Fore.RED+IIDRKafkaAgentStatus+Fore.RESET,]
        data.append(IIDRKafkaAgentdataArray)

    get_iidrOracleAgentServers = config_get_iidrOracleAgent_node()
    for server in get_iidrOracleAgentServers:
        count=count+1
        host = str(os.getenv(server.ip))

        IIDROracleAgentPort = readValuefromAppConfig("app.iidr.Oracle.DB.Agent.Port")
        IIDROracleDBAgentStatus = getTelnetStatus(os.getenv(server.ip),IIDROracleAgentPort)
        IIDROracleAgentInstallStatus='No'
        IIDROracleAgentInstall = isInstalledIIDROracleAgent(str(host))
        logger.info("IIDROracleAgentInstall : "+str(IIDROracleAgentInstall))
        if(len(str(IIDROracleAgentInstall))>0):
            IIDROracleAgentInstallStatus='Yes'

        IIDROracleAgentdataArray=[Fore.GREEN+str(count)+Fore.RESET,
                   Fore.GREEN+"IIDR Oracle Agent"+Fore.RESET,
                   Fore.GREEN+os.getenv(server.ip)+Fore.RESET,
                   Fore.GREEN+IIDROracleAgentInstallStatus+Fore.RESET if(IIDROracleAgentInstallStatus=='Yes') else Fore.RED+IIDROracleAgentInstallStatus+Fore.RESET,
                   Fore.GREEN+IIDROracleDBAgentStatus+Fore.RESET if(IIDROracleDBAgentStatus=='ON') else Fore.RED+IIDROracleDBAgentStatus+Fore.RESET,]
        data.append(IIDROracleAgentdataArray)

    get_dataIntegrationSubscriptionManagerServers = config_get_dataIntegrationSubscriptionManager_node()
    for server in get_dataIntegrationSubscriptionManagerServers:
        count=count+1
        host = str(os.getenv(server.ip))

        IIDRSubscriptionMangerPort = readValuefromAppConfig("app.iidr.iidrSubscriptionMangerPort")
        IIDRSubscriptionMangerStatus = getTelnetStatus(os.getenv(server.ip),IIDRSubscriptionMangerPort)
        IIDRSubscriptionMangerInstallStatus='No'
        IIDRSubscriptionMangerInstall = isInstalledIIDRSubscriptionManager(str(host))
        logger.info("IIDRSubscriptionMangerInstall : "+str(IIDRSubscriptionMangerInstall))
        if(len(str(IIDRSubscriptionMangerInstall))>0):
            IIDRSubscriptionMangerInstallStatus='Yes'

        IIDRdataArray=[Fore.GREEN+str(count)+Fore.RESET,
                   Fore.GREEN+"IIDR Subscription Manger"+Fore.RESET,
                   Fore.GREEN+os.getenv(server.ip)+Fore.RESET,
                   Fore.GREEN+IIDRSubscriptionMangerInstallStatus+Fore.RESET if(IIDRSubscriptionMangerInstallStatus=='Yes') else Fore.RED+IIDRSubscriptionMangerInstallStatus+Fore.RESET,
                   Fore.GREEN+IIDRSubscriptionMangerStatus+Fore.RESET if(IIDRSubscriptionMangerStatus=='ON') else Fore.RED+IIDRSubscriptionMangerStatus+Fore.RESET,]
        data.append(IIDRdataArray)

    env = str(readValuefromAppConfig("app.setup.env"))
    if env != "dr":
        logger.info("DI servers list")
        dIServers = config_get_dataIntegration_nodes()
        counter=1
        for node in dIServers:
            count=count+1
            host_dict_obj.add(str(counter),str(node.ip))
            output = getConsolidatedStatus(node,str(node.type))
            installStatus = isInstalledNot(os.getenv(node.ip),str(node.type))
            dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                       Fore.GREEN+str(node.role)+" "+str(node.type)+Fore.RESET,
                       Fore.GREEN+os.getenv(node.name)+Fore.RESET,
                       Fore.GREEN+installStatus+Fore.RESET if(installStatus=='Yes') else Fore.RED+installStatus+Fore.RESET,
                       Fore.GREEN+"ON"+Fore.RESET if(output==0) else Fore.RED+"OFF"+Fore.RESET]

            data.append(dataArray)
            counter=counter+1
    printTabular(None,headers,data)

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> List-All')
    signal.signal(signal.SIGINT, signal_handler)
    try:
        listAllServers()
    except Exception as e:
        logger.error("Exception in Servers->List-all"+str(e))
        verboseHandle.printConsoleError("Exception in Servers->List-all"+str(e))
        handleException(e)