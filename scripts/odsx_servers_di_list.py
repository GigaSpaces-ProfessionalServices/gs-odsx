
import argparse
import os
import subprocess
import sys

from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_servers_di_install import getDIServerHostList
from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_dataIntegration_nodes, config_get_iidrAccessServer_node, \
    config_get_iidrKafkaAgent_node, config_get_iidrOracleAgent_node, config_get_dataIntegrationSubscriptionManager_node
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36, executeRemoteCommandAndGetOutputValuePython36
from utils.ods_ssh import get_ssh_user
from utils.ods_validation import isValidHost, port_check
from utils.odsx_print_tabular_data import printTabular, printTabularGrid, printTabularGridWrap, printTabularStream
from utils.ods_cluster_config import config_get_dataIntegrationiidr_nodes
from utils.ods_validation import getTelnetStatus
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_list import isInstalledIIDRAccessServer, isInstalledIIDROracleAgent, isInstalledIIDRKafkaAgent, \
    isInstalledIIDRSubscriptionManager
from utils.ods_app_config import readValuefromAppConfig

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

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

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR

def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    parser.add_argument('-dryrun', '--dryrun',
                        help='Dry run flag',
                        default='false', action='store_true')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])

def getKafkaStatus(node):
    logger.info("getConsolidatedStatus() : "+str(os.getenv(node.ip)))
    cmdList = ["systemctl --user status odsxkafka"]
    for cmd in cmdList:
        logger.info("cmd :"+str(cmd)+" host :"+str(os.getenv(node.ip)))
        logger.info("Getting status.. :"+str(cmd))
        user = get_ssh_user()
        if node.type == "Zookeeper Witness" and cmd == "systemctl --user status odsxkafka":
            output=0
            return Fore.GREEN+"NA"+Fore.RESET
        if node.type == "kafka Broker 1b" and cmd == "systemctl --user status odsxzookeeper":
            output=0
            return Fore.GREEN+"NA"+Fore.RESET
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(os.getenv(node.ip), user, cmd)
            logger.info("output1 : "+str(output))
            if(output!=0):
                #verboseHandle.printConsoleInfo(" Service :"+str(cmd)+" not started.")
                logger.info(" Service :"+str(cmd)+" not started."+str(os.getenv(node.ip)))
                return Fore.RED+"OFF"+Fore.RESET
            return Fore.GREEN+"ON"+Fore.RESET

def getZookeeperStatus(node):
    logger.info("getConsolidatedStatus() : "+str(os.getenv(node.ip)))
    cmdList = ["systemctl --user status odsxzookeeper"]
    for cmd in cmdList:
        logger.info("cmd :"+str(cmd)+" host :"+str(os.getenv(node.ip)))
        logger.info("Getting status.. :"+str(cmd))
        user = get_ssh_user()
        if node.type == "Zookeeper Witness" and cmd == "systemctl --user status odsxkafka":
            output=0
            return Fore.GREEN+"NA"+Fore.RESET
        if node.type == "kafka Broker 1b" and cmd == "systemctl --user status odsxzookeeper":
            output=0
            return Fore.GREEN+"NA"+Fore.RESET
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(os.getenv(node.ip), user, cmd)
            logger.info("output1 : "+str(output))
            if(output!=0):
                #verboseHandle.printConsoleInfo(" Service :"+str(cmd)+" not started.")
                logger.info(" Service :"+str(cmd)+" not started."+str(os.getenv(node.ip)))
                return Fore.RED+"OFF"+Fore.RESET
            return Fore.GREEN+"ON"+Fore.RESET


def getConsolidatedStatus(node):
    output=''
    logger.info("getConsolidatedStatus() : "+str(os.getenv(node.ip)))
    cmdList = [ "sudo systemctl status odsxkafka" , "sudo systemctl status odsxzookeeper", "sudo systemctl status telegraf"]
    for cmd in cmdList:
        logger.info("cmd :"+str(cmd)+" host :"+str(os.getenv(node.ip)))
        if(str(node.type)=='kafka Broker 1b' and cmd=='systemctl --user status odsxzookeeper'):
            output=0
        elif(str(node.type)=='Zookeeper Witness' and cmd=='systemctl --user status odsxkafka'):
            output=0
        else:
            logger.info("Getting status.. :"+str(cmd))
            user = get_ssh_user()
            with Spinner():
                output = executeRemoteCommandAndGetOutputPython36(os.getenv(node.ip), user, cmd)
                logger.info("output1 : "+str(output))
                if(output!=0):
                    #verboseHandle.printConsoleInfo(" Service :"+str(cmd)+" not started.")
                    logger.info(" Service :"+str(cmd)+" not started."+str(os.getenv(node.ip)))
                    return Fore.RED+"OFF"+Fore.RESET
    if output==0:
        return Fore.GREEN+"ON"+Fore.RESET
    return Fore.RED+"OFF"+Fore.RESET

def roleOfCurrentNode(ip):
    logger.info("isCurrentNodeLeaderNode(ip) "+str(ip))
    cmd = "echo srvr | nc "+ip+" 2181"
    #print(cmd)
    output = subprocess.getoutput(cmd)
    #print(output)
    logger.info("output "+str(output))
    if(str(output).__contains__('Mode: leader')):
        return "Primary"
    elif(str(output).__contains__('Mode: follower')):
        return "Secondary"
    else:
        return "None"
def isZkInstalledNot(host,role):
    if(str(role)=='kafka Broker 1b'):
        return Fore.GREEN+"NA"+Fore.RESET
    logger.info("isKafkaInstalledNot"+str(host)+" : "+str(role))
    isInstalled = "Yes"
    commandToExecute='ls ~/.config/systemd/user/odsxzookeeper.service'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, get_ssh_user(), commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    if len(str(outputShFile))==0:
        return Fore.RED+"NO"+Fore.RESET
    return Fore.GREEN+"Yes"+Fore.RESET

def isKafkaInstalledNot(host,role):
    if(str(role)=='Zookeeper Witness'):
        return Fore.GREEN+"NA"+Fore.RESET
    logger.info("isKafkaInstalledNot"+str(host)+" : "+str(role))
    isInstalled = "Yes"
    commandToExecute='ls ~/.config/systemd/user/odsxkafka.service'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, get_ssh_user(), commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    if len(str(outputShFile))==0:
        return Fore.RED+"NO"+Fore.RESET
    return Fore.GREEN+"Yes"+Fore.RESET

def isMDMInstalled(host,nodeType):
    if(str(nodeType)=='Zookeeper Witness'):
        return Fore.GREEN+"NA"+Fore.RESET
    logger.info("isMDMInstalled"+str(host))
    isInstalled = "Yes"
    commandToExecute='ls ~/.config/systemd/user/di-mdm.service'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, get_ssh_user(), commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    if len(str(outputShFile))==0:
        return Fore.RED+"NO"+Fore.RESET
    return Fore.GREEN+"Yes"+Fore.RESET

def getMDMStatus(host,nodeType):
    if(str(nodeType)=='Zookeeper Witness'):
        return Fore.GREEN+"NA"+Fore.RESET
    cmd = "systemctl --user status di-mdm.service"
    with Spinner():
        user = get_ssh_user()
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        logger.info("output1 : "+str(output))
        if(output!=0):
            logger.info(" Service :"+str(cmd)+" not started."+str(host))
            return Fore.RED+"OFF"+Fore.RESET
        return Fore.GREEN+"ON"+Fore.RESET

def isDIMInstalled(host,nodeType):
    if(str(nodeType)=='Zookeeper Witness'):
        return Fore.GREEN+"NA"+Fore.RESET
    logger.info("isDIMInstalled"+str(host))
    isInstalled = "Yes"
    commandToExecute='ls ~/.config/systemd/user/di-manager.service'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, get_ssh_user(), commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    if len(str(outputShFile))==0:
        return Fore.RED+"NO"+Fore.RESET
    return Fore.GREEN+"Yes"+Fore.RESET

def getDIMStatus(host,nodeType):
    if(str(nodeType)=='Zookeeper Witness'):
        return Fore.GREEN+"NA"+Fore.RESET
    cmd = "systemctl --user status di-manager.service"
    with Spinner():
        user = get_ssh_user()
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        logger.info("output1 : "+str(output))
        if(output!=0):
            logger.info(" Service :"+str(cmd)+" not started."+str(host))
            return Fore.RED+"OFF"+Fore.RESET
        return Fore.GREEN+"ON"+Fore.RESET

def isFLinkInstalled(host,nodeType):
    if(str(nodeType)=='Zookeeper Witness'):
        return Fore.GREEN+"NA"+Fore.RESET
    logger.info("isDIMInstalled"+str(host))
    isInstalled = "Yes"
    dbaGigaPath=readValuefromAppConfig("app.giga.path")
    commandToExecute='ls '+ dbaGigaPath +'/di-flink/latest-flink/bin/start-cluster.sh'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, get_ssh_user(), commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    if len(str(outputShFile))==0:
        return Fore.RED+"NO"+Fore.RESET
    return Fore.GREEN+"Yes"+Fore.RESET

def getFlinkStatus(host,nodeType):
    if(str(nodeType)=='Zookeeper Witness'):
        return Fore.GREEN+"NA"+Fore.RESET
    cmd = ""
    with Spinner():
        if(isValidHost(host)):
            status = port_check(host,8081)
            if(status==False):
                logger.info(" Service :di-flink not started."+str(host))
                return Fore.RED+"OFF"+Fore.RESET
    cmd = "systemctl --user status di-flink-taskmanager.service"
    with Spinner():
        user = get_ssh_user()
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        logger.info("output1 : "+str(output))
        if(output!=0):
            logger.info(" Service :"+str(cmd)+" not started."+str(host))
            return Fore.RED+"OFF"+Fore.RESET
    cmd = "systemctl --user status di-flink-jobmanager.service"
    with Spinner():
        user = get_ssh_user()
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        logger.info("output1 : "+str(output))
        if(output!=0):
            logger.info(" Service :"+str(cmd)+" not started."+str(host))
            return Fore.RED+"OFF"+Fore.RESET

    return Fore.GREEN+"ON"+Fore.RESET

#For all combinations
def isInstalledNot(host,role):
    logger.info("isInstalledNot"+str(host)+" : "+str(role))
    isInstalled = "Yes"
    if role != "kafka Broker 1b":
        commandToExecute='ls ~/.config/systemd/user/odsxzookeeper.service'
        logger.info("commandToExecute :"+str(commandToExecute))
        outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, get_ssh_user(), commandToExecute)
        outputShFile=str(outputShFile).replace('\n','')
        logger.info("outputShFile :"+str(outputShFile))
        if len(str(outputShFile))==0:
            return Fore.GREEN+"NA"+Fore.RESET
    if role != "Zookeeper Witness":
        commandToExecute='ls ~/.config/systemd/user/odsxkafka.service'
        logger.info("commandToExecute :"+str(commandToExecute))
        outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, get_ssh_user(), commandToExecute)
        outputShFile=str(outputShFile).replace('\n','')
        logger.info("outputShFile :"+str(outputShFile))
        if len(str(outputShFile))==0:
            return Fore.GREEN+"NA"+Fore.RESET

    commandToExecute='ls /usr/lib/systemd/system/telegraf.service'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, get_ssh_user(), commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    if len(str(outputShFile))==0:
        return "No"

    return isInstalled

def getSingleZkStatus(node):
    user = get_ssh_user()
    cmd = "systemctl --user status odsxzookeeper"
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(os.getenv(node.ip), user, cmd)
        logger.info("output1 : "+str(output))
        if(output!=0):
            logger.info(" Service :"+str(cmd)+" not started."+str(os.getenv(node.ip)))
        return output

def getSingleKafkaStatus(node):
    user = get_ssh_user()
    cmd = "systemctl --user status odsxkafka"
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(os.getenv(node.ip), user, cmd)
        logger.info("output1 : "+str(output))
        if(output!=0):
            logger.info(" Service :"+str(cmd)+" not started."+str(os.getenv(node.ip)))
        return output

def getSingleConsolidatedStatus(node):
    output=''
    logger.info("getSingleConsolidatedStatus() : "+str(os.getenv(node.ip)))
    cmdList = [ "sudo systemctl status odsxkafka" , "sudo systemctl status odsxzookeeper", "sudo systemctl status telegraf"]
    for cmd in cmdList:
        logger.info("cmd :"+str(cmd)+" host :"+str(os.getenv(node.ip)))
        user = get_ssh_user()
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(os.getenv(node.ip), user, cmd)
            logger.info("output1 : "+str(output))
            if(output!=0):
                logger.info(" Service :"+str(cmd)+" not started."+str(os.getenv(node.ip)))
                return output
    return output

def listDIServers():
    logger.info("listDIServers()")
    host_dict_obj = obj_type_dictionary()
    dIServers = config_get_dataIntegration_nodes("config/cluster.config")
    headers = [
                Fore.YELLOW+"Component"+Fore.RESET,
                Fore.YELLOW+"Kafka\n"+Fore.YELLOW+"Broker 1"+Fore.RESET,
                Fore.YELLOW+"Kafka\n"+Fore.YELLOW+"Broker 2"+Fore.RESET,
                Fore.YELLOW+"Kafka\n"+Fore.YELLOW+"Broker 3"+Fore.RESET,
                Fore.YELLOW+"ZK1"+Fore.RESET,
                Fore.YELLOW+"ZK2"+Fore.RESET,
                Fore.YELLOW+"ZK3"+Fore.RESET,
                Fore.YELLOW+"DI\n"+Fore.YELLOW+"Manager"+Fore.RESET,
                Fore.YELLOW+"DI\n"+Fore.YELLOW+"MDM"+Fore.RESET,
                Fore.YELLOW+"DI\n"+Fore.YELLOW+"FLink"+Fore.RESET,
               Fore.YELLOW+"DI\n"+Fore.YELLOW+"Subscription\n"+Fore.YELLOW+"Manager"+Fore.RESET,
               Fore.YELLOW+"IIDR\n"+Fore.YELLOW+"Access\n"+Fore.YELLOW+"Server"+Fore.RESET,
               Fore.YELLOW+"IIDR\n"+Fore.YELLOW+"Kafka\n"+Fore.YELLOW+"Agent"+Fore.RESET,
               Fore.YELLOW+"IIDR\n"+Fore.YELLOW+"Oracle\n"+Fore.YELLOW+"Agent"+Fore.RESET]
    data=[]
    counter=1
    kafkaPortStatus1 = 'OFF'
    kafkaPortStatus2 = 'OFF'
    kafkaPortStatus3 = 'OFF'
    zkPortStatus1 = 'OFF'
    zkPortStatus2 = 'OFF'
    zkPortStatus3 = 'OFF'

    kafkaInstallStatus1 = 'NO'
    kafkaInstallStatus2 = 'NO'
    kafkaInstallStatus3 = 'NO'
    zkInstallStatus1 = 'NO'
    zkInstallStatus2 = 'NO'
    zkInstallStatus3 = 'NO'

    IIDRSubscriptionMangerInstallStatus=""
    IIDRAccessServerInstallStatus=""
    IIDRKafkaAgentInstallStatus=""
    IIDROracleAgentInstallStatus=""
    IIDRSubscriptionMangerStatus=""
    IIDRAccessServerStatus=""
    IIDRKafkaAgentStatus=""
    IIDROracleDBAgentStatus=""

    for node in dIServers:
        host_dict_obj.add(str(counter),str(os.getenv(node.ip)))
        output = getConsolidatedStatus(node)
        DIKafkaPort = readValuefromAppConfig("app.di.kafka.Port")
        zkClientPort = readValuefromAppConfig("app.di.base.zk.clientPort")

        if counter == 1:
            kafkaPortStatus1 = getTelnetStatus(os.getenv(node.ip),DIKafkaPort)
            zkPortStatus1 = getTelnetStatus(os.getenv(node.ip),zkClientPort)
            kafkaInstallStatus1 = isKafkaInstalledNot(os.getenv(node.ip),str(node.type))
            zkInstallStatus1 = isZkInstalledNot(os.getenv(node.ip),str(node.type))
        elif counter == 2:
            kafkaPortStatus2 = getTelnetStatus(os.getenv(node.ip),DIKafkaPort)
            zkPortStatus2 = getTelnetStatus(os.getenv(node.ip),zkClientPort)
            kafkaInstallStatus2 = isKafkaInstalledNot(os.getenv(node.ip),str(node.type))
            zkInstallStatus2 = isZkInstalledNot(os.getenv(node.ip),str(node.type))
        elif counter == 3:
            kafkaPortStatus3 = getTelnetStatus(os.getenv(node.ip),DIKafkaPort)
            zkPortStatus3 = getTelnetStatus(os.getenv(node.ip),zkClientPort)
            kafkaInstallStatus3 = isKafkaInstalledNot(os.getenv(node.ip),str(node.type))
            zkInstallStatus3 = isZkInstalledNot(os.getenv(node.ip),str(node.type))

        #role = roleOfCurrentNode(os.getenv(node.ip))
        #For Combination
        #installStatus = isInstalledNot(os.getenv(node.ip),str(node.type))
        # installStatusKafka = isKafkaInstalledNot(os.getenv(node.ip),str(node.type))
        # installStatusZk = isZkInstalledNot(os.getenv(node.ip),str(node.type))
        # logger.info("Install status Zk: "+str(installStatusZk)+"Install status kafka: "+str(installStatusKafka)+" : "+str(os.getenv(node.ip))+" : "+str(node.type))
        nodeListSize = len(str((getDIServerHostList())).split(','))
        installStatusMDM=isMDMInstalled(os.getenv(node.ip),str(node.type))
        installStatusDIM=isDIMInstalled(os.getenv(node.ip),str(node.type))
        installStatusFLink=isFLinkInstalled(os.getenv(node.ip),str(node.type))
        serviceStatusMDM=getMDMStatus(os.getenv(node.ip),str(node.type))
        serviceStatusDIM=getDIMStatus(os.getenv(node.ip),str(node.type))
        serviceStatusFLink=getFlinkStatus(os.getenv(node.ip),str(node.type))
        counter=counter+1

    get_iidrAccessServerServers = config_get_iidrAccessServer_node()
    for server in get_iidrAccessServerServers:
        IIDRAccessServerPort = readValuefromAppConfig("app.iidr.Access.Server.Port")
        IIDRAccessServerStatus = getTelnetStatus(os.getenv(server.ip),IIDRAccessServerPort)
        IIDRAccessServerInstallStatus='No'
        IIDRAccessServerInstall = isInstalledIIDRAccessServer(str(os.getenv(server.ip)))
        logger.info("IIDRAccessServerInstall : "+str(IIDRAccessServerInstall))
        if(len(str(IIDRAccessServerInstall))>0):
            IIDRAccessServerInstallStatus='Yes'


    get_iidrKafkaAgentServers = config_get_iidrKafkaAgent_node()
    for server in get_iidrKafkaAgentServers:
        IIDRKafkaAgentPort = readValuefromAppConfig("app.iidr.Kafka.Agent.Port")
        IIDRKafkaAgentStatus = getTelnetStatus(os.getenv(server.ip),IIDRKafkaAgentPort)
        IIDRKafkaAgentInstallStatus='No'
        IIDRKafkaAgentInstall = isInstalledIIDRKafkaAgent(str(os.getenv(server.ip)))
        logger.info("IIDRKafkaAgentInstall : "+str(IIDRKafkaAgentInstall))
        if(len(str(IIDRKafkaAgentInstall))>0):
            IIDRKafkaAgentInstallStatus='Yes'


    get_iidrOracleAgentServers = config_get_iidrOracleAgent_node()
    for server in get_iidrOracleAgentServers:
        IIDROracleAgentPort = readValuefromAppConfig("app.iidr.Oracle.DB.Agent.Port")
        IIDROracleDBAgentStatus = getTelnetStatus(os.getenv(server.ip),IIDROracleAgentPort)
        IIDROracleAgentInstallStatus='No'
        IIDROracleAgentInstall = isInstalledIIDROracleAgent(str(os.getenv(server.ip)))
        logger.info("IIDROracleAgentInstall : "+str(IIDROracleAgentInstall))
        if(len(str(IIDROracleAgentInstall))>0):
            IIDROracleAgentInstallStatus='Yes'


    get_dataIntegrationSubscriptionManagerServers = config_get_dataIntegrationSubscriptionManager_node()
    for server in get_dataIntegrationSubscriptionManagerServers:
        IIDRSubscriptionMangerPort = readValuefromAppConfig("app.iidr.iidrSubscriptionMangerPort")
        IIDRSubscriptionMangerStatus = getTelnetStatus(os.getenv(server.ip),IIDRSubscriptionMangerPort)
        IIDRSubscriptionMangerInstallStatus='No'
        IIDRSubscriptionMangerInstall = isInstalledIIDRSubscriptionManager(str(os.getenv(server.ip)))
        logger.info("IIDRSubscriptionMangerInstall : "+str(IIDRSubscriptionMangerInstall))
        if(len(str(IIDRSubscriptionMangerInstall))>0):
            IIDRSubscriptionMangerInstallStatus='Yes'

    dataHostArray=[Fore.YELLOW+"HostName"+Fore.RESET,
                   Fore.YELLOW+"DI1"+Fore.RESET,
                   Fore.YELLOW+"DI2"+Fore.RESET,
                   Fore.YELLOW+"DI3"+Fore.RESET,
                   Fore.YELLOW+"DI1"+Fore.RESET,
                   Fore.YELLOW+"DI2"+Fore.RESET,
                   Fore.YELLOW+"DI3"+Fore.RESET,
                   Fore.YELLOW+"DI1"+Fore.RESET,
                   Fore.YELLOW+"DI1"+Fore.RESET,
                   Fore.YELLOW+"DI1"+Fore.RESET,
                   Fore.YELLOW+"IIDR1"+Fore.RESET,
                   Fore.YELLOW+"IIDR1"+Fore.RESET,
                   Fore.YELLOW+"IIDR1"+Fore.RESET,
                   Fore.YELLOW+"IIDR-DBAgent"+Fore.RESET
                   ]

    dataInstallCheckArray=[Fore.YELLOW+"Install Status"+Fore.RESET,
                           kafkaInstallStatus1,
                           kafkaInstallStatus2,
                           kafkaInstallStatus3,
                           zkInstallStatus1,
                           zkInstallStatus2,
                           zkInstallStatus3,
                           installStatusDIM,
                           installStatusMDM,
                           installStatusFLink,
                           Fore.GREEN+IIDRSubscriptionMangerInstallStatus+Fore.RESET if(IIDRSubscriptionMangerInstallStatus=='Yes') else Fore.RED+IIDRSubscriptionMangerInstallStatus+Fore.RESET,
                           Fore.GREEN+IIDRAccessServerInstallStatus+Fore.RESET if(IIDRAccessServerInstallStatus=='Yes') else Fore.RED+IIDRAccessServerInstallStatus+Fore.RESET,
                            Fore.GREEN+IIDRKafkaAgentInstallStatus+Fore.RESET if(IIDRKafkaAgentInstallStatus=='Yes') else Fore.RED+IIDRKafkaAgentInstallStatus+Fore.RESET,
                           Fore.GREEN+IIDROracleAgentInstallStatus+Fore.RESET if(IIDROracleAgentInstallStatus=='Yes') else Fore.RED+IIDROracleAgentInstallStatus+Fore.RESET
                           ]

    dataStatusArray=[Fore.YELLOW+"Port Status"+Fore.RESET,
            Fore.GREEN+kafkaPortStatus1+Fore.RESET if(kafkaPortStatus1=='ON') else Fore.RED+kafkaPortStatus1+Fore.RESET,
            Fore.GREEN+kafkaPortStatus2+Fore.RESET if(kafkaPortStatus2=='ON') else Fore.RED+kafkaPortStatus2+Fore.RESET,
            Fore.GREEN+kafkaPortStatus3+Fore.RESET if(kafkaPortStatus3=='ON') else Fore.RED+kafkaPortStatus3+Fore.RESET,
            Fore.GREEN+zkPortStatus1+Fore.RESET if(zkPortStatus1=='ON') else Fore.RED+zkPortStatus1+Fore.RESET,
            Fore.GREEN+zkPortStatus2+Fore.RESET if(zkPortStatus2=='ON') else Fore.RED+zkPortStatus2+Fore.RESET,
            Fore.GREEN+zkPortStatus3+Fore.RESET if(zkPortStatus3=='ON') else Fore.RED+zkPortStatus3+Fore.RESET,
            Fore.GREEN+serviceStatusDIM+Fore.RESET if(serviceStatusDIM=='ON') else Fore.RED+serviceStatusDIM+Fore.RESET,
            Fore.GREEN+serviceStatusMDM+Fore.RESET if(serviceStatusMDM=='ON') else Fore.RED+serviceStatusMDM+Fore.RESET,
            Fore.GREEN+serviceStatusFLink+Fore.RESET if(serviceStatusFLink=='ON') else Fore.RED+serviceStatusFLink+Fore.RESET,
            Fore.GREEN+IIDRSubscriptionMangerStatus+Fore.RESET if(IIDRSubscriptionMangerStatus=='ON') else Fore.RED+IIDRSubscriptionMangerStatus+Fore.RESET,
            Fore.GREEN+IIDRAccessServerStatus+Fore.RESET if(IIDRAccessServerStatus=='ON') else Fore.RED+IIDRAccessServerStatus+Fore.RESET,
            Fore.GREEN+IIDRKafkaAgentStatus+Fore.RESET if(IIDRKafkaAgentStatus=='ON') else Fore.RED+IIDRKafkaAgentStatus+Fore.RESET,
            Fore.GREEN+IIDROracleDBAgentStatus+Fore.RESET if(IIDROracleDBAgentStatus=='ON') else Fore.RED+IIDROracleDBAgentStatus+Fore.RESET]

    data.append(dataHostArray)
    data.append(dataInstallCheckArray)
    data.append(dataStatusArray)
    # printTabular(None,headers,data)
    printTabularGrid(None,headers,data)
    return host_dict_obj

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> DI -> List')
    try:
        args = []
        menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
        args.append(sys.argv[0])
        myCheckArg()
        listDIServers()
    except Exception as e:
        handleException(e)
