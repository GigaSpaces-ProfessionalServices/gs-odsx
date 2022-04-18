# to remove space
import argparse
import os
import sys
from utils.odsx_print_tabular_data import printTabular
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from colorama import Fore
import socket, platform
from utils.ods_validation import getSpaceServerStatus,port_check_config
from scripts.spinner import Spinner
from utils.ods_ssh import executeRemoteCommandAndGetOutput, executeRemoteShCommandAndGetOutput, executeRemoteCommandAndGetOutputPython36
from utils.ods_app_config import readValuefromAppConfig
import requests, json
from requests.auth import HTTPBasicAuth
from utils.odsx_db2feeder_utilities import getPasswordByHost, getUsernameByHost

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

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
        #print(host_gsc_dict_obj)
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
    cmdToExecute = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh --username="+username+" --password="+password+" version | grep -v JAVA_HOME"
    logger.info("cmdToExecute : "+str(cmdToExecute))
    output = executeRemoteCommandAndGetOutput(ip,"root",cmdToExecute)
    output=str(output).replace('\n','')
    logger.info("output : "+str(output))
    return output

def listSpaceServer():
    try:
        logger.debug("listing space server")
        logger.info("listSpaceServer()")
        spaceServers = config_get_space_hosts()
        verboseHandle.printConsoleWarning("Menu -> Security -> Space -> List\n")
        headers = [Fore.YELLOW+"IP"+Fore.RESET,
                   Fore.YELLOW+"Host"+Fore.RESET,
                   Fore.YELLOW+"GSC"+Fore.RESET,
                   Fore.YELLOW+"Status"+Fore.RESET
                   #Fore.YELLOW+"Version"+Fore.RESET
                   ]
        data=[]
        userConfig = readValuefromAppConfig("app.server.user")
        # changed : 25-Aug hence systemctl always with root no need to ask
        #user = str(input("Enter your user ["+userConfig+"]: "))
        #if(len(str(user))==0):
        #    user=userConfig
        user='root'
        logger.info("app.server.user: "+str(user))

        host_gsc_dict_obj = getGSCForHost()
        host_nic_dict_obj = host_nic_dictionary()

        for server in spaceServers:
            if (port_check_config(server.ip,22)):
                cmd = 'systemctl is-active gs.service'
                logger.info("server.ip : "+str(server.ip)+" cmd :"+str(cmd))
                output = executeRemoteCommandAndGetOutputPython36(server.ip, user, cmd)
                logger.info("executeRemoteCommandAndGetOutputPython36 : output:"+str(output))
                host_nic_dict_obj.add(server.ip,str(output))
            else:
                logger.info(" Host GSC :"+str(server.ip)+" is not reachable")

        logger.info("host_nic_dict_obj : "+str(host_nic_dict_obj))
        for server in spaceServers:
            logger.info("server.ip : "+str(server.ip))
            #status = getStatusOfHost(host_nic_dict_obj,server)
            status=''
            gsc=''
            if (port_check_config(server.ip,22)):
                status = getStatusOfSpaceHost(str(server.ip))
                logger.info("status GSC : "+str(status))
                logger.info("Host GSC :"+str(server.name))
                #gsc = host_gsc_dict_obj.get(str(socket.gethostbyaddr(server.name).__getitem__(0)))
                gsc = host_gsc_dict_obj.get(str(server.name))
                logger.info("GSC : "+str(gsc))
            else:
                status="NOT REACHABLE"
                gsc = host_gsc_dict_obj.get(str(socket.gethostbyaddr(server.name).__getitem__(0)))
                #gsc = host_gsc_dict_obj.get(str(server.name))
                logger.info(" Host :"+str(server.ip)+" is not reachable")
            #version = getVersion(server.ip)
            if(status=="ON"):
                dataArray=[Fore.GREEN+server.ip+Fore.RESET,
                           Fore.GREEN+server.name+Fore.RESET,
                           Fore.GREEN+str(gsc)+Fore.RESET,
                           Fore.GREEN+str(status)+Fore.RESET
                           #Fore.GREEN+str(version)+Fore.RESET
                           ]
            else:
                dataArray=[Fore.GREEN+server.ip+Fore.RESET,
                           Fore.GREEN+server.name+Fore.RESET,
                           Fore.GREEN+str(gsc)+Fore.RESET,
                           Fore.RED+str(status)+Fore.RESET
                           #Fore.GREEN+str(version)+Fore.RESET
                           ]
            data.append(dataArray)

        printTabular(None,headers,data)
    except Exception as e:
        logger.error("Error in odsx_servers_space_list "+str(e))
        handleException(e)

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


if __name__ == '__main__':
    args = []
    menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
    args.append(sys.argv[0])
    myCheckArg()
    username = ""
    password = ""
    appId=""
    safeId=""
    objectId=""
    try:
        appId = str(readValuefromAppConfig("app.space.security.appId")).replace('"','')
        safeId = str(readValuefromAppConfig("app.space.security.safeId")).replace('"','')
        objectId = str(readValuefromAppConfig("app.space.security.objectId")).replace('"','')
        logger.info("appId : "+appId+" safeID : "+safeId+" objectID : "+objectId)
        managerNodes = config_get_manager_node()
        managerHost = getManagerHost(managerNodes)
        logger.info("managerHost : main"+str(managerHost))
        username = str(getUsernameByHost(managerHost,appId,safeId,objectId))
        password = str(getPasswordByHost(managerHost,appId,safeId,objectId))
        with Spinner():
            listSpaceServer()
    except Exception as e:
        handleException(e)

