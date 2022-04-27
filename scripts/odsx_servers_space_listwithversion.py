# to remove space
import argparse
import os
import sys
from utils.odsx_print_tabular_data import printTabular
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_space_hosts
from colorama import Fore
import socket, platform
from utils.ods_validation import getSpaceServerStatus
from scripts.spinner import Spinner
from utils.ods_ssh import executeRemoteCommandAndGetOutput, executeRemoteShCommandAndGetOutput, executeRemoteCommandAndGetOutputPython36
from utils.ods_app_config import readValuefromAppConfig
import requests, json

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR

class host_nic_dictionary(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
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
    managerServerConfig = readValuefromAppConfig("app.manager.hosts")
    host_gsc_dict_obj =  host_nic_dictionary()
    host_gsc_mul_host_dict_obj =  host_nic_dictionary()
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
        response = requests.get(('http://'+managerServerConfig+':8090/v2/containers'), headers={'Accept': 'application/json'})
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

def getStatusOfSpaceHost(server):
    commandToExecute = "ps -ef | grep GSA"
    with Spinner():
        output = executeRemoteCommandAndGetOutput(server, 'root', commandToExecute)
    if(str(output).__contains__('services=GSA')):
        logger.info("services=GSA")
        return "ON"
    else:
        logger.info("services!=GSA")
        return "OFF"

def getVersion(ip):
    logger.info("getVersion() ip :"+str(ip))
    cmdToExecute = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh version | grep -v JAVA_HOME"
    logger.info("cmdToExecute : "+str(cmdToExecute))
    output = executeRemoteCommandAndGetOutput(ip,"root",cmdToExecute)
    output=str(output).replace('\n','')
    logger.info("output : "+str(output))
    return output

def listSpaceServer():
    try:
        logger.debug("listing space server with version")
        logger.info("listSpaceServer()")
        spaceServers = config_get_space_hosts()
        verboseHandle.printConsoleWarning("Servers -> Space -> ListWithVersion\n")
        headers = [Fore.YELLOW+"IP"+Fore.RESET,
                   Fore.YELLOW+"Host"+Fore.RESET,
                   Fore.YELLOW+"GSC"+Fore.RESET,
                   Fore.YELLOW+"Status"+Fore.RESET,
                   Fore.YELLOW+"Version"+Fore.RESET
                   ]
        data=[]
        user='root'
        logger.info("app.server.user: "+str(user))

        host_gsc_dict_obj = getGSCForHost()
        host_nic_dict_obj = host_nic_dictionary()

        for server in spaceServers:
            cmd = 'systemctl is-active gs.service'
            host = str(os.getenv(server.ip))
            logger.info("server.ip : "+host+" cmd :"+str(cmd))
            output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
            logger.info("executeRemoteCommandAndGetOutputPython36 : output:"+str(output))
            host_nic_dict_obj.add(host,str(output))

        logger.info("host_nic_dict_obj : "+str(host_nic_dict_obj))
        for server in spaceServers:
            host = str(os.getenv(server.ip))
            logger.info("server.ip : "+host)
            #status = getStatusOfHost(host_nic_dict_obj,server)
            status = getStatusOfSpaceHost(str(host))
            logger.info("status : "+str(status))
            logger.info("Host:"+str(host))
            gsc = host_gsc_dict_obj.get(str(host))
            logger.info("GSC : "+str(gsc))
            version = getVersion(host)
            dataArray=[Fore.GREEN+host+Fore.RESET,
                       Fore.GREEN+host+Fore.RESET,
                       Fore.GREEN+str(gsc)+Fore.RESET,
                       Fore.GREEN+status+Fore.RESET if(status=='ON') else Fore.RED+status+Fore.RESET,
                       Fore.GREEN+str(version)+Fore.RESET
                       ]

            data.append(dataArray)

        printTabular(None,headers,data)
    except Exception as e:
        logger.error("Error in odsx_servers_space_list "+str(e))
if __name__ == '__main__':
    args = []
    menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
    args.append(sys.argv[0])
    myCheckArg()
    with Spinner():
        listSpaceServer()
