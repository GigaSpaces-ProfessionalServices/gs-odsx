#!/usr/bin/env python3
import hashlib
import json, yaml
import os, configparser
from collections import namedtuple
from datetime import datetime
from json import JSONEncoder
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_print_tabular_data import printTabular
from utils.ods_ssh import executeRemoteCommandAndGetOutputValuePython36,executeRemoteCommandAndGetOutput
from scripts.logManager import LogManager
from scripts.spinner import Spinner

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

class Clusters:
    def __init__(self, cluster):
        self.cluster = cluster


class Cluster:
    def __init__(self, name, configVersion, servers):
        self.name = name
        self.configVersion = configVersion
        self.servers = servers


class Streams:
    def __init__(self, id, name, description, creationDate, serverName, serverip, serverPathOfConfig):
        self.id = id
        self.name = name
        self.description = description
        self.creationDate = creationDate
        self.serverName = serverName
        self.serverip = serverip
        self.serverPathOfConfig = serverPathOfConfig


class Replications:
    def __init__(self, id, spacename, serverName, serverip, locator, lookup):
        self.id = id
        self.spacename = spacename
        self.serverName = serverName
        self.serverip = serverip
        self.locator = locator
        self.lookup = lookup

class Parameters:
    def __init__(self, waitIntervalAfterServerDown, waitIntervalForContainerCheckAfterServerUp, waitIntervalForDeletionAfterDemote):
        self.waitIntervalAfterServerDown = waitIntervalAfterServerDown
        self.waitIntervalForContainerCheckAfterServerUp = waitIntervalForContainerCheckAfterServerUp
        self.waitIntervalForDeletionAfterDemote = waitIntervalForDeletionAfterDemote

class Gsc:
    def __init__(self, count, zones):
        self.count = count
        self.zones = zones

class PolicyAssociations:
    def __init__(self, targetNodeType, nodes, policy, gsc):
        self.targetNodeType = targetNodeType
        self.nodes = nodes
        self.policy = policy
        self.gsc = gsc

class Policies:
    def __init__(self, name, description, type, definition, parameters):
        self.name = name
        self.description = description
        self.type = type
        self.definition = definition
        self.parameters = parameters

class Policyconfiguration:
    def __init__(self, policies, policyAssociations):
        self.policies = policies
        self.policyAssociations = policyAssociations


class AllServers:
    def __init__(self, managers, nb, spaces, grafana, influxdb, dataIntegration, dataEngine, dataValidation):
        self.managers = managers
        self.nb = nb
        self.spaces = spaces
        self.grafana = grafana
        self.influxdb = influxdb
        self.dataIntegration = dataIntegration
        self.dataValidation = dataValidation
        self.dataEngine = dataEngine

class Managers:
    def __init__(self, node):
        self.node = node

class NB:
    def __init__(self, node):
        self.node = node

class Grafana:
    def __init__(self,node):
        self.node = node

class Influxdb:
    def __init__(self,node):
        self.node = node

class DataIntegration:
    def __init__(self,nodes):
        self.nodes = nodes

class DataValidation:
    def __init__(self,nodes):
        self.nodes = nodes

class DataEngine:
    def __init__(self,nodes):
        self.nodes = nodes

class Nodes:
    def __init__(self, ip, name, role, type):
        self.name = name
        self.type = type
        self.ip = ip
        self.role = role

class Nodes1:
    def __init__(self, ip, name, engine, role, type):
        self.name = name
        self.engine = engine
        self.type = type
        self.ip = ip
        self.role = role

class Node:
    def __init__(self, ip, name, role):
        self.name = name
        self.ip = ip
        self.role = role

class Spaces:
    def __init__(self,servers):
        self.servers = servers

class Servers:
    def __init__(self, host):
        self.host = host


class Host:
    def __init__(self, ip, name, gsc):
        self.name = name
        self.ip = ip
        self.gsc = gsc

class ClusterEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

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

def customClusterDecoder(clusterDict):
    return namedtuple('X', clusterDict.keys())(*clusterDict.values())


def create_sample_config_file():
    hostDetail1 = Host("127.0.0.1", "jay-desktop-1", "2")
    hostDetail2 = Host("127.0.0.1", "jay-desktop-2", "2")

    hostDetailList = []
    hostDetailList.append(hostDetail1)
    hostDetailList.append(hostDetail2)
    server = Servers(hostDetailList)

    spaces = Spaces(server)

    node1 = Node("127.0.0.1", "jay-desktop-1", "admin")
    node2 = Node("127.0.0.1", "jay-desktop-2", "admin")

    nodeList = [node1, node2]

    nb = NB( nodeList)

    manager = Managers(nodeList)

    grafana = Grafana(nodeList)

    influxdb = Influxdb(nodeList)

    allservers = AllServers(manager, nb, spaces, grafana, influxdb)

    dt_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    streams = Streams("123", "demo-stream", "demo stream", "2021-06-11 20:16:34", "jay-desktop-2", "18.116.28.1",
                      "/home/dbsh/cr8/latest_cr8/etc/CR8Config.json","Stopped")

    cluster = Cluster("cluster-1", "1.0", dt_string, "false", "true", allservers)
    clusters = Clusters(cluster)
    with open('config/cluster.config', 'w') as outfile:
        json.dump(clusters, outfile, indent=2, cls=ClusterEncoder)


def parse_config_json(filePath):
    f = open(filePath)
    clusterObj = json.load(f, object_hook=customClusterDecoder)
    return clusterObj


def get_cluster_obj(filePath='config/cluster.config', verbose=False):
    if verbose:
        verboseHandle.setVerboseFlag()
    logger.debug("getting cluster object from " + filePath)
    config_data = parse_config_json(filePath)
    nodes = []

    for node1 in list(config_data.cluster.servers.managers.node):
        nodes.append(Node(node1.ip, node1.name, node1.role))
    managers = Managers(nodes)

    nodes = []
    for node1 in list(config_data.cluster.servers.nb.node):
        nodes.append(Node(node1.ip, node1.name, node1.role))
    nb = NB(nodes)
    nodes = []
    grafana = []
    influxdb = []
    dataIntegration = []
    dataValidation = []
    dataEngine = []
    if hasattr(config_data.cluster.servers, 'grafana'):
        for node1 in list(config_data.cluster.servers.grafana.node):
            nodes.append(Node(node1.ip, node1.name, node1.role))
        grafana = Grafana(nodes)
    nodes = []
    if hasattr(config_data.cluster.servers, 'influxdb'):
        for node1 in list(config_data.cluster.servers.influxdb.node):
            nodes.append(Node(node1.ip, node1.name, node1.role))
        influxdb = Influxdb(nodes)

    nodes = []
    if hasattr(config_data.cluster.servers, 'dataIntegration'):
        for node1 in list(config_data.cluster.servers.dataIntegration.nodes):
            nodes.append(Nodes(node1.ip, node1.name, node1.role,  node1.type))
        dataIntegration = DataIntegration(nodes)

    nodes = []
    if hasattr(config_data.cluster.servers, 'dataValidation'):
        for node1 in list(config_data.cluster.servers.dataValidation.nodes):
            nodes.append(Nodes(node1.ip, node1.name, node1.role, node1.type))
        dataValidation = DataValidation(nodes)
        
    nodes = []    
    if hasattr(config_data.cluster.servers, 'dataEngine'):
        for node1 in list(config_data.cluster.servers.dataEngine.nodes):
            nodes.append(Nodes1(node1.ip, node1.name, node1.engine, node1.role, node1.type))
        dataEngine = DataEngine(nodes)

    #partition = Partitions(config_data.cluster.servers.spaces.partitions.primary,
    #                       config_data.cluster.servers.spaces.partitions.backup)
    hosts = []
    for host in list(config_data.cluster.servers.spaces.servers.host):
        hosts.append(Host(host.ip, host.name, host.gsc))

    spaces = Spaces(Servers(hosts))
    allservers = AllServers( managers, nb, spaces, grafana, influxdb, dataIntegration,dataEngine, dataValidation)

    # print(config_data.cluster.timestamp)
    cluster = Cluster(config_data.cluster.name, config_data.cluster.configVersion,
                      allservers)
    config_data = Clusters(cluster)
    return config_data


def get_space_partition(filePath='config/cluster.config'):
    return get_cluster_obj(filePath).cluster.servers.spaces.partitions


def get_spaces_servers(filePath='config/cluster.config'):
    return get_cluster_obj(filePath).cluster.servers.spaces.servers


def config_update_timestamp(filePath='config/cluster.config', verbose=False):
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    config_data.cluster.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.debug("updated timestamp : " + str(config_data.cluster.timestamp) + ", filename : " + filePath)
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)


def config_get_manager_node(filePath='config/cluster.config'):
    return get_cluster_obj(filePath).cluster.servers.managers.node

def isMangerExist(existingNodes,hostIp):
    for manager in existingNodes:
        if(str(manager.ip)==str(hostIp)):
            return 'true'
    return "false"

def config_add_manager_node(hostIp, hostName, role,filePath='config/cluster.config'):
    newNode = Node(hostIp, hostName, role)
    config_data = get_cluster_obj(filePath)
    existingNodes = config_data.cluster.servers.managers.node
    sizeOfNodes = len(existingNodes)
    logger.info("Size of node"+str(sizeOfNodes)+" CURRENT NODE"+str(hostIp) )
    logger.info("Size of existing nodes : "+str(sizeOfNodes))
    if(sizeOfNodes>0) :
        logger.info("isMangerExist(existingNodes,hostIp) "+isMangerExist(existingNodes,hostIp))
        if(isMangerExist(existingNodes,hostIp)=='true'):
            #verboseHandle.printConsoleInfo("Host is already exist."+str(hostIp))
            confirmAnswer='y'
            #confirmAnswer = str(input(Fore.YELLOW+"Host :"+hostIp+" is already exist.Do you want to override the host ? [yes (y) / no (n)]: "+Fore.RESET))
            logger.info("Host is already exist."+str(confirmAnswer))
            if(confirmAnswer=="y" or confirmAnswer=="yes"):
                logger.info("Host is already exist. Node overrides"+str(confirmAnswer))
                for manager in existingNodes:
                    if(str(manager.ip)==str(hostIp)):
                        logger.info("OVERRIDING IP : "+str(manager.ip))
                        manager.ip=hostIp
                        manager.name=hostName
                logger.info("Host overriden "+str(hostIp)+" To "+str(hostName))
                config_data.cluster.servers.managers.node = existingNodes
                with open(filePath, 'w') as outfile:
                    json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)
            elif(confirmAnswer=="n" or confirmAnswer=="no"):
                logger.info("ADDING NEW NODE")
                logger.info("Host is already exist. Node adding"+str(confirmAnswer))
                return addToExistingNode(newNode,hostIp,hostName,filePath,config_data,existingNodes)
        else:
            logger.info("ADDING NODE"+str(hostIp))
            logger.info("Host not found. Node adding")
            return addToExistingNode(newNode,hostIp,hostName,filePath,config_data,existingNodes)
    else:
        logger.info("ADDING NODE..."+str(hostIp))
        logger.info("Host not found. Node adding")
        return addToExistingNode(newNode,hostIp,hostName,filePath,config_data,existingNodes)

def addToExistingNode(newNode,hostIp,hostName,filePath,config_data,existingNodes):
    existingNodes.append(newNode)
    logger.info("Host added "+str(hostIp)+" To "+str(hostName))
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)
    logger.info("new manager node added " + hostIp)
    return existingNodes

def config_get_manager_list(filePath='config/cluster.config'):
    managerNodes = config_get_manager_node()
    verboseHandle.printConsoleWarning("Please choose an option from below :")
    managerDict = {}
    counter = 0
    for manager in managerNodes:
        counter = counter + 1
        managerDict.update({counter: manager})
        verboseHandle.printConsoleInfo(
            str(counter) + ". "+manager.name + " (" + manager.ip + ")")
    verboseHandle.printConsoleInfo(
        str(99) + ". ESC" " (Escape from menu.)")
    return  managerDict

def config_get_manager_listWithoutDisplay(filePath='config/cluster.config'):
    managerNodes = config_get_manager_node()
    managerDict = {}
    counter = 0
    for manager in managerNodes:
        counter = counter + 1
        managerDict.update({counter: manager})
    return  managerDict

def config_remove_manager_nodeById(managername,managerip,filePath='config/cluster.config', verbose=False):
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    managerNodes = config_get_manager_node()
    counter=0
    for manager in managerNodes:
        if(manager.name==managername and manager.ip==managerip):
            managerNodes.pop(counter)
        counter=counter+1
    config_data.cluster.servers.managers.node = managerNodes
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)

def config_remove_manager_nodeByIP(managerIP,filePath='config/cluster.config',verbose=False):
    logger.debug("Removing manager node "+str(managerIP)+".")
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    managerNodes = config_get_manager_node()
    counter=0
    for manager in managerNodes:
        if(manager.ip==managerIP):
            managerNodes.pop(counter)
        counter=counter+1
    config_data.cluster.servers.managers.node = managerNodes
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)


def config_get_space_node(filePath='config/cluster.config'):
    return get_cluster_obj(filePath).cluster.servers.spaces.servers.host

def config_get_space_list(filePath='config/cluster.config'):
    spaceNodes = config_get_space_node()
    verboseHandle.printConsoleWarning("Please choose an option from below :")
    spaceDict = {}
    counter = 0
    for spaceNode in spaceNodes:
        counter = counter + 1
        spaceDict.update({counter: spaceNode})
        verboseHandle.printConsoleInfo(
            str(counter) + ". "+spaceNode.name + " (" + spaceNode.ip + ")")
    verboseHandle.printConsoleInfo(
        str(99) + ". ESC" " (Escape from menu.)")
    return  spaceDict

def config_get_space_hosts_list(filePath='config/cluster.config'):
    hosts=[]
    spaceNodes = config_get_space_node()
    #verboseHandle.printConsoleWarning("Please choose an option from below :")
    spaceDict = {}
    counter = 0
    for spaceNode in spaceNodes:
        counter = counter + 1
        spaceDict.update({counter: spaceNode})
        hosts.append(spaceNode.ip)
    return  hosts

def config_get_space_list_with_status(user,filePath='config/cluster.config'):
    logger.info("config_get_space_list_with_status()")
    host_nic_dict_obj = host_nic_dictionary()
    spaceServers = config_get_space_hosts()
    for server in spaceServers:
        spaceHost = str(os.getenv(server.ip))
        cmd = 'ps -ef | grep GSA'
        with Spinner():
            output = executeRemoteCommandAndGetOutput(spaceHost, 'root', cmd)
            #output = executeRemoteShCommandAndGetOutput(server.ip,user,cmd)
            if(str(output).__contains__('services=GSA')):
                logger.info("services=GSA")
                host_nic_dict_obj.add(spaceHost,"ON")
            else:
                logger.info("services!=GSA")
                host_nic_dict_obj.add(spaceHost,"OFF")

    spaceNodes = config_get_space_node()
    verboseHandle.printConsoleWarning("Please choose an option from below :")
    spaceDict = {}
    counter = 0
    headers = [Fore.YELLOW+"SrNo."+Fore.RESET,
               Fore.YELLOW+"IP"+Fore.RESET,
               Fore.YELLOW+"Host"+Fore.RESET,
               Fore.YELLOW+"Install"+Fore.RESET,
               Fore.YELLOW+"Status"+Fore.RESET
               ]
    data=[]
    for server in spaceNodes:
        spaceHost = str(os.getenv(server.ip))
        status = getSpaceServerStatus(spaceHost)
        counter = counter + 1
        spaceDict.update({counter: server})
        installStatus='No'
        install = isInstalledAndGetVersion(spaceHost)
        logger.info("install : "+str(install))
        if(len(str(install))>8):
            installStatus='Yes'
        status = host_nic_dict_obj.get(spaceHost)
        dataArray=[Fore.GREEN+str(counter)+Fore.RESET,
                   Fore.GREEN+spaceHost+Fore.RESET,
                   Fore.GREEN+spaceHost+Fore.RESET,
                   Fore.GREEN+installStatus+Fore.RESET if(installStatus=='Yes') else Fore.RED+installStatus+Fore.RESET,
                   Fore.GREEN+status+Fore.RESET if(status=='ON') else Fore.RED+status+Fore.RESET,]
        data.append(dataArray)
    printTabular(None,headers,data)
    verboseHandle.printConsoleInfo(
        str(99) + ". ESC" " (Escape from menu.)")
    return  spaceDict

def isInstalledAndGetVersion(host):
    logger.info("isInstalledAndGetVersion")
    #commandToExecute="ls -la /dbagiga | grep \"\->\" | awk \'{print $11}\'"
    commandToExecute='cd /dbagiga;cd -P gigaspaces-smart-ods;echo ""$(basename $(pwd))'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
    outputShFile=str(outputShFile).replace('\n','').replace('/dbagiga/','')
    logger.info("outputShFile :"+str(outputShFile))
    return str(outputShFile)

def isInstalledAndGetVersionOldGS(host):
    logger.info("isInstalledAndGetVersion")
    #commandToExecute="ls -la /dbagiga | grep \"\->\" | awk \'{print $11}\'"
    commandToExecute='cd /dbagiga;cd -P gigaspaces-smart-ods-old;echo ""$(basename $(pwd))'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
    outputShFile=str(outputShFile).replace('\n','').replace('/dbagiga/','')
    logger.info("outputShFile :"+str(outputShFile))
    return str(outputShFile)

def config_get_manager_listWithStatus(filePath='config/cluster.config'):
    with Spinner():
        try:
            headers = [Fore.YELLOW+"SrNo."+Fore.RESET,
                       Fore.YELLOW+"Manager Name"+Fore.RESET,
                       #Fore.YELLOW+"IP"+Fore.RESET,
                       Fore.YELLOW+"Install"+Fore.RESET,
                       Fore.YELLOW+"Status"+Fore.RESET]
            data=[]
            managerDict = {}
            counter = 0
            managerNodes = config_get_manager_node()
            for node in managerNodes:
                installStatus='No'
                status = getSpaceServerStatus(os.getenv(str(node.ip)))
                counter = counter + 1
                managerDict.update({counter: node})
                install = isInstalledAndGetVersion(os.getenv(str(node.ip)))
                logger.info("install : "+str(install))
                if(len(str(install))>0):
                    installStatus='Yes'
                dataArray=[Fore.GREEN+str(counter)+Fore.RESET,
                           Fore.GREEN+os.getenv(node.name)+Fore.RESET,
                           #Fore.GREEN+os.getenv(node.ip)+Fore.RESET,
                           Fore.GREEN+installStatus+Fore.RESET if(installStatus=='Yes') else Fore.RED+installStatus+Fore.RESET,
                           Fore.GREEN+status+Fore.RESET if(status=='ON') else Fore.RED+status+Fore.RESET]
                data.append(dataArray)
            printTabular(None,headers,data)
            verboseHandle.printConsoleInfo(str(99) + ". ESC" " (Escape from menu.)")
            return  managerDict
        except Exception as e:
            handleException(e)

def config_get_space_listWithoutDisplay(filePath='config/cluster.config'):
    spaceNodes = config_get_space_node()
    spaceDict = {}
    counter = 0
    for spaceNode in spaceNodes:
        counter = counter + 1
        spaceDict.update({counter: spaceNode})
    return  spaceDict

def config_remove_space_nodeById(spacename,spaceip,filePath='config/cluster.config', verbose=False):
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    spaceNodes = config_get_space_node()
    counter=0
    for spaceNode in spaceNodes:
        if(spaceNode.name==spacename and spaceNode.ip==spaceip):
            spaceNodes.pop(counter)
        counter=counter+1
    config_data.cluster.servers.spaces.servers.host = spaceNodes
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)

def config_remove_space_nodeByIP(spaceIP,filePath='config/cluster.config',verbose=False):
    logger.debug("Removing manager node "+str(spaceIP)+".")
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    spaceNodes = config_get_space_node()
    counter=0
    for spaceNode in spaceNodes:
        if(spaceNode.ip==spaceIP):
            spaceNodes.pop(counter)
        counter=counter+1
    config_data.cluster.servers.spaces.servers.host = spaceNodes
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)



def config_add_space_node(hostIp, hostName, gsc,filePath='config/cluster.config'):
    newHost = Host(hostIp, hostName, gsc)
    filePath='config/cluster.config'
    config_data = get_cluster_obj(filePath)
    existingNodes = config_data.cluster.servers.spaces.servers.host
    sizeOfNodes = len(existingNodes)
    logger.info("Size of node"+str(sizeOfNodes)+" CURRENT NODE"+str(hostIp) )
    logger.info("Size of existing nodes : "+str(sizeOfNodes))
    if(sizeOfNodes>0) :
        logger.info("isMangerExist(existingNodes,hostIp) "+isMangerExist(existingNodes,hostIp))
        if(isMangerExist(existingNodes,hostIp)=='true'):
            logger.info("Host is already exist."+str(hostIp))
            #verboseHandle.printConsoleInfo("Host is already exist."+str(hostIp))
            confirmAnswer='y'
            #confirmAnswer = str(input(Fore.YELLOW+"Host :"+hostIp+" is already exist.Do you want to override the host ? [yes (y) / no (n)]: "+Fore.RESET))
            logger.info("Host is already exist."+str(confirmAnswer))
            if(confirmAnswer=="y" or confirmAnswer=="yes"):
                logger.info("Host is already exist. Node overrides"+str(confirmAnswer))
                for manager in existingNodes:
                    if(str(manager.ip)==str(hostIp)):
                        logger.info("OVERRIDING IP : "+str(manager.ip))
                        manager.ip=hostIp
                        manager.name=hostName
                logger.info("Host overriden "+str(hostIp)+" To "+str(hostName))
                config_data.cluster.servers.spaces.servers.host = existingNodes
                with open(filePath, 'w') as outfile:
                    json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)
            elif(confirmAnswer=="n" or confirmAnswer=="no"):
                logger.info("ADDING NEW NODE")
                logger.info("Host is already exist. Node adding"+str(confirmAnswer))
                return addToExistingNode(newHost,hostIp,hostName,filePath,config_data,existingNodes)
        else:
            logger.info("ADDING NODE.."+str(hostIp))
            logger.info("Host not found. Node adding")
            return addToExistingNode(newHost,hostIp,hostName,filePath,config_data,existingNodes)
    else:
        logger.info("ADDING NODE"+str(hostIp))
        logger.info("Host not found.. Node adding")
        return addToExistingNode(newHost,hostIp,hostName,filePath,config_data,existingNodes)


def addToExistingSpaceNode(newHost,hostIp,hostName,filePath,config_data,existingNodes):
    existingNodes.append(newHost)
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)
    logger.info("new space node added " + hostIp)
    return existingNodes

def config_update_space_gsc_byHost(host,gsc,filePath='config/cluster.config', verbose=False):
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    spaceNodes = config_get_space_node()
    for node in spaceNodes:
        if(node.ip==host):
            node.gsc=str(gsc)
            logger.info("Updated space gsc for host:"+host+" To GSC="+gsc)

    config_data.cluster.servers.spaces.servers.host = spaceNodes
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)

def isNbNodeExist(existingNodes,hostIp):
    for manager in existingNodes:
        if(str(manager.ip)==str(hostIp)):
            return 'true'
    return "false"

def config_add_nb_node(hostIp, hostName, role, filePath):
    newNode = Node(hostIp, hostName, role)
    config_data = get_cluster_obj(filePath)
    existingNodes = config_data.cluster.servers.nb.node
    sizeOfNodes = len(existingNodes)
    logger.info("Size of node"+str(sizeOfNodes)+" CURRENT NODE"+str(hostIp) )
    logger.info("Size of existing nodes : "+str(sizeOfNodes))
    if(sizeOfNodes>0) :
        logger.info("isMangerExist(existingNodes,hostIp) "+isNbNodeExist(existingNodes,hostIp))
        if(isNbNodeExist(existingNodes,hostIp)=='true'):
            logger.info("Host is already exist.")
            #verboseHandle.printConsoleInfo("Host is already exist. "+str(hostIp))
            #Removed confirmation because no question stop required in between installation - uninstallation process if found then override
            #confirmAnswer = str(input(Fore.YELLOW+"Host :"+hostIp+" is already exist.Do you want to override the host ? [yes (y) / no (n)]: "+Fore.RESET))
            #logger.info("Host is already exist."+str(confirmAnswer))
            #if(confirmAnswer=="y" or confirmAnswer=="yes"):
            logger.info("Host is already exist. Node overrides"+str(hostIp))
            for manager in existingNodes:
                if(str(manager.ip)==str(hostIp)):
                    logger.info("OVERRIDING IP : "+str(manager.ip))
                    manager.ip=hostIp
                    manager.name=hostName
                logger.info("Host overriden "+str(hostIp)+" To "+str(hostName))
                config_data.cluster.servers.nb.node = existingNodes
                with open(filePath, 'w') as outfile:
                    json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)
            #elif(confirmAnswer=="n" or confirmAnswer=="no"):
            #    logger.info("ADDING NEW NODE")
            #    logger.info("Host is already exist. Node adding"+str(confirmAnswer))
            #    return addToExistingNode(newNode,hostIp,hostName,filePath,config_data,existingNodes)
        else:
            logger.info("ADDING NODE"+str(hostIp))
            logger.info("Host not found. Node adding")
            return addToExistingNode(newNode,hostIp,hostName,filePath,config_data,existingNodes)
    else:
        logger.info("ADDING NODE..."+str(hostIp))
        logger.info("Host not found. Node adding")
        return addToExistingNode(newNode,hostIp,hostName,filePath,config_data,existingNodes)

def config_remove_nb_streamByNameIP(nbName,nbIP,filePath='config/cluster.config', verbose=False):
    logger.info("config_remove_nb_streamByNameIP () : nbName :"+str(nbName)+" nbIp:"+str(nbIP))
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    nbNodes = config_data.cluster.servers.nb.node
    counter=0
    for nbNode in nbNodes:
        if(nbNode.name==nbName and nbNode.ip==nbIP):
            logger.info("Nbname : "+nbName+" NbIP:"+nbIP+" has been removed.")
            nbNodes.pop(counter)
        counter=counter+1

    config_data.cluster.servers.nb.node = nbNodes
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)

def config_get_nb_list(filePath='config/cluster.config'):
    return get_cluster_obj(filePath).cluster.servers.nb.node

def config_get_grafana_list(filePath='config/cluster.config'):
    return get_cluster_obj(filePath).cluster.servers.grafana.node

def isGrafanaNodeExist(existingNodes,hostIp):
    for node in existingNodes:
        if(str(node.ip)==str(hostIp)):
            return 'true'
    return "false"

def config_add_grafana_node(hostIp, hostName, role,  filePath='config/cluster.config'):
    logger.info("config_add_grafana_node")
    newNode = Node(hostIp, hostName, role)
    filePath='config/cluster.config'
    config_data = get_cluster_obj(filePath)
    existingNodes = config_data.cluster.servers.grafana.node
    sizeOfNodes = len(existingNodes)
    logger.info("Size of node"+str(sizeOfNodes)+" CURRENT NODE"+str(hostIp) )
    logger.info("Size of existing nodes : "+str(sizeOfNodes))
    if(sizeOfNodes>0) :
        logger.info("isGrafanaNodeExist(existingNodes,hostIp) "+isGrafanaNodeExist(existingNodes,hostIp))
        if(isGrafanaNodeExist(existingNodes,hostIp)=='true'):
            logger.info("Host is already exist. Node overrides"+str(hostIp))
            #verboseHandle.printConsoleInfo("Host is already exist."+str(hostIp))
            for node in existingNodes:
                if(str(node.ip)==str(hostIp)):
                    logger.info("OVERRIDING IP : "+str(node.ip))
                    node.ip=hostIp
                    node.name=hostName
                logger.info("Host overriden "+str(hostIp)+" To "+str(hostName))
                config_data.cluster.servers.grafana.node = existingNodes
                with open(filePath, 'w') as outfile:
                    json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)
        else:
            logger.info("ADDING NODE"+str(hostIp))
            return addToExistingNode(newNode,hostIp,hostName,filePath,config_data,existingNodes)
    else:
        logger.info("ADDING NODE..."+str(hostIp))
        return addToExistingNode(newNode,hostIp,hostName,filePath,config_data,existingNodes)

def config_remove_grafana_byNameIP(grafanaName,grafanaIP,filePath='config/cluster.config', verbose=False):
    logger.info("config_remove_grafana_byNameIP () : grafanaName :"+str(grafanaName)+" nbIp:"+str(grafanaIP))
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    grafanaNodes = config_data.cluster.servers.grafana.node
    counter=0
    for grafanaNode in grafanaNodes:
        logger.info(grafanaNode.name+" :: "+grafanaName)
        if(grafanaNode.name==grafanaName and grafanaNode.role=='grafana'):
            logger.info("Grafana name : "+grafanaName+" Grafana IP:"+grafanaIP+" has been removed.")
            grafanaNodes.pop(counter)
        counter=counter+1

    config_data.cluster.servers.grafana.node = grafanaNodes
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)


def config_get_grafana_node(filePath='config/cluster.config'):
    return get_cluster_obj(filePath).cluster.servers.grafana.node

def config_get_influxdb_node(filePath='config/cluster.config'):
    return get_cluster_obj(filePath).cluster.servers.influxdb.node

def config_get_dataIntegration_nodes(filePath='config/cluster.config'):
    return get_cluster_obj(filePath).cluster.servers.dataIntegration.nodes

def config_get_dataValidation_nodes(filePath='config/cluster.config'):
    return get_cluster_obj(filePath).cluster.servers.dataValidation.nodes

def config_get_dataEngine_nodes(filePath='config/cluster.config'):
    return get_cluster_obj(filePath).cluster.servers.dataEngine.nodes

def isInfluxdbNodeExist(existingNodes, hostIp):
    for node in existingNodes:
        if(str(node.ip)==str(hostIp)):
            return 'true'
    return "false"

def isDataIntegrationNodeExist(existingNodes, hostIp):
    for node in existingNodes:
        if(str(node.ip)==str(hostIp)):
            return 'true'
    return "false"

def isDataValidationNodeExist(existingNodes, hostIp):
    for node in existingNodes:
        if(str(node.ip)==str(hostIp)):
            return 'true'
    return "false"

def isDataEngineNodeExist(existingNodes, hostIp):
    for node in existingNodes:
        if(str(node.ip)==str(hostIp)):
            return 'true'
    return "false"

def config_add_influxdb_node(hostIp, hostName, role,  filePath='config/cluster.config'):
    logger.info("config_add_influxdb_node")
    newNode = Node(hostIp, hostName, role )
    filePath='config/cluster.config'
    config_data = get_cluster_obj(filePath)
    existingNodes = config_data.cluster.servers.influxdb.node
    sizeOfNodes = len(existingNodes)
    logger.info("Size of node"+str(sizeOfNodes)+" CURRENT NODE"+str(hostIp) )
    logger.info("Size of existing nodes : "+str(sizeOfNodes))
    if(sizeOfNodes>0) :
        logger.info("isInfluxdbNodeExist(existingNodes,hostIp) "+isInfluxdbNodeExist(existingNodes,hostIp))
        if(isInfluxdbNodeExist(existingNodes,hostIp)=='true'):
            logger.info("Host is already exist. Node overrides"+str(hostIp))
            #verboseHandle.printConsoleInfo("Host is already exist. "+str(hostIp))
            for node in existingNodes:
                if(str(node.ip)==str(hostIp)):
                    logger.info("OVERRIDING IP : "+str(node.ip))
                    node.ip=hostIp
                    node.name=hostName
                logger.info("Host overriden "+str(hostIp)+" To "+str(hostName))
                config_data.cluster.servers.influxdb.node = existingNodes
                with open(filePath, 'w') as outfile:
                    json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)
        else:
            logger.info("ADDING NODE"+str(hostIp))
            return addToExistingNode(newNode,hostIp,hostName,filePath,config_data,existingNodes)
    else:
        logger.info("ADDING NODE..."+str(hostIp))
        return addToExistingNode(newNode,hostIp,hostName,filePath,config_data,existingNodes)

def config_remove_influxdb_byNameIP(influxdbName,influxdbIP,filePath='config/cluster.config', verbose=False):
    logger.info("config_remove_influxdb_byNameIP () : influxdbName :"+str(influxdbName)+" nbIp:"+str(influxdbIP))
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    influxdbNodes = config_data.cluster.servers.influxdb.node
    counter=0
    for influxdbNode in influxdbNodes:
        logger.info(influxdbNode.name+" :: "+influxdbName)
        if(influxdbNode.name==influxdbName and influxdbNode.role=='influxdb'):
            logger.info("influxdb name : "+influxdbName+" influxdb IP:"+influxdbIP+" has been removed.")
            influxdbNodes.pop(counter)
        counter=counter+1

    config_data.cluster.servers.influxdb.node = influxdbNodes
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)

def config_add_dataIntegration_node(hostIp, hostName, role, type, filePath='config/cluster.config'):
    logger.info("config_add_dataIntegration_node")
    newNode = Nodes(hostIp, hostName, role, type)
    config_data = get_cluster_obj(filePath)
    existingNodes = config_data.cluster.servers.dataIntegration.nodes
    sizeOfNodes = len(existingNodes)
    logger.info("Size of node"+str(sizeOfNodes)+" CURRENT NODE"+str(hostIp) )
    logger.info("Size of existing nodes : "+str(sizeOfNodes))
    if(sizeOfNodes>0) :
        logger.info("isdataIntegrationNodeExist(existingNodes,hostIp) "+isDataIntegrationNodeExist(existingNodes,hostIp))
        if(isDataIntegrationNodeExist(existingNodes,hostIp)=='true'):
            logger.info("Host is already exist. Node overrides"+str(hostIp))
            #verboseHandle.printConsoleInfo("Host is already exist."+str(hostIp))
            for node in existingNodes:
                if(str(node.ip)==str(hostIp)):
                    logger.info("OVERRIDING IP : "+str(node.ip))
                    node.ip=hostIp
                    node.name=hostName
                    node.type=type
                logger.info("Host overriden "+str(hostIp)+" To "+str(hostName))
                config_data.cluster.servers.dataIntegration.nodes = existingNodes
                with open(filePath, 'w') as outfile:
                    json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)
        else:
            logger.info("ADDING NODE"+str(hostIp))
            return addToExistingNode(newNode,hostIp,hostName,filePath,config_data,existingNodes)
    else:
        logger.info("ADDING NODE..."+str(hostIp))
        return addToExistingNode(newNode,hostIp,hostName,filePath,config_data,existingNodes)

def config_remove_dataIntegration_byNameIP(dataIntegrationName,dataIntegrationIP,filePath='config/cluster.config', verbose=False):
    logger.info("config_remove_dataIntegration_byNameIP () : dataIntegrationName :"+str(dataIntegrationName)+" nbIp:"+str(dataIntegrationIP))
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    dataIntegrationNodes = config_data.cluster.servers.dataIntegration.nodes
    counter=0
    for dataIntegrationNode in dataIntegrationNodes:
        logger.info(dataIntegrationNode.name+" :: "+dataIntegrationName)
        if(dataIntegrationNode.name==dataIntegrationName and dataIntegrationNode.role=='dataIntegration'):
            logger.info("dataIntegration name : "+dataIntegrationName+" dataIntegration IP:"+dataIntegrationIP+" has been removed.")
            dataIntegrationNodes.pop(counter)
        counter=counter+1

    config_data.cluster.servers.dataIntegration.nodes = dataIntegrationNodes
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)

def config_add_dataValidation_node(hostIp, hostName, role,  type, filePath='config/cluster.config'):
    logger.info("config_add_dataValidation_node")
    newNode = Nodes(hostIp, hostName, role, type)
    config_data = get_cluster_obj(filePath)
    existingNodes = config_data.cluster.servers.dataValidation.nodes
    sizeOfNodes = len(existingNodes)
    logger.info("Size of node"+str(sizeOfNodes)+" CURRENT NODE"+str(hostIp) )
    logger.info("Size of existing nodes : "+str(sizeOfNodes))
    if(sizeOfNodes>0) :
        logger.info("isdataValidationNodeExist(existingNodes,hostIp) "+isDataValidationNodeExist(existingNodes,hostIp))
        if(isDataValidationNodeExist(existingNodes,hostIp)=='true'):
            logger.info("Host is already exist. Node overrides"+str(hostIp))
            for node in existingNodes:
                if(str(node.ip)==str(hostIp)):
                    logger.info("OVERRIDING IP : "+str(node.ip))
                    node.ip=hostIp
                    node.name=hostName
                    node.type=type
                logger.info("Host overriden "+str(hostIp)+" To "+str(hostName))
                config_data.cluster.servers.dataValidation.nodes = existingNodes
                with open(filePath, 'w') as outfile:
                    json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)
        else:
            logger.info("ADDING NODE"+str(hostIp))
            return addToExistingNode(newNode,hostIp,hostName,filePath,config_data,existingNodes)
    else:
        logger.info("ADDING NODE..."+str(hostIp))
        return addToExistingNode(newNode,hostIp,hostName,filePath,config_data,existingNodes)

def config_remove_dataValidation_byNameIP(dataValidationName,dataValidationIP,filePath='config/cluster.config', verbose=False):
    logger.info("config_remove_dataValidation_byNameIP () : dataValidationName :"+str(dataValidationName)+" nbIp:"+str(dataValidationIP))
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    dataValidationNodes = config_data.cluster.servers.dataValidation.nodes
    counter=0
    for dataValidationNode in dataValidationNodes:
        logger.info(dataValidationNode.name+" :: "+dataValidationName)
        if(dataValidationNode.name==dataValidationName and dataValidationNode.role=='dataValidation'):
            logger.info("dataValidation name : "+dataValidationName+" dataValidation IP:"+dataValidationIP+" has been removed.")
            dataValidationNodes.pop(counter)
        counter=counter+1

    config_data.cluster.servers.dataValidation.nodes = dataValidationNodes
    
def config_add_dataEngine_node(hostIp, hostName, engine, role, type, filePath='config/cluster.config'):
    logger.info("config_add_dataEngine_node")
    newNode = Nodes1(hostIp, hostName, engine, role, type)
    config_data = get_cluster_obj(filePath)
    existingNodes = config_data.cluster.servers.dataEngine.nodes
    sizeOfNodes = len(existingNodes)
    logger.info("Size of node"+str(sizeOfNodes)+" CURRENT NODE"+str(hostIp) )
    logger.info("Size of existing nodes : "+str(sizeOfNodes))
    if(sizeOfNodes>0) :
        logger.info("isdataEngineNodeExist(existingNodes,hostIp) "+isDataEngineNodeExist(existingNodes,hostIp))
        if(isDataEngineNodeExist(existingNodes,hostIp)=='true'):
            logger.info("Host is already exist. Node overrides"+str(hostIp))
            for node in existingNodes:
                if(str(node.ip)==str(hostIp)):
                    logger.info("OVERRIDING IP : "+str(node.ip))
                    node.ip=hostIp
                    node.name=hostName
                    node.type=type
                logger.info("Host overriden "+str(hostIp)+" To "+str(hostName))
                config_data.cluster.servers.dataEngine.nodes = existingNodes
                with open(filePath, 'w') as outfile:
                    json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)
        else:
            logger.info("ADDING NODE"+str(hostIp))
            return addToExistingNode(newNode,hostIp,hostName,filePath,config_data,existingNodes)
    else:
        logger.info("ADDING NODE..."+str(hostIp))
        return addToExistingNode(newNode,hostIp,hostName,filePath,config_data,existingNodes)

def isInstalledAdabasService(host):
    logger.info("isInstalledAndGetVersion")
    commandToExecute='ls /etc/systemd/system/odsxadabas.*'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    return str(outputShFile)

def config_remove_dataEngine_byNameIP(dataEngineName,dataEngineIP,filePath='config/cluster.config', verbose=False):
    logger.info("config_remove_dataEngine_byNameIP () : dataEngineName :"+str(dataEngineName)+" nbIp:"+str(dataEngineIP))
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    dataEngineNodes = config_data.cluster.servers.dataEngine.nodes
    counter=0
    for dataEngineNode in dataEngineNodes:
        logger.info(dataEngineNode.name+" :: "+dataEngineName)
        if(dataEngineNode.name==dataEngineName and (dataEngineNode.role=='dataEngine' or dataEngineNode.role=='mq-connector')):
            logger.info("dataEngine name : "+dataEngineName+" dataEngine IP:"+dataEngineIP+" has been removed.")
            dataEngineNodes.pop(counter)
        counter=counter+1

    config_data.cluster.servers.dataEngine.nodes = dataEngineNodes
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)

def config_get_cdc_streams(filePath='config/cluster.config'):
    return get_cluster_obj(filePath).cluster.streams


def config_get_replications(filePath='config/cluster.config'):
    return get_cluster_obj(filePath).cluster.replications

def config_get_policyConfigurations(filePath='config/cluster.config'):
    return get_cluster_obj(filePath).cluster.policyConfiguration

def config_add_policy_association(targetNodeType, nodes, policy, gscCount, gscZones, filePath='config/cluster.config'):
    print("Adding policy association")
    newPolicyAssociation = PolicyAssociations(targetNodeType, nodes, policy, Gsc(gscCount, gscZones))
    config_data = get_cluster_obj(filePath)
    existingPolicyAssociation = config_data.cluster.policyConfiguration.policyAssociations
    #check if policy exist then replace
    for policyAssociated in list(existingPolicyAssociation):
        if policyAssociated.policy == policy:
            existingPolicyAssociation.remove(policyAssociated)
    existingPolicyAssociation.append(newPolicyAssociation)
    config_data.cluster.policyConfiguration.policyAssociations = existingPolicyAssociation
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)
    logger.info("New policy associated " + policy)
    verboseHandle.printConsoleInfo("New policy associated " + policy)
    return existingPolicyAssociation

def config_add_cdc_stream(name, description, creationDate, serverName, serverip, serverPathOfConfig,status,
                          filePath='config/cluster.config'):
    config_data = get_cluster_obj(filePath)
    existingStreams = config_data.cluster.streams
    autoid = len(existingStreams) + 1

    stream = Streams("CT-" + str(int(hashlib.sha1(str(autoid).encode("utf-8")).hexdigest(), 16) % (10 ** 6)), name,
                     description,
                     creationDate, serverName, serverip, serverPathOfConfig,status)
    existingStreams.append(stream)
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)
    logger.info("new cdc stream added " + serverip)
    return existingStreams

def config_update_stream_statusByCreationDate(creationDate,status,filePath='config/cluster.config', verbose=False):
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    streams = config_get_cdc_streams()
    for stream in streams:
        if(stream.creationDate==creationDate):
            stream.status=status
            logger.info("Updated stream Status for Stream Id"+stream.id+" To "+stream.status)
    config_data.cluster.streams = streams
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)

def config_update_stream_statusById(streamId,status,filePath='config/cluster.config', verbose=False):
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    streams = config_get_cdc_streams()
    for stream in streams:
        if(stream.id==streamId):
            stream.status=status
            logger.info("Updated stream Status for Stream Id"+str(stream.id)+" To "+str(stream.status))

    config_data.cluster.streams = streams
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)

def config_update_stream_statusByHost(host,status,filePath='config/cluster.config', verbose=False):
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    streams = config_get_cdc_streams()
    for stream in streams:
        if(stream.serverip==host):
            stream.status=status
            logger.info("Updated stream Status for Stream Id"+stream.id+" To "+stream.status)

    config_data.cluster.streams = streams
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)


def config_remove_cdc_streamById(streamId,filePath='config/cluster.config', verbose=False):
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    streams = config_get_cdc_streams()
    counter=0
    for stream in streams:
        if(stream.id==streamId):
            streams.pop(counter)
            logger.info("Stream id :"+streamId+" has been removed.")
        counter=counter+1

    config_data.cluster.streams = streams
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)

def config_get_streamName_statusById(streamId,filePath='config/cluster.config', verbose=False):
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    streams = config_get_cdc_streams()
    for stream in streams:
        if(stream.id==streamId):
            return stream.name

def config_remove_cdc_stream(filePath='config/cluster.config', verbose=False):
    if verbose:
        verboseHandle.setVerboseFlag()
    config_data = get_cluster_obj(filePath)
    streams = config_get_cdc_streams()
    streams=[]
    config_data.cluster.streams = streams
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)

def getStreamIdByStreamCreationDateTime(creationDate):
    streams = config_get_cdc_streams()
    for stream in streams:
        if(stream.creationDate==creationDate):
            return stream.id

def getStreamIdAndNameWithoutDisplay():
    streams = config_get_cdc_streams()
    streamDict = {}
    counter = 0
    for stream in streams:
        counter = counter + 1
        streamDict.update({counter: stream})
    return  streamDict

def getStreamIdAndName():
    streams = config_get_cdc_streams()
    verboseHandle.printConsoleWarning("Please choose an option from below :")
    streamDict = {}
    counter = 0

    headers = ["No.", "ID", "Name", "Status"]

    rows, cols = (len(streams), len(headers))
    data = []

    for stream in streams:
        col = []
        counter = counter + 1
        streamDict.update({counter: stream})
        verboseHandle.printConsoleInfo(
            str(counter) + ". "+stream.id + " (" + stream.name + ")")
    verboseHandle.printConsoleInfo(
        str(99) + ". ESC" " (Escape from menu.)")
    return  streamDict

def config_get_cluster_airgap(filePath='config/cluster.config'):
    return 'true'


def config_get_space_hosts(filePath='config/cluster.config'):
    return get_cluster_obj(filePath).cluster.servers.spaces.servers.host

def config_add_cdc_node(filePath='config/cluster.config'):
    return get_cluster_obj(filePath).cluster.servers.cdc.node

def config_add_cdc_node(hostIp, hostName, role, filePath='config/cluster.config'):
    print("Addiing node")
    newNode = Node(hostIp, hostName, role)
    config_data = get_cluster_obj(filePath)
    existingNodes = config_data.cluster.servers.cdc.node
    existingNodes.append(newNode)
    with open(filePath, 'w') as outfile:
        json.dump(config_data, outfile, indent=2, cls=ClusterEncoder)
    logger.info("New cdc node added " + hostIp)
    verboseHandle.printConsoleInfo("New cdc node added, " + hostIp)
    return existingNodes

def config_cdc_list(filePath='config/cluster.config'):
    config_data = get_cluster_obj(filePath)
    return config_data.cluster.servers.cdc.node

def getCDCIPAndName():
    cdcNodes = config_cdc_list()
    verboseHandle.printConsoleWarning("Please choose an option from below :")
    streamDict = {}
    counter = 0
    for cdc in cdcNodes:
        counter = counter + 1
        streamDict.update({counter: cdc})
        verboseHandle.printConsoleInfo(
            str(counter) + ". "+cdc.name + " (" + cdc.ip + ")")
    verboseHandle.printConsoleInfo(
        str(99) + ". ESC" " (Escape from menu.)")
    return  streamDict

def getGrafanaServerHostList():
    nodeList = config_get_grafana_list()
    nodes=""
    for node in nodeList:
        #if(str(node.role).casefold() == 'server'):
        if(len(nodes)==0):
            nodes = os.getenv(node.ip)
        else:
            nodes = nodes+','+os.getenv(node.ip)
    return nodes

def getInfluxdbServerHostList():
    nodeList = config_get_influxdb_node()
    nodes=""
    for node in nodeList:
        #if(str(node.role).casefold() == 'server'):
        if(len(nodes)==0):
            nodes = os.getenv(node.ip)
        else:
            nodes = nodes+','+os.getenv(node.ip)
    return nodes

def getSpaceHostFromEnv():
    logger.info("getSpaceHostFromEnv()")
    hosts = ''
    spaceNodes = config_get_space_hosts()
    for node in spaceNodes:
        hosts+=str(os.getenv(str(node.ip)))+','
    hosts=hosts[:-1]
    return hosts

def getManagerHostFromEnv():
    logger.info("getManagerHostFromEnv()")
    hosts = ''
    managerNodes = config_get_manager_node()
    for node in managerNodes:
        hosts+=str(os.getenv(str(node.ip)))+','
    hosts=hosts[:-1]
    return hosts


def cleanDIHostFronConfig():
    logger.info("cleanDIHost")
    nodeList = config_get_dataIntegration_nodes()
    nodes = ""
    for node in nodeList:
        if (len(nodeList) == 1):
            nodes = node.ip
        else:
            nodes = nodes + ',' + node.ip
    logger.info("nodes :"+str(nodes))
    with Spinner():
        for host in nodes.split(','):
            config_remove_dataIntegration_byNameIP(host,host)
            config_remove_dataEngine_byNameIP(host,host)
    logger.info("Clean DI host completed.")

def cleanSpaceHostFronConfig():
    logger.info("cleanSpaceHost")
    nodeList = config_get_space_hosts()
    nodes = ""
    for node in nodeList:
        if (len(nodeList) == 1):
            nodes = node.ip
        else:
            nodes = nodes + ',' + node.ip
    logger.info("nodes :"+str(nodes))
    with Spinner():
        for host in nodes.split(','):
            config_remove_space_nodeById(host,host)
    logger.info("Clean space host completed.")

def cleanManagerHostFronConfig():
    logger.info("cleanManagerHostFronConfig")
    nodeList = config_get_manager_node()
    nodes = ""
    for node in nodeList:
        if (len(nodeList) == 1):
            nodes = node.ip
        else:
            nodes = nodes + ',' + node.ip
    logger.info("nodes :"+str(nodes))
    with Spinner():
        for host in nodes.split(','):
            config_remove_manager_nodeByIP(host)
    logger.info("Clean DI host completed.")


def discoverHostConfig():
    try:
        #file = '/home/tapan/Gigaspace/Bank_Leumi/tempBranch/filename.yaml'
        sourceInstallerDirectory = str(os.getenv("ENV_CONFIG"))
        logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)
        file = sourceInstallerDirectory+'/host.yaml'
        with open(file) as f:
            content = yaml.safe_load(f)

        managerHostCount=1
        if 'manager' in content['servers']:
            cleanManagerHostFronConfig()
            for k,v in content['servers']['manager'].items():
                host = 'mgr'+str(managerHostCount)+""
                os.environ[host] = str(v)
                config_add_manager_node(host, host, 'admin', filePath='config/cluster.config')
                managerHostCount+=1
        #status = os.system('bash')
        spaceHostCount=1
        if 'space' in content['servers']:
            cleanSpaceHostFronConfig()
            for k,v in content['servers']['space'].items():
                host = 'space'+str(spaceHostCount)+""
                os.environ[host] = str(v)
                config_add_space_node(host, host, 'gsc', filePath='config/cluster.config')
                spaceHostCount+=1

        dataIntegrationHostCount=1
        if 'dataIntegration' in content['servers']:
            cleanDIHostFronConfig()
            for host,v in content['servers']['dataIntegration'].items():
                host = 'di'+str(dataIntegrationHostCount)
                os.environ[host] = str(v)
                type=''
                if(dataIntegrationHostCount==1):
                    type='kafka Broker 1a'
                if(dataIntegrationHostCount==2):
                    type='kafka Broker 1b'
                if(dataIntegrationHostCount==3):
                    type='kafka Broker 2'
                if(dataIntegrationHostCount==4):
                    type='Zookeeper Witness'
                config_add_dataIntegration_node(host, host, 'dataIntegration', type, filePath='config/cluster.config')
                config_add_dataEngine_node(host, host, "dataEngine", "mq-connector", "")
                dataIntegrationHostCount+=1

        if 'grafana' in content['servers']:
            nbHostCount=1
            for host,v in content['servers']['grafana'].items():
                host = 'grafana'+str(nbHostCount)
                os.environ[host] = str(v)
                config_add_grafana_node(host,host,'Grafana', "config/cluster.config")
                nbHostCount+=1

        if 'influxdb' in content['servers']:
            nbHostCount=1
            for host,v in content['servers']['influxdb'].items():
                host = 'influxdb'+str(nbHostCount)
                os.environ[host] = str(v)
                config_add_influxdb_node(host,host,'Influxdb', "config/cluster.config")
                nbHostCount+=1

        if 'nb_applicative' in content['servers']:
            nbHostCount=1
            for host,v in content['servers']['nb_applicative'].items():
                host = 'nb_app'+str(nbHostCount)
                os.environ[host] = str(v)
                config_add_nb_node(host,host,'applicative server', "config/cluster.config")
                nbHostCount+=1

        if 'nb_management' in content['servers']:
            nbHostCount=1
            for host,v in content['servers']['nb_management'].items():
                host = 'nb_mgt'+str(nbHostCount)
                os.environ[host] = str(v)
                config_add_nb_node(host,host,'management server', "config/cluster.config")
                nbHostCount+=1

        if 'space' in content['servers']:
            nbHostCount=1
            for host,v in content['servers']['space'].items():
                host = 'nb_agent'+str(nbHostCount)
                os.environ[host] = str(v)
                config_add_nb_node(host,host,'agent', "config/cluster.config")
                nbHostCount+=1
        dvHostCount=1
        if 'data_validator_server' in content['servers']:
            for host,v in content['servers']['data_validator_server'].items():
                host = 'datavalidation'+str(dvHostCount)
                os.environ[host]=str(v)
                config_add_dataValidation_node(host, host,'DataValidation', 'server')
                dvHostCount+=1
        if 'data_validator_agent' in content['servers']:
            for host,v in content['servers']['data_validator_agent'].items():
                host = 'datavalidation'+str(dvHostCount)
                os.environ[host]=str(v)
                config_add_dataValidation_node(host, host,'DataValidation', 'agent')
                dvHostCount+=1
        if 'pivot' in content['servers']:
            pivotHostCount=1
            for host,v in content['servers']['pivot'].items():
                host='pivot'+str(pivotHostCount)
                os.environ[host]=str(v)
    except Exception as e:
        handleException(e)

if __name__ == "__main__":
    logger.debug("init")
    #config_data = get_cluster_obj("../config/cluster.config")
    #print(config_get_dataIntegration_nodes("../config/cluster.config"))
    # config_add_dataIntegration_node("127.0.0.11", "jay-desktop-2", "dataIntegration", "true", "Master","../config/cluster.config")
    #config_remove_dataIntegration_byNameIP("jay-desktop-2","127.0.0.11","../config/cluster.config")
    # config_add_nb_node("127.0.0.1", "jay-desktop-2", "admin", "true","../config/cluster.config")
    # config_add_space_node("127.0.0.1", "jay-desktop-3", "admin", "true", "../config/cluster.config")

    #print(config_get_dataEngine_nodes("../config/cluster.config"))
    #config_add_dataEngine_node("127.0.0.1", "jay-desktop-3","cr8", "dataEngine", "true", "Master","../config/cluster.config")
    #config_remove_dataEngine_byNameIP("jay-desktop-3","127.0.0.1","../config/cluster.config")
