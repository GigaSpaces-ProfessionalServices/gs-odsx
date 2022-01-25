#!/usr/bin/env python3

import os,time,subprocess,requests, json, math
from colorama import Fore
from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import set_value_in_property_file,readValueByConfigObj
from utils.ods_cluster_config import config_get_dataIntegration_nodes,config_add_dataEngine_node
from utils.ods_scp import scp_upload
from utils.ods_ssh import connectExecuteSSH
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_app_config import readValuefromAppConfig, set_value_in_property_file
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_print_tabular_data import printTabular
from scripts.spinner import Spinner
from utils.ods_ssh import executeRemoteCommandAndGetOutput
from utils.ods_scp import scp_upload

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
clusterHosts = []
confirmCreateGSC=''

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

class host_dictionary_obj(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

def getDIServerHostList():
    nodeList = config_get_dataIntegration_nodes()
    nodes = ""
    for node in nodeList:
        # if(str(node.role).casefold() == 'server'):
        if (len(nodes) == 0):
            nodes = node.ip
        else:
            nodes = nodes + ',' + node.ip
    return nodes

def getBootstrapAddress(hostConfig):
    logger.info("getBootstrapAddress()")
    bootstrapAddress=''
    for host in hostConfig.split(','):
        bootstrapAddress=bootstrapAddress+host+':9092,'
    bootstrapAddress=bootstrapAddress[:-1]
    logger.info("getBootstrapAddress : "+str(bootstrapAddress))
    return bootstrapAddress

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

def listDeployed(managerHost):
    global gs_space_dictionary_obj
    try:
        logger.info("managerHost :"+str(managerHost))
        response = requests.get("http://"+str(managerHost)+":8090/v2/pus/")
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Resources on cluster:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Name"+Fore.RESET,
                   Fore.YELLOW+"Resource"+Fore.RESET,
                   Fore.YELLOW+"Zone"+Fore.RESET,
                   Fore.YELLOW+"processingUnitType"+Fore.RESET,
                   Fore.YELLOW+"Status"+Fore.RESET
                   ]
        gs_space_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_dictionary_obj : "+str(gs_space_dictionary_obj))
        counter=0
        dataTable=[]
        for data in jsonArray:
            dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                         Fore.GREEN+data["name"]+Fore.RESET,
                         Fore.GREEN+data["resource"]+Fore.RESET,
                         Fore.GREEN+str(data["sla"]["zones"])+Fore.RESET,
                         Fore.GREEN+data["processingUnitType"]+Fore.RESET,
                         Fore.GREEN+data["status"]+Fore.RESET
                         ]
            gs_space_dictionary_obj.add(str(counter+1),str(data["name"]))
            counter=counter+1
            dataTable.append(dataArray)
        printTabular(None,headers,dataTable)
        return gs_space_dictionary_obj
    except Exception as e:
        handleException(e)

def listSpacesOnServer(managerNodes):
    try:
        logger.info("listSpacesOnServer : managerNodes :"+str(managerNodes))
        managerHost=''
        for node in managerNodes:
            status = getSpaceServerStatus(node.ip)
            logger.info("Ip :"+str(node.ip)+"Status : "+str(status))
            if(status=="ON"):
                managerHost = node.ip;
        logger.info("managerHost :"+managerHost)
        response = requests.get("http://"+managerHost+":8090/v2/spaces")
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Existing spaces on cluster:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Name"+Fore.RESET,
                   Fore.YELLOW+"PU Name"+Fore.RESET
                   ]
        gs_space_host_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_host_dictionary_obj : "+str(gs_space_host_dictionary_obj))
        counter=0
        dataTable=[]
        for data in jsonArray:
            dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                         Fore.GREEN+data["name"]+Fore.RESET,
                         Fore.GREEN+data["processingUnitName"]+Fore.RESET
                         ]
            gs_space_host_dictionary_obj.add(str(counter+1),str(data["name"]))
            counter=counter+1
            dataTable.append(dataArray)
        #printTabular(None,headers,dataTable)
        return gs_space_host_dictionary_obj
    except Exception as e:
        handleException(e)

def get_gs_host_details(managerNodes):
    try:
        logger.info("get_gs_host_details() : managerNodes :"+str(managerNodes))
        for node in managerNodes:
            status = getSpaceServerStatus(node.ip)
            if(status=="ON"):
                managerHostConfig = node.ip;
        logger.info("managerHostConfig : "+str(managerHostConfig))
        response = requests.get('http://'+managerHostConfig+':8090/v2/hosts', headers={'Accept': 'application/json'})
        logger.info("response status of host :"+str(managerHostConfig)+" status :"+str(response.status_code))
        jsonArray = json.loads(response.text)
        gs_servers_host_dictionary_obj = host_dictionary_obj()
        for data in jsonArray:
            gs_servers_host_dictionary_obj.add(str(data['name']),str(data['address']))
        logger.info("gs_servers_host_dictionary_obj : "+str(gs_servers_host_dictionary_obj))
        return gs_servers_host_dictionary_obj
    except Exception as e:
        handleException(e)

def displaySpaceHostWithNumber(managerNodes, spaceNodes):
    try:
        logger.info("displaySpaceHostWithNumber() managerNodes :"+str(managerNodes)+" spaceNodes :"+str(spaceNodes))
        gs_host_details_obj = get_gs_host_details(managerNodes)
        logger.info("gs_host_details_obj : "+str(gs_host_details_obj))
        counter = 0
        space_dict_obj = host_dictionary_obj()
        logger.info("space_dict_obj : "+str(space_dict_obj))
        for node in spaceNodes:
            if(gs_host_details_obj.__contains__(str(node.name)) or (str(node.name) in gs_host_details_obj.values())):
                space_dict_obj.add(str(counter+1),node.name)
                counter=counter+1
        logger.info("space_dict_obj : "+str(space_dict_obj))
        #verboseHandle.printConsoleWarning("Space hosts lists")
        headers = [Fore.YELLOW+"No"+Fore.RESET,
                   Fore.YELLOW+"Host"+Fore.RESET]
        dataTable=[]
        for data in range (1,len(space_dict_obj)+1):
            dataArray = [Fore.GREEN+str(data)+Fore.RESET,
                         Fore.GREEN+str(space_dict_obj.get(str(data)))+Fore.RESET]
            dataTable.append(dataArray)
        #printTabular(None,headers,dataTable)
        return space_dict_obj
    except Exception as e:
        handleException(e)


def proceedToCreateGSC():
    logger.info("proceedToCreateGSC()")
    #for host in managerNodes:
    #    scp_upload(str(host.ip),'root',dPipelineLocationSource,dPipelineLocationTarget)
    for host in spaceNodes:
        scp_upload(str(host.ip),'root',dPipelineLocationSource,dPipelineLocationTarget)
        commandToExecute = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh container create --count="+str(numberOfGSC)+" --zone="+str(zoneGSC)+" --memory="+str(memoryGSC)+" --vm-option -Dspring.profiles.active=connector --vm-option -Dpipeline.config.location="+str(dPipelineLocationTarget)+" "+str(host.ip)
        print(commandToExecute)
        logger.info(commandToExecute)
        with Spinner():
            output = executeRemoteCommandAndGetOutput(managerHost, 'root', commandToExecute)
            print(output)
            logger.info("Output:"+str(output))


def createGSCInputParam(managerHost,spaceNode):
    logger.info("createGSCInputParam()")
    global numberOfGSC
    global zoneGSC
    global memoryGSC
    global dPipelineLocationTarget
    global dPipelineLocationSource

    numberOfGSC = str(input(Fore.YELLOW+"Enter number of GSCs per host [2] : "+Fore.RESET))
    while(len(str(numberOfGSC))==0):
        numberOfGSC=2
    logger.info("numberOfGSC :"+str(numberOfGSC))

    zoneGSC = str(input(Fore.YELLOW+"Enter zone of GSC to create [adsCons] : "+Fore.RESET))
    while(len(str(zoneGSC))==0):
        zoneGSC='adsCons'
    logger.info("zoneGSC :"+str(zoneGSC))

    memoryGSC = str(input(Fore.YELLOW+"Enter memory of GSC [12g] : "+Fore.RESET))
    while(len(str(memoryGSC))==0):
        memoryGSC='12g'
    dPipelineSourceConfig = str(readValueByConfigObj("app.dataengine.mq.dpipleline.source")).replace('[','').replace(']','').replace("'","").replace(', ',',')
    dPipelineLocationSourceInput = str(input(Fore.YELLOW+"Enter -Dpipeline.config.location source ["+str(dPipelineSourceConfig)+"] : "+Fore.RESET))
    if(len(str(dPipelineLocationSourceInput))==0):
        dPipelineLocationSource=str(dPipelineSourceConfig)

    dPipelineTargetConfig = str(readValueByConfigObj("app.dataengine.mq.dpipleline.target")).replace('[','').replace(']','').replace("'","").replace(', ',',')
    dPipelineLocationTargetInput = str(input(Fore.YELLOW+"Enter -Dpipeline.config.location target ["+str(dPipelineTargetConfig)+"] : "+Fore.RESET))
    if(len(str(dPipelineLocationTargetInput))==0):
        dPipelineLocationTarget=str(dPipelineTargetConfig)

    #proceedToCreateGSC()

def uploadFileRest(managerHostConfig):
    try:
        logger.info("uploadFileRest : managerHostConfig : "+str(managerHostConfig))
        #/home/ec2-user/TieredStorageImpl-1.0-SNAPSHOT.jar
        global pathOfSourcePU
        pathOfSourcePU = str(readValuefromAppConfig("app.tieredstorage.pu.filepath")).replace('"','')
        pathOfSourcePUInput = str(input(Fore.YELLOW+"Enter path including filename of processing unit to deploy ["+str(pathOfSourcePU)+"]:"+Fore.RESET))
        if(len(str(pathOfSourcePUInput))>0):
            pathOfSourcePU = pathOfSourcePUInput
        while(len(str(pathOfSourcePU))==0):
            pathOfSourcePU = str(input(Fore.YELLOW+"Enter path including filename of processing unit to deploy :"+Fore.RESET))
        logger.info("pathOfSourcePU :"+str(pathOfSourcePU))
        set_value_in_property_file('app.tieredstorage.pu.filepath',str(pathOfSourcePU))

        logger.info("url : "+"curl -X PUT -F 'file=@"+str(pathOfSourcePU)+"' http://"+managerHostConfig+":8090/v2/pus/resources")
        status = os.system("curl -X PUT -F 'file=@"+str(pathOfSourcePU)+"' http://"+managerHostConfig+":8090/v2/pus/resources")
        logger.info("status : "+str(status))
    except Exception as e:
        handleException(e)

def getDataPUREST():
    backUpRequired=0
    data={
        "resource": ""+resource+"",
        "name": ""+resourceName+"",
        "maxInstancesPerMachine": int(maxInstancesPerMachine),
        "contextProperties": {#"pu.autogenerated-instance-sla" :""+slaProperties+"",
            #"tieredCriteriaConfig.filePath" : ""+tieredCriteriaConfigFilePathTarget+"",
            "spring.kafka.bootstrap-servers" : ""+kafkaBootStrapServers+"",
            "space.name" : ""+spaceName+"",
            "spring.kafka.consumer-group" : ""+consumerGroup+""
        }
    }
    return data

def validateResponseGetDescription(responseCode):
    logger.info("validateResponse() "+str(responseCode))
    response = requests.get("http://"+managerHost+":8090/v2/requests/"+str(responseCode))
    jsonData = json.loads(response.text)
    logger.info("response : "+str(jsonData))
    if(str(jsonData["status"]).__contains__("failed")):
        return "Status :"+str(jsonData["status"])+" Description:"+str(jsonData["error"])
    else:
        return "Status :"+str(jsonData["status"])+" Description:"+str(jsonData["description"])

def proceedToDeployPU(data):
    logger.info("proceedToDeployPU()")
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    logger.info("url : "+"http://"+managerHost+":8090/v2/pus")

    response = requests.post("http://"+managerHost+":8090/v2/pus",data=json.dumps(data),headers=headers)
    deployResponseCode = str(response.content.decode('utf-8'))
    print("deployResponseCode : "+str(deployResponseCode))
    logger.info("deployResponseCode :"+str(deployResponseCode))
    if(deployResponseCode.isdigit()):
        status = validateResponseGetDescription(deployResponseCode)
        logger.info("response.status_code :"+str(response.status_code))
        logger.info("response.content :"+str(response.content) )
        if(response.status_code==202):
            logger.info("Response :"+str(status))
            retryCount=5
            while(retryCount>0 or (not str(status).casefold().__contains__('successful')) or (not str(status).casefold().__contains__('failed'))):
                status = validateResponseGetDescription(deployResponseCode)
                verboseHandle.printConsoleInfo("Response :"+str(status))
                retryCount = retryCount-1
                time.sleep(2)
                if(str(status).casefold().__contains__('successful')):
                    return
                elif(str(status).casefold().__contains__('failed')):
                    return
        else:
            logger.info("Unable to deploy :"+str(status))
            verboseHandle.printConsoleInfo("Unable to deploy : "+str(status))
    else:
        logger.info("Unable to deploy :"+str(deployResponseCode))
        verboseHandle.printConsoleInfo("Unable to deploy : "+str(deployResponseCode))


def displaySummaryOfInputParam():
    logger.info("displaySummaryOfInputParam()")
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleWarning("***Summary***")
    if(confirmCreateGSC=='y'):
        verboseHandle.printConsoleWarning("Enter number of GSCs per host :"+str(numberOfGSC))
        verboseHandle.printConsoleWarning("Enter zone of GSC to create :"+zoneGSC)
        verboseHandle.printConsoleWarning("Enter memory of GSC [12g] :"+memoryGSC)
        verboseHandle.printConsoleWarning("Enter -Dpipeline.config.location source : "+dPipelineLocationSource)
        verboseHandle.printConsoleWarning("Enter -Dpipeline.config.location target : "+dPipelineLocationTarget)
    verboseHandle.printConsoleWarning("Name of resource will be deploy : "+resource)
    verboseHandle.printConsoleWarning("Enter name of PU to deploy :"+resourceName)
    verboseHandle.printConsoleWarning("Enter zone of processing unit to deploy :"+zoneOfPU)
    verboseHandle.printConsoleWarning("spring.kafka.bootstrap-servers : "+str(kafkaBootStrapServers))
    verboseHandle.printConsoleWarning("Enter spring.kafka.consumer-group :"+consumerGroup)


def proceedToDeployPUInputParam(managerHost):
    logger.info("proceedToDeployPUInputParam()")

    uploadFileRest(managerHost)

    head , tail = os.path.split(pathOfSourcePU)
    logger.info("tail :"+str(tail))
    global resource
    resource = str(tail)
    print("\n")
    print(str(Fore.YELLOW+"Name of resource will be deploy ["+str(tail)+"] "+Fore.RESET))
    #while(len(str(resource))==0):
    #    resource = tail
    logger.info("resource :"+str(resource))

    global resourceName
    resourceName = str(input(Fore.YELLOW+"Enter name of PU to deploy [adabasConsumer] :"+Fore.RESET))
    if(len(str(resourceName))==0):
        resourceName = 'adabasConsumer'
    logger.info("nameOfPU :"+str(resourceName))

    global partition
    partition='1'

    global zoneOfPU
    zoneOfPU = str(input(Fore.YELLOW+"Enter zone of processing unit to deploy [adsCons] :"+Fore.RESET))
    if(len(str(zoneOfPU))==0):
        zoneOfPU = 'adsCons'
    logger.info("Zone Of PU :"+str(zoneOfPU))

    global maxInstancesPerMachine
    maxInstancesPerMachine = '1'
    logger.info("maxInstancePerVM Of PU :"+str(maxInstancesPerMachine))

    global kafkaBootStrapServers
    hostConfig = getDIServerHostList()
    kafkaBootStrapServers = getBootstrapAddress(hostConfig)
    verboseHandle.printConsoleWarning("spring.kafka.bootstrap-servers : ["+str(kafkaBootStrapServers)+"]")

    global spaceName
    spaceName = str(input(Fore.YELLOW+"Enter space.name [adbsSpace] : "+Fore.RESET))
    if(len(str(spaceName))==0):
        spaceName='adbsSpace'

    global consumerGroup
    consumerGroup = str(input(Fore.YELLOW+"Enter spring.kafka.consumer-group [DIH] :"+Fore.RESET))
    if(len(consumerGroup)==0):
        consumerGroup='DIH'

    data = getDataPUREST()
    print(data)
    displaySummaryOfInputParam()

    finalConfirm = str(input(Fore.YELLOW+"Are you sure want to proceed ? (y/n) [y] :"+Fore.RESET))
    if(len(str(finalConfirm))==0):
        finalConfirm='y'
    if(finalConfirm=='y'):
        print("confirmCreateGSC "+confirmCreateGSC)
        if(confirmCreateGSC=='y'):
            logger.info("Creating GSC :")
            proceedToCreateGSC()
        proceedToDeployPU(data)
    else:
        return

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> List -> MQ-Connector -> Kafka consumer -> Deploy')
    try:
        nodes = getDIServerHostList()
        logger.info("DI / kafka host found :"+str(nodes))
        if(len(nodes)>0):
            managerNodes = config_get_manager_node()
            logger.info("managerNodes: main"+str(managerNodes))
            if(len(str(managerNodes))>0):
                spaceNodes = config_get_space_hosts()
                logger.info("spaceNodes: main"+str(spaceNodes))
                managerHost = getManagerHost(managerNodes)
                logger.info("managerHost : main"+str(managerHost))
                if(len(str(managerHost))>0):
                    listSpacesOnServer(managerNodes)
                    listDeployed(managerHost)
                    space_dict_obj = displaySpaceHostWithNumber(managerNodes,spaceNodes)
                    if(len(space_dict_obj)>0):
                        confirmCreateGSC = str(input(Fore.YELLOW+"Do you want to create GSC ? (y/n) [y] : "))
                        if(len(str(confirmCreateGSC))==0 or confirmCreateGSC=='y'):
                            confirmCreateGSC='y'
                            createGSCInputParam(managerHost,spaceNodes)
                        proceedToDeployPUInputParam(managerHost)
                    else:
                        logger.info("Please check space server.")
                        verboseHandle.printConsoleInfo("Please check space server.")
                else:
                    logger.info("Please check manager server status.")
                    verboseHandle.printConsoleInfo("Please check manager server status.")
            else:
                logger.info("No Manager configuration found please check.")
                verboseHandle.printConsoleInfo("No Manager configuration found please check.")
        else:
            logger.info("No kafka servers configurations found. Please install kafka servers first.")
            verboseHandle.printConsoleInfo("No kafka servers configurations found. Please install kafka servers first.")
    except Exception as e:
        handleException(e)