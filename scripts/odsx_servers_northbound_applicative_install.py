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

def update_app_config_file_shared(linePatternToReplace, value, lines1,sourceNbConfFile,flag):
    if lines1 == None:
        file_name = sourceNbConfFile
        lines = open(file_name, 'r').readlines()
    else:
        lines = lines1
    lineNo = -1
    for line in lines:
        lineNo = lineNo + 1
        if line.startswith(linePatternToReplace) :
            #print(linePatternToReplace + '"' + value + '"')
            break
    lines[lineNo] = ""
    lines[lineNo] = linePatternToReplace + '"' + value + '"\n'

    out = open(sourceNbConfFile, 'w')
    out.writelines(lines)
    out.close()
    return lines

def proceedForEnvHostConfiguration(sourceNbConfFile,flag):
    logger.info("proceedForEnvHostConfiguration()")
    userCMD = os.getlogin()
    if userCMD == 'ec2-user':
        cmd = 'sudo cp '+sourceInstallerDirectory+'/nb/'+flag+'/nb.conf.template '+sourceNbConfFile+';sudo chown ec2-user:ec2-user '+sourceNbConfFile # Creating .tar file on Pivot machine
    else :
        cmd = 'cp '+sourceInstallerDirectory+'/nb/'+flag+'/nb.conf.template '+sourceNbConfFile # Creating .tar file on Pivot machine
    with Spinner():
        status = os.system(cmd)
    nbConfig = createPropertiesMapFromFile(sourceNbConfFile)
    existingConsul_server = str(nbConfig.get("CONSUL_SERVERS")).replace('"','')
    #update_app_config_file_shared(linePatternToReplace, value, lines1,fileName)
    lines = update_app_config_file_shared("consul_servers=".upper(), getNBApplicativeHostFromEnv(), None,sourceNbConfFile,flag)
    lines = update_app_config_file_shared("influxdb_servers=".upper(), validateAndConfigureInfluxdb(), lines,sourceNbConfFile,flag)
    lines = update_app_config_file_shared("pivot_servers=".upper(), str(os.getenv('pivot1')), lines,sourceNbConfFile,flag)
    update_app_config_file_shared("CONSUL_REPLICA_NUMBER=".upper(), str(len(getNBApplicativeHostFromEnv().split(","))), lines,sourceNbConfFile,flag)

def displayInputParam(nbConfig):
    print(str("CONSUL_SERVERS= "+nbConfig.get("CONSUL_SERVERS")).replace('"',''))
    print(str("CONSUL_REPLICA_NUMBER= "+nbConfig.get("CONSUL_REPLICA_NUMBER")).replace('"',''))
    print(str("NB_DOMAIN= "+nbConfig.get("NB_DOMAIN")).replace('"',''))
    print(str("SSL_CERTIFICATE= "+nbConfig.get("SSL_CERTIFICATE")).replace('"',''))
    print(str("SSL_PRIVATE_KEY= "+nbConfig.get("SSL_PRIVATE_KEY")).replace('"',''))
    print(str("SSL_CA_CERTIFICATE= "+nbConfig.get("SSL_CA_CERTIFICATE")).replace('"',''))
    print(str("MAX_UPLOAD_SIZE= "+nbConfig.get("MAX_UPLOAD_SIZE")).replace('"',''))
    print(str("INFLUXDB_SERVERS= "+nbConfig.get("INFLUXDB_SERVERS")).replace('"',''))
    print(str("GRIDUI_SERVERS= "+nbConfig.get("GRIDUI_SERVERS")).replace('"',''))
    print(str("OPSMANAGER_SERVERS= "+nbConfig.get("OPSMANAGER_SERVERS")).replace('"',''))
    print(str("GRAFANA_SERVERS= "+nbConfig.get("GRAFANA_SERVERS")).replace('"',''))
    print(str("PIVOT_SERVERS= "+nbConfig.get("PIVOT_SERVERS")).replace('"',''))

def summaryForApplicativeInstallation():
    nbConfig = sourceInstallerDirectory+"/nb/applicative/nb.conf"
    proceedForEnvHostConfiguration(nbConfig,'applicative')
    nbConfig = createPropertiesMapFromFile(nbConfig)
    verboseHandle.printConsoleInfo("nb.conf params for applicative servers.")
    displayInputParam(nbConfig)
    pass

def cleanNbConfig():
    logger.info("cleanNbConfig()")
    userCMD = os.getlogin()
    direcrotyArray = ['management','applicative']
    for dir in direcrotyArray:
        if userCMD == 'ec2-user':
            cmd = 'sudo rm -f '+sourceInstallerDirectory+'/nb/'+dir+'/nb.conf'
            logger.info(cmd)
        else:
            cmd = 'rm -f '+sourceInstallerDirectory+'/nb/'+dir+'/nb.conf'
        with Spinner():
            status = os.system(cmd)
            logger.info("removed nb.conf status "+str(status))

def proceedForPreInstallation(nbServers, param):
    logger.info("proceedForPreInstallation : "+param)
    nb_user='root'
    remotePath='/dbagiga'

    cmd = 'tar -cvf install/install.tar install' # Creating .tar file on Pivot machine
    with Spinner():
        status = os.system(cmd)
        logger.info("Creating tar file status : "+str(status))

    for hostip in nbServers.split(','):
        verboseHandle.printConsoleInfo(param+" Pre-installation started for host : "+hostip)
        cmd = 'mkdir -p '+remotePath+'; chmod 777 /dbagiga'
        logger.info("cmd :"+str(cmd))
        with Spinner():
            output = executeRemoteCommandAndGetOutput(hostip, nb_user, cmd)
            logger.info("Created directory "+str(remotePath))
        logger.info("hostip : "+str(hostip))

        with Spinner():
            logger.info("hostip ::"+str(hostip)+" user :"+str(nb_user)+" remotePath: "+str(remotePath))
            scp_upload(hostip, nb_user, 'install/install.tar', '')

        if param.casefold()=='applicative':
            commandToExecute="scripts/servers_northbound_applicative_preinstall.sh"
        logger.info("commandToExecute :"+commandToExecute)
        additionalParam=remotePath+' '+sourceInstallerDirectory
        logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(hostip)+" User:"+str(nb_user))

        with Spinner():
            outputShFile= executeRemoteShCommandAndGetOutput(hostip, nb_user, additionalParam, commandToExecute)
            logger.info("Output"+str(outputShFile))
    pass

def proceedForApplicativeInstallation():
    logger.info("proceedForApplicativeInstallation()")
    nbApplicativeServers = getNBApplicativeHostFromEnv()
    remotePath='/dbagiga/nb-infra'
    nb_user='root'
    proceedForPreInstallation(nbApplicativeServers,'APPLICATIVE')

    for hostip in nbApplicativeServers.split(","):
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
        logger.info("Completed Installation for applicative server:"+str(hostip))
        verboseHandle.printConsoleInfo("Completed installation for applicative server:"+str(hostip))
    cleanNbConfig()
    logger.info("Completed installation for all applicative servers")
    verboseHandle.printConsoleInfo("Completed installation for all applicative servers")

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> NB -> Applicative -> Install')
    sourceInstallerDirectory=""
    try:
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
        summaryForApplicativeInstallation()
        confirmInstall = str(input(Fore.YELLOW+"Are you sure want to proceed for NB applicavive servers ["+getNBApplicativeHostFromEnv()+"] installation ? (y/n) [y] :"+Fore.RESET))
        if confirmInstall.casefold()=='':
            confirmInstall='y'
        if(confirmInstall.casefold()=='y'):
            proceedForApplicativeInstallation()
        if confirmInstall.casefold()=='n':
            cleanNbConfig()
    except Exception as e:
        handleException(e)
