#!/usr/bin/env python3

import os
import signal
import time
from pathlib import Path

import json
import requests
from colorama import Fore
from configobj import ConfigObj

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig, set_value_in_property_file, getYamlFilePathInsideFolder
from utils.ods_cleanup import signal_handler
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_scp import scp_upload
from utils.ods_ssh import executeRemoteCommandAndGetOutput
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_keypress import userInputWrapper
from utils.odsx_print_tabular_data import printTabular

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '[92m'  # GREEN
    WARNING = '[93m'  # YELLOW
    FAIL = '[91m'  # RED
    RESET = '[0m'  # RESET COLOR

class host_dictionary_obj(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

managerHostConfig=''
# TieredStorage log file configuration  ---Ends

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

def listSpacesOnServer(managerNodes):
    try:
        logger.info("listSpacesOnServer : managerNodes :"+str(managerNodes))
        managerHost=''
        for node in managerNodes:
            status = getSpaceServerStatus(os.getenv(node.ip))
            logger.info("Ip :"+str(node.ip)+"Status : "+str(status))
            if(status=="ON"):
                managerHost = os.getenv(node.ip);
        logger.info("managerHost :"+managerHost)
        response = requests.get("http://"+managerHost+":8090/v2/spaces")
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Existing spaces on cluster:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Name"+Fore.RESET,
                   Fore.YELLOW+"PU Name"+Fore.RESET,
                   Fore.YELLOW+"Partition"+Fore.RESET,
                   Fore.YELLOW+"Backup Partition"+Fore.RESET
                   ]
        gs_space_host_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_host_dictionary_obj : "+str(gs_space_host_dictionary_obj))
        counter=0
        dataTable=[]
        for data in jsonArray:
            if "backupsPerPartition" not in data["topology"]:
                continue

            if(str(data["topology"]["backupsPerPartition"])=="1"):
                isBackup="YES"
            if(str(data["topology"]["backupsPerPartition"])=="0"):
                isBackup="NO"
            dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                         Fore.GREEN+data["name"]+Fore.RESET,
                         Fore.GREEN+data["processingUnitName"]+Fore.RESET,
                         Fore.GREEN+str(data["topology"]["partitions"])+Fore.RESET,
                         Fore.GREEN+isBackup+Fore.RESET
                         ]
            gs_space_host_dictionary_obj.add(str(counter+1),str(data["name"]))
            counter=counter+1
            dataTable.append(dataArray)
        printTabular(None,headers,dataTable)
        return gs_space_host_dictionary_obj
    except Exception as e:
        handleException(e)

def get_gs_host_details(managerNodes):
    try:
        logger.info("get_gs_host_details() : managerNodes :"+str(managerNodes))
        for node in managerNodes:
            status = getSpaceServerStatus(os.getenv(node.ip))
            if(status=="ON"):
                managerHostConfig = os.getenv(node.ip);
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
            if(gs_host_details_obj.__contains__(str(os.getenv(node.name))) or (str(os.getenv(node.name)) in gs_host_details_obj.values())):
                space_dict_obj.add(str(counter+1),os.getenv(node.name))
                counter=counter+1
        logger.info("space_dict_obj : "+str(space_dict_obj))
        verboseHandle.printConsoleWarning("Space hosts lists")
        headers = [Fore.YELLOW+"No"+Fore.RESET,
                   Fore.YELLOW+"Host"+Fore.RESET]
        dataTable=[]
        for data in range (1,len(space_dict_obj)+1):
            dataArray = [Fore.GREEN+str(data)+Fore.RESET,
                         Fore.GREEN+str(space_dict_obj.get(str(data)))+Fore.RESET]
            dataTable.append(dataArray)
        printTabular(None,headers,dataTable)
        return space_dict_obj
    except Exception as e:
        handleException(e)

def getManagerHost(managerNodes):
    managerHost=""
    try:
        logger.info("getManagerHost() : managerNodes :"+str(managerNodes))
        for node in managerNodes:
            status = getSpaceServerStatus(os.getenv(node.ip))
            if(status=="ON"):
                managerHost = os.getenv(node.ip)
        return managerHost
    except Exception as e:
        handleException(e)

def isMemoryAvailableOnHost(managerNodes,host, memory,memoryRequiredGSCInBytes):
    try:
        logger.info("isMemoryAvailableOnHost : "+host+" memory :"+str(memory)+" memoryRequiredGSCInBytes:"+str(memoryRequiredGSCInBytes))
        managerHost = getManagerHost(managerNodes)
        logger.info("URL : http://"+str(managerHost)+":8090/v2/hosts/"+str(host)+"/statistics/os")
        response = requests.get("http://"+managerHost+":8090/v2/hosts/"+host+"/statistics/os", headers={'Accept': 'application/json'})
        logger.info(response.status_code)
        logger.info(response.content)
        jsonArray = json.loads(response.text)
        global freePhysicalMemorySizeInBytes
        freePhysicalMemorySizeInBytes = jsonArray['freePhysicalMemorySizeInBytes']
        actualFreePhysicalMemorySizeInBytes = jsonArray['actualFreePhysicalMemorySizeInBytes']
        logger.info("freePhysicalMemorySizeInBytes :"+str(freePhysicalMemorySizeInBytes))
        logger.info("memoryRequiredGSCInBytes :"+str(memoryRequiredGSCInBytes))
        if(freePhysicalMemorySizeInBytes > memoryRequiredGSCInBytes):
            logger.info("Memory available.")
            return True
        else:
            logger.info("No sufficent memory available: Required Memory:"+str(memoryRequiredGSCInBytes)+" Available Memory:"+str(freePhysicalMemorySizeInBytes) +" on host:"+host)
            verboseHandle.printConsoleInfo("No sufficent memory available: Required Memory:"+str(memoryRequiredGSCInBytes)+" Available Memory:"+str(freePhysicalMemorySizeInBytes)+" on host:"+host)
            return False
    except Exception as e:
        handleException(e)

def convertMemoryGSCToBytes(memoryGSC, type, bsize=1024):
    logger.info("convertMemoryGSCToBytes() memoryGSC"+str(memoryGSC)+" type:"+str(type))
    a = {'k' : 1, 'm': 2, 'g' : 3, 't' : 4, 'p' : 5, 'e' : 6 }
    r = float(memoryGSC)
    for i in range(a[type]):
        r = r * bsize
    logger.info("r :"+str(r))
    return r

def checkIsMemoryAvailableOnHost(managerNodes,memoryGSC,memoryRequiredGSCInBytes,zoneGSC,numberOfGSC,managerHostConfig):
    logger.info("checkIsMemoryAvailableOnHost()")
    try:
        for i in range(1,len(space_dict_obj)+1):
            host = space_dict_obj.get(str(i))
            isMemoryAvailable = isMemoryAvailableOnHost(managerNodes,host,memoryGSC,memoryRequiredGSCInBytes)
            if(isMemoryAvailable):
                logger.info("Memory is available.")
            else:
                return isMemoryAvailable
        return isMemoryAvailable
    except Exception as e:
        handleException(e)

def createGSCInputParam(managerNodes,spaceNodes,managerHostConfig):
    logger.info("createGSCInputParam()")
    global confirmCreateGSC
    global numberOfGSC
    global memoryGSC
    global zoneGSC
    global specificHost
    global individualHostConfirm
    try:
        confirmCreateGSC = str(readValuefromAppConfig("app.tieredstorage.gsc.create"))
        #str(userInputWrapper(Fore.YELLOW+"Do you want to create GSC ? (y/n) [n] :"+Fore.RESET))
        if(len(confirmCreateGSC)==0):
            confirmCreateGSC='n'
        if(confirmCreateGSC=='y'):
            #global space_dict_obj
            #space_dict_obj = displaySpaceHostWithNumber(managerNodes,spaceNodes)
            #individualHostConfirm = str(userInputWrapper(Fore.YELLOW+"Do you want to create GSC on specific host ? (y/n) [n] :"))
            #if(len(str(individualHostConfirm))==0):
            individualHostConfirm = 'n'
            if(individualHostConfirm=='y'):
                hostToCreateGSC = str(userInputWrapper("Enter space host serial number to create gsc [1] :"+Fore.RESET))
                if(len(hostToCreateGSC)==0):
                    hostToCreateGSC="1"
                specificHost = space_dict_obj.get(hostToCreateGSC)
                verboseHandle.printConsoleInfo("GSC will be created on :"+str(specificHost))
            logger.info("individualHostConfirm : "+str(individualHostConfirm))

            numberOfGSC = str(readValuefromAppConfig("app.tieredstorage.gsc.perhost"))
            #print(Fore.YELLOW+"Number of GSC per host:"+numberOfGSC+Fore.RESET)
            #if(len(str(numberOfGSC))==0):
            #    numberOfGSC=2
            logger.info("numberofGSC :"+str(numberOfGSC))

            memoryGSC = str(readValuefromAppConfig("app.tieredstorage.gsc.memory"))
            #print(Fore.YELLOW+"Memory to create gsc :"+memoryGSC+Fore.RESET)
            #if(len(memoryGSC)==0):
            #    memoryGSC="12g"

            zoneGSC = str(readValuefromAppConfig("app.tieredstorage.gsc.zone"))
            #print(Fore.YELLOW+"GSC zone :"+Fore.RESET)
            #while(len(str(zoneGSC))==0):
            #    zoneGSC = str(userInputWrapper("Enter zone :"+Fore.RESET))

            size = 1024
            type = memoryGSC[len(memoryGSC)-1:len(memoryGSC)]
            memoryGSCWithoutSuffix = memoryGSC[0:len(memoryGSC)-1]
            logger.info("memoryGSCWithoutSuffix :"+str(memoryGSCWithoutSuffix))
            memoryRequiredGSCInBytes = convertMemoryGSCToBytes(memoryGSCWithoutSuffix,type,size)
            logger.info("memoryRequiredGSCInBytes :"+str(memoryRequiredGSCInBytes))
            global isMemoryAvailable
            logger.info("space_dict_obj :"+str(space_dict_obj))
            # Creating GSC on each available host
            isMemoryAvailable = checkIsMemoryAvailableOnHost(managerNodes,memoryGSC,memoryRequiredGSCInBytes,zoneGSC,numberOfGSC,managerHostConfig)
            #if(isMemoryAvailable):
            #    createGSC(memoryGSC,zoneGSC,numberOfGSC,managerHostConfig,individualHostConfirm)
            return isMemoryAvailable
    except Exception as e:
        handleException(e)

def dataContainerREST(host,zone,memory):
    logger.info("dataContainerREST()")
    data ={
        "vmArguments": [
            "-Xms"+memory+" -Xmx"+memory
        ],
        "memory": memory,
        "zone": zone,
        "host": host
    }
    #response = requests.post("http://54.154.72.190:8090/v2/spaces?name=space&partitions=1&backups=true")
    return  data

def createGSC(memoryGSC,zoneGSC,numberOfGSC,managerHostConfig,individualHostConfirm):
    try:
        logger.info("createGSC()"+str(memoryGSC)+" : "+str(zoneGSC)+" : "+str(numberOfGSC)+" : "+managerHostConfig)
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        if(individualHostConfirm=='y'):
            logger.info("specificHost :"+str(specificHost))
            data = dataContainerREST(specificHost,zoneGSC,memoryGSC)
            logger.info("data:"+str(data))
            for i in range(1,int(numberOfGSC)+1):
                logger.info("numofGSC")
                logger.info("GSC "+str(i+1)+" url : http://"+str(managerHostConfig)+":8090/v2/containers")
                response = requests.post("http://"+managerHostConfig+":8090/v2/containers",data=json.dumps(data),headers=headers)
                logger.info("GSC "+str(i+1)+" response_status_code:"+str(response.status_code))
                if(response.status_code==202):
                    logger.info("GSC "+str(i+1)+" created on host :"+str(specificHost))
                    verboseHandle.printConsoleInfo("GSC "+str(i+1)+" created on host :"+str(specificHost))
        if(individualHostConfirm=='n'):
            with Spinner():
                counter=0
                for i in range(1,len(space_dict_obj)+1):
                    host = space_dict_obj.get(str(i))
                    cmd = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh container create --zone "+str(zoneGSC)+" --count "+str(numberOfGSC)+" --memory "+str(memoryGSC)+" "+str(host)+" | grep -v JAVA_HOME"
                    logger.info("cmd : "+str(cmd))
                    verboseHandle.printConsoleInfo("zone="+str(zoneGSC)+" count="+str(numberOfGSC)+" memory="+str(memoryGSC)+" "+str(host))
                    with Spinner():
                        output = executeRemoteCommandAndGetOutput(host, 'root', cmd)
                    logger.info("Extracting .tar file :"+str(output))
                    verboseHandle.printConsoleInfo(str(output))

    except Exception as e:
        handleException(e)

def uploadFileRest(managerHostConfig):
    try:
        logger.info("uploadFileRest : managerHostConfig : "+str(managerHostConfig))
        #/home/ec2-user/TieredStorageImpl-1.0-SNAPSHOT.jar
        global pathOfSourcePU
        pathOfSourcePU = ".gs.jars.ts.tieredStorageBuild"
        pathOfSourcePU = str(getYamlFilePathInsideFolder(pathOfSourcePU)).replace('"','')
        #print(Fore.YELLOW+"Path filename of processing unit to deploy :"+str(pathOfSourcePU)+Fore.RESET)
        #if(len(str(pathOfSourcePUInput))>0):
        #    pathOfSourcePU = pathOfSourcePUInput
        #while(len(str(pathOfSourcePU))==0):
        #    pathOfSourcePU = str(userInputWrapper(Fore.YELLOW+"Enter path including filename of processing unit to deploy :"+Fore.RESET))
        logger.info("pathOfSourcePU :"+str(pathOfSourcePU))
        #set_value_in_property_file('app.tieredstorage.pu.filepath',str(pathOfSourcePU))
        #set_value_yaml_config("current.gs.jars.ts.currentTs",str(pathOfSourcePU))
        logger.info("url : "+"curl -X PUT -F 'file=@"+str(pathOfSourcePU)+"' http://"+managerHostConfig+":8090/v2/pus/resources")
        status = os.system("curl -X PUT -F 'file=@"+str(pathOfSourcePU)+"' http://"+managerHostConfig+":8090/v2/pus/resources")
        logger.info("status : "+str(status))
    except Exception as e:
        handleException(e)

def dataPuREST(resource,resourceName,zone,partition,maxInstancesPerMachine,backUpRequired):
    logger.info("dataPuREST()")
    try:
        global slaProperties
        slaProperties = str(readValuefromAppConfig("app.tieredstorage.pu.autogenerated-instance-sla"))
        #print(Fore.YELLOW+"pu.autogenerated-instance-sla value :"+slaProperties+Fore.RESET)
        #if(len(str(slaProperties))==0):
        #    slaProperties="true"
        logger.info("slaProperties :"+str(slaProperties))

        global tieredCriteriaConfigFilePath
        tieredCriteriaConfigFilePath = str(getYamlFilePathInsideFolder(".object.config.ddlparser.ddlCriteriaFileName")).replace('"','')
        #tieredCriteriaConfigFilePathInput = \
        #print(Fore.YELLOW+"tieredCriteriaConfig.filePath : "+str(tieredCriteriaConfigFilePath)+Fore.RESET)
        #if(len(str(tieredCriteriaConfigFilePathInput))>0):
        #    tieredCriteriaConfigFilePath = tieredCriteriaConfigFilePathInput
        #while(len(str(tieredCriteriaConfigFilePath))==0):
        #    tieredCriteriaConfigFilePath = str(userInputWrapper(Fore.YELLOW+"Enter tieredCriteriaConfig.filePath : "+Fore.RESET))
        logger.info("filePath :"+str(tieredCriteriaConfigFilePath))
        #set_value_in_property_file('app.tieredstorage.criteria.filepath',str(tieredCriteriaConfigFilePath))

        global tieredCriteriaConfigFilePathTarget
        dbaGigaDir=str(readValuefromAppConfig("app.giga.path"))
        tieredCriteriaConfigFilePathTarget = str(readValuefromAppConfig("app.tieredstorage.criteria.filepath.target")).replace('"','').replace("/dbagiga/",dbaGigaDir)
        #tieredCriteriaConfigFilePathTargetInput = \
        #print(Fore.YELLOW+" tieredCriteriaConfig.filePath.target : "+str(tieredCriteriaConfigFilePathTarget)+Fore.RESET)
        #if(len(str(tieredCriteriaConfigFilePathTargetInput))>0):
        #    tieredCriteriaConfigFilePathTarget = tieredCriteriaConfigFilePathTargetInput
        #while(len(str(tieredCriteriaConfigFilePathTarget))==0):
        #    tieredCriteriaConfigFilePathTarget = str(userInputWrapper(Fore.YELLOW+"Enter tieredCriteriaConfig.filePath.target : "+Fore.RESET))
        logger.info("filePath.target :"+str(tieredCriteriaConfigFilePathTarget))
        #set_value_in_property_file('app.tieredstorage.criteria.filepath.target',str(tieredCriteriaConfigFilePathTarget))

        global spacePropertyConfigFilePath
        spacePropertyConfigFilePath = str(getYamlFilePathInsideFolder(".gs.config.ts.spaceproperty")).replace('"','')
        logger.info("app.space.property.filePath :"+str(spacePropertyConfigFilePath))
        #spacePropertyConfigFilePathInput =
        #print(Fore.YELLOW+" space.property.filePath : "+str(spacePropertyConfigFilePath)+Fore.RESET)
        #if(len(str(spacePropertyConfigFilePathInput))>0):
        #    spacePropertyConfigFilePath = spacePropertyConfigFilePathInput
        #while(len(str(spacePropertyConfigFilePath))==0):
        #    spacePropertyConfigFilePath = str(userInputWrapper(Fore.YELLOW+"Enter space.property.filePath : "+Fore.RESET))
        logger.info("spacePropertyConfigFilePath :"+str(spacePropertyConfigFilePath))
        #set_value_in_property_file('app.space.property.filePath',str(spacePropertyConfigFilePath))

        global spacePropertyConfigFilePathTarget
        spacePropertyConfigFilePathTarget = str(readValuefromAppConfig("app.space.property.filePath.target")).replace('"','').replace("/dbagiga/",dbaGigaDir)
        logger.info("app.space.property.filePath.target :"+str(spacePropertyConfigFilePathTarget))
        #spacePropertyConfigFilePathTargetInput =
        #print(Fore.YELLOW+"space.property.filePath.target : "+str(spacePropertyConfigFilePathTarget)+Fore.RESET)
        #if(len(str(spacePropertyConfigFilePathTargetInput))>0):
        #    spacePropertyConfigFilePathTarget = spacePropertyConfigFilePathTargetInput
        #while(len(str(spacePropertyConfigFilePathTarget))==0):
        #    spacePropertyConfigFilePathTarget = str(userInputWrapper(Fore.YELLOW+"Enter space.property.filePath.target : "+Fore.RESET))
        logger.info("spacePropertyConfigFilePathTarget :"+str(spacePropertyConfigFilePathTarget))
        #set_value_in_property_file('app.space.property.filePath.target',str(spacePropertyConfigFilePathTarget))

        global spaceNameCfg
        spaceNameCfg = str(readValuefromAppConfig("app.tieredstorage.pu.spacename"))
        #print(Fore.YELLOW+"Space name to set space.name : "+str(spaceNameCfg)+Fore.RESET)
        #if(len(str(spaceNameCfg))==0):
        #    spaceNameCfg = 'bllspace'
        logger.info("space.name :"+str(spaceNameCfg))

        data={
                "resource": ""+resource+"",
                "topology": {
                    "schema": "partitioned",
                    "partitions": int(partition),
                    "backupsPerPartition": int(backUpRequired)
                },
                "name": ""+resourceName+"",
                "sla": {
                    "maxInstancesPerMachine": int(maxInstancesPerMachine),
                    "zones": [
                        ""+zone+""
                    ],
                    "maxInstancesPerVM": 1
                },
                "contextProperties": {
                                      "pu.autogenerated-instance-sla" :""+slaProperties+"",
                                      "tieredCriteriaConfig.filePath" : ""+tieredCriteriaConfigFilePathTarget+"",
                                      "space.propertyFilePath" : ""+spacePropertyConfigFilePathTarget+"",
                                      "space.name" : ""+spaceNameCfg+"",
                                      "tieredCriteriaConfig.dirtyBitFile" : ""+tieredDirtyBitFile +""
                                      }
            }

        return data
    except Exception as e:
        handleException(e)

def displaySummaryOfInputParam(confirmCreateGSC):
    try:
        verboseHandle.printConsoleWarning("------------------------------------------------------------")
        verboseHandle.printConsoleWarning("***Summary***")
        verboseHandle.printConsoleWarning("Want to create GSC :"+str(confirmCreateGSC))
        if(confirmCreateGSC=='y'):
            verboseHandle.printConsoleWarning("Number of GSC per host :"+str(numberOfGSC))
            verboseHandle.printConsoleWarning("Enter memory to create gsc :"+str(memoryGSC))
            verboseHandle.printConsoleWarning("Enter zone :"+str(zoneGSC))
        verboseHandle.printConsoleWarning("Enter path of resource :"+str(pathOfSourcePU))
        verboseHandle.printConsoleWarning("Enter name of resource :"+str(resource))
        verboseHandle.printConsoleWarning("Enter name of PU to deploy :"+str(resourceName))
        verboseHandle.printConsoleWarning("Build zone of resource to deploy :"+str(zoneOfPU))
        verboseHandle.printConsoleWarning("Enter partitions :"+str(partition))
        verboseHandle.printConsoleWarning("Enter maxInstancePerMachine :"+str(maxInstancesPerMachine))
        verboseHandle.printConsoleWarning("Enter maxInstancesPerVM :"+str('1'))
        verboseHandle.printConsoleWarning("SLA [HA] ? (y/n) :"+str(str(backUpRequired)))
        verboseHandle.printConsoleWarning("Enter pu.autogenerated-instance-sla value :"+str(slaProperties))
        verboseHandle.printConsoleWarning("Enter tieredCriteriaConfig.filePath :"+str(tieredCriteriaConfigFilePath))
        verboseHandle.printConsoleWarning("Enter tieredCriteriaConfig.filePath.target :"+str(tieredCriteriaConfigFilePathTarget))
        verboseHandle.printConsoleWarning("Enter space.property.filePath : "+str(spacePropertyConfigFilePath))
        verboseHandle.printConsoleWarning("Enter space.property.filePath.target : "+str(spacePropertyConfigFilePathTarget))
        verboseHandle.printConsoleWarning("Enter space name to set space.name : "+str(spaceNameCfg))
    except Exception as e:
        handleException(e)

def copyFile(hostips, srcPath, destPath, dryrun=False):
    logger.info("copyFile :"+str(hostips)+" : "+str(srcPath)+" : "+str(destPath))
    username = "root"
    '''
    if not dryrun:
        username = userInputWrapper("Enter username for host [root] : ")
        if username == "":
            username = "root"
    else:
        username = "root"
    '''
    for hostip in hostips:
        if scp_upload(hostip, username, srcPath, destPath):
            verboseHandle.printConsoleInfo(hostip)
            logger.info(
                "Done copying, hostip=" + hostip + ", username=" + username + ", srcPath=" + srcPath + ", destPath=" + destPath)
        else:
            return False
    return True

def getSpaceNodeIps():
    logger.info("spaceNodes() ")
    ips = []
    spaceNodes = config_get_space_hosts()
    for node in spaceNodes:
        ips.append(os.getenv(node.ip))
    logger.info("ips : "+str(ips))
    return ips

def copyFilesFromODSXToSpaceServer():
    logger.info("copyFilesFromODSXToSpaceServer()")
    ips = getSpaceNodeIps()
    logger.info(" ips : "+str(ips)+" tieredCriteriaConfigFilePath :"+str(tieredCriteriaConfigFilePath)+" tieredCriteriaConfigFilePathTarget : "+str(tieredCriteriaConfigFilePathTarget))
    copyFile(ips,tieredCriteriaConfigFilePath , tieredCriteriaConfigFilePathTarget)
    logger.info(" ips : "+str(ips)+" spacePropertyConfigFilePath : "+str(spacePropertyConfigFilePath)+" spacePropertyConfigFilePathTarget : "+str(spacePropertyConfigFilePathTarget))
    copyFile(ips,spacePropertyConfigFilePath , spacePropertyConfigFilePathTarget)

def set_value_in_property_file(key, value, filename):
    #file='config/app.config'
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)
    file= filename
    config = ConfigObj(file)
    if(len(value)==0):
        value=''
    config[key] = value        #Update Key
    config.write()             #Write Content
    x = open(file)
    s = x.read().replace(' = ','=')
    x.close()
    x=open(file,"w")
    x.write(s)
    x.close
def proceedForTieredStorageDeployment(managerHostConfig,confirmCreateGSC):
    logger.info("proceedForTieredStorageDeployment()")
    try:
        print("\n")
        head , tail = os.path.split(pathOfSourcePU)
        logger.info("tail :"+str(tail))
        global resource
        resource = str(tail)
        #print(str(Fore.YELLOW+"Name of resource will be deploy ["+str(tail)+"] "+Fore.RESET))
        #while(len(str(resource))==0):
        #    resource = tail
        logger.info("resource :"+str(resource))

        global resourceName
        resourceName = str(readValuefromAppConfig("app.tieredstorage.pu.name"))
        #print(Fore.YELLOW+"Name of PU to deploy : "+resourceName+Fore.RESET)
        #if(len(str(resourceName))==0):
        #    resourceName = 'bllservice'
        logger.info("nameOfPU :"+str(resourceName))

        global partition
        partition = str(readValuefromAppConfig("app.tieredstorage.gsc.partitions"))
        #print(Fore.YELLOW+"Partition required :"+partition+Fore.RESET)
        #if(len(str(partition))==0):
        #    partition='50'
        #while( not partition.isdigit()):
        #    partition = str(userInputWrapper(Fore.YELLOW+"Enter partition required [1-9] :"+Fore.RESET))
        logger.info("Enter partition required :"+str(partition))

        global zoneOfPU
        zoneOfPU = str(readValuefromAppConfig("app.tieredstorage.pu.zone"))
        #print(Fore.YELLOW+"Zone of processing unit to deploy :"+zoneOfPU+Fore.RESET)
        #while(len(str(zoneOfPU))==0):
        #    zoneOfPU = 'bll'
        logger.info("Zone Of PU :"+str(zoneOfPU))

        global maxInstancesPerMachine
        maxInstancesPerMachine = str(readValuefromAppConfig("app.tieredstorage.pu.maxInstancesPerMachine"))
        #print(Fore.YELLOW+"Enter maxInstancesPerMachine to deploy :"+maxInstancesPerMachine+Fore.RESET)
        #if(len(str(maxInstancesPerMachine))==0):
        #    maxInstancesPerMachine = '1'
        #while(not maxInstancesPerMachine.isdigit()):
        #    maxInstancesPerMachine = str(userInputWrapper(Fore.YELLOW+"Enter maxInstancesPerMachine to deploy [1-9] :"+Fore.RESET))
        logger.info("maxInstancePerVM Of PU :"+str(maxInstancesPerMachine))

        global backUpRequired
        global tieredDirtyBitFile
        backUpRequired = str(readValuefromAppConfig("app.tieredstorage.pu.backuprequired"))
        #print(Fore.YELLOW+"SLA [HA] :"+backUpRequired+Fore.RESET)
        if(len(str(backUpRequired))==0 or backUpRequired=='y'):
            backUpRequired=1
        if(str(backUpRequired)=='n'):
            backUpRequired=0
        tieredDirtyBitFile = str(getYamlFilePathInsideFolder(".gs.config.ts.criteria")).replace('"','')
        fle = Path(tieredDirtyBitFile)
        fle.touch(exist_ok=True)
        data = dataPuREST(resource,resourceName,zoneOfPU,partition,maxInstancesPerMachine,backUpRequired)

        displaySummaryOfInputParam(confirmCreateGSC)
        finalConfirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to proceed ? (y/n) [y] :"+Fore.RESET))
        if(len(str(finalConfirm))==0):
            finalConfirm='y'
        if(finalConfirm=='y'):
            if(confirmCreateGSC=='y'):
                logger.info("Creating GSC :")
                createGSC(memoryGSC,zoneGSC,numberOfGSC,managerHostConfig,individualHostConfirm)
            copyFilesFromODSXToSpaceServer()

            headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
            logger.info("url : "+"http://"+managerHostConfig+":8090/v2/pus")
            logger.info("dJson Paylod : "+str(data))
            # set dirty bit file for initial deployment
            set_value_in_property_file("firstTimedeployment", "true", tieredDirtyBitFile)
            tieredDirtyBitFileValue = open(tieredDirtyBitFile, "r")
            print(tieredDirtyBitFileValue.read())
            response = requests.post("http://"+managerHostConfig+":8090/v2/pus",data=json.dumps(data),headers=headers)
            deployResponseCode = str(response.content.decode('utf-8'))
            verboseHandle.printConsoleInfo("deployResponseCode : "+str(deployResponseCode))
            logger.info("deployResponseCode :"+str(deployResponseCode))

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
                        print("Before setting dirty flag false "+str(retryCount))
                        tieredDirtyBitFileValue = open(tieredDirtyBitFile, "r")
                        print(tieredDirtyBitFileValue.read())

                        print("Setting dirty flag false")
                        set_value_in_property_file("firstTimedeployment", "false", tieredDirtyBitFile)
                        tieredDirtyBitFileValue = open(tieredDirtyBitFile, "r")
                        print(tieredDirtyBitFileValue.read())
                        serviceName = 'object-management.service'
                        verboseHandle.printConsoleWarning("restarting "+serviceName)
                        os.system('sudo systemctl daemon-reload')
                        os.system('systemctl stop '+serviceName)
                        os.system('systemctl start '+serviceName)
                        verboseHandle.printConsoleInfo("Done restarting "+serviceName)
                        return
                    elif(str(status).casefold().__contains__('failed')):
                        return

            else:
                logger.info("Unable to deploy :"+str(status))
                verboseHandle.printConsoleInfo("Unable to deploy : "+str(status))
        else:
            return
        #logger.info("GSC "+str(managerHostConfig)+" response_status_code:"+str(response.status_code))
        #if(response.status_code==202):
        #    logger.info("PU "+str(resource)+" created on host :"+str(managerHostConfig))
    except Exception as e:
        handleException(e)

def validateResponseGetDescription(responseCode):
    logger.info("validateResponse() "+str(responseCode))
    response = requests.get("http://"+managerHost+":8090/v2/requests/"+str(responseCode))
    jsonData = json.loads(response.text)
    logger.info("response : "+str(jsonData))
    if(str(jsonData["status"]).__contains__("failed")):
        return "Status :"+str(jsonData["status"])+" Description:"+str(jsonData["error"])
    else:
        return "Status :"+str(jsonData["status"])+" Description:"+str(jsonData["description"])



if __name__ == '__main__':
    logger.info("Menu -> TieredStorage -> Deploy")
    #loggerTiered.info("Deploy")
    verboseHandle.printConsoleWarning("Menu -> TieredStorage -> Deploy")
    signal.signal(signal.SIGINT, signal_handler)
    try:
        managerNodes = config_get_manager_node()
        logger.info("managerNodes: main"+str(managerNodes))
        if(len(str(managerNodes))>0):
            spaceNodes = config_get_space_hosts()
            logger.info("spaceNodes: main"+str(spaceNodes))
            managerHost = getManagerHost(managerNodes)
            logger.info("managerHost : main"+str(managerHost))
            if(len(str(managerHost))>0):
                managerHostConfig = managerHost
                logger.info("managerHostConfig : "+str(managerHost))
                listSpacesOnServer(managerNodes)
                space_dict_obj = displaySpaceHostWithNumber(managerNodes,spaceNodes)
                isMemoryAvailable = createGSCInputParam(managerNodes,spaceNodes,managerHostConfig)
                logger.info("isMemoryAvailable : "+str(isMemoryAvailable))
                logger.info("confirmCreateGSC : "+str(confirmCreateGSC))
                if(confirmCreateGSC=='y'):
                    if(isMemoryAvailable):
                        uploadFileRest(managerHostConfig)
                        proceedForTieredStorageDeployment(managerHostConfig,confirmCreateGSC)
                    else:
                        logger.info("No memeory available double check.")
                if(confirmCreateGSC=='n'):
                    uploadFileRest(managerHostConfig)
                    proceedForTieredStorageDeployment(managerHostConfig,confirmCreateGSC)
            else:
                logger.info("Please check manager server status.")
                verboseHandle.printConsoleInfo("Please check manager server status.")
        else:
            logger.info("No Manager configuration found please check.")
            verboseHandle.printConsoleInfo("No Manager configuration found please check.")

    except Exception as e:
        logger.error("Exception in odsx_tieredstorage_deploy "+str(e))
        verboseHandle.printConsoleError("Exception in odsx_tieredstorage_deploy "+str(e))
        handleException(e)