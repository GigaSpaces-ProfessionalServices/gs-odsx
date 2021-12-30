
import argparse, subprocess
import os
import sys
from utils.odsx_print_tabular_data import printTabular
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_dataIntegration_nodes
from colorama import Fore
from scripts.spinner import Spinner
from utils.ods_ssh import executeRemoteCommandAndGetOutput,executeRemoteCommandAndGetOutputPython36

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
    logger.info("getConsolidatedStatus() : "+str(node.ip))
    cmdList = [ "systemctl status odsxzookeeper" , "systemctl status odsxkafka"]
    for cmd in cmdList:
        logger.info("cmd :"+str(cmd)+" host :"+str(node.ip))
        logger.info("Getting status.. :"+str(cmd))
        user = 'root'
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(node.ip, user, cmd)
            logger.info("output1 : "+str(output))
            if(output!=0):
                #verboseHandle.printConsoleInfo(" Service :"+str(cmd)+" not started.")
                logger.info(" Service :"+str(cmd)+" not started."+str(node.ip))
            return output

def getConsolidatedStatus(node):
    output=''
    logger.info("getConsolidatedStatus() : "+str(node.ip))
    cmdList = [ "systemctl status odsxkafka" , "systemctl status odsxzookeeper", "systemctl status odsxcr8", "systemctl status telegraf"]
    for cmd in cmdList:
        logger.info("cmd :"+str(cmd)+" host :"+str(node.ip))
        if(str(node.type)=='Witness' and cmd=='systemctl status odsxcr8'):
            output=0
        else:
            logger.info("Getting status.. :"+str(cmd))
            user = 'root'
            with Spinner():
                output = executeRemoteCommandAndGetOutputPython36(node.ip, user, cmd)
                logger.info("output1 : "+str(output))
                if(output!=0):
                    #verboseHandle.printConsoleInfo(" Service :"+str(cmd)+" not started.")
                    logger.info(" Service :"+str(cmd)+" not started."+str(node.ip))
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

def listDIServers():
    logger.info("listDIServers()")
    host_dict_obj = obj_type_dictionary()
    dIServers = config_get_dataIntegration_nodes("config/cluster.config")
    headers = [Fore.YELLOW+"Sr Num"+Fore.RESET,
               Fore.YELLOW+"Name"+Fore.RESET,
               Fore.YELLOW+"Type"+Fore.RESET,
               Fore.YELLOW+"Resume Mode"+Fore.RESET,
               Fore.YELLOW+"Role"+Fore.RESET,
               Fore.YELLOW+"Status"+Fore.RESET,
               Fore.YELLOW+"Kafka Status"+Fore.RESET,
               Fore.YELLOW+"DIRole"+Fore.RESET]
    data=[]
    counter=1
    for node in dIServers:
        host_dict_obj.add(str(counter),str(node.ip))
        output = getConsolidatedStatus(node)
        kafkaOutput = getKafkaStatus(node)
        role = roleOfCurrentNode(node.ip)
        if(kafkaOutput==0 and output==0):
            dataArray=[Fore.GREEN+str(counter)+Fore.RESET,
                       Fore.GREEN+node.name+Fore.RESET,
                       Fore.GREEN+node.type+Fore.RESET,
                       Fore.GREEN+node.resumeMode+Fore.RESET,
                       Fore.GREEN+node.role+Fore.RESET,
                       Fore.GREEN+"ON"+Fore.RESET,
                       Fore.GREEN+"ON"+Fore.RESET,
                       Fore.GREEN+str(role)+Fore.RESET]
        elif(kafkaOutput==0 and output!=1):
            dataArray=[Fore.GREEN+str(counter)+Fore.RESET,
                       Fore.GREEN+node.name+Fore.RESET,
                       Fore.GREEN+node.type+Fore.RESET,
                       Fore.GREEN+node.resumeMode+Fore.RESET,
                       Fore.GREEN+node.role+Fore.RESET,
                       Fore.RED+"OFF"+Fore.RESET,
                       Fore.GREEN+"ON"+Fore.RESET,
                       Fore.GREEN+str(role)+Fore.RESET]
        elif(kafkaOutput!=1 and output==0):
            dataArray=[Fore.GREEN+str(counter)+Fore.RESET,
                       Fore.GREEN+node.name+Fore.RESET,
                       Fore.GREEN+node.type+Fore.RESET,
                       Fore.GREEN+node.resumeMode+Fore.RESET,
                       Fore.GREEN+node.role+Fore.RESET,
                       Fore.GREEN+"ON"+Fore.RESET,
                       Fore.RED+"OFF"+Fore.RESET,
                       Fore.GREEN+str(role)+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+str(counter)+Fore.RESET,
                       Fore.GREEN+node.name+Fore.RESET,
                       Fore.GREEN+node.type+Fore.RESET,
                       Fore.GREEN+node.resumeMode+Fore.RESET,
                       Fore.GREEN+node.role+Fore.RESET,
                       Fore.RED+"OFF"+Fore.RESET,
                       Fore.RED+"OFF"+Fore.RESET,
                       Fore.GREEN+str(role)+Fore.RESET]
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
