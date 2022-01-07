#!/usr/bin/env python3
import hashlib
import json
import os
from collections import namedtuple
from datetime import datetime
from json import JSONEncoder
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_print_tabular_data import printTabular
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36
from scripts.logManager import LogManager
from scripts.spinner import Spinner

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


class Clusters:
    def __init__(self, cluster):
        self.cluster = cluster


class Cluster:
    def __init__(self, name, configVersion, timestamp, airGap, resumeModeAll, servers, streams, replications, policyConfiguration):
        self.name = name
        self.configVersion = configVersion
        self.timestamp = timestamp
        self.airGap = airGap
        self.resumeModeAll = resumeModeAll
        self.servers = servers
        self.streams = streams
        self.replications = replications
        self.policyConfiguration = policyConfiguration


class Streams:
    def __init__(self, id, name, description, creationDate, serverName, serverip, serverPathOfConfig,status):
        self.id = id
        self.name = name
        self.description = description
        self.creationDate = creationDate
        self.serverName = serverName
        self.serverip = serverip
        self.serverPathOfConfig = serverPathOfConfig
        self.status = status


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
    def __init__(self, resumeMode, managers, cdc, nb, spaces, grafana, influxdb, dataIntegration,dataValidation):
        self.resumeMode = resumeMode
        self.managers = managers
        self.cdc = cdc
        self.nb = nb
        self.spaces = spaces
        self.grafana = grafana
        self.influxdb = influxdb
        self.dataIntegration = dataIntegration
        self.dataValidation = dataValidation

class Managers:
    def __init__(self, node):
        self.node = node


class CDC:
    def __init__(self, resumeMode, node):
        self.resumeMode = resumeMode
        self.node = node


class NB:
    def __init__(self, resumeMode, node):
        self.resumeMode = resumeMode
        self.node = node

class Grafana:
    def __init__(self,resumeMode,node):
        self.resumeMode = resumeMode
        self.node = node

class Influxdb:
    def __init__(self,resumeMode,node):
        self.resumeMode = resumeMode
        self.node = node

class DataIntegration:
    def __init__(self,resumeMode,nodes):
        self.resumeMode = resumeMode
        self.nodes = nodes

class DataValidation:
    def __init__(self,resumeMode,nodes):
        self.resumeMode = resumeMode
        self.nodes = nodes

class Nodes:
    def __init__(self, ip, name, role, resumeMode, type):
        self.name = name
        self.type = type
        self.ip = ip
        self.role = role
        self.resumeMode = resumeMode

class Node:
    def __init__(self, ip, name, role, resumeMode):
        self.name = name
        self.ip = ip
        self.role = role
        self.resumeMode = resumeMode


class Spaces:
    def __init__(self, partitions, servers):
        self.partitions = partitions
        self.servers = servers


class Partitions:
    def __init__(self, primary, backup):
        self.primary = primary
        self.backup = backup


class Servers:
    def __init__(self, host):
        self.host = host


class Host:
    def __init__(self, ip, name, gsc, resumeMode):
        self.name = name
        self.ip = ip
        self.resumeMode = resumeMode
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
    hostDetail1 = Host("127.0.0.1", "jay-desktop-1", "2", "true")
    hostDetail2 = Host("127.0.0.1", "jay-desktop-2", "2", "true")

    hostDetailList = []
    hostDetailList.append(hostDetail1)
    hostDetailList.append(hostDetail2)
    server = Servers(hostDetailList)
    partitions = Partitions("1", "true")
    spaces = Spaces(partitions, server)

    node1 = Node("127.0.0.1", "jay-desktop-1", "admin", "true")
    node2 = Node("127.0.0.1", "jay-desktop-2", "admin", "true")
    nodeList = [node1, node2]

    nb = NB("true", nodeList)

    cdc = CDC("true", nodeList)

    manager = Managers(nodeList)

    grafana = Grafana("true",nodeList)

    influxdb = Influxdb("true",nodeList)

    allservers = AllServers("true", manager, cdc, nb, spaces, grafana, influxdb)

    dt_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    streams = Streams("123", "demo-stream", "demo stream", "2021-06-11 20:16:34", "jay-desktop-2", "18.116.28.1",
                      "/home/dbsh/cr8/latest_cr8/etc/CR8Config.json","Stopped")

    cluster = Cluster("cluster-1", "1.0", dt_string, "false", "true", allservers, streams)
    clusters = Clusters(cluster)
    with open('config/cluster.config', 'w') as outfile:
        json.dump(clusters, outfile, indent=2, cls=ClusterEncoder)


def parse_config_json(filePath):
    f = open(filePath, )
    clusterObj = json.load(f, object_hook=customClusterDecoder)
    return clusterObj


def get_cluster_obj(filePath='config/cluster.config', verbose=False):
    if verbose:
        verboseHandle.setVerboseFlag()
    logger.debug("getting cluster object from " + filePath)
    config_data = parse_config_json(filePath)
    nodes = []
    for node1 in list(config_data.cluster.servers.managers.node):
        nodes.append(Node(node1.ip, node1.name, node1.role, node1.resumeMode))
    managers = Managers(nodes)
    nodes = []
    for node1 in list(config_data.cluster.servers.cdc.node):
        nodes.append(Node(node1.ip, node1.name, node1.role, node1.resumeMode))
    cdc = CDC(config_data.cluster.servers.cdc.resumeMode, nodes)
    nodes = []
    for node1 in list(config_data.cluster.servers.nb.node):
        nodes.append(Node(node1.ip, node1.name, node1.role, node1.resumeMode))
    nb = NB(config_data.cluster.servers.nb.resumeMode, nodes)
    nodes = []
    grafana = []
    influxdb = []
    dataIntegration = []
    dataValidation = []
    if hasattr(config_data.cluster.servers, 'grafana'):
        for node1 in list(config_data.cluster.servers.grafana.node):
            nodes.append(Node(node1.ip, node1.name, node1.role, node1.resumeMode))
        grafana = Grafana(config_data.cluster.servers.grafana.resumeMode,nodes)
    nodes = []
    if hasattr(config_data.cluster.servers, 'influxdb'):
        for node1 in list(config_data.cluster.servers.influxdb.node):
            nodes.append(Node(node1.ip, node1.name, node1.role, node1.resumeMode))
        influxdb = Influxdb(config_data.cluster.servers.influxdb.resumeMode,nodes)

    nodes = []
    if hasattr(config_data.cluster.servers, 'dataIntegration'):
        for node1 in list(config_data.cluster.servers.dataIntegration.nodes):
            nodes.append(Nodes(node1.ip, node1.name, node1.role, node1.resumeMode, node1.type))
        dataIntegration = DataIntegration(config_data.cluster.servers.dataIntegration.resumeMode,nodes)

    nodes = []
    if hasattr(config_data.cluster.servers, 'dataValidation'):
        for node1 in list(config_data.cluster.servers.dataValidation.nodes):
            nodes.append(Nodes(node1.ip, node1.name, node1.role, node1.resumeMode, node1.type))
        dataValidation = DataValidation(config_data.cluster.servers.dataValidation.resumeMode,nodes)

    partition = Partitions(config_data.cluster.servers.spaces.partitions.primary,
                           config_data.cluster.servers.spaces.partitions.backup)
    hosts = []
    for host in list(config_data.cluster.servers.spaces.servers.host):
        hosts.append(Host(host.ip, host.name, host.gsc, host.resumeMode))

    spaces = Spaces(partition, Servers(hosts))
    allservers = AllServers(config_data.cluster.servers.resumeMode, managers, cdc,
                            nb, spaces, grafana, influxdb, dataIntegration, dataValidation)

    streams = []
    for stream in list(config_data.cluster.streams):
        streams.append(Streams(stream.id, stream.name,
                               stream.description, stream.creationDate,
                               stream.serverName, stream.serverip,
                               stream.serverPathOfConfig,
                               stream.status))

    replications = []
    if hasattr(config_data.cluster, 'replications'):
        for replication in list(config_data.cluster.replications):
            replications.append(
                Replications(replication.id, replication.spacename, replication.serverName, replication.serverip,
                             replication.locator, replication.lookup))

    policies = []
    policiesAssociations = []
    if hasattr(config_data.cluster, 'policyConfiguration'):
        for policy in list(config_data.cluster.policyConfiguration.policies):
            policies.append(Policies(policy.name, policy.description, policy.type, policy.definition, Parameters(policy.parameters.waitIntervalAfterServerDown, policy.parameters.waitIntervalForContainerCheckAfterServerUp, policy.parameters.waitIntervalForDeletionAfterDemote)))

        for policiesAssociation in list(config_data.cluster.policyConfiguration.policyAssociations):
            policiesAssociations.append(PolicyAssociations(policiesAssociation.targetNodeType, policiesAssociation.nodes, policiesAssociation.policy, Gsc(policiesAssociation.gsc.count, policiesAssociation.gsc.zones)))
            #policiesAssociationGsc=[]
            #for eachGsc in list(policiesAssociation.gsc):
            #    print(eachGsc)
            #    policiesAssociationGsc.append(Gsc(eachGsc.count, eachGsc.zones))
            #policiesAssociations.append(PolicyAssociations(policiesAssociation.targetNodeType, policiesAssociation.nodes, policiesAssociation.policy, policiesAssociationGsc))


    # print(config_data.cluster.timestamp)
    cluster = Cluster(config_data.cluster.name, config_data.cluster.configVersion,
                      config_data.cluster.timestamp, config_data.cluster.airGap,
                      config_data.cluster.resumeModeAll, allservers, streams, replications,Policyconfiguration(policies, policiesAssociations))
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

def config_add_manager_node(hostIp, hostName, role, resumeMode, filePath='config/cluster.config'):
    newNode = Node(hostIp, hostName, role, resumeMode)
    config_data = get_cluster_obj(filePath)
    existingNodes = config_data.cluster.servers.managers.node
    sizeOfNodes = len(existingNodes)
    logger.info("Size of node"+str(sizeOfNodes)+" CURRENT NODE"+str(hostIp) )
    logger.info("Size of existing nodes : "+str(sizeOfNodes))
    if(sizeOfNodes>0) :
        logger.info("isMangerExist(existingNodes,hostIp) "+isMangerExist(existingNodes,hostIp))
        if(isMangerExist(existingNodes,hostIp)=='true'):
            verboseHandle.printConsoleInfo("Host is already exist."+str(hostIp))
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
    host_nic_dict_obj = host_nic_dictionary()
    spaceServers = config_get_space_hosts()
    for server in spaceServers:
        cmd = 'systemctl is-active gs.service'
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(server.ip, user, cmd)
            #output = executeRemoteShCommandAndGetOutput(server.ip,user,cmd)
            host_nic_dict_obj.add(server.ip,str(output))

    spaceNodes = config_get_space_node()
    verboseHandle.printConsoleWarning("Please choose an option from below :")
    spaceDict = {}
    counter = 0
    headers = [Fore.YELLOW+"SrNo."+Fore.RESET,
               Fore.YELLOW+"IP"+Fore.RESET,
               Fore.YELLOW+"Host"+Fore.RESET,
               Fore.YELLOW+"Status"+Fore.RESET
               ]
    data=[]
    for server in spaceNodes:
        status = getSpaceServerStatus(server.ip)
        counter = counter + 1
        spaceDict.update({counter: server})
        #verboseHandle.printConsoleInfo(str(counter) + ". "+spaceNode.name + " (" + spaceNode.ip + ")")
        status = host_nic_dict_obj.get(server.ip)
        if(status=="3"):
            status="OFF"
        elif(status=="0"):
            status="ON"
        else:
            logger.info("Host Not reachable..")
            status="OFF"
        if(status=="ON"):
            dataArray=[Fore.GREEN+str(counter)+Fore.RESET,
                       Fore.GREEN+server.ip+Fore.RESET,
                       Fore.GREEN+server.name+Fore.RESET,
                       Fore.GREEN+str(status)+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+str(counter)+Fore.RESET,
                       Fore.GREEN+server.ip+Fore.RESET,
                       Fore.GREEN+server.name+Fore.RESET,
                       Fore.RED+str(status)+Fore.RESET]
        data.append(dataArray)
    printTabular(None,headers,data)
    verboseHandle.printConsoleInfo(
        str(99) + ". ESC" " (Escape from menu.)")
    return  spaceDict

def config_get_manager_listWithStatus(filePath='config/cluster.config'):
    headers = [Fore.YELLOW+"SrNo."+Fore.RESET,
               Fore.YELLOW+"Manager Name"+Fore.RESET,
               Fore.YELLOW+"IP"+Fore.RESET,
               Fore.YELLOW+"Status"+Fore.RESET]
    data=[]
    managerDict = {}
    counter = 0
    managerNodes = config_get_manager_node()
    for node in managerNodes:
        status = getSpaceServerStatus(node.ip)
        counter = counter + 1
        managerDict.update({counter: node})
        if(status=="ON"):
            dataArray=[Fore.GREEN+str(counter)+Fore.RESET,
                       Fore.GREEN+node.name+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.GREEN+status+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+str(counter)+Fore.RESET,
                       Fore.GREEN+node.name+Fore.RESET,
                       Fore.GREEN+node.ip+Fore.RESET,
                       Fore.RED+status+Fore.RESET]
        data.append(dataArray)
    printTabular(None,headers,data)
    verboseHandle.printConsoleInfo(str(99) + ". ESC" " (Escape from menu.)")
    return  managerDict

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



def config_add_space_node(hostIp, hostName, gsc, resumeMode, filePath='config/cluster.config'):
    newHost = Host(hostIp, hostName, gsc, resumeMode)
    config_data = get_cluster_obj(filePath)
    existingNodes = config_data.cluster.servers.spaces.servers.host
    sizeOfNodes = len(existingNodes)
    logger.info("Size of node"+str(sizeOfNodes)+" CURRENT NODE"+str(hostIp) )
    logger.info("Size of existing nodes : "+str(sizeOfNodes))
    if(sizeOfNodes>0) :
        logger.info("isMangerExist(existingNodes,hostIp) "+isMangerExist(existingNodes,hostIp))
        if(isMangerExist(existingNodes,hostIp)=='true'):
            logger.info("Host is already exist.")
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

def config_add_nb_node(hostIp, hostName, role, resumeMode, filePath='config/cluster.config'):
    newNode = Node(hostIp, hostName, role, resumeMode)
    config_data = get_cluster_obj(filePath)
    existingNodes = config_data.cluster.servers.nb.node
    sizeOfNodes = len(existingNodes)
    logger.info("Size of node"+str(sizeOfNodes)+" CURRENT NODE"+str(hostIp) )
    logger.info("Size of existing nodes : "+str(sizeOfNodes))
    if(sizeOfNodes>0) :
        logger.info("isMangerExist(existingNodes,hostIp) "+isNbNodeExist(existingNodes,hostIp))
        if(isNbNodeExist(existingNodes,hostIp)=='true'):
            logger.info("Host is already exist.")
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

def config_add_grafana_node(hostIp, hostName, role, resumeMode, filePath='config/cluster.config'):
    logger.info("config_add_grafana_node")
    newNode = Node(hostIp, hostName, role, resumeMode)
    config_data = get_cluster_obj(filePath)
    existingNodes = config_data.cluster.servers.grafana.node
    sizeOfNodes = len(existingNodes)
    logger.info("Size of node"+str(sizeOfNodes)+" CURRENT NODE"+str(hostIp) )
    logger.info("Size of existing nodes : "+str(sizeOfNodes))
    if(sizeOfNodes>0) :
        logger.info("isGrafanaNodeExist(existingNodes,hostIp) "+isGrafanaNodeExist(existingNodes,hostIp))
        if(isGrafanaNodeExist(existingNodes,hostIp)=='true'):
            logger.info("Host is already exist. Node overrides"+str(hostIp))
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

def config_add_influxdb_node(hostIp, hostName, role, resumeMode, filePath='config/cluster.config'):
    logger.info("config_add_influxdb_node")
    newNode = Node(hostIp, hostName, role, resumeMode)
    config_data = get_cluster_obj(filePath)
    existingNodes = config_data.cluster.servers.influxdb.node
    sizeOfNodes = len(existingNodes)
    logger.info("Size of node"+str(sizeOfNodes)+" CURRENT NODE"+str(hostIp) )
    logger.info("Size of existing nodes : "+str(sizeOfNodes))
    if(sizeOfNodes>0) :
        logger.info("isInfluxdbNodeExist(existingNodes,hostIp) "+isInfluxdbNodeExist(existingNodes,hostIp))
        if(isInfluxdbNodeExist(existingNodes,hostIp)=='true'):
            logger.info("Host is already exist. Node overrides"+str(hostIp))
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

def config_add_dataIntegration_node(hostIp, hostName, role, resumeMode, type, filePath='config/cluster.config'):
    logger.info("config_add_dataIntegration_node")
    newNode = Nodes(hostIp, hostName, role, resumeMode,type)
    config_data = get_cluster_obj(filePath)
    existingNodes = config_data.cluster.servers.dataIntegration.nodes
    sizeOfNodes = len(existingNodes)
    logger.info("Size of node"+str(sizeOfNodes)+" CURRENT NODE"+str(hostIp) )
    logger.info("Size of existing nodes : "+str(sizeOfNodes))
    if(sizeOfNodes>0) :
        logger.info("isdataIntegrationNodeExist(existingNodes,hostIp) "+isDataIntegrationNodeExist(existingNodes,hostIp))
        if(isDataIntegrationNodeExist(existingNodes,hostIp)=='true'):
            logger.info("Host is already exist. Node overrides"+str(hostIp))
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

def config_add_dataValidation_node(hostIp, hostName, role, resumeMode, type, filePath='config/cluster.config'):
    logger.info("config_add_dataValidation_node")
    newNode = Nodes(hostIp, hostName, role, resumeMode,type)
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
    return get_cluster_obj(filePath).cluster.airGap


def config_get_space_hosts(filePath='config/cluster.config'):
    return get_cluster_obj(filePath).cluster.servers.spaces.servers.host

def config_add_cdc_node(filePath='config/cluster.config'):
    return get_cluster_obj(filePath).cluster.servers.cdc.node

def config_add_cdc_node(hostIp, hostName, role, resumeMode, filePath='config/cluster.config'):
    print("Addiing node")
    newNode = Node(hostIp, hostName, role, resumeMode)
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


# add,remove, update,get
# for spaceservers in get_spaces_servers().host:
#    print(spaceservers)

# updateTimestamp()
if __name__ == "__main__":
    logger.debug("init")
    #config_data = get_cluster_obj("../config/cluster.config")
    #print(config_get_dataIntegration_nodes("../config/cluster.config"))
    # config_add_dataIntegration_node("127.0.0.11", "jay-desktop-2", "dataIntegration", "true", "Master","../config/cluster.config")
    #config_remove_dataIntegration_byNameIP("jay-desktop-2","127.0.0.11","../config/cluster.config")
    # config_add_nb_node("127.0.0.1", "jay-desktop-2", "admin", "true","../config/cluster.config")
    # config_add_space_node("127.0.0.1", "jay-desktop-3", "admin", "true", "../config/cluster.config")
