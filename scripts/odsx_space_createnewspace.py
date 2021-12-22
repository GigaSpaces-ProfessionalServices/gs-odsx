#!/usr/bin/env python3

import os
from colorama import Fore
from scripts.logManager import LogManager
import requests, json, math
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_validation import getSpaceServerStatus
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
    managerHost=''
    for node in managerNodes:
        status = getSpaceServerStatus(node.ip)
        if(status=="ON"):
            managerHost = node.ip;
    response = requests.get("http://"+managerHost+":8090/v2/spaces")
    jsonArray = json.loads(response.text)
    verboseHandle.printConsoleWarning("Existing spaces on cluster:")
    headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
               Fore.YELLOW+"Name"+Fore.RESET,
               Fore.YELLOW+"PU Name"+Fore.RESET,
               Fore.YELLOW+"Partition"+Fore.RESET,
               Fore.YELLOW+"Backup Partition"+Fore.RESET,
               Fore.YELLOW+"Type"+Fore.RESET,
               Fore.YELLOW+"Status"+Fore.RESET
               ]
    gs_space_host_dictionary_obj = host_dictionary_obj()
    counter=0
    dataTable=[]
    for data in jsonArray:
        if(str(data["topology"]["backupsPerPartition"])=="1"):
            isBackup="YES"
        if(str(data["topology"]["backupsPerPartition"])=="0"):
            isBackup="NO"
        statusAndType = getStatusAndTypeOfSpaceOrPU(managerHost,str(data["processingUnitName"]))
        dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                     Fore.GREEN+data["name"]+Fore.RESET,
                     Fore.GREEN+data["processingUnitName"]+Fore.RESET,
                     Fore.GREEN+str(data["topology"]["partitions"])+Fore.RESET,
                     Fore.GREEN+isBackup+Fore.RESET,
                     Fore.GREEN+statusAndType[1]+Fore.RESET,
                     Fore.GREEN+statusAndType[0]+Fore.RESET
                     ]
        gs_space_host_dictionary_obj.add(str(counter+1),str(data["name"]))
        counter=counter+1
        dataTable.append(dataArray)
    printTabular(None,headers,dataTable)
    return gs_space_host_dictionary_obj

def get_gs_host_details(managerNodes):

    for node in managerNodes:
        status = getSpaceServerStatus(node.ip)
        if(status=="ON"):
            managerHostConfig = node.ip;

    response = requests.get('http://'+managerHostConfig+':8090/v2/hosts', headers={'Accept': 'application/json'})

    jsonArray = json.loads(response.text)
    gs_servers_host_dictionary_obj = host_dictionary_obj()
    for data in jsonArray:
        gs_servers_host_dictionary_obj.add(str(data['address']),str(data['address']))
    return gs_servers_host_dictionary_obj

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
    gs_host_details_obj = get_gs_host_details(managerNodes)
    counter = 0
    space_dict_obj = host_dictionary_obj()
    for node in spaceNodes:
        if(gs_host_details_obj.__contains__(str(node.ip))):
            space_dict_obj.add(str(counter+1),node.ip)
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

def createGSC(memoryGSC,zoneGSC,numberOfGSC,managerHostConfig):
    logger.info("createGSC()")
    for i in range(1,len(space_dict_obj)+1):
        host = space_dict_obj.get(str(i))
        #isMemoryAvailable = isMemoryAvailableOnHost(managerNodes,host,memoryGSC,memoryRequiredGSCInBytes)
        #if(isMemoryAvailable):
        data = dataContainerREST(host,zoneGSC,memoryGSC)
        logger.info("data:"+str(data))
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        # creating 2 GSC by def
        for i in range(1,int(numberOfGSC)+1):
            logger.info("numofGSC")
            logger.info("GSC "+str(i+1)+" url : http://"+str(managerHostConfig)+":8090/v2/containers")
            response = requests.post("http://"+managerHostConfig+":8090/v2/containers",data=json.dumps(data),headers=headers)
            logger.info("GSC "+str(i+1)+" response_status_code:"+str(response.status_code))
            if(response.status_code==202):
                logger.info("GSC "+str(i+1)+" created on host :"+str(host))
                #verboseHandle.printConsoleInfo("GSC "+str(i+1)+" created on host :"+str(host))
        #else:
        #    logger.info("No sufficent memory available: Required Memory:"+str(memoryRequiredGSCInBytes)+" Available Memory:"+str(freePhysicalMemorySizeInBytes) +" on host:"+host)
        #    verboseHandle.printConsoleInfo("No sufficent memory available: Required Memory:"+str(memoryRequiredGSCInBytes)+" Available Memory:"+str(freePhysicalMemorySizeInBytes)+" on host:"+host)
        #    return isMemoryAvailable
        verboseHandle.printConsoleInfo("GSC ["+str(numberOfGSC)+"] created on host :"+str(host))

def createGSCInputParam(managerNodes,spaceNodes,managerHostConfig):
    logger.info("createGSC()")
    confirmCreateGSC = str(input("Do you want to create GSC ? (y/n) [y] :"+Fore.RESET))
    if(len(confirmCreateGSC)==0):
        confirmCreateGSC='y'
    if(confirmCreateGSC=='y'):
        global space_dict_obj
        space_dict_obj = displaySpaceHostWithNumber(managerNodes,spaceNodes)
        '''
        hostToCreateGSC = str(input("Enter space host serial number to create gsc [1] :"+Fore.RESET))
        if(len(hostToCreateGSC)==0):
            hostToCreateGSC="1"
        host = space_dict_obj.get(hostToCreateGSC)
        '''
        global numberOfGSC
        numberOfGSC = str(input("Enter number of GSC per host [2] :"+Fore.RESET))
        if(len(str(numberOfGSC))==0):
            numberOfGSC=2
        logger.info("numberofGSC :"+str(numberOfGSC))

        global memoryGSC
        memoryGSC = str(input("Enter memory to create gsc [12g] :"+Fore.RESET))
        if(len(memoryGSC)==0):
            memoryGSC="12g"

        global zoneGSC
        zoneGSC = str(input("Enter zone :"+Fore.RESET))
        while(len(str(zoneGSC))==0):
            zoneGSC = str(input("Enter zone :"+Fore.RESET))

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
            #isMemoryAvailable = createGSC(managerNodes,memoryGSC,memoryRequiredGSCInBytes,zoneGSC,numberOfGSC,managerHostConfig)
        return isMemoryAvailable


def displaySummaryOfInputParameter():
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleWarning("***Summary***")
    verboseHandle.printConsoleWarning("Number of GSC per host :"+str(numberOfGSC))
    verboseHandle.printConsoleWarning("Enter memory to create gsc :"+str(memoryGSC))
    verboseHandle.printConsoleWarning("Enter zone :"+str(zoneGSC))
    verboseHandle.printConsoleWarning("Enter space name :"+spaceName)
    verboseHandle.printConsoleWarning("Build globally over the cluster (y/n) :"+str(isBuildGlobally))
    verboseHandle.printConsoleWarning("Enter partitions :"+str(partitions))
    verboseHandle.printConsoleWarning("SLA [HA] ? (y/n) :"+str(str(backUpRequired)))

def createNewSpaceREST(managerHostConfig):
    logger.info("createNewSpaceREST() : managerHostConfig:"+str(managerHostConfig))
    confirmCreateSpace = str(input("Do you want to create space ? (y/n) [y] :"+Fore.RESET))
    if(len(confirmCreateSpace)==0):
        confirmCreateSpace='y'
    if(confirmCreateSpace=='y'):
        global spaceName
        spaceName = str(input("Enter space name  [mySpace] :"+Fore.RESET))
        if(len(str(spaceName))==0):
            spaceName="mySpace"

        global isBuildGlobally
        isBuildGlobally = str(input("Build globally over the cluster (y/n) [y] :"+Fore.RESET))
        if(len(str(isBuildGlobally))==0):
            isBuildGlobally='y'

        global partitions
        partitions = str(input("Enter partitions [1] :"+Fore.RESET))
        if(len(str(partitions))==0):
            partitions="1"

        global backUpRequired
        backUpRequired = str(input("SLA [HA] ? (y/n) [y] :"+Fore.RESET))
        if(len(str(backUpRequired))==0 or backUpRequired=='y'):
            backUpRequired='true'
        if(str(backUpRequired)=='n'):
            backUpRequired='false'
        
        displaySummaryOfInputParameter()
        
        createConfirm = str(input("Are you sure want to proceed ? (y/n) [y] :"))
        if(len(str(createConfirm))==0):
            createConfirm='y'
        if(createConfirm=='y'):
            createGSC(memoryGSC,zoneGSC,numberOfGSC,managerHostConfig)
        if(isBuildGlobally=='y'):
            for i in range(1,len(space_dict_obj)+1):
                host = space_dict_obj.get(str(i))
                logger.info("http://"+managerHostConfig+":8090/v2/spaces?name="+spaceName+"&partitions="+partitions+"&backups="+backUpRequired)
                response = requests.post("http://"+managerHostConfig+":8090/v2/spaces?name="+spaceName+"&partitions="+partitions+"&backups="+backUpRequired)
                logger.info(str(response.status_code))
                if(response.status_code==202):
                    logger.info("Space "+spaceName+" created.")
            verboseHandle.printConsoleInfo("Space "+spaceName+" created.")

def getManagerHost(managerNodes):
    for node in managerNodes:
        status = getSpaceServerStatus(node.ip)
    if(status=="ON"):
        managerHost = node.ip
    return managerHost

if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Space -> Create new space")
    try:
        managerNodes = config_get_manager_node()
        spaceNodes = config_get_space_hosts()
        managerHost = getManagerHost(managerNodes)
        if(len(str(managerHost))>0):
            managerHostConfig = managerHost
            listSpacesOnServer(managerNodes)
            isMemoryAvailable = createGSCInputParam(managerNodes,spaceNodes,managerHostConfig)
            logger.info("isMemoryAvailable : "+str(isMemoryAvailable))
            if(isMemoryAvailable):
                createNewSpaceREST(managerHostConfig)
    except Exception as e:
        logger.error("Exception in odsx_space_createnewspace "+str(e))
        verboseHandle.printConsoleError("Exception in odsx_space_createnewspace "+str(e))