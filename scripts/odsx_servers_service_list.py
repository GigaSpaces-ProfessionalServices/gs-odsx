import argparse
import os
import socket
import sys
from concurrent.futures import ThreadPoolExecutor

import json
import requests
from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_servers_manager_list import isInstalledAndGetVersion
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_service_hosts, getManagerHostFromEnv
from utils.ods_ssh import executeRemoteCommandAndGetOutput, executeRemoteCommandAndGetOutputPython36
from utils.ods_validation import port_check_config
from utils.odsx_print_tabular_data import printTabular

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR

class host_nic_dictionary(dict):
    def __init__(self):
        self = dict()

    def add(self, key, value):
        self[key] = value

def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    parser.add_argument('-dryrun', '--dryrun',
                        help='Dry run flag',
                        default='false', action='store_true')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])

def getGSCForHost():
    logger.info("getGSCForHost")
    managerServerConfig = getManagerHostFromEnv()
    host_gsc_dict_obj = host_nic_dictionary()
    managerServerConfigArr=[]
    if(str(managerServerConfig).__contains__(',')):  # if cluster manager configured
        managerServerConfig = str(managerServerConfig).replace('"','')
        managerServerConfigArr = managerServerConfig.split(',')
        logger.info("MangerServerConfigArray: "+str(managerServerConfigArr))
        host_gsc_dict_obj = getGSCByManagerServerConfig(managerServerConfigArr[0], host_gsc_dict_obj)
    else:
        logger.info("managerServerConfig :"+str(managerServerConfig))
        host_gsc_dict_obj = getGSCByManagerServerConfig(managerServerConfig, host_gsc_dict_obj)
    return host_gsc_dict_obj

def getGSCByManagerServerConfig(managerServerConfig, host_gsc_dict_obj):
    logger.info("getGSCByManagerServerConfig() : managerServerConfig :"+str(managerServerConfig)+" host_gsc_dict_obj :"+str(host_gsc_dict_obj))
    try:
        logger.info("Getting response for :"+str(managerServerConfig))
        response = requests.get(('http://'+managerServerConfig+':8090/v2/containers'), headers={'Accept': 'application/json'})
        output = response.content.decode("utf-8")
        logger.info("Json Response container:"+str(output))
        datas = json.loads(output)
        for i in datas :
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

def getStatusOfServiceHost(server):
    commandToExecute = "ps -ef | grep GSA"
    output = executeRemoteCommandAndGetOutput(server, 'root', commandToExecute)
    if(str(output).__contains__('services=GSA')):
        logger.info("services=GSA")
        return "ON"
    else:
        logger.info("services!=GSA")
        return "OFF"

def checkActiveStatus(server,host_nic_dict_obj,user):
    if (port_check_config(os.getenv(server.ip),22)):
        cmd = 'systemctl is-active gsa.service'
        logger.info("server.ip : "+str(os.getenv(server.ip))+" cmd :"+str(cmd))
        output = executeRemoteCommandAndGetOutputPython36(os.getenv(server.ip), user, cmd)
        logger.info("executeRemoteCommandAndGetOutputPython36 : output:"+str(output))
        host_nic_dict_obj.add(os.getenv(server.ip),str(output))
    else:
        logger.info(" Host :"+str(os.getenv(server.ip))+" is not reachable")

def printListOfService(server,data,host_gsc_dict_obj):
    host = os.getenv(server.ip)
    logger.info("server.ip : "+str(server.ip))
    installStatus='No'
    install = isInstalledAndGetVersion(os.getenv(str(server.ip)))
    logger.info("install : "+str(install))
    if(len(str(install))>8):
        installStatus='Yes'
    if (port_check_config(host,22)):
        status = getStatusOfServiceHost(str(host))
        logger.info("status : "+str(status))
        logger.info("Host:"+str(host))
        #adding split to get just hostname and not fully qualified name
        isAwsEnv = readValuefromAppConfig("app.isaws.env")
        gsc=''
        if str(isAwsEnv).strip().lower() == 'true':
            gsc = host_gsc_dict_obj.get(str(socket.gethostbyaddr(host).__getitem__(0)))
        else:
            gsc = host_gsc_dict_obj.get(str(socket.gethostbyaddr(host).__getitem__(0)).split('.')[0])
        logger.info("GSC : "+str(gsc))
    else:
        status="NOT REACHABLE"
        gsc = host_gsc_dict_obj.get(str(host))
        logger.info(" Host :"+str(server.ip)+" is not reachable")
    dataArray=[Fore.GREEN+host+Fore.RESET,
               Fore.GREEN+str(gsc)+Fore.RESET,
               Fore.GREEN+installStatus+Fore.RESET if(installStatus=='Yes') else Fore.RED+installStatus+Fore.RESET,
               Fore.GREEN+status+Fore.RESET if(status=='ON') else Fore.RED+status+Fore.RESET,
               Fore.GREEN+install+Fore.RESET if(installStatus=='Yes') else Fore.RED+'N/A'+Fore.RESET]
    data.append(dataArray)


def listServiceServer():
    try:
        logger.debug("listing service server")
        logger.info("listServiceServer()")
        serviceServers = config_get_service_hosts()
        verboseHandle.printConsoleWarning("Menu -> Servers -> Service -> List\n")
        headers = [Fore.YELLOW+"Host"+Fore.RESET,
                   Fore.YELLOW+"GSC"+Fore.RESET,
                   Fore.YELLOW+"Installed"+Fore.RESET,
                   Fore.YELLOW+"Status"+Fore.RESET,
                   Fore.YELLOW+"Version"+Fore.RESET
                   ]
        global data
        data=[]
        user='root'
        logger.info("app.server.user: "+str(user))

        host_gsc_dict_obj = getGSCForHost()
        global host_nic_dict_obj
        host_nic_dict_obj = host_nic_dictionary()

        serviceHostsLength = len(serviceServers)+1
        with ThreadPoolExecutor(serviceHostsLength) as executor:
           for server in serviceServers:
               executor.submit(checkActiveStatus,server,host_nic_dict_obj,user)

        logger.info("host_nic_dict_obj : "+str(host_nic_dict_obj))
        with ThreadPoolExecutor(serviceHostsLength) as executor:
            for server in serviceServers:
                    executor.submit(printListOfService,server,data,host_gsc_dict_obj)

        printTabular(None,headers,data)
    except Exception as e:
        logger.error("Error in odsx_servers_service_list "+str(e))
if __name__ == '__main__':
    args = []
    menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
    args.append(sys.argv[0])
    myCheckArg()
    listServiceServer()
