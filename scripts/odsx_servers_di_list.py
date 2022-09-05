
import argparse, subprocess
import os
import sys

from scripts.odsx_servers_di_install import getDIServerHostList
from utils.ods_validation import isValidHost, port_check
from utils.odsx_print_tabular_data import printTabular
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_dataIntegration_nodes
from colorama import Fore
from scripts.spinner import Spinner
from utils.ods_ssh import executeRemoteCommandAndGetOutput,executeRemoteCommandAndGetOutputPython36,executeRemoteCommandAndGetOutputValuePython36


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
    cmdList = ["systemctl status odsxkafka"]
    for cmd in cmdList:
        logger.info("cmd :"+str(cmd)+" host :"+str(os.getenv(node.ip)))
        logger.info("Getting status.. :"+str(cmd))
        user = 'root'
        if node.type == "Zookeeper Witness" and cmd == "systemctl status odsxkafka":
            output=0
            return output
        if node.type == "kafka Broker 1b" and cmd == "systemctl status odsxzookeeper":
            output=0
            return output
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(os.getenv(node.ip), user, cmd)
            logger.info("output1 : "+str(output))
            if(output!=0):
                #verboseHandle.printConsoleInfo(" Service :"+str(cmd)+" not started.")
                logger.info(" Service :"+str(cmd)+" not started."+str(os.getenv(node.ip)))
            return output

def getZookeeperStatus(node):
    logger.info("getConsolidatedStatus() : "+str(os.getenv(node.ip)))
    cmdList = ["systemctl status odsxzookeeper"]
    for cmd in cmdList:
        logger.info("cmd :"+str(cmd)+" host :"+str(os.getenv(node.ip)))
        logger.info("Getting status.. :"+str(cmd))
        user = 'root'
        if node.type == "Zookeeper Witness" and cmd == "systemctl status odsxkafka":
            output=0
            return output
        if node.type == "kafka Broker 1b" and cmd == "systemctl status odsxzookeeper":
            output=0
            return output
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(os.getenv(node.ip), user, cmd)
            logger.info("output1 : "+str(output))
            if(output!=0):
                #verboseHandle.printConsoleInfo(" Service :"+str(cmd)+" not started.")
                logger.info(" Service :"+str(cmd)+" not started."+str(os.getenv(node.ip)))
            return output


def getConsolidatedStatus(node):
    output=''
    logger.info("getConsolidatedStatus() : "+str(os.getenv(node.ip)))
    cmdList = [ "systemctl status odsxkafka" , "systemctl status odsxzookeeper", "systemctl status telegraf"]
    for cmd in cmdList:
        logger.info("cmd :"+str(cmd)+" host :"+str(os.getenv(node.ip)))
        if(str(node.type)=='kafka Broker 1b' and cmd=='systemctl status odsxzookeeper'):
            output=0
        elif(str(node.type)=='Zookeeper Witness' and cmd=='systemctl status odsxkafka'):
            output=0
        else:
            logger.info("Getting status.. :"+str(cmd))
            user = 'root'
            with Spinner():
                output = executeRemoteCommandAndGetOutputPython36(os.getenv(node.ip), user, cmd)
                logger.info("output1 : "+str(output))
                if(output!=0):
                    #verboseHandle.printConsoleInfo(" Service :"+str(cmd)+" not started.")
                    logger.info(" Service :"+str(cmd)+" not started."+str(os.getenv(node.ip)))
                    return output
    return output

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
    logger.info("isKafkaInstalledNot"+str(host)+" : "+str(role))
    isInstalled = "Yes"
    commandToExecute='ls /etc/systemd/system/odsxzookeeper.service'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    if len(str(outputShFile))==0:
        return "No"
    return isInstalled

def isKafkaInstalledNot(host,role):
    logger.info("isKafkaInstalledNot"+str(host)+" : "+str(role))
    isInstalled = "Yes"
    commandToExecute='ls /etc/systemd/system/odsxkafka.service'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    if len(str(outputShFile))==0:
        return "No"
    return isInstalled

def isMDMInstalled(host):
    logger.info("isMDMInstalled"+str(host))
    isInstalled = "Yes"
    commandToExecute='ls /etc/systemd/system/di-mdm.service'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    if len(str(outputShFile))==0:
        return Fore.RED+"NO"+Fore.RESET
    return Fore.GREEN+"Yes"+Fore.RESET

def getMDMStatus(host):
    cmd = "systemctl status di-mdm.service"
    with Spinner():
        user='root'
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        logger.info("output1 : "+str(output))
        if(output!=0):
            logger.info(" Service :"+str(cmd)+" not started."+str(host))
            return Fore.RED+"OFF"+Fore.RESET
        return Fore.GREEN+"ON"+Fore.RESET

def isDIMInstalled(host):
    logger.info("isDIMInstalled"+str(host))
    isInstalled = "Yes"
    commandToExecute='ls /etc/systemd/system/di-manager.service'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    if len(str(outputShFile))==0:
        return Fore.RED+"NO"+Fore.RESET
    return Fore.GREEN+"Yes"+Fore.RESET

def getDIMStatus(host):
    cmd = "systemctl status di-manager.service"
    with Spinner():
        user='root'
        output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
        logger.info("output1 : "+str(output))
        if(output!=0):
            logger.info(" Service :"+str(cmd)+" not started."+str(host))
            return Fore.RED+"OFF"+Fore.RESET
        return Fore.GREEN+"ON"+Fore.RESET

def isFLinkInstalled(host):
    logger.info("isDIMInstalled"+str(host))
    isInstalled = "Yes"
    commandToExecute='ls /dbagiga/di-flink/latest-flink/bin/start-cluster.sh'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    if len(str(outputShFile))==0:
        return Fore.RED+"NO"+Fore.RESET
    return Fore.GREEN+"Yes"+Fore.RESET

def getFlinkStatus(host):
    cmd = ""

    with Spinner():
        if(isValidHost(host)):
            status = port_check(host,8081)
            if(status==False):
                logger.info(" Service :di-flink not started."+str(host))
                return Fore.RED+"OFF"+Fore.RESET
        return Fore.GREEN+"ON"+Fore.RESET

#For all combinations
def isInstalledNot(host,role):
    logger.info("isInstalledNot"+str(host)+" : "+str(role))
    isInstalled = "Yes"
    if role != "kafka Broker 1b":
        commandToExecute='ls /etc/systemd/system/odsxzookeeper.service'
        logger.info("commandToExecute :"+str(commandToExecute))
        outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
        outputShFile=str(outputShFile).replace('\n','')
        logger.info("outputShFile :"+str(outputShFile))
        if len(str(outputShFile))==0:
            return "No"
    if role != "Zookeeper Witness":
        commandToExecute='ls /etc/systemd/system/odsxkafka.service'
        logger.info("commandToExecute :"+str(commandToExecute))
        outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
        outputShFile=str(outputShFile).replace('\n','')
        logger.info("outputShFile :"+str(outputShFile))
        if len(str(outputShFile))==0:
            return "No"

    commandToExecute='ls /usr/lib/systemd/system/telegraf.service'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    if len(str(outputShFile))==0:
        return "No"

    return isInstalled

def getSingleZkStatus(node):
    user="root"
    cmd = "systemctl status odsxzookeeper"
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(os.getenv(node.ip), user, cmd)
        logger.info("output1 : "+str(output))
        if(output!=0):
            logger.info(" Service :"+str(cmd)+" not started."+str(os.getenv(node.ip)))
        return output

def getSingleKafkaStatus(node):
    user="root"
    cmd = "systemctl status odsxkafka"
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(os.getenv(node.ip), user, cmd)
        logger.info("output1 : "+str(output))
        if(output!=0):
            logger.info(" Service :"+str(cmd)+" not started."+str(os.getenv(node.ip)))
        return output

def getSingleConsolidatedStatus(node):
    output=''
    logger.info("getSingleConsolidatedStatus() : "+str(os.getenv(node.ip)))
    cmdList = [ "systemctl status odsxkafka" , "systemctl status odsxzookeeper", "systemctl status telegraf"]
    for cmd in cmdList:
        logger.info("cmd :"+str(cmd)+" host :"+str(os.getenv(node.ip)))
        user = 'root'
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
    headers = [Fore.YELLOW+"Id"+Fore.RESET,
               Fore.YELLOW+"Host"+Fore.RESET,
               Fore.YELLOW+"Type"+Fore.RESET,
               Fore.YELLOW+"Kafka\n"+Fore.YELLOW+"Inst."+Fore.RESET,
               Fore.YELLOW+"ZK\n"+Fore.YELLOW+"Inst."+Fore.RESET,
               Fore.YELLOW+"Status\n"+Fore.YELLOW+"Infra"+Fore.RESET,
               Fore.YELLOW+"Kafka\n"+Fore.YELLOW+"Status"+Fore.RESET,
               Fore.YELLOW+"ZK\n"+Fore.YELLOW+"Status"+Fore.RESET,
               Fore.YELLOW+"MDM\n"+Fore.YELLOW+"Inst./Status"+Fore.RESET,
               Fore.YELLOW+"DIM\n"+Fore.YELLOW+"Inst./Status"+Fore.RESET,
               Fore.YELLOW+"FLink\n"+Fore.YELLOW+"Inst./Status"+Fore.RESET]
    data=[]
    counter=1
    for node in dIServers:
        host_dict_obj.add(str(counter),str(os.getenv(node.ip)))
        output = getConsolidatedStatus(node)
        kafkaOutput = getKafkaStatus(node)
        zkOutput = getZookeeperStatus(node)
        #role = roleOfCurrentNode(os.getenv(node.ip))
        #For Combination
        #installStatus = isInstalledNot(os.getenv(node.ip),str(node.type))
        installStatusKafka = isKafkaInstalledNot(os.getenv(node.ip),str(node.type))
        installStatusZk = isZkInstalledNot(os.getenv(node.ip),str(node.type))
        logger.info("Install status Zk: "+str(installStatusZk)+"Install status kafka: "+str(installStatusKafka)+" : "+str(os.getenv(node.ip))+" : "+str(node.type))
        nodeListSize = len(str((getDIServerHostList())).split(','))
        installStatusMDM=isMDMInstalled(os.getenv(node.ip))
        installStatusDIM=isDIMInstalled(os.getenv(node.ip))
        installStatusFLink=isFLinkInstalled(os.getenv(node.ip))
        serviceStatusMDM=getMDMStatus(os.getenv(node.ip))
        serviceStatusDIM=getDIMStatus(os.getenv(node.ip))
        serviceStatusFLink=getFlinkStatus(os.getenv(node.ip))
        if(nodeListSize==4):
            if(kafkaOutput==0 and zkOutput==0 and output==0):
                dataArray=[Fore.GREEN+str(counter)+Fore.RESET,
                           Fore.GREEN+os.getenv(node.name)+Fore.RESET,
                           Fore.GREEN+node.type+Fore.RESET,
                           Fore.GREEN+installStatusKafka+Fore.RESET if(installStatusKafka=='Yes') else Fore.RED+installStatusKafka+Fore.RESET,
                           Fore.GREEN+installStatusZk+Fore.RESET if(installStatusZk=='Yes') else Fore.RED+installStatusZk+Fore.RESET,
                           Fore.GREEN+"ON"+Fore.RESET,
                           Fore.GREEN+"ON"+Fore.RESET,
                           Fore.GREEN+"ON"+Fore.RESET,
                           Fore.GREEN+installStatusMDM+"/"+serviceStatusMDM,
                           Fore.GREEN+installStatusDIM+"/"+serviceStatusDIM,
                           Fore.GREEN+installStatusFLink+"/"+serviceStatusFLink]
            elif(kafkaOutput==0 and zkOutput==0 and output!=0):
                dataArray=[Fore.GREEN+str(counter)+Fore.RESET,
                           Fore.GREEN+os.getenv(node.name)+Fore.RESET,
                           Fore.GREEN+node.type+Fore.RESET,
                           Fore.GREEN+installStatusKafka+Fore.RESET if(installStatusKafka=='Yes') else Fore.RED+installStatusKafka+Fore.RESET,
                           Fore.GREEN+installStatusZk+Fore.RESET if(installStatusZk=='Yes') else Fore.RED+installStatusZk+Fore.RESET,
                           Fore.RED+"OFF"+Fore.RESET,
                           Fore.GREEN+"ON"+Fore.RESET,
                           Fore.GREEN+"ON"+Fore.RESET,
                           Fore.GREEN+installStatusMDM+"/"+serviceStatusMDM,
                           Fore.GREEN+installStatusDIM+"/"+serviceStatusDIM,
                           Fore.GREEN+installStatusFLink+"/"+serviceStatusFLink]
            elif(kafkaOutput!=0 and zkOutput==0 and output!=0):
                dataArray=[Fore.GREEN+str(counter)+Fore.RESET,
                           Fore.GREEN+os.getenv(node.name)+Fore.RESET,
                           Fore.GREEN+node.type+Fore.RESET,
                           Fore.GREEN+installStatusKafka+Fore.RESET if(installStatusKafka=='Yes') else Fore.RED+installStatusKafka+Fore.RESET,
                           Fore.GREEN+installStatusZk+Fore.RESET if(installStatusZk=='Yes') else Fore.RED+installStatusZk+Fore.RESET,
                           Fore.RED+"OFF"+Fore.RESET,
                           Fore.RED+"OFF"+Fore.RESET,
                           Fore.GREEN+"NA"+Fore.RESET,
                           Fore.GREEN+installStatusMDM+"/"+serviceStatusMDM,
                           Fore.GREEN+installStatusDIM+"/"+serviceStatusDIM,
                           Fore.GREEN+installStatusFLink+"/"+serviceStatusFLink]
            elif(kafkaOutput==0 and zkOutput!=0 and output!=0):
                dataArray=[Fore.GREEN+str(counter)+Fore.RESET,
                           Fore.GREEN+os.getenv(node.name)+Fore.RESET,
                           Fore.GREEN+node.type+Fore.RESET,
                           Fore.GREEN+installStatusKafka+Fore.RESET if(installStatusKafka=='Yes') else Fore.RED+installStatusKafka+Fore.RESET,
                           Fore.GREEN+installStatusZk+Fore.RESET if(installStatusZk=='Yes') else Fore.RED+installStatusZk+Fore.RESET,
                           Fore.RED+"OFF"+Fore.RESET,
                           Fore.GREEN+"NA"+Fore.RESET,
                           Fore.RED+"OFF"+Fore.RESET,
                           Fore.GREEN+installStatusMDM+"/"+serviceStatusMDM,
                           Fore.GREEN+installStatusDIM+"/"+serviceStatusDIM,
                           Fore.GREEN+installStatusFLink+"/"+serviceStatusFLink]
            else:
                dataArray=[Fore.GREEN+str(counter)+Fore.RESET,
                           Fore.GREEN+os.getenv(node.name)+Fore.RESET,
                           Fore.GREEN+node.type+Fore.RESET,
                           Fore.GREEN+installStatusKafka+Fore.RESET if(installStatusKafka=='Yes') else Fore.RED+installStatusKafka+Fore.RESET,
                           Fore.GREEN+installStatusZk+Fore.RESET if(installStatusZk=='Yes') else Fore.RED+installStatusZk+Fore.RESET,
                           Fore.RED+"OFF"+Fore.RESET,
                           Fore.RED+"OFF"+Fore.RESET,
                           Fore.RED+"OFF"+Fore.RESET,
                           Fore.GREEN+installStatusMDM+"/"+serviceStatusMDM,
                           Fore.GREEN+installStatusDIM+"/"+serviceStatusDIM,
                           Fore.GREEN+installStatusFLink+"/"+serviceStatusFLink]
        else:
            dataArray=[Fore.GREEN+str(counter)+Fore.RESET,
                       Fore.GREEN+os.getenv(node.name)+Fore.RESET,
                       Fore.GREEN+node.type+Fore.RESET,
                       Fore.GREEN+installStatusKafka+Fore.RESET if(installStatusKafka=='Yes') else Fore.RED+installStatusKafka+Fore.RESET,
                       Fore.GREEN+installStatusZk+Fore.RESET if(installStatusZk=='Yes') else Fore.RED+installStatusZk+Fore.RESET,
                       Fore.GREEN+"ON"+Fore.RESET if(getSingleConsolidatedStatus(node)==0) else Fore.RED+"OFF"+Fore.RESET,
                       Fore.GREEN+"ON"+Fore.RESET if(getSingleKafkaStatus(node)==0) else Fore.RED+"OFF"+Fore.RESET,
                       Fore.GREEN+"ON"+Fore.RESET if(getSingleZkStatus(node)==0) else Fore.RED+"OFF"+Fore.RESET,
                       Fore.GREEN+installStatusMDM+"/"+serviceStatusMDM,
                       Fore.GREEN+installStatusDIM+"/"+serviceStatusDIM,
                       Fore.GREEN+installStatusFLink+"/"+serviceStatusFLink]
        data.append(dataArray)
        counter=counter+1
    printTabular(None,headers,data)
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
