#!/usr/bin/env python3

import os
import time

import json
import math
import requests
from colorama import Fore
from requests.auth import HTTPBasicAuth

from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_db2feeder_utilities import getPasswordByHost, getUsernameByHost
from utils.odsx_keypress import userInputWrapper
from utils.odsx_print_tabular_data import printTabular

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
    response = requests.get("http://"+str(managerHost)+":8090/v2/pus/"+str(puName),auth = HTTPBasicAuth(username,password))
    jsonArray = json.loads(response.text)
    statusAndType.append(jsonArray["status"])
    statusAndType.append(jsonArray["processingUnitType"])
    return statusAndType

def listSpacesOnServer(managerHost):
    response = requests.get("http://"+managerHost+":8090/v2/spaces",auth = HTTPBasicAuth(username,password))
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

def get_gs_host_details(managerHost):
    logger.info("get_gs_host_details()")
    response = requests.get('http://'+managerHost+':8090/v2/hosts', headers={'Accept': 'application/json'},auth = HTTPBasicAuth(username,password))

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

def displaySpaceHostWithNumber(managerHost, spaceNodes):
    try:
        logger.info("displaySpaceHostWithNumber() managerNodes :"+str(managerHost)+" spaceNodes :"+str(spaceNodes))
        gs_host_details_obj = get_gs_host_details(managerHost)
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
    response = requests.get("http://"+managerHost+":8090/v2/hosts/"+host+"/statistics/os", headers={'Accept': 'application/json'},auth = HTTPBasicAuth(username,password))
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
            response = requests.post("http://"+managerHostConfig+":8090/v2/containers",data=json.dumps(data),headers=headers,auth = HTTPBasicAuth(username,password))
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

    #global space_dict_obj
    #space_dict_obj = displaySpaceHostWithNumber(managerNodes,spaceNodes)
    '''
    hostToCreateGSC = str(userInputWrapper("Enter space host serial number to create gsc [1] :"+Fore.RESET))
    if(len(hostToCreateGSC)==0):
        hostToCreateGSC="1"
    host = space_dict_obj.get(hostToCreateGSC)
    '''
    global numberOfGSC
    numberOfGSC = str(userInputWrapper("Enter number of GSC per host [2] :"+Fore.RESET))
    if(len(str(numberOfGSC))==0):
        numberOfGSC=2
    logger.info("numberofGSC :"+str(numberOfGSC))

    global memoryGSC
    memoryGSC = str(userInputWrapper("Enter memory to create gsc [12g] :"+Fore.RESET))
    if(len(memoryGSC)==0):
        memoryGSC="12g"

    global zoneGSC
    zoneGSC = str(userInputWrapper("Enter zone :"+Fore.RESET))
    while(len(str(zoneGSC))==0):
        zoneGSC = str(userInputWrapper("Enter zone :"+Fore.RESET))

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
    if(confirmCreateGSC=='y'):
        verboseHandle.printConsoleWarning("Number of GSC per host :"+str(numberOfGSC))
        verboseHandle.printConsoleWarning("Enter memory to create gsc :"+str(memoryGSC))
        verboseHandle.printConsoleWarning("Enter zone :"+str(zoneGSC))
    verboseHandle.printConsoleWarning("Enter space name :"+spaceName)
    verboseHandle.printConsoleWarning("Build globally over the cluster (y/n) :"+str(isBuildGlobally))
    verboseHandle.printConsoleWarning("Enter partitions :"+str(partitions))
    verboseHandle.printConsoleWarning("SLA [HA] ? (y/n) :"+str(str(backUpRequired)))


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
                    logger.info("Unable to deploy :"+str(status))
                    verboseHandle.printConsoleInfo("Unable to deploy : "+str(status))
            else:
                logger.info("Unable to deploy :"+str(deployResponseCode))
                verboseHandle.printConsoleInfo("Unable to deploy : "+str(deployResponseCode))


def createNewSpaceREST(managerHostConfig):
    logger.info("createNewSpaceREST() : managerHostConfig:"+str(managerHostConfig))
    #confirmCreateSpace = #str(userInputWrapper("Do you want to create space ? (y/n) [y] :"+Fore.RESET))
    #if(len(confirmCreateSpace)==0):
    confirmCreateSpace='y'
    if(confirmCreateSpace=='y'):
        global spaceName
        spaceName = str(readValuefromAppConfig("app.newspace.name"))#str(userInputWrapper("Enter space name  [mySpace] :"+Fore.RESET))
        #if(len(str(spaceName))==0):
        #    spaceName="mySpace"

        global isBuildGlobally
        isBuildGlobally = str(readValuefromAppConfig("app.newspace.createglobally"))#str(userInputWrapper("Build globally over the cluster (y/n) [y] :"+Fore.RESET))
        #if(len(str(isBuildGlobally))==0):
        #    isBuildGlobally='y'

        global partitions
        partitions = str(readValuefromAppConfig("app.newspace.partitions"))#str(userInputWrapper("Enter partitions [1] :"+Fore.RESET))
        #if(len(str(partitions))==0):
        #    partitions="1"

        global backUpRequired
        backUpRequired = str(readValuefromAppConfig("app.newspace.ha"))#str(userInputWrapper("SLA [HA] ? (y/n) [y] :"+Fore.RESET))
        if(len(str(backUpRequired))==0 or backUpRequired=='y'):
            backUpRequired='true'
        if(str(backUpRequired)=='n'):
            backUpRequired='false'
        
        displaySummaryOfInputParameter()
        
        createConfirm = str(userInputWrapper("Are you sure want to proceed ? (y/n) [y] :"))
        if(len(str(createConfirm))==0):
            createConfirm='y'
        if(confirmCreateGSC=='y'):
            createGSC(memoryGSC,zoneGSC,numberOfGSC,managerHostConfig)
        if(isBuildGlobally=='y'):
            #for i in range(1,len(space_dict_obj)+1):
            #    host = space_dict_obj.get(str(i))
            logger.info("http://"+managerHostConfig+":8090/v2/spaces?name="+spaceName+"&partitions="+partitions+"&backups="+backUpRequired)
            #print("http://"+managerHostConfig+":8090/v2/spaces?name="+spaceName+"&partitions="+partitions+"&backups="+backUpRequired)
            response = requests.post("http://"+managerHostConfig+":8090/v2/spaces?name="+spaceName+"&partitions="+partitions+"&backups="+backUpRequired,auth = HTTPBasicAuth(username,password))
            proceedForValidateResponse(response)
        elif(isBuildGlobally=='n'):
            response = requests.post("http://"+managerHostConfig+":8090/v2/spaces?name="+spaceName+"&partitions="+partitions+"&backups="+backUpRequired,auth = HTTPBasicAuth(username,password))
            proceedForValidateResponse(response)
            verboseHandle.printConsoleInfo("Space "+spaceName+" created.")

def validateResponseGetDescription(responseCode):
    logger.info("validateResponse() "+str(responseCode))
    response = requests.get("http://"+managerHost+":8090/v2/requests/"+str(responseCode),auth = HTTPBasicAuth(username,password))
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

if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Space -> Create new space")
    username = ""
    password = ""
    appId=""
    safeId=""
    objectId=""
    try:
        appId = str(readValuefromAppConfig("app.space.security.appId")).replace('"','')
        safeId = str(readValuefromAppConfig("app.space.security.safeId")).replace('"','')
        objectId = str(readValuefromAppConfig("app.space.security.objectId")).replace('"','')
        logger.info("appId : "+appId+" safeID : "+safeId+" objectID : "+objectId)
        managerNodes = config_get_manager_node()
        spaceNodes = config_get_space_hosts()
        managerHost = getManagerHost(managerNodes)
        isMemoryAvailable=''
        if(len(str(managerHost))>0):
            username = str(getUsernameByHost(managerHost,appId,safeId,objectId))
            password = str(getPasswordByHost(managerHost,appId,safeId,objectId))
            #managerHostConfig = str(userInputWrapper(Fore.YELLOW+"Proceed with manager host ["+managerHost+"] : "))
            managerHostConfig = managerHost
            if(len(str(managerHostConfig))>0):
                managerHost = managerHostConfig

            listSpacesOnServer(managerHost)
            global space_dict_obj
            space_dict_obj = displaySpaceHostWithNumber(managerHost,spaceNodes)

            global confirmCreateGSC
            confirmCreateGSC = str(readValuefromAppConfig("app.newspace.wanttocreategsc"))#str(userInputWrapper("Do you want to create GSC ? (y/n) [y] :"+Fore.RESET))
            #if(len(confirmCreateGSC)==0):
            #    confirmCreateGSC='y'
            #if(confirmCreateGSC=='y'):
            #    isMemoryAvailable = createGSCInputParam(managerNodes,spaceNodes,managerHost)
            #logger.info("isMemoryAvailable : "+str(isMemoryAvailable))
            #if(confirmCreateGSC=='n' or isMemoryAvailable):
            createNewSpaceREST(managerHost)
    except Exception as e:
        logger.error("Exception in odsx_space_createnewspace "+str(e))
        verboseHandle.printConsoleError("Exception in odsx_space_createnewspace "+str(e))
        handleException(e)