#!/usr/bin/env python3

import os, time
from colorama import Fore
from scripts.logManager import LogManager
import requests, json, math
from scripts.spinner import Spinner
from utils.ods_scp import scp_upload
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_app_config import readValuefromAppConfig, getYamlFilePathInsideFolder
from utils.ods_ssh import executeRemoteCommandAndGetOutput
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_keypress import userInputWrapper
from utils.odsx_print_tabular_data import printTabular
from scripts.odsx_tieredstorage_undeploy import listDeployed
verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR

class host_dictionary_obj(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

managerHostConfig=''

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


def getStatusAndTypeOfSpaceOrPU(managerHost,puName):
    logger.info("getStatusOfSpaceOrPU()")
    statusAndType=[]
    logger.info("URL : http://"+str(managerHost)+":8090/v2/pus/"+str(puName))
    response = requests.get("http://"+str(managerHost)+":8090/v2/pus/"+str(puName))
    jsonArray = json.loads(response.text)
    statusAndType.append(jsonArray["status"])
    statusAndType.append(jsonArray["processingUnitType"])
    return statusAndType

def listSpacesOnServer(managerNodes):
    try:
        logger.info("listSpacesOnServer : managerNodes :"+str(managerNodes))
        managerHost=''
        for node in managerNodes:
            status = getSpaceServerStatus(os.getenv(node.ip))
            logger.info("Ip :"+str(os.getenv(node.ip))+"Status : "+str(status))
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
def dataContainerREST(host,zone,memory):
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

def convert_size(size_bytes,i):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    #i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

def isMemoryAvailableOnHost(managerNodes,host, memory,memoryRequiredGSCInBytes):
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
    for i in range(1,len(space_dict_obj)+1):
        host = space_dict_obj.get(str(i))
        isMemoryAvailable = isMemoryAvailableOnHost(managerNodes,host,memoryGSC,memoryRequiredGSCInBytes)
        if(isMemoryAvailable):
            logger.info("Memory is available.")
        else:
            return isMemoryAvailable
    return isMemoryAvailable

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
                    cmd = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh container create --zone "+str(zoneGSC)+" --count "+str(numberOfGSC)+" --memory "+str(memoryGSC)+" "+str(host)+""
                    logger.info("cmd : "+str(cmd))
                    with Spinner():
                        output = executeRemoteCommandAndGetOutput(host, 'root', cmd)
                    logger.info("Extracting .tar file :"+str(output))
                    verboseHandle.printConsoleInfo(str(output))

                    #REST Create GSCFlow
                    '''
                    data = dataContainerREST(host,zoneGSC,memoryGSC)
                    logger.info("data:"+str(data))
                    # creating 2 GSC by def
                    for i in range(1,int(numberOfGSC)+1):
                        counter=counter+1
                        logger.info("numofGSC")
                        logger.info("GSC "+str(i)+" url : http://"+str(managerHostConfig)+":8090/v2/containers")
                        response = requests.post("http://"+managerHostConfig+":8090/v2/containers",data=json.dumps(data),headers=headers)
                        logger.info("GSC "+str(i)+" response_status_code:"+str(response.status_code))
                        responseCode = str(response.content.decode('utf-8'))
                        logger.info("GSC "+str(i)+" response_code_request ::"+str(responseCode))
                        if(response.status_code==202):
                            logger.info("GSC "+str(i)+" created on host :"+str(host))
                        if(responseCode.isdigit()):
                            status = validateResponseGetDescription(responseCode)
                            logger.info("response.content :"+str(response.content) )
                            logger.info("Response :"+str(status))
                            retryCount=5
                            while(retryCount>0 or (not str(status).casefold().__contains__('successful'))):
                                status = validateResponseGetDescription(responseCode)
                                #verboseHandle.printConsoleInfo("Response create gsc:"+str(status))
                                logger.info("Response create gsc:"+str(status))
                                retryCount = retryCount-1
                                #time.sleep(1)
                                if(str(status).casefold().__contains__('successful')):
                                        retryCount=0
                            logger.info("Response create gsc:"+str(status))
                            #verboseHandle.printConsoleInfo("Response create gsc:"+str(status))
                        else:
                            logger.info("Unable to create container :"+str(status))
                            verboseHandle.printConsoleInfo("Unable to create container : "+str(status))
                        verboseHandle.printConsoleInfo("GSC "+str(i)+" created on host :"+str(host))
                    '''

    except Exception as e:
        handleException(e)

def createGSCInputParam(managerNodes,spaceNodes,managerHostConfig):
    logger.info("createGSC()")

    #global space_dict_obj
    #space_dict_obj = displaySpaceHostWithNumber(managerNodes,spaceNodes)
    '''
    hostToCreateGSC = str(userInputWrapper("Enter space host serial number to create gsc [1] :"+Fore.RESET))
    if(len(hostToCreateGSC)==0):
        hostToCreateGSC="1"
    host = space_dict_obj.get(hostToCreateGSC)
    '''
    global numberOfGSC
    global specificHost
    global individualHostConfirm
    numberOfGSC = str(readValuefromAppConfig("app.newspace.creategsc.gscperhost")) #str(userInputWrapper("Enter number of GSC per host [2] :"+Fore.RESET))
    if(len(str(numberOfGSC))==0):
        numberOfGSC=2
    logger.info("numberofGSC :"+str(numberOfGSC))

    global memoryGSC
    memoryGSC = str(readValuefromAppConfig("app.newspace.creategsc.gscmemory")) #str(userInputWrapper("Enter memory to create gsc [12g] :"+Fore.RESET))
    if(len(memoryGSC)==0):
        memoryGSC="12g"

    global zoneGSC
    zoneGSC = str(readValuefromAppConfig("app.newspace.creategsc.gsczone")) #str(userInputWrapper("Enter zone :"+Fore.RESET))
    while(len(str(zoneGSC))==0):
        zoneGSC = str(userInputWrapper("Enter zone :"+Fore.RESET))
    individualHostConfirm = str(readValuefromAppConfig("app.newspace.creategsc.specifichost"))#str(userInputWrapper(Fore.YELLOW+"Do you want to create GSC on specific host ? (y/n) [n] :"))
    #if(len(str(individualHostConfirm))==0):
    #    individualHostConfirm = 'n'
    if(individualHostConfirm=='y'):
        hostToCreateGSC = str(userInputWrapper("Enter space host serial number to create gsc [1] :"+Fore.RESET))
        if(len(hostToCreateGSC)==0):
            hostToCreateGSC="1"
        specificHost = space_dict_obj.get(hostToCreateGSC)
        verboseHandle.printConsoleInfo("GSC will be created on :"+str(specificHost))
    logger.info("individualHostConfirm : "+str(individualHostConfirm))
    size = 1024
    type = memoryGSC[len(memoryGSC)-1:len(memoryGSC)]
    memoryGSCWithoutSuffix = memoryGSC[0:len(memoryGSC)-1]
    logger.info("memoryGSCWithoutSuffix :"+str(memoryGSCWithoutSuffix))
    memoryRequiredGSCInBytes = convertMemoryGSCToBytes(memoryGSCWithoutSuffix,type,size)
    logger.info("memoryRequiredGSCInBytes :"+str(memoryRequiredGSCInBytes))

    logger.info("space_dict_obj :"+str(space_dict_obj))
    # Creating GSC on each available host
    isMemoryAvailable = checkIsMemoryAvailableOnHost(managerNodes,memoryGSC,memoryRequiredGSCInBytes,zoneGSC,numberOfGSC,managerHostConfig)
    #if(isMemoryAvailable):
    #isMemoryAvailable = createGSC(managerNodes,memoryGSC,memoryRequiredGSCInBytes,zoneGSC,numberOfGSC,managerHostConfig)
    return isMemoryAvailable


def displaySummaryOfInputParameter():
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleWarning("***Summary***")
    verboseHandle.printConsoleWarning("Want to create GSC :"+str(confirmCreateGSC))
    if(confirmCreateGSC=='y'):
        verboseHandle.printConsoleWarning("Number of GSC per host :"+str(numberOfGSC))
        verboseHandle.printConsoleWarning("Enter memory to create gsc :"+str(memoryGSC))
        verboseHandle.printConsoleWarning("Enter zone :"+str(zoneGSC))
    verboseHandle.printConsoleWarning("Enter space name :"+str(spaceName))
    verboseHandle.printConsoleWarning("Enter space zone :"+str(zoneOfPU))
    verboseHandle.printConsoleWarning("Enter resource name :"+str(resourceName))
    verboseHandle.printConsoleWarning("Enter resource file name :"+str(resource))
    verboseHandle.printConsoleWarning("Enter partitions :"+str(partitions))
    verboseHandle.printConsoleWarning("Enter max instance per machine :"+str(maxInstancesPerMachine))
    verboseHandle.printConsoleWarning("Enter space.property.filePath : "+str(spacePropertyConfigFilePath))
    verboseHandle.printConsoleWarning("Enter space.property.filePath.target : "+str(spacePropertyConfigFilePathTarget))
    if(backUpRequired == 1):
        haStatus=True
    else:
        haStatus=False
    verboseHandle.printConsoleWarning("SLA [HA] ? (y/n) :"+str(str(haStatus)))


def proceedForValidateResponse(response):
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
                    logger.info(str(status))
                    verboseHandle.printConsoleInfo("deployment status : "+str(status))
            else:
                logger.info("Unable to deploy :"+str(deployResponseCode))
                verboseHandle.printConsoleInfo("Unable to deploy : "+str(deployResponseCode))

def dataPuREST(resource,resourceName,zone,partition,maxInstancesPerMachine,backUpRequired):
    logger.info("dataPuREST()")
    try:
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
                "tieredCriteriaConfig.filePath" : "",
                "space.propertyFilePath" : ""+spacePropertyConfigFilePathTarget+"",
                "space.name" : ""+spaceName+"",
            }
        }

        return data
    except Exception as e:
        handleException(e)

def uploadFileRest(managerHostConfig):
    try:
        logger.info("uploadFileRest : managerHostConfig : "+str(managerHostConfig))
        logger.info("pathOfSourcePU :"+str(pathOfSourcePU))
        #set_value_in_property_file('app.tieredstorage.pu.filepath',str(pathOfSourcePU))

        logger.info("url : "+"curl -X PUT -F 'file=@"+str(pathOfSourcePU)+"' http://"+managerHostConfig+":8090/v2/pus/resources")
        status = os.system("curl -X PUT -F 'file=@"+str(pathOfSourcePU)+"' http://"+managerHostConfig+":8090/v2/pus/resources ")
        logger.info("status : "+str(status))
    except Exception as e:
        handleException(e)


def createNewSpaceREST(managerHostConfig):
    try:
        logger.info("createNewSpaceREST() : managerHostConfig:"+str(managerHostConfig))
        confirmCreateSpace = "y"#str(userInputWrapper("Do you want to create space ? (y/n) [y] :"+Fore.RESET))
        if(len(confirmCreateSpace)==0 or confirmCreateSpace == 'y'):
            confirmCreateSpace='y'
            if(confirmCreateSpace=='y'):
                # print("\n")
                global pathOfSourcePU
                pathOfSourcePU =  str(getYamlFilePathInsideFolder(".gs.jars.space.spacejar"))

                head , tail = os.path.split(pathOfSourcePU)
                logger.info("tail :"+str(tail))
                global resource
                resource = str(tail)
                logger.info("resource :"+str(resource))

                global spaceName
                sName = str(readValuefromAppConfig("app.newspace.name"))
                spaceName = sName #str(userInputWrapper("Enter space name  ["+sName+"] :"+Fore.RESET))  #str(userInputWrapper("Enter space name  [mySpace] :"+Fore.RESET))
                if(len(str(spaceName))==0):
                    spaceName=sName

                # global isBuildGlobally
                # # isBuildGloballyValue = str(readValuefromAppConfig("app.newspace.createglobally"))
                # isBuildGlobally = str(userInputWrapper("Build globally over the cluster (y/n) [n] :"+Fore.RESET))
                # if(len(str(isBuildGlobally))==0):
                #     isBuildGlobally='n'

                global zoneOfPU
                zoneOfPUValue = str(readValuefromAppConfig("app.newspace.pu.zone"))
                zoneOfPU = zoneOfPUValue #str(userInputWrapper("Enter space zone ["+zoneOfPUValue+"] :"+Fore.RESET))
                if(len(str(zoneOfPU))==0):
                    zoneOfPU=zoneOfPUValue

                global resourceName
                resourceNameValue = str(readValuefromAppConfig("app.newspace.pu.name"))
                resourceName = resourceNameValue #str(userInputWrapper("Enter service name ["+resourceNameValue+"] :"+Fore.RESET))
                if(len(str(resourceName))==0):
                    resourceName=resourceNameValue

                global partitions
                partitionsValue = str(readValuefromAppConfig("app.newspace.partitions"))
                partitions = partitionsValue #str(userInputWrapper("Enter partitions ["+partitionsValue+"] :"+Fore.RESET))
                if(len(str(partitions))==0):
                    partitions=partitionsValue

                # global maxInstancesPerMachine
                # maxInstancesPerMachine = '1'
                global maxInstancesPerMachine
                maxInstancesPerMachineValue = str(readValuefromAppConfig("app.newspace.pu.maxinstancepermachine"))
                maxInstancesPerMachine = maxInstancesPerMachineValue #str(userInputWrapper("Enter max instance per machine ["+maxInstancesPerMachineValue+"] :"+Fore.RESET))
                if(len(str(maxInstancesPerMachine))==0):
                    maxInstancesPerMachine=maxInstancesPerMachineValue

                global backUpRequired
                backUpRequiredValue = str(readValuefromAppConfig("app.newspace.ha"))#
                backUpRequired = backUpRequiredValue #str(userInputWrapper("SLA [HA] ? (y/n) ["+backUpRequiredValue+"] :"+Fore.RESET))
                if(len(str(backUpRequired))==0 or backUpRequired=='y'):
                    backUpRequired=1
                if(str(backUpRequired)=='n'):
                    backUpRequired=0

                global isSpacePropertyRequired
                isSpacePropertyRequired = str(readValuefromAppConfig("app.newspace.wantspaceproperty"))#str(userInputWrapper(Fore.YELLOW+"Do you want to add space property ? (y/n) [y]: "+Fore.RESET))
                #if(len(isSpacePropertyRequired)==0):
                #    isSpacePropertyRequired='y'
                logger.info("isSpacePropertyRequired : "+str(isSpacePropertyRequired))
                global spacePropertyConfigFilePath
                global spacePropertyConfigFilePathTarget
                spacePropertyConfigFilePath=''
                spacePropertyConfigFilePathTarget=''
                if(isSpacePropertyRequired=='y'):
                    spacePropertyConfigFilePath = str(getYamlFilePathInsideFolder(".gs.config.imspace.imspacepropertyfile"))
                    logger.info("gs.config.ts.spaceproperty :"+str(spacePropertyConfigFilePath))
                    logger.info("spacePropertyConfigFilePath :"+str(spacePropertyConfigFilePath))
                    dbaGigaDir=str(readValuefromAppConfig("app.giga.path"))
                    spacePropertyConfigFilePathTarget = str(readValuefromAppConfig("app.newspace.spaceproperty.filepath.target")).replace('"','').replace("/dbagiga/",dbaGigaDir)
                    logger.info("app.newspace.spaceproperty.filepath.target :"+str(spacePropertyConfigFilePathTarget))
                    logger.info("spacePropertyConfigFilePathTarget :"+str(spacePropertyConfigFilePathTarget))
                else:
                    logger.info("Skipping space property configure.")

                displaySummaryOfInputParameter()
                createConfirm = str(userInputWrapper("Are you sure want to proceed ? (y/n) [y] :"))
                if(len(str(createConfirm))==0):
                    createConfirm='y'
                if(createConfirm=='y'):
                    if(confirmCreateGSC == 'y'):
                        createGSC(memoryGSC,zoneGSC,numberOfGSC,managerHostConfig,individualHostConfirm)
                    copyFilesFromODSXToSpaceServer()
                    uploadFileRest(managerHostConfig)
                    data = dataPuREST(resource,resourceName,zoneOfPU,partitions,maxInstancesPerMachine,backUpRequired)
                    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
                    # if(isBuildGlobally=='y'):
                    #for i in range(1,len(space_dict_obj)+1):
                    #    host = space_dict_obj.get(str(i))
                    # logger.info("http://"+managerHostConfig+":8090/v2/spaces?name="+spaceName+"&partitions="+partitions+"&backups="+backUpRequired)
                    #print("http://"+managerHostConfig+":8090/v2/spaces?name="+spaceName+"&partitions="+partitions+"&backups="+backUpRequired)
                    # response = requests.post("http://"+managerHostConfig+":8090/v2/spaces?name="+spaceName+"&partitions="+partitions+"&backups="+backUpRequired)
                    # response = requests.post("http://"+managerHostConfig+":8090/v2/pus",data=json.dumps(data),headers=headers)
                    response = requests.post("http://"+managerHostConfig+":8090/v2/pus",data=json.dumps(data),headers=headers)
                    deployResponseCode = str(response.content.decode('utf-8'))
                    print("deployResponseCode : "+str(deployResponseCode))
                    logger.info("deployResponseCode :"+str(deployResponseCode))
                    # proceedForValidateResponse(response)
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
                                logger.info("deployment status : "+str(status))
                                verboseHandle.printConsoleInfo(str(status))
                    else:
                        return
    except Exception as e:
        handleException(e)
    # elif(isBuildGlobally=='n'):
    #     response = requests.post("http://"+managerHostConfig+":8090/v2/pus",data=json.dumps(data),headers=headers)
    #     deployResponseCode = str(response.content.decode('utf-8'))
    #     print("deployResponseCode : "+str(deployResponseCode))
    #     logger.info("deployResponseCode :"+str(deployResponseCode))

    # response = requests.post("http://"+managerHostConfig+":8090/v2/pus",data=json.dumps(data),headers=headers)
    # response = requests.post("http://"+managerHostConfig+":8090/v2/spaces?name="+spaceName+"&partitions="+partitions+"&backups="+backUpRequired)
    # proceedForValidateResponse(response)
    # verboseHandle.printConsoleInfo("Space "+spaceName+" created.")

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
    logger.info(" ips : "+str(ips)+" spacePropertyConfigFilePath : "+str(spacePropertyConfigFilePath)+" spacePropertyConfigFilePathTarget : "+str(spacePropertyConfigFilePathTarget))
    copyFile(ips,spacePropertyConfigFilePath , spacePropertyConfigFilePathTarget)

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

def validateResponseGetDescription(responseCode):
    logger.info("validateResponse() "+str(responseCode))
    response = requests.get("http://"+managerHost+":8090/v2/requests/"+str(responseCode))
    jsonData = json.loads(response.text)
    logger.info("response : "+str(jsonData))
    if(str(jsonData["status"]).__contains__("failed")):
        return "Status :"+str(jsonData["status"])+" Description:"+str(jsonData["error"])
    else:
        return "Status :"+str(jsonData["status"])+" Description:"+str(jsonData["description"])

def getManagerHost(managerNodes):
    for node in managerNodes:
        status = getSpaceServerStatus(os.getenv(node.ip))
    if(status=="ON"):
        managerHost = os.getenv(node.ip)
    return managerHost

# if __name__ == '__main__':
#     verboseHandle.printConsoleWarning("Menu -> Space -> Create new space")
#     try:
#         managerNodes = config_get_manager_node()
#         spaceNodes = config_get_space_hosts()
#         managerHost = getManagerHost(managerNodes)
#         global isMemoryAvailable
#         isMemoryAvailable = False
#         if(len(str(managerHost))>0):
#             managerHostConfig = str(userInputWrapper(Fore.YELLOW+"Proceed with manager host ["+managerHost+"] : "))
#             if(len(str(managerHostConfig))>0):
#                 managerHost = managerHostConfig
#
#             listSpacesOnServer(managerNodes)
#             space_dict_obj = displaySpaceHostWithNumber(managerNodes,spaceNodes)
#
#             global confirmCreateGSC
#             confirmCreateGSC = str(userInputWrapper("Do you want to create GSC ? (y/n) [y] :"+Fore.RESET))
#             if(len(confirmCreateGSC)==0):
#                 confirmCreateGSC='y'
#             if(confirmCreateGSC=='y'):
#                  createGSCInputParam(managerNodes,spaceNodes,managerHost)
#             logger.info("isMemoryAvailable : "+str(isMemoryAvailable))
#             if(confirmCreateGSC=='n' or isMemoryAvailable):
#                 createNewSpaceREST(managerHost)
#     except Exception as e:
#         logger.error("Exception in odsx_space_createnewspace "+str(e))
#         verboseHandle.printConsoleError("Exception in odsx_space_createnewspace "+str(e))
#         handleException(e)
if __name__ == '__main__':
    logger.info("Menu -> Space -> Create new space")
    #loggerTiered.info("Deploy")
    verboseHandle.printConsoleWarning("Menu -> Space -> Create new space")
    try:
        managerNodes = config_get_manager_node()
        logger.info("managerNodes: main"+str(managerNodes))
        global isMemoryAvailable
        isMemoryAvailable = False
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
                global confirmCreateGSC
                confirmCreateGSC = str(readValuefromAppConfig("app.newspace.wanttocreategsc")) #str(userInputWrapper("Do you want to create GSC ? (y/n) [y] :"+Fore.RESET))

                logger.info("isMemoryAvailable : "+str(isMemoryAvailable))
                logger.info("confirmCreateGSC : "+str(confirmCreateGSC))
                if(confirmCreateGSC=='y' or len(str(confirmCreateGSC)) == 0):
                    isMemoryAvailable = createGSCInputParam(managerNodes,spaceNodes,managerHostConfig)
                    confirmCreateGSC='y'
                    if(isMemoryAvailable):
                        createNewSpaceREST(managerHost)
                    else:
                        logger.info("No memeory available double check.")
                        verboseHandle.printConsoleInfo("No memeory available double check.")
                if(confirmCreateGSC=='n'):
                    createNewSpaceREST(managerHost)
            else:
                logger.info("Please check manager server status.")
                verboseHandle.printConsoleInfo("Please check manager server status.")
        else:
            logger.info("No Manager configuration found please check.")
            verboseHandle.printConsoleInfo("No Manager configuration found please check.")

    except Exception as e:
        logger.error("Exception in odsx_space_createspace.py "+str(e))
        verboseHandle.printConsoleError("Exception in odsx_space_createspace.py "+str(e))
        handleException(e)