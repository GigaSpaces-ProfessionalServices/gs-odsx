#!/usr/bin/env python3
import argparse
import os
import signal
import sys

from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import getYamlFilePathInsideFolder
from utils.ods_cleanup import signal_handler
from utils.ods_cluster_config import config_get_grafana_list, config_get_nb_list
from utils.ods_scp import scp_upload
from utils.ods_ssh import connectExecuteSSH, executeRemoteCommandAndGetOutput, executeLocalCommandAndGetOutput
from utils.odsx_read_properties_file import createPropertiesMapFromFile

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
serviceName = "catalogue-service.service"
user = "root"


def getGrafanaServerHostList():
    nodeList = config_get_grafana_list()
    nodes=""
    for node in nodeList:
        if(len(nodes)==0):
            nodes = os.getenv(node.ip)
        else:
            nodes = nodes+','+os.getenv(node.ip)
    return nodes

def getNBServerHostList():
    nodeList = config_get_nb_list()
    nodes=""
    for node in nodeList:
        if(str(node.role).casefold().__contains__('applicative')):
            if(len(nodes)==0):
                nodes = os.getenv(node.ip)
            else:
                nodes = nodes+','+os.getenv(node.ip)
    return nodes

def getConsulHost():
    logger.info("getConsulHost() : start")
    consulHost = '0.0.0.0';
    consulHostList = getNBServerHostList()

    logger.info("All Consul Hosts : "+consulHostList)

    if(len(consulHostList)<=0):
        verboseHandle.printConsoleInfo("Consul host not found..")

    consulHost = consulHostList.split(",")[0]
    
    logger.info("Consul Host : "+consulHost)
    publicIP = ""
    try:
        publicIP = executeRemoteCommandAndGetOutput(consulHost,user,"curl --silent --connect-timeout 5 http://169.254.169.254/latest/meta-data/public-ipv4")
    except Exception as e:
        logger.error("error in getting public ip of consul host")
        
    logger.info("Consul Host : "+str(publicIP))
    verboseHandle.printConsoleDebug(str(publicIP))

    if(len(str(publicIP))>0):
        consulHost = str(publicIP)
    
    logger.info("getConsulHost() : end")
    return consulHost


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
    parser = argparse.ArgumentParser(description='Script to register Catalogue service')
    parser.add_argument('m', nargs='?')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])

def setupService():
    global grafanaEndpoint
    sourceInstallerDirectory=""
    sourceInstallerDirectory = str(os.getenv("ENV_CONFIG"))
    logger.info("setupService() : start")
    #grafanaEndpointInput = Fore.YELLOW + "Enter endpoint for grafana server :" + Fore.RESET
    # ALON & AHARON Ask to take nb_domain from nb.conf from /dbagigashare/current/nb/management/ instead of pivot host
    nbConfig = sourceInstallerDirectory+"/nb/management/nb.conf.template"
    nbConfig = createPropertiesMapFromFile(nbConfig)
    grafanaEndpoint = str(nbConfig.get("NB_DOMAIN"))

    consulHost = getConsulHost()
    catalogJar = str(getYamlFilePathInsideFolder(".grafana.catalog.jars.catalogjar"))
    verboseHandle.printConsoleWarning("-------------Summary---------------------")
    verboseHandle.printConsoleInfo("Endpoint for grafana server : "+grafanaEndpoint)
    verboseHandle.printConsoleInfo("Catalogue Jar :"+str(catalogJar))
    verboseHandle.printConsoleWarning("-----------------------------------------")

    confirmMsg = Fore.YELLOW + "Are you sure, you want to setup Catalogue service ? (y/n) [y]:" + Fore.RESET
    from utils.odsx_keypress import userInputWrapper
    choice = str(userInputWrapper(confirmMsg))
    if choice.casefold() == 'n':
        exit(0)

    commandToExecute = "scripts/settings_catalogueService_setup.sh "+consulHost+" "+catalogJar;
    logger.info("Command "+commandToExecute)
    try:
        os.system(commandToExecute)
        logger.info("setupService() completed")
    except Exception as e:
        logger.error("error occurred in setupService()")
    
    logger.info("setupService() : end")

def setupGrafanaDashboard():
    logger.info("setupGrafanaDashboard() : start")
    verboseHandle.printConsoleInfo("Configuring Catalogue dashboard in Grafana..")
    global grafanaHosts
    grafanaHosts = getGrafanaServerHostList()
    grafanaHostList = grafanaHosts.split(",")
 
    for host in grafanaHostList:
        uploadDashbordJsonFile(host)
        #uploadDashboadProvisionFile(host)

   
    restartGrafana()

    logger.info("setupGrafanaDashboard() : end")
    verboseHandle.printConsoleInfo("Catalogue dashboard is configured successfully!")

def restartGrafana():
    logger.info("restartGrafana() : start")
    verboseHandle.printConsoleInfo("Restarting Grafana service..")
   
    try:
    
        if(len(grafanaHosts)>0):

            commandToExecute="scripts/restartGrafana.sh"
            additionalParam=""
            logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(grafanaHosts)+" User:"+str(user))
            with Spinner():
                outputShFile= connectExecuteSSH(grafanaHosts, user,commandToExecute,additionalParam)
                verboseHandle.printConsoleInfo("Host "+str(grafanaHosts)+" restart grafana service command executed.")
        else:
            logger.info("No server details found.")
            verboseHandle.printConsoleInfo("No server details found.")
    except Exception as e:
        logger.error("Exception in Grafana -> Restart : restartGrafana() : "+str(e))
        verboseHandle.printConsoleError("Exception in Grafana -> Stop : restartGrafana() : "+str(e))
    
    logger.info("restartGrafana(): end")

    verboseHandle.printConsoleInfo("Grafana Restarted successfully!")

def uploadDashbordJsonFile(host):
    logger.info("uploadDashbordJsonFile(): start host :" + str(host))
    
    localIP=""
    try:
        localIP = executeLocalCommandAndGetOutput("curl --silent --connect-timeout 2 http://169.254.169.254/latest/meta-data/public-ipv4")
        localIP = str(localIP)
       
    except Exception as e:
        logger.error("error in getting public ip of pivot machine")

    if(str(localIP)=='b\'\''):
        localIP = executeLocalCommandAndGetOutput("hostname")

    localIP = localIP[1:]
    catalogue_service_url = 'http://'+str(grafanaEndpoint)+':3211/services'
    catalogue_table_url = 'http://'+str(grafanaEndpoint)+':3211/metadata'

    try:
        with Spinner():
            logger.info("hostip ::" + str(host) + " user :" + str(user))

            ### Setting up Service Catalogue dashboard
            scp_upload(host, "root", 'systemServices/catalogue/grafana/service-catalogue.json', '/usr/share/grafana/conf/provisioning/dashboards/')

            executeRemoteCommandAndGetOutput(host, "root","sudo sed -i 's,catalogue_service_url,'"+catalogue_service_url+"',g' /usr/share/grafana/conf/provisioning/dashboards/service-catalogue.json")
            executeRemoteCommandAndGetOutput(host, "root","chown grafana:grafana /usr/share/grafana/conf/provisioning/dashboards/service-catalogue.json")
    
            ### Setting up Table Catalogue dashboard
            scp_upload(host, "root", 'systemServices/catalogue/grafana/table-catalogue.json', '/usr/share/grafana/conf/provisioning/dashboards/')

            executeRemoteCommandAndGetOutput(host, "root","sudo sed -i 's,catalogue_table_url,'"+catalogue_table_url+"',g' /usr/share/grafana/conf/provisioning/dashboards/table-catalogue.json")
            executeRemoteCommandAndGetOutput(host, "root","chown grafana:grafana /usr/share/grafana/conf/provisioning/dashboards/table-catalogue.json")
    
    except Exception as e:
        handleException(e)
    logger.info("uploadDashbordJsonFile(): end")

def uploadDashboadProvisionFile(host):
    logger.info("uploadDashboadProvisionFile(): start host :" + str(host))
    try:
        with Spinner():
            logger.info("hostip ::" + str(host) + " user :" + str(user))
            scp_upload(host, "root", 'systemServices/catalogue/grafana/catalogue.yaml', '/etc/grafana/provisioning/dashboards/')
            executeRemoteCommandAndGetOutput(host, "root","chown grafana:grafana /etc/grafana/provisioning/dashboards/catalogue.yaml")
    except Exception as e:
        handleException(e)
    
    logger.info("uploadDashboadProvisionFile(): end")

if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Settings -> CatalogueService -> Setup")
    args = []
    signal.signal(signal.SIGINT, signal_handler)
    args = myCheckArg()
    setupService()
    setupGrafanaDashboard()
