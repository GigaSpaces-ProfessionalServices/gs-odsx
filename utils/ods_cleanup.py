#!/usr/bin/env python3
import os,sys
from utils.ods_cluster_config import get_cluster_obj, ClusterEncoder, config_get_grafana_node, config_get_influxdb_node
from utils.ods_app_config import set_value_in_property_file, readValueByConfigObj
from scripts.logManager import LogManager
from json import JSONEncoder
import json
from utils.ods_ssh import executeRemoteCommandAndGetOutput
from scripts.spinner import Spinner
from colorama import Fore

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR

def clenupManagerNode(filePath='config/cluster.config', verbose=False):
    verboseHandle.printConsoleWarning("Removing Servers-Managers-Nodes...")
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    managerNode=[]
    config_data.cluster.servers.managers.node=managerNode
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)
    #set_value_in_property_file('app.manager.hosts','')
    verboseHandle.printConsoleInfo("Servers-Manager-Nodes removed.")

def clenupCDCNode(filePath='config/cluster.config', verbose=False):
    verboseHandle.printConsoleWarning("Removing Servers-CDC-Nodes...")
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    cdcNode=[]
    config_data.cluster.servers.cdc.node=cdcNode
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)
    verboseHandle.printConsoleInfo("Servers-CDC-Nodes removed.")

def cleanupNBNode(filePath='config/cluster.config', verbose=False):
    verboseHandle.printConsoleWarning("Removing Servers-NorthBound-Nodes...")
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    nbNode=[]
    config_data.cluster.servers.nb.node=nbNode
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)
    verboseHandle.printConsoleInfo("Servers-NorthBound-Nodes removed.")

def cleanupSpacesServerHosts(filePath='config/cluster.config', verbose=False):
    verboseHandle.printConsoleWarning("Removing Spaces-Server-Hosts...")
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    hostNode=[]
    config_data.cluster.servers.spaces.servers.host=hostNode
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)
    verboseHandle.printConsoleInfo("Spaces-Server-Hosts removed.")

def cleanupStreams(filePath='config/cluster.config', verbose=False):
    verboseHandle.printConsoleWarning("Removing Streams...")
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    streamNode=[]
    config_data.cluster.streams=streamNode
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)
    verboseHandle.printConsoleInfo("Streams removed.")

def cleanupInfluxServerDetails(filePath='config/cluster.config', verbose=False):
    logger.info("cleanupInfluxServerDetails()")
    verboseHandle.printConsoleInfo("Cleaning Influxdb server details")
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    influxDbNode=[]
    config_data.cluster.servers.influxdb.node=influxDbNode
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)
    #set_value_in_property_file('app.influxdb.hosts','')
    verboseHandle.printConsoleInfo("Influxdb server details cleaned up.")

def cleanupGrafanaServerDetails(filePath='config/cluster.config', verbose=False):
    logger.info("cleanupGrafanaServerDetails()")
    verboseHandle.printConsoleInfo("Cleaning Grafana server details")
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    grafanaNode=[]
    config_data.cluster.servers.grafana.node=grafanaNode
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)
    #set_value_in_property_file('app.grafana.hosts','')
    verboseHandle.printConsoleInfo("Grafana server details cleaned up.")

def cleanUp():
    answer = input("Do you want to clean Manager Server? (yes(y)/no(n)/cancel(c): ")
    logger.info("Selected answer manager:"+str(answer))
    if(answer.lower() == "y"):
        clenupManagerNode()
        dbaGigaLogPath=str(readValueByConfigObj("app.gigalog.path"))
        dbaGigaWorkPath=str(readValueByConfigObj("app.gigawork.path"))
        answerServer = input("Do you want to clean Manager Server folders? \n /dbagiga \n "+dbaGigaLogPath+"/ \n "+dbaGigaWorkPath+"/ \nsetenv.sh \n install \n install.tar \n /usr/local/bin/start_gs.sh \n /usr/local/bin/stop_gs.sh \n /etc/systemd/system/gs.service \n(yes(y)/no(n)/cancel(c): ")
        if(answerServer.lower() == "y"):
            cmd = 'rm -rf setenv.sh gs install install.tar  /dbagiga/*  '+dbaGigaLogPath+'/*  '+dbaGigaWorkPath+'/* /usr/local/bin/start_gs.sh /usr/local/bin/stop_gs.sh /etc/systemd/system/gs.service'
            verboseHandle.printConsoleInfo("Removing..")
            verboseHandle.printConsoleWarning("Removing with user [root]")
            host = input("Please enter host:")
            with Spinner():
                output = executeRemoteCommandAndGetOutput(host, "root", cmd)
            logger.info("Servers-Manager files and folders removed. :"+str(output))
            verboseHandle.printConsoleInfo("Servers-Manager files and folders removed.")
            verboseHandle.printConsoleInfo(output)
    elif(answer.lower() == "c"):
        return

    answer = input("Do you want to clean CDC Server? (yes(y)/no(n)/cancel(c): ")
    logger.info("Selected answer cdc:"+str(answer))
    if(answer.lower() == "y"):
        clenupCDCNode()
    elif(answer.lower() == "c"):
        return

    answer = input("Do you want to clean NB Server? (yes(y)/no(n)/cancel(c): ")
    logger.info("Selected answer NB:"+str(answer))
    if(answer.lower() == "y"):
        cleanupNBNode()
    elif(answer.lower() == "c"):
        return

    answer = input("Do you want to clean Space Server? (yes(y)/no(n)/cancel(c): ")
    logger.info("Selected answer space:"+str(answer))
    if(answer.lower() == "y"):
        cleanupSpacesServerHosts()
        dbaGigaLogPath=str(readValueByConfigObj("app.gigalog.path"))
        answerServer = input("Do you want to clean Space Server folders? \n /dbagiga \n "+dbaGigaLogPath+"/ \n "+dbaGigaWorkPath+"/ \nsetenv.sh \n install \n install.tar \n /usr/local/bin/start_gs.sh \n /usr/local/bin/stop_gs.sh \n /etc/systemd/system/gs.service \n(yes(y)/no(n)/cancel(c): ")
        if(answerServer.lower() == "y"):
            cmd = 'rm -rf setenv.sh gs install install.tar  /dbagiga/*  '+dbaGigaLogPath+'/*  '+dbaGigaWorkPath+'/* /usr/local/bin/start_gs.sh /usr/local/bin/stop_gs.sh /etc/systemd/system/gs.service'
            verboseHandle.printConsoleInfo("Removing..")
            verboseHandle.printConsoleWarning("Removing with user [root]")
            host = input("Please enter host:")
            with Spinner():
                output = executeRemoteCommandAndGetOutput(host, "root", cmd)
            logger.info("Servers-spaec files and folders removed. :"+str(output))
            verboseHandle.printConsoleInfo("Servers-space files and folders removed.")
            verboseHandle.printConsoleInfo(output)
    elif(answer.lower() == "c"):
        return

    answer = input("Do you want to clean Stream Server? (yes(y)/no(n)/cancel(c): ")
    logger.info("Selected answer stream:"+str(answer))
    if(answer.lower() == "y"):
        cleanupStreams()
    elif(answer.lower() == "c"):
        return

    answer = input("Do you want to clean Grafana Server? (yes(y)/no(n)/cancel(c): ")
    logger.info("Selected answer Grafana:"+str(answer))
    if(answer.lower() == "y"):
        cleanupGrafanaServerDetails()
    elif(answer.lower() == "c"):
        return

    answer = input("Do you want to clean Influxdb Server? (yes(y)/no(n)/cancel(c): ")
    logger.info("Selected answer Influxdb:"+str(answer))
    if(answer.lower() == "y"):
        cleanupInfluxServerDetails()
    elif(answer.lower() == "c"):
        return

def signal_handler(sig, frame):
    print('\n\nOperation aborted by user!\n')
    sys.exit(0)


if __name__ == '__main__':
    cleanUp()
