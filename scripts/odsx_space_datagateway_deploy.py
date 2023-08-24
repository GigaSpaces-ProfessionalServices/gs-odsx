#!/usr/bin/env python3

import os, time
from colorama import Fore
from scripts.logManager import LogManager
import requests, json, math
from scripts.spinner import Spinner
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

def listDataGatewaysOnServer(managerNodes):
    try:
        logger.info("listDataGatewaysOnServer : managerNodes :"+str(managerNodes))
        managerHost=''
        for node in managerNodes:
            status = getSpaceServerStatus(os.getenv(node.ip))
            logger.info("Ip :"+str(os.getenv(node.ip))+"Status : "+str(status))
            if(status=="ON"):
                managerHost = os.getenv(node.ip);
        logger.info("managerHost :"+managerHost)
        response = requests.get("http://"+managerHost+":8090/v2/pus")
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Existing data gateway on cluster:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Name"+Fore.RESET,
                   Fore.YELLOW+"Instances"+Fore.RESET
                   ]
        gs_space_host_dictionary_obj = host_dictionary_obj()
        counter=0
        dataTable=[]
        for data in jsonArray:
            if "data_gateway" not in data["processingUnitType"]:
                continue
            dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                         Fore.GREEN+data["name"]+Fore.RESET,
                         Fore.GREEN+str(data["topology"]["instances"])+Fore.RESET
                         ]
            #gs_space_host_dictionary_obj.add(str(counter+1),str(data["name"]))
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
    return  data

def getSpaceDictObj(managerNodes, spaceNodes):
    try:
        gs_host_details_obj = get_gs_host_details(managerNodes)
        #logger.info("gs_host_details_obj : "+str(gs_host_details_obj))
        counter = 0
        space_dict_obj = host_dictionary_obj()
        #logger.info("space_dict_obj : "+str(space_dict_obj))
        for node in spaceNodes:
            if(gs_host_details_obj.__contains__(str(os.getenv(node.name))) or (str(os.getenv(node.name)) in gs_host_details_obj.values())):
                space_dict_obj.add(str(counter+1),os.getenv(node.name))
                counter=counter+1
        #logger.info("space_dict_obj : "+str(space_dict_obj))
        #verboseHandle.printConsoleWarning("Space hosts lists")
        #headers = [Fore.YELLOW+"No"+Fore.RESET,
        #           Fore.YELLOW+"Host"+Fore.RESET]
        #dataTable=[]
        #for data in range (1,len(space_dict_obj)+1):
        #    dataArray = [Fore.GREEN+str(data)+Fore.RESET,
        #                 Fore.GREEN+str(space_dict_obj.get(str(data)))+Fore.RESET]
        #    dataTable.append(dataArray)
        #printTabular(None,headers,dataTable)
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
        logger.info("No sufficient memory available: Required Memory:"+str(memoryRequiredGSCInBytes)+" Available Memory:"+str(freePhysicalMemorySizeInBytes) +" on host:"+host)
        verboseHandle.printConsoleInfo("No sufficient memory available: Required Memory:"+str(memoryRequiredGSCInBytes)+" Available Memory:"+str(freePhysicalMemorySizeInBytes)+" on host:"+host)
        return False


def convertMemoryGSCToBytes(memoryGSC, type, bsize=1024):
    logger.info("convertMemoryGSCToBytes() memoryGSC"+str(memoryGSC)+" type:"+str(type))
    a = {'k' : 1, 'm': 2, 'g' : 3, 't' : 4, 'p' : 5, 'e' : 6 }
    r = float(memoryGSC)
    for i in range(a[type]):
        r = r * bsize
    logger.info("r :"+str(r))
    return r

def checkIsMemoryAvailableOnHost(managerNodes,memoryGSC,memoryRequiredGSCInBytes):
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
                for i in range(1,int(numberOfGSC)+1):
                    idx = i % len(space_dict_obj)
                    host = space_dict_obj[str(idx)]
                    #host = space_dict_obj.get(str(i))
                    cmd = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh container create --zone "+str(zoneGSC)+" --count "+str(numberOfGSC)+" --memory "+str(memoryGSC)+" "+str(host)+""
                    logger.info("cmd : "+str(cmd))
                    with Spinner():
                        output = executeRemoteCommandAndGetOutput(host, 'root', cmd)
                    logger.info("Extracting .tar file :"+str(output))
                    verboseHandle.printConsoleInfo(str(output))

    except Exception as e:
        handleException(e)

def createGSCInputParam(managerNodes,spaceNodes,managerHostConfig):
    logger.info("createGSC()")
    hostToCreateGSC=""
    #hostToCreateGSC = str(userInputWrapper("Enter space host serial number to create gsc [1] :"+Fore.RESET))

    if(len(hostToCreateGSC)==0):
        hostToCreateGSC="1"
    host = space_dict_obj.get(hostToCreateGSC)

    global numberOfGSC
    global specificHost
    global individualHostConfirm
    individualHostConfirm='n'
    numberOfGSC = str(readValuefromAppConfig("app.datagateway.instances"))
    logger.info("numberofGSC :"+str(numberOfGSC))

    global memoryGSC
    memoryGSC= str(readValuefromAppConfig("app.datagateway.creategsc.gscmemory"))

    global zoneGSC
    zoneGSC = str(readValuefromAppConfig("app.datagateway.creategsc.gsczone"))

    type = memoryGSC[len(memoryGSC)-1:len(memoryGSC)]
    memoryGSCWithoutSuffix = memoryGSC[0:len(memoryGSC)-1]
    logger.info("memoryGSCWithoutSuffix :"+str(memoryGSCWithoutSuffix))
    memoryRequiredGSCInBytes = convertMemoryGSCToBytes(memoryGSCWithoutSuffix,type)
    logger.info("memoryRequiredGSCInBytes :"+str(memoryRequiredGSCInBytes))

    logger.info("space_dict_obj :"+str(space_dict_obj))
    # Creating GSC on each available host
    isMemoryAvailable = checkIsMemoryAvailableOnHost(managerNodes,memoryGSC,memoryRequiredGSCInBytes)
    #if(isMemoryAvailable):
    #isMemoryAvailable = createGSC(managerNodes,memoryGSC,memoryRequiredGSCInBytes,zoneGSC,numberOfGSC,managerHostConfig)
    return isMemoryAvailable


def displaySummaryOfInputParameter():
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleWarning("***Summary***")
    verboseHandle.printConsoleWarning("Want to create GSC :"+str(confirmCreateGSC))
    if(confirmCreateGSC=='y'):
        verboseHandle.printConsoleWarning("Number of GSC :"+str(numberOfGSC))
        verboseHandle.printConsoleWarning("Enter memory to create gsc :"+str(memoryGSC))
        verboseHandle.printConsoleWarning("Enter zone :"+str(zoneGSC))
    verboseHandle.printConsoleWarning("Enter data gateway name :"+str(resourceName))
    verboseHandle.printConsoleWarning("Enter instance count :"+str(instances))


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

def dataPuREST(resourceName,instances):
    logger.info("dataPuREST()")
    try:
        data={
            "name": ""+resourceName+"",
            "instances": ""+ str(instances)+""
        }
        return data
    except Exception as e:
        handleException(e)


def createNewDataGatewayREST(managerHostConfig):
    try:
        logger.info("createNewDataGatewayREST() : managerHostConfig:"+str(managerHostConfig))

        global resourceName
        resourceNameValue = str(readValuefromAppConfig("app.datagateway.name"))
        resourceName = resourceNameValue
        # #str(userInputWrapper("Enter service name ["+resourceNameValue+"] :"+Fore.RESET))

        global instances
        instancesValue = str(readValuefromAppConfig("app.datagateway.instances"))
        instances = instancesValue
        #partitionsValue #str(userInputWrapper("Enter instances ["+partitionsValue+"] :"+Fore.RESET))
        if(len(str(instances))==0):
            instances=instancesValue

        displaySummaryOfInputParameter()
        createConfirm = str(userInputWrapper("Are you sure want to proceed ? (y/n) [y] :"))
        if(len(str(createConfirm))==0):
            createConfirm='y'
        if(createConfirm=='y'):
            if(confirmCreateGSC == 'y'):
                createGSC(memoryGSC,zoneGSC,numberOfGSC,managerHostConfig,individualHostConfirm)
            data = dataPuREST(resourceName,instances)
            headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

            response = requests.post("http://"+managerHostConfig+":8090/v2/data-gateway?name="+str(resourceName)+"&instances="+str(instances),data=json.dumps(data),headers=headers)
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

def validateResponseGetDescription(responseCode):
    try:
        logger.info("validateResponse() "+str(responseCode))
        response = requests.get("http://"+managerHost+":8090/v2/requests/"+str(responseCode))
        jsonData = json.loads(response.text)
        logger.info("response : "+str(jsonData))
        if(str(jsonData["status"]).__contains__("failed")):
            return "Status :"+str(jsonData["status"])+" Description:"+str(jsonData["error"])
        else:
            return "Status :"+str(jsonData["status"])+" Description:"+str(jsonData["description"])
    except Exception as e:
        logger.error("Error in response data")#handleException(e)

def getManagerHost(managerNodes):
    for node in managerNodes:
        status = getSpaceServerStatus(os.getenv(node.ip))
    if(status=="ON"):
        managerHost = os.getenv(node.ip)
    return managerHost

if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Space -> Data Gateway -> Deploy")
    try:
        managerNodes = config_get_manager_node()
        global isMemoryAvailable
        isMemoryAvailable = False
        if(len(str(managerNodes))>0):
            spaceNodes = config_get_space_hosts()
            managerHost = getManagerHost(managerNodes)
            if(len(str(managerHost))>0):
                managerHostConfig = managerHost
                listDataGatewaysOnServer(managerNodes)
                space_dict_obj = getSpaceDictObj(managerNodes,spaceNodes)
                global confirmCreateGSC
                confirmCreateGSC = str(readValuefromAppConfig("app.datagateway.wanttocreategsc"))

                if(confirmCreateGSC=='y' or len(str(confirmCreateGSC)) == 0):
                    isMemoryAvailable = createGSCInputParam(managerNodes,spaceNodes,managerHostConfig)
                    confirmCreateGSC='y'
                    if(isMemoryAvailable):
                        createNewDataGatewayREST(managerHost)
                    else:
                        logger.info("No memeory available double check.")
                        verboseHandle.printConsoleInfo("No memory available double check.")
                if(confirmCreateGSC=='n'):
                    createNewDataGatewayREST(managerHost)
            else:
                logger.info("Please check manager server status.")
                verboseHandle.printConsoleInfo("Please check manager server status.")
        else:
            logger.info("No Manager configuration found please check.")
            verboseHandle.printConsoleInfo("No Manager configuration found please check.")

    except Exception as e:
        logger.error("Exception in odsx_space_datagateway_deploy.py "+str(e))
        verboseHandle.printConsoleError("Exception in odsx_space_datagateway_deploy.py "+str(e))
        handleException(e)