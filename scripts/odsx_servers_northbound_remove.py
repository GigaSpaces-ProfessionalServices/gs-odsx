#!/usr/bin/env python3
import os
import sys
from utils.ods_ssh import connectExecuteSSH
from scripts.logManager import LogManager
from utils.ods_validation import validateClusterCsvHost
from utils.ods_cluster_config import config_remove_nb_streamByNameIP, config_get_nb_list
from utils.odsx_read_properties_file import createPropertiesMapFromFile
from colorama import Fore

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR

def getNBAgentHostList():
    logger.info("getNBAgentHostList()")
    nodeList = config_get_nb_list()
    nodes=""
    for node in nodeList:
        if(str(node.role).casefold().__contains__('agent')):
            if(len(nodes)==0):
                nodes = node.ip
            else:
                nodes = nodes+','+node.ip
    return nodes

def getNBMAnagementtHostList():
    logger.info("getNBMAnagementtHostList()")
    nodeList = config_get_nb_list()
    nodes=""
    for node in nodeList:
        if(str(node.role).casefold().__contains__('management')):
            if(len(nodes)==0):
                nodes = node.ip
            else:
                nodes = nodes+','+node.ip
    return nodes

def getNBServerHostList():
    logger.info("getNBServerHostList()")
    nodeList = config_get_nb_list()
    nodes=""
    for node in nodeList:
        if(str(node.role).casefold().__contains__('applicative')):
            if(len(nodes)==0):
                nodes = node.ip
            else:
                nodes = nodes+','+node.ip
    return nodes

def removeAgent(nodes):
    logger.info("removeAgent()")
    nodeList = nodes.split(",")
    logger.info("nodeList : "+str(nodeList))
    for node in nodeList:
        verboseHandle.printConsoleInfo("Removing Agent :"+str(node))
        logger.info("Current host :"+str(node))
        verboseHandle.printConsoleInfo("NB Agent going to remove :"+str(node))
        connectExecuteSSH(str(node), "root", "scripts/servers_northbound_remove.sh", remotePath+"/nb-infra" + " --uninstall")
        config_remove_nb_streamByNameIP(str(node),str(node))
        logger.info("Host removed.:"+str(node))
        print("Host removed.:"+str(node))

def removeManagement(managementNodes):
    logger.info("removeManagement()")
    nodeList = managementNodes.split(',')
    logger.info("nodeList : "+str(nodeList))
    for node in nodeList:
        verboseHandle.printConsoleInfo("Removing management server :"+str(node))
        logger.info("Current host :"+str(node))
        verboseHandle.printConsoleInfo("NB management server going to remove :"+str(node))
        connectExecuteSSH(str(node), "root", "scripts/servers_northbound_remove.sh", remotePath+"/nb-infra" + " --uninstall")
        config_remove_nb_streamByNameIP(str(node),str(node))
        logger.info("Host removed.:"+str(node))
        print("Host removed.:"+str(node))

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Servers -> Northbound -> Remove')
    logger.info("Servers -> Northbound -> Remove")
    args = []
    menuDrivenFlag = 'm'# To differentiate between CLI and Menudriven Argument handling help section
    if(len(str(sys.argv[0]))>0):
        args.append(sys.argv[0])
    try:
        isConsulServerValid=True
        isGridUIServerValid=True
        if len(sys.argv) > 1 and sys.argv[1] != menuDrivenFlag:
            for arg in sys.argv[1:]:
                args.append(arg)
        # print('install :',args)
        remotePath = "/home/ec2-user"
        verboseHandle.printConsoleInfo("Starting nb un-installation")
        nbConfig = createPropertiesMapFromFile("config/nb.conf")
        serverNodes = getNBServerHostList() # Checking in cofig json if entries are present for server or not
        confirmServerRemove=""
        confirmAgentRemove=""
        confirmManagementRemove=""
        logger.info("serverNodes : "+str(serverNodes))
        if(len(str(serverNodes))>0):
            verboseHandle.printConsoleInfo("Consul_servers going to remove ["+serverNodes+"]")
            confirmServerRemove = str(input(Fore.YELLOW+"Are you sure want to proceed above NB applicative server un-installation ? (y/n) [y]:"+Fore.RESET))
            if(len(str(confirmServerRemove))==0):
                confirmServerRemove='y'
        else:
            verboseHandle.printConsoleInfo("No entries for NB applicative server found")

        nodes =""
        agentNodes = getNBAgentHostList()
        logger.info("agentNodes : "+str(agentNodes))
        if(len(agentNodes)>0):
            verboseHandle.printConsoleInfo("Consul agents going to remove ["+agentNodes+"]")
            confirmAgentRemove = str(input(Fore.YELLOW+"Are you sure want to proceed above NB applicative agent un-installation ? (y/n) [y]:"+Fore.RESET))
            if(len(str(confirmAgentRemove))==0):
                confirmAgentRemove='y'
        else:
            verboseHandle.printConsoleInfo("No consul_agents found.")

        managementNodes = getNBMAnagementtHostList()
        logger.info("managementNodes :"+str(managementNodes))
        if(len(managementNodes)>0):
            verboseHandle.printConsoleInfo("Management server going to remove ["+managementNodes+"]")
            confirmManagementRemove = str(input(Fore.YELLOW+"Are you sure want to proceed above NB management server un-installation ? (y/n) [y] :"+Fore.RESET))
            if(len(str(confirmManagementRemove))==0):
                confirmManagementRemove='y'
        else:
            verboseHandle.printConsoleInfo("No management server found.")
        if(confirmServerRemove == 'y'):
            logger.info("confirmServerRemove == y ")
            nodeList = serverNodes.split(',')
            logger.info("nodeList :"+str(nodeList))
            for hostip in nodeList:
                verboseHandle.printConsoleInfo("Removing NB applicative server :"+str(hostip))
                logger.info("Current NB applicative host :"+str(hostip))
                connectExecuteSSH(str(hostip), "root", "scripts/servers_northbound_remove.sh", remotePath+"/nb-infra" + " --uninstall")
                config_remove_nb_streamByNameIP(str(hostip),str(hostip))
                logger.info("Host removed.:"+str(hostip))
                print("Host removed.:"+str(hostip))

        if(confirmAgentRemove == 'y'):
            logger.info("confirmAgentRemove == y")
            #Remove from cluster json
            removeAgent(agentNodes)
        if(confirmManagementRemove=='y'):
            removeManagement(managementNodes)
    except Exception as e:
        logger.error("Exception in northbound remove."+str(e))
        print("Exception in northbound remove."+str(e))
