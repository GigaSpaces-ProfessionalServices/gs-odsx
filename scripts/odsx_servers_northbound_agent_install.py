#!/usr/bin/env python3

import os
import platform
from os import path
from utils.ods_app_config import set_value_in_property_file, readValuefromAppConfig
from colorama import Fore
from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_add_nb_node, config_get_nb_list, config_get_grafana_list, config_get_influxdb_node, config_get_manager_node
from utils.ods_scp import scp_upload
from utils.ods_ssh import connectExecuteSSH, executeRemoteCommandAndGetOutput
from utils.odsx_read_properties_file import createPropertiesMapFromFile
from utils.ods_ssh import executeRemoteShCommandAndGetOutput
from scripts.odsx_servers_northbound_applicative_install import proceedForEnvHostConfiguration

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
nbConfig = {}

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

def getManagementHostList():
    logger.info("getManagementHostList()")
    nodeList = config_get_nb_list()
    nodes=""
    for node in nodeList:
        if(str(node.role).casefold() == 'management'):
            if(len(nodes)==0):
                nodes = node.ip
            else:
                nodes = nodes+','+node.ip
    return nodes

def check_prerequisite_NB():
    baseDir = "installationpackages/nb/"
    if path.exists(baseDir + "nb-infra"):
        if path.exists(baseDir + "nb-infra/nb.conf"):
            if path.exists(baseDir + "nb-infra/ssl/server.crt") and path.exists(
                    baseDir + "nb-infra/ssl/cacert.crt") and path.exists(
                baseDir + "/nb-infra/ssl/server.key"):
                if path.exists(baseDir + "nb-infra/consul-1.9.5-2.x86_64.rpm") and path.exists(
                        baseDir + "nb-infra/nginx-1.19.10-1.el7.ngx.x86_64.rpm"):
                    verboseHandle.printConsoleInfo("All required installation files exist")
                    return True
                else:
                    verboseHandle.printConsoleError("consul or nginx rpm file missing")
            else:
                verboseHandle.printConsoleError("ssl key or certificate is missing")
                return False
        else:
            verboseHandle.printConsoleError("nb.conf file not exit")
            return False
    else:
        verboseHandle.printConsoleError("nb installation directory is missing")
        return False


# Ask for required bn.conf properties
def update_app_config_file(linePatternToReplace, value, lines1):
    if lines1 == None:
        file_name = "/dbagigashare/current/NB/APPLICATIVE/nb.conf.template"
        lines = open(file_name, 'r').readlines()
    else:
        lines = lines1
    lineNo = -1
    for line in lines:
        lineNo = lineNo + 1
        # if line.startswith("#") or line.startswith("\n"):
        #    continue
        # else:
        #    print(line)
        if line.startswith(linePatternToReplace):
            print(linePatternToReplace + '"' + value + '"')
            break
    lines[lineNo] = ""
    lines[lineNo] = linePatternToReplace + '"' + value + '"\n'

    out = open("config/nb.conf", 'w')
    out.writelines(lines)
    out.close()
    return lines


class host_dictionary(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR


host_dict_obj = host_dictionary()
host_dict_management_obj = host_dictionary()
nb_user = ""
applicationServerFlag = ""

def getConsulServers(consul_replica_number):
    logger.info("getConsulServers(consul_replica_number) : "+str(consul_replica_number))
    consul_servers = ""
    '''
    for x in range(1,int(consul_replica_number)+1):
        server = str(input(Fore.YELLOW+"Enter CONSUL_SERVER"+str(x)+" :"+Fore.RESET))
        while(len(server)==0):
            server = str(input(Fore.YELLOW+"Enter CONSUL_SERVER"+str(x)+" :"+Fore.RESET))
        logger.info("CONSUL_SERVER"+str(x)+" :"+str(server))
        if(len(str(consul_servers))>0):
            consul_servers = consul_servers+','+server
        else:
            consul_servers = server
    '''
    consul_servers = getNBApplicativeHostFromEnv()
    logger.info("consul_servers : "+str(consul_servers))
    return consul_servers

def proceedForApplicationServiceAgentInstallation():
    logger.info("proceedForApplicationServiceAgentInstallation()")
    spaceHostsConfig = str(getNBAgentHostFromEnv()).replace('"','')
    logger.info("spaceHostsConfig : "+str(spaceHostsConfig))
    existingAgentHostConfirm=""
    if(len(str(spaceHostsConfig))>0):
        print(Fore.YELLOW+"Proceeding with NB agent configuration ["+str(spaceHostsConfig)+"] "+Fore.RESET)
        spaceHostsConfigArray = spaceHostsConfig.split(',')
        logger.info("Total number of space hosts :"+str(len(spaceHostsConfigArray)))
        for host in spaceHostsConfigArray:
            logger.info("entered Host"+str(host))
            host_dict_obj.add(host, '')
        #elif(existingAgentHostConfirm=='n'):
        #    proceedWithFreshAgentInstallation()
    else:
        logger.info("No NB Agent /space host configuration found.")
        verboseHandle.printConsoleInfo("No NB Agent /space host configuration found.")
        #proceedWithFreshAgentInstallation()

def proceedWithFreshAgentInstallation():
    logger.info("proceedWithFreshAgentInstallation()")
    noOfHost = str(input(Fore.YELLOW + "Enter number of host to install NB agents :" + Fore.RESET))
    while (len(str(noOfHost)) == 0 or (not noOfHost.isdigit())):
        noOfHost = str(input(Fore.YELLOW + "Enter number of host to install NB agents : " + Fore.RESET))
    logger.info("noOfHost"+str(noOfHost))
    logger.debug("No of host :" + str(noOfHost))
    noOfHost = int(noOfHost)
    agentHostConfig=""
    for x in range(1, noOfHost + 1):
        host = str(input(Fore.YELLOW + "Enter NB agent host" + str(x) + " :" + Fore.RESET))
        while (len(str(host)) == 0):
            host = str(input(Fore.YELLOW + "Enter NB agent host" + str(x) + " :" + Fore.RESET))
        logger.info("entered Host"+str(host))
        host_dict_obj.add(host, '')
        if(len(str(agentHostConfig))>0):
            agentHostConfig = agentHostConfig+','+host
        else:
            agentHostConfig = host
    #set_value_in_property_file('app.space.hosts',agentHostConfig)

def proceedForManagementServiceInstallation():
    logger.info("proceedForManagementServiceInstallation()")
    managementConfirm=''
    #managementConfirm = str(input("Do you wanto to proceed with NB management server installation (y/n) [y]?"))
    #if(len(str(managementConfirm))==0):
    managementConfirm='y'
    logger.info("managementConfirm : "+str(managementConfirm))
    if(managementConfirm=='y'):
        managementHostsConfig = str(getNBManagementHostFromEnv()).replace('"','')
        logger.info("managementHostsConfig : "+str(managementHostsConfig))
        existingManagementHostConfirm=""
        if(len(str(managementHostsConfig))>0):
            #print(Fore.YELLOW+"Proceeding with existing NB management configuration ["+str(managementHostsConfig)+"] "+Fore.RESET)
            managementHostsConfigArray = managementHostsConfig.split(',')
            logger.info("Total number of NB management hosts :"+str(len(managementHostsConfigArray)))
            for host in managementHostsConfigArray:
                logger.info("entered Host"+str(host))
                host_dict_management_obj.add(host, '')
            logger.info("host_dict_management_obj : "+str(host_dict_management_obj))
            #elif(existingManagementHostConfirm=='n'):
            #    proceedWithFreshManagementInstallation()
        else:
            logger.info("No NB management host configuration found.")
            verboseHandle.printConsoleInfo("No NB management host configuration found.")
            #proceedWithFreshManagementInstallation()
    else:
        logger.info("Skipping NB management server installation.")
        verboseHandle.printConsoleInfo("Skipping NB management server installation.")

def proceedWithFreshManagementInstallation():
    logger.info("proceedWithFreshManagementInstallation()")
    noOfHost = str(input(Fore.YELLOW + "Enter number of host to install NB management  :" + Fore.RESET))
    while (len(str(noOfHost)) == 0 or (not noOfHost.isdigit())):
        noOfHost = str(input(Fore.YELLOW + "Enter number of host to install NB management : " + Fore.RESET))
    logger.info("noOfHost"+str(noOfHost))
    logger.debug("No of host :" + str(noOfHost))
    noOfHost = int(noOfHost)
    managementHostConfig=""
    for x in range(1, noOfHost + 1):
        host = str(input(Fore.YELLOW + "Enter management host" + str(x) + " :" + Fore.RESET))
        while (len(str(host)) == 0):
            host = str(input(Fore.YELLOW + "Enter management host" + str(x) + " :" + Fore.RESET))
        logger.info("entered Host"+str(host))
        host_dict_management_obj.add(host, '')
        if(len(str(managementHostConfig))>0):
            managementHostConfig = managementHostConfig+','+host
        else:
            managementHostConfig = host
    logger.info("host_dict_management_obj : "+str(host_dict_management_obj))
    set_value_in_property_file('app.northbound.management.hosts',managementHostConfig)


def validateAndConfigureGrafana():
    logger.info("validateAndConfigureGrafana()")
    grafanaServers = config_get_grafana_list()
    for server in grafanaServers:
            return str(os.getenv(server.ip))

def validateAndConfigureInfluxdb():
    logger.info("validateAndConfigureInfluxdb()")
    influxdbServers = config_get_influxdb_node()
    for server in influxdbServers:
        return str(os.getenv(server.ip))

def getNBApplicativeHostFromEnv():
    logger.info("getNBApplicativeHostFromEnv()")
    hosts = ''
    managerNodes = config_get_nb_list()
    for node in managerNodes:
        if(str(node.role).casefold().__contains__('applicative')):
            hosts+=str(os.getenv(str(node.ip)))+','
    hosts=hosts[:-1]
    return hosts

def getNBOPSManagerHostFromEnv():
    logger.info("getNBOPSManagerHostFromEnv")
    hosts = ''
    managerNodes = config_get_manager_node()
    for node in managerNodes:
        hosts+=str(os.getenv(str(node.ip)))+','
    hosts=hosts[:-1]
    return hosts

def getNBManagementHostFromEnv():
    logger.info("getNBManagementHostFromEnv()")
    hosts = ''
    managerNodes = config_get_nb_list()
    for node in managerNodes:
        if(str(node.role).casefold().__contains__('management')):
            hosts+=str(os.getenv(str(node.ip)))+','
    hosts=hosts[:-1]
    return hosts

def getNBAgentHostFromEnv():
    logger.info("getNBAgentHostFromEnv()")
    hosts = ''
    managerNodes = config_get_nb_list()
    for node in managerNodes:
        if(str(node.role).casefold().__contains__('agent')):
            hosts+=str(os.getenv(str(node.ip)))+','
    hosts=hosts[:-1]
    return hosts

def setConfProperties():
    logger.info("setConfProperties()")
    nbConfig = createPropertiesMapFromFile("/dbagigashare/current/NB/APPLICATIVE/nb.conf.template")
    global sourceNbConfFile
    existingConsul_server=""
    nbConfig = "/dbagigashare/current/NB/APPLICATIVE/nb.conf"
    proceedForEnvHostConfiguration(nbConfig)
    nbConfig = createPropertiesMapFromFile(nbConfig)
    existingConsul_server = str(nbConfig.get("CONSUL_SERVERS")).replace('"','')
    logger.info("existingConsul_server : "+str(existingConsul_server))
    consul_replica_number=""
    consul_servers=""
    existingServerConfirm=""
    if(len(str(existingConsul_server))>0):
        #print(Fore.YELLOW+"Proceeding with existing configuration Applicative Servers  ["+str(getNBApplicativeHostFromEnv())+"] "+Fore.RESET)
        consul_replica_number = str(len(existingConsul_server.split(",")))
        consul_servers=str(existingConsul_server).replace('"','')
    else:
        consul_replica_number = len(str(getNBApplicativeHostFromEnv()).split(','))
        logger.info("CONSUL_REPLICA_NUMBER :"+str(consul_replica_number))
        consul_servers = getConsulServers(consul_replica_number)

    logger.info("consul_servers : getConsulServers()"+str(consul_servers))

    nb_domain = str(nbConfig.get("NB_DOMAIN")).replace('"','')
    #if(len(str(nb_domain).replace('"',''))==0):
    #    nb_domain="example.gigaspaces.com"
    #nb_domain_input = \
    #print(Fore.YELLOW+"NB_DOMAIN :"+nb_domain+Fore.RESET)
    #if(len(str(nb_domain_input))>0):
    #    nb_domain =nb_domain_input
    logger.info("nb_domain :"+str(nb_domain) )

    #if consul_replica_number == "":
    consul_replica_number = str(nbConfig.get("CONSUL_REPLICA_NUMBER")).replace('"','')
    #logger.info("consul_replica_number : "+str(consul_replica_number))

    ssl_certificate = str(nbConfig.get("SSL_CERTIFICATE")).replace('"','')
    #if(len(str(ssl_certificate).replace('"',''))==0):
    #    ssl_certificate="server.crt"
    #ssl_certificate_input =
    #print(Fore.YELLOW+"Enter SSL_CERTIFICATE :"+ssl_certificate+Fore.RESET)
    #if(len(str(ssl_certificate_input))>0):
    #    ssl_certificate =ssl_certificate_input
    logger.info("ssl_certificate :"+str(ssl_certificate))

    ssl_private_key = str(nbConfig.get("SSL_PRIVATE_KEY")).replace('"','')
    #if(len(str(ssl_private_key).replace('"',''))==0):
    #    ssl_private_key="server.key"
    #ssl_private_key_input = \
    #print(Fore.YELLOW+"SSL_PRIVATE_KEY :"+ssl_private_key+Fore.RESET)
    #if(len(str(ssl_private_key_input))>0):
    #    ssl_private_key =ssl_private_key_input
    logger.info("ssl_private_key :"+str(ssl_private_key))

    ssl_ca_certificate = str(nbConfig.get("SSL_CA_CERTIFICATE")).replace('"','')
    #if(len(str(ssl_ca_certificate).replace('"',''))==0):
    #    ssl_ca_certificate="cacert.crt"
    #ssl_ca_certificate_input =
    #print(Fore.YELLOW+"SSL_CA_CERTIFICATE :"+ssl_ca_certificate+Fore.RESET)
    #if(len(str(ssl_ca_certificate_input))>0):
    #    ssl_ca_certificate =ssl_ca_certificate_input
    logger.info("ssl_ca_certificate : "+str(ssl_ca_certificate))

    max_upload_size = str(nbConfig.get("MAX_UPLOAD_SIZE")).replace('"','')
    #if(len(str(max_upload_size).replace('"',''))==0):
    #    max_upload_size="20m"
    #maxUploadSize_input = \
    #print(Fore.YELLOW+"MAX_UPLOAD_SIZE :"+max_upload_size+Fore.RESET)
    #if(len(str(maxUploadSize_input))>0):
    #    max_upload_size =maxUploadSize_input
    logger.info("max_upload_size : "+str(max_upload_size))

    # Check if Application Service if yes then allow Agent else Ask for OPS Manager
    gridui_servers=""
    opsmanager_servers=""
    global applicationServerFlag
    #applicationServerFlag = str(input(Fore.YELLOW+"Do you want to install as application service (y/n) [y] :"+Fore.RESET))
    #logger.info("applicationServerFlag :"+str(applicationServerFlag))
    #if applicationServerFlag == "":
    applicationServerFlag = "y"
    #elif applicationServerFlag.lower() != "y" and applicationServerFlag.lower() != "n":
    #    verboseHandle.printConsoleError("please select valid option (y/n) "+applicationServerFlag.lower())
    #    exit(0)
    influxdb_servers=""
    if applicationServerFlag == "y":
        logger.info("applicationServerFlag==y")
        influxdb_servers = validateAndConfigureInfluxdb()
        logger.info("influxdb_servers :"+str(influxdb_servers))
        if(influxdb_servers == None):
            influxdb_servers = ""
        logger.info("influxdb_servers :"+str(influxdb_servers))
        if(len(str(influxdb_servers))>0):
            proceedForApplicationServiceAgentInstallation()
        else:
            logger.error("No infuxdb server details found please install them before applicative server installation.")
            verboseHandle.printConsoleInfo("No infuxdb server details found please install them before applicative server installation.")
            return False

    grafana_servers=""
    if applicationServerFlag == "n":
        proceedForManagementServiceInstallation()

        grafana_servers = validateAndConfigureGrafana()
        influxdb_servers = validateAndConfigureInfluxdb()
        if(grafana_servers == None):
            grafana_servers = ""
        if(influxdb_servers == None):
            influxdb_servers = ""
        logger.info("grafana_servers :"+str(grafana_servers))
        logger.info("influxdb_servers :"+str(influxdb_servers))

        if(len(str(grafana_servers))>0 and len(str(influxdb_servers))>0):
            gridui_servers_config = str(nbConfig.get("GRIDUI_SERVERS")).replace('"','')
            gridui_servers = getNBOPSManagerHostFromEnv()
            #print(Fore.YELLOW +"GRIDUI_SERVERS ["+str(gridui_servers)+"]"+Fore.RESET)
            logger.info("gridui_servers :"+str(gridui_servers))
            if validateHost(gridui_servers) == False:
                verboseHandle.printConsoleError("gridui_servers is not valid please try again ..")
                return False
            opsmanager_servers_config = gridui_servers
            #print(Fore.YELLOW +"OPSMANAGER_SERVERS ["+opsmanager_servers_config+"]"+Fore.RESET)
            logger.info("opsmanager_servers :"+str(opsmanager_servers))
            if validateHost(opsmanager_servers) == False:
                verboseHandle.printConsoleError("opsmanager_servers is not valid please try again ..")
                return False
        else:
            logger.error("No infuxdb / grafana server details found please install them before management installation.")
            verboseHandle.printConsoleInfo("No infuxdb / grafana server details found please install them before management installation.")
            return False

    lines = update_app_config_file("consul_servers=".upper(), consul_servers, None)
    lines = update_app_config_file("consul_replica_number=".upper(), consul_replica_number, lines)
    lines = update_app_config_file("nb_domain=".upper(), nb_domain, lines)
    lines = update_app_config_file("ssl_certificate=".upper(), ssl_certificate, lines)
    lines = update_app_config_file("ssl_private_key=".upper(), ssl_private_key, lines)
    lines = update_app_config_file("ssl_ca_certificate=".upper(), ssl_ca_certificate, lines)
    lines = update_app_config_file("max_upload_size=".upper(),max_upload_size,lines)
    lines = update_app_config_file("gridui_servers=".upper(), gridui_servers, lines)
    lines = update_app_config_file("grafana_servers=".upper(), grafana_servers, lines)
    lines = update_app_config_file("influxdb_servers=".upper(), influxdb_servers, lines)
    update_app_config_file("opsmanager_servers=".upper(), gridui_servers, lines)


# validate connections for each NB server & agents
def validateHost(hostips):
    logger.info("validateHost() :"+str(hostips))
    for hostip in hostips.replace(" ", "").split(","):
        current_os = platform.system().lower()
        if current_os == "windows":
            parameter = "-n"
        else:
            parameter = "-c"
        exit_code = os.system(f"ping {parameter} 1 -w2 {hostip} > /dev/null 2>&1")
        #if exit_code != 0:  # commented this code because in some host this command is not working
            #return False
    return True


# upload nb packages to install
def proceedForUploadPackageToRemoteHost(remotePath,hostip,nb_user):
    logger.info("proceedForUploadPackageToRemoteHost() remotePath:+"+remotePath+" : hostip:"+hostip+" nb_user:"+nb_user)
    cmd = 'mkdir -p '+remotePath+'; chmod 777 /dbagiga'
    logger.info("agent : cmd :"+str(cmd))
    with Spinner():
        output = executeRemoteCommandAndGetOutput(hostip, nb_user, cmd)
        logger.info("Created directory "+str(remotePath))
    logger.info("hostip :"+str(hostip))

    logger.info("Building .tar file : tar -cvf install/install.tar install")
    userCMD = os.getlogin()
    if userCMD == 'ec2-user':
        cmd = 'sudo tar -cvf install/install.tar /dbagigashare/current/' # Creating .tar file on Pivot machine
    else :
        cmd = 'tar -cvf install/install.tar /dbagigashare/current/' # Creating .tar file on Pivot machine
    logger.info("cmd :"+str(cmd))
    with Spinner():
        status = os.system(cmd)
        logger.info("Creating tar file status : "+str(status))
    with Spinner():
        logger.info("scp_upload hostip agent::"+str(hostip)+" user :"+str(nb_user)+" remotePath: "+str(remotePath))
        scp_upload(hostip, nb_user, 'install/install.tar', '')

    #scp_upload(hostip, nb_user, "installationpackages/nb/nb-infra/", remotePath) # Removed hence required consolidated upload of install folder

    commandToExecute="scripts/servers_northbound_agent_preinstall.sh"
    additionalParam=remotePath+' '
    logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(hostip)+" User:"+str(nb_user))
    with Spinner():
        outputShFile= executeRemoteShCommandAndGetOutput(hostip, nb_user, additionalParam, commandToExecute)
        logger.info("Output Agent"+str(outputShFile))


def upload_packages_to_nb_servers(confirmServerInstall,confirmAgentInstall,confirmManagementInstall):
    logger.info("upload_packages_to_nb_servers() : confirmServerInstall:"+str(confirmServerInstall)+" :: confirmAgentInstall:"+str(confirmAgentInstall)+" confirmManagementInstall:"+str(confirmManagementInstall))
    nbConfig = createPropertiesMapFromFile("/dbagigashare/current/NB/APPLICATIVE/nb.conf")
    #print(nbConfig.get("CONSUL_SERVERS"))
    #nb_user = str(input(Fore.YELLOW+"Enter user name to connect to nb servers [root]:"+Fore.RESET))
    #if nb_user == "":
    nb_user = "root"
    logger.info("nb_user :"+str(nb_user))
    remotePath = str(readValuefromAppConfig("app.nb.targetfolder"))
    #print(Fore.YELLOW+"Remote path to copy nb installation package :"+remotePath+Fore.RESET)
    logger.info("input remotePath :"+str(remotePath))
    nbinfraPathAppend = False
    if remotePath == "":
        remotePath = "/dbagiga"
        nbinfraPathAppend = True
    else:
        remotePath = remotePath + "/nb-infra"
    confirmInstallation = str(input(Fore.YELLOW+"Are you sure want to proceed installation ? (y/n) [y]:"+Fore.RESET))
    if(len(str(confirmInstallation))==0):
        confirmInstallation='y'
    if(confirmInstallation == 'y'):
        logger.info("remotePath :"+str(remotePath))
        logger.info("upload_packages  : len(host_dict_obj) :"+str(len(host_dict_obj)))
        #if len(host_dict_obj) == 0:  # Removed hence one shot installation required
        # Server Installation....
        if(confirmServerInstall=='y'):
            logger.info("confirmServerInstall=='y'")
            for hostip in nbConfig.get("CONSUL_SERVERS").replace(" ", "").replace("\"", "").split(","):
                cmd = 'mkdir -p '+remotePath+'; chmod 777 /dbagiga'
                logger.info("cmd :"+str(cmd))
                with Spinner():
                    output = executeRemoteCommandAndGetOutput(hostip, nb_user, cmd)
                    logger.info("Created directory "+str(remotePath))
                logger.info("hostip : "+str(hostip))

                logger.info("Building .tar file : tar -cvf install/install.tar install")
                cmd = 'tar -cvf install/install.tar /dbagigashare/current/' # Creating .tar file on Pivot machine
                with Spinner():
                    status = os.system(cmd)
                    logger.info("Creating tar file status : "+str(status))
                with Spinner():
                    logger.info("hostip ::"+str(hostip)+" user :"+str(nb_user)+" remotePath: "+str(remotePath))
                    scp_upload(hostip, nb_user, 'install/install.tar', '')

                #scp_upload(hostip, nb_user, "installationpackages/nb/nb-infra/", remotePath) # Removed hence required consolidated upload of install folder

                commandToExecute="scripts/servers_northbound_preinstall.sh"
                additionalParam=remotePath+' '
                logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(hostip)+" User:"+str(nb_user))
                with Spinner():
                    outputShFile= executeRemoteShCommandAndGetOutput(hostip, nb_user, additionalParam, commandToExecute)
                    logger.info("Output"+str(outputShFile))

        # Agent Installation....
        #if len(host_dict_obj) > 0:  # Removed hence one shot installation required
        if(confirmAgentInstall=='y'):
            logger.info("confirmAgentInstall=='y' | host_dict_obj : "+str(host_dict_obj))
            for hostip in host_dict_obj:
                proceedForUploadPackageToRemoteHost(remotePath,hostip,nb_user)
        if(confirmManagementInstall=='y'):
            logger.info("confirmManagementInstall=='y' | host_dict_management_obj :"+str(host_dict_management_obj))
            for hostip in host_dict_management_obj:
                proceedForUploadPackageToRemoteHost(remotePath,hostip,nb_user)


        verboseHandle.printConsoleInfo("done copying nb package in all servers")
        if (nbinfraPathAppend == True):
            remotePath = remotePath + "/nb-infra"
        install_packages_to_nb_servers(nb_user, remotePath, confirmServerInstall, confirmAgentInstall, confirmManagementInstall)
        return 'True'
    elif(confirmInstallation == 'n'):
        cleanNbConfig()
        return 'False'
    else:
        return 'False'

# install packages
def install_packages_to_nb_servers(nb_user, remotePath, confirmServerInstall, confirmAgentInstall, confirmManagementInstall):
    logger.info("install_packages_to_nb_servers user: "+str(nb_user)+" remotepath: "+str(remotePath)+" confirmServerInstall: "+str(confirmServerInstall)+" confirmAgentInstall:"+str(confirmAgentInstall)+" confirmManagementInstall:"+str(confirmManagementInstall))
    if(confirmServerInstall=='y'):
        logger.info("install_packages_to_nb_servers "+str(nb_user+" : "+str(remotePath)))
        nbConfig = createPropertiesMapFromFile("/dbagigashare/current/NB/APPLICATIVE/nb.conf")
        logger.info("len(host_dict_obj) :" +str(len(host_dict_obj)))
        #if len(host_dict_obj) == 0:        # Removed hence one shot installation required
        logger.info("Starting nb server installation")
        verboseHandle.printConsoleInfo("Starting nb server installation")
        for hostip in nbConfig.get("CONSUL_SERVERS").replace(" ", "").split(","):
            hostip = str(hostip).replace('"', '')
            logger.info("connectExecuteSSH :")
            with Spinner():
                logger.info("connectExecuteSSH : hostip "+str(hostip)+" user:"+str(nb_user)+" remotePath:"+str(remotePath))
                connectExecuteSSH(hostip, nb_user, "scripts/servers_northbound_install.sh", remotePath + " ")
            logger.info("Adding server-node :"+str(hostip))
            #config_add_nb_node(hostip, hostip, "applicative server",  "config/cluster.config")

            cmd =  "sed -i '/export CONSUL_HTTP_ADDR=/d' .bash_profile;  echo export CONSUL_HTTP_ADDR="+str(hostip)+":8500 >>.bash_profile;"
            logger.info("agent : cmd :"+str(cmd))
            with Spinner():
                output = executeRemoteCommandAndGetOutput(hostip, nb_user, cmd)
                logger.info("Configured CONSUL_HTTP_ADDR :"+str(hostip))

            logger.info("hostip :"+str(hostip))
            logger.info("Completed Installation for consul server:"+str(hostip))
            verboseHandle.printConsoleInfo("Completed Installation for consul server:"+str(hostip))
        logger.info("Completed installation for all consul server")
        verboseHandle.printConsoleInfo("Completed installation for all consul server")

        #if len(host_dict_obj) > 0:        # Removed hence one shot installation required
    if(confirmAgentInstall=='y'):
        logger.info("Starting nb server agent installation")
        verboseHandle.printConsoleInfo("Starting nb server agent installation")
        for hostip in host_dict_obj:
            print(hostip)
            hostip = str(hostip).replace('"', '')
            logger.info(" hostip :"+str(hostip))
            with Spinner():
                logger.info("connectExecuteSSH Agent: hostip "+str(hostip)+" user:"+str(nb_user)+" remotePath:"+str(remotePath))
                connectExecuteSSH(hostip, nb_user, "scripts/servers_northbound_install.sh", remotePath + " --agent")
            logger.info("Adding agent-node :"+str(hostip))
            #config_add_nb_node(hostip, hostip, "agent server", "config/cluster.config")
            logger.info("Completed Installation for agent server:"+str(hostip))
            verboseHandle.printConsoleInfo("Completed Installation for agent server:"+str(hostip))
        logger.info("Completed installation for all agent server")
        verboseHandle.printConsoleInfo("Completed installation for all agent server")
    if(confirmManagementInstall=='y'):
        logger.info("Starting nb server management installation")
        verboseHandle.printConsoleInfo("Starting nb server management installation")
        logger.info("host_dict_management_obj :"+str(host_dict_management_obj))
        for hostip in host_dict_management_obj:
            print(hostip)
            hostip = str(hostip).replace('"', '')
            logger.info(" hostip :"+str(hostip))
            with Spinner():
                logger.info("connectExecuteSSH Agent: hostip "+str(hostip)+" user:"+str(nb_user)+" remotePath:"+str(remotePath))
                connectExecuteSSH(hostip, nb_user, "scripts/servers_northbound_install.sh", remotePath + " --management")
            logger.info("Adding agent-node :"+str(hostip))
            #config_add_nb_node(hostip, hostip, "management server", "config/cluster.config")
            logger.info("Completed Installation for management server:"+str(hostip))
            verboseHandle.printConsoleInfo("Completed Installation for management server:"+str(hostip))
        cleanNbConfig()
        logger.info("Completed installation for all management server")
        verboseHandle.printConsoleInfo("Completed installation for all management server")

def cleanNbConfig():
    userCMD = os.getlogin()
    if userCMD == 'ec2-user':
        cmd = 'sudo rm -f /dbagigashare/current/NB/APPLICATIVE/nb.conf'
    else:
        cmd = 'rm -f /dbagigashare/current/NB/APPLICATIVE/nb.conf'
    with Spinner():
        status = os.system(cmd)
        logger.info("removed nb.conf status "+str(status))

# validate
class ConsulMember:
    def __init__(self, node, address, status, type, build, protocol, dc, segment):
        self.node = node
        self.address = address
        self.status = status
        self.type = type
        self.build = build
        self.protocol = protocol
        self.dc = dc
        self.segment = segment


def validate_nb_install():
    logger.info("validate_nb_install()")
    nbConfig = createPropertiesMapFromFile("config/nb.conf")
    servers = []
    #Get servers configured as Consul_servers and space_host for validating instead of getting related hosts
    for host in nbConfig.get("CONSUL_SERVERS").replace(" ", "").replace('"','').split(","):
        servers.append(host)
    for host in str(getNBAgentHostFromEnv()).replace(" ", "").replace('"','').split(","):
        servers.append(host)

    logger.info("Agent and consul servers : : "+str(servers))

    return True


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> NB ->Agent -> Install')
    try:
        #check_prerequisite_NB()
        confirmAgentInstall=""
        confirmServerInstall=""
        confirmManagementInstall=""
        if setConfProperties() != False:
            print("All prerequisite are valid and continuing with installation")
            #confirmServerInstall = str(input(Fore.YELLOW+"Are you sure want to proceed above NB applicative server installation ? (y/n) [y]:"+Fore.RESET))
            #if(len(str(confirmServerInstall))==0):
            confirmServerInstall='n'
            nbConfig = createPropertiesMapFromFile("config/nb.conf")
            opsmanager_servers = str(nbConfig.get("OPSMANAGER_SERVERS")).replace('"','')
            #if(applicationServerFlag=='y'):
            #    confirmAgentInstall = str(input(Fore.YELLOW+"Are you sure want to proceed above NB applicative agent installation ? (y/n) [y]:"+Fore.RESET))
            #    if(len(str(confirmAgentInstall))==0):
            confirmAgentInstall='y'
            nodesManagement = getManagementHostList()
            #if(len(str(nodesManagement))>0 and applicationServerFlag=='n'):
            #    confirmManagementInstall = str(input(Fore.YELLOW+"Are you sure want to proceed above NB management server installation ? (y/n) [y]:"+Fore.RESET))
            #    if(len(str(confirmManagementInstall))==0):
            #        confirmManagementInstall='y'
            flag = upload_packages_to_nb_servers(confirmServerInstall,confirmAgentInstall,confirmManagementInstall)
            if(flag == 'True'):
                if validate_nb_install() == False:
                    logger.info("Basic validation failed please verify by doing : consul member")
                    verboseHandle.printConsoleWarning("Basic validation failed please verify by doing : consul members")
                else:
                    verboseHandle.printConsoleInfo(
                        "validation successful. Installation completed")
            else:
                pass
    except Exception as e:
        handleException(e)
