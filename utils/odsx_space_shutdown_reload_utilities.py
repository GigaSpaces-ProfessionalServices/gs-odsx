# to remove space
import argparse
from asyncore import read
from logging import exception
import os
from shutil import ExecError
import sys
import time
from utils.ods_space import getAllObjPrimaryCount, verifyPrimaryBackupObjCount
from utils.odsx_dataengine_utilities import getAllFeeders
import pexpect
from utils.ods_app_config import readValuefromAppConfig
from utils.odsx_print_tabular_data import printTabular
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_manager_node, config_get_nb_list, config_get_space_hosts_list
from colorama import Fore
from utils.ods_validation import getSpaceServerStatus
from scripts.spinner import Spinner
from utils.ods_ssh import executeRemoteCommandAndGetOutput 
import requests, json
from requests.auth import HTTPBasicAuth

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR
    BLUE = '\033[94m'
    BOLD = '\033[1m'


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


def shutdownSpaceServers(user,isSecure=False):
    logger.info("shutdownSpaceServers() : start")
    spaceHosts = config_get_space_hosts_list()
    logger.debug("spaceHosts : "+str(spaceHosts))
    for host in spaceHosts:
        spaceHost = os.getenv(host)
        argsString='scripts/odsx_servers_space_stop.py m --host '+spaceHost+' -u '+user
        if (isSecure==True):
            argsString='scripts/odsx_security_servers_space_stop.py m --host '+spaceHost+' -u '+user
        logger.info(argsString)
        os.system('python3 scripts/servers_manager_scriptbuilder.py '+argsString)
    logger.info("shutdownSpaceServers() : end") 

def killContainer(managerHost, containerId,isSecure=False,username=None,password=None):
    logger.info("killContainer() : start")
    killContainerURL = 'http://' + managerHost + ':8090/v2/containers/'+containerId
    if(isSecure==True and username is not None and password is not None):
        response = requests.delete(killContainerURL,auth = HTTPBasicAuth(username, password))
    else:
        response = requests.delete(killContainerURL)
    logger.debug("killContainer() response : "+str(response))
    logger.info("killContainer() : end")
    if(response.status_code==202):
        return True
    return False


def undeployProcessingUnit(managerHost, puId,isSpace,isSecure=False,username=None,password=None):
    logger.info("undeployProcessingUnit() : start")
    puId=str(puId)
    logger.info("undeployProcessingUnit() : puId -> "+puId)
    strDrainMode = readValuefromAppConfig("app.tieredstorage.drainmode")
    strDrainMode= str(strDrainMode)
    strDrainTimeout = readValuefromAppConfig("app.tieredstorage.drainTimeout")
    strDrainTimeout = str(strDrainTimeout)
    
    undeployURL = 'http://' + managerHost + ':8090/v2/pus/'+puId+'?keepFile=true'
    if(isSpace==True):
        undeployURL+="&drainMode="+strDrainMode+"&drainTimeout="+strDrainTimeout

    if(isSecure==True and username is not None and password is not None):
        #print("in if")
        #print("undeployURL ->"+str(undeployURL))
        response = requests.delete(undeployURL,auth = HTTPBasicAuth(username, password))
    else:
        #print("in else")
        response = requests.delete(undeployURL)
    logger.info("undeployProcessingUnit() response : "+str(response))
    
    #print("response.status_code ------------undeployProcessingUnit=>"+str(response.status_code))
    if(response.status_code==202):
        
        undeployResponseCode = str(response.content.decode('utf-8'))
        status = validateResponse(managerHost,undeployResponseCode,isSecure,username,password)
        with Spinner():
            while(status.casefold() != 'successful'):
                time.sleep(2)
                status = validateResponse(managerHost,undeployResponseCode,isSecure,username,password)
                verboseHandle.printConsoleInfo("Undeploy  : "+str(puId)+"   Status : "+str(status))
        verboseHandle.printConsoleInfo(" Undeploy  : "+str(puId)+"   Status : "+str(status))
        
        logger.info("undeployProcessingUnit() : end")
        return True
    logger.info("undeployProcessingUnit() : end")
    return False

def validateResponse(managerHost,responseCode,isSecure=False,username=None,password=None):
    logger.info("validateResponse() "+str(responseCode))
    try:
        if(isSecure==True and username is not None and password is not None):
            response = requests.get("http://"+managerHost+":8090/v2/requests/"+str(responseCode),auth = HTTPBasicAuth(username,password))
        else:
            response = requests.get("http://"+managerHost+":8090/v2/requests/"+str(responseCode))
        jsonData = json.loads(response.text)
        logger.info("response : "+str(jsonData))
        return str(jsonData["status"])
    except Exception as e:
        handleException(e)

def undeploySpace(managerHost, statefulPUList,isSecure=False,username=None,password=None):
    logger.info("undeploySpace() : start")
    verboseHandle.printConsoleInfo("Undeploying space.............")
    statefulPUMsg = ''
    logger.info("statefulPUList => "+str(statefulPUList))
    for name in statefulPUList:
        isUndeployed = undeployProcessingUnit(managerHost,name,True,isSecure,username,password)
        if(isUndeployed==True):
            statefulPUMsg+= "Space '"+str(name)+"' is undeployed successfully!\n"
    
    verboseHandle.printConsoleInfo("Spaces are undeployed successfully!!")
    logger.info("undeploySpace() : end")
    return statefulPUMsg



def undeployMicroservices(managerHost, puList, consulServiceList,isSecure=False,username=None,password=None):
    logger.info("undeployMicroservices() : start")
    verboseHandle.printConsoleInfo("Undeploying microservices.............")
    isServiceExist=False
    puMsg = ''
    
    for pu in puList:
        name = str(pu['name'])
        if(consulServiceList.__contains__(str(name))):
            isServiceExist = True
            instancesList = pu['instances']
            isUndeployed = undeployProcessingUnit(managerHost,name,False,isSecure,username,password)
            
            if(isUndeployed==True):
                puMsg+= "Service '"+str(name)+"' is undeployed successfully!\n"
                if(len(instancesList)>0):
                    for instance in instancesList:
                        containerId = getContainerIdForInstance(managerHost,instance,isSecure,username,password)
                        isContainerKilled = killContainer(managerHost, str(containerId),isSecure,username,password)
                        if(isContainerKilled==True):
                            puMsg+= "Service Container '"+str(containerId)+"' conataining instantace '"+str(instance)+"' is killed successfully!\n"
    
    if(isServiceExist==True):
        verboseHandle.printConsoleInfo("Microservices are undeployed successfully!!")
    else:
        verboseHandle.printConsoleInfo("Microservice does not exist!")

    logger.info("undeployMicroservices() : end")
    return puMsg

def undeployFeeders(isSecure=False):
    logger.info("undeployFeeders() : start")

    feederMsg = ''
    #print("statefulPUList="+str(statefulPUList))
    
    feederPuList = getAllFeeders()
    isDB2Feeder = False
    isMSSQLFeeder = False
    isAdabasFeeder = False
    isKafkaConsumer = False
    for dataArr in feederPuList:
        name = dataArr[1]
        
        #print ("name -"+str(name))
        if(str(name).casefold().__contains__("db2")):
            isDB2Feeder = True
        if(str(name).casefold().__contains__("mssql")):  
            isMSSQLFeeder = True
        if(str(name).casefold().__contains__("adabasconsumer")):  
            isAdabasFeeder = True
        if(str(name).casefold().__contains__("kafka")):  
            isKafkaConsumer = True    
        
    if(isDB2Feeder == True):
        verboseHandle.printConsoleInfo("Undeploying DB2 Feeders.............")
        cmd = "python3 scripts/odsx_dataengine_db2-feeder_remove-undeploy.py"
        if(isSecure==True):
            cmd = "python3 scripts/odsx_security_dataengine_db2-feeder_remove-undeploy.py"
        child = pexpect.spawn(cmd)
        child.expect("Proceeding with manager host.*")
        child.sendline('\r')

        child.expect(".*For all above PUs.*")
        child.sendline('\r')

        child.expect(".*Enter drain mode.*")
        child.sendline('\r')

        child.expect("Do you want to remove gsc?.*")
        child.sendline('\r')
        child.interact()
        child.close()

        verboseHandle.printConsoleInfo("DB2 Feeders undeployed successfully!!")
        
    if(isMSSQLFeeder == True):
        print()
        verboseHandle.printConsoleInfo("Undeploying MS-SQL Feeders.............")
        cmd = "python3 scripts/odsx_dataengine_mssql-feeder_remove-undeploy.py"
        if(isSecure==True):
            cmd = "python3 scripts/odsx_security_dataengine_mssql-feeder_remove-undeploy.py"
        child = pexpect.spawn(cmd)
        child.expect("Proceeding with manager host.*")
        child.sendline('\r')

        child.expect(".*For all above PUs.*")
        child.sendline('\r')

        child.expect(".*Enter drain mode.*")
        child.sendline('\r')

        child.expect("Do you want to remove gsc?.*")
        child.sendline('\r')
        child.interact()
        child.close()

        verboseHandle.printConsoleInfo("MS-SQL Feeders undeployed successfully!!")

    if(isKafkaConsumer == True):
        print()
        verboseHandle.printConsoleInfo("Undeploying Kafka consumer Feeders.............")
        cmd = "python3 scripts/odsx_dataengine_kafka-consumer_undeploy.py"
        if(isSecure==True):
            cmd = "python3 scripts/odsx_security_dataengine_kafka-consumer_undeploy.py"
        child = pexpect.spawn(cmd)
        child.expect("Proceeding with manager host.*")
        child.sendline('\r')

        child.expect(".*For all above PUs.*")
        child.sendline('\r')

        child.expect(".*Enter drain mode.*")
        child.sendline('\r')

        child.expect("Do you want to remove gsc?.*")
        child.sendline('\r')
        child.interact()
        child.close()
        verboseHandle.printConsoleInfo("Kafka feeders undeployed successfully!!")

    if(isAdabasFeeder == True): 
        print()
        verboseHandle.printConsoleInfo("Undeploying Adabas Feeders.............")
        cmd = "python3 scripts/odsx_dataengine_adabas-service_remove.py"
        if(isSecure==True):
            cmd = "python3 scripts/odsx_security_dataengine_kafka-consumer_undeploy.py"
        child = pexpect.spawn(cmd)
        child.expect("Proceeding with manager host.*")
        child.sendline('\r')

        child.expect(".*For all above PUs.*")
        child.sendline('\r')

        child.expect(".*Enter drain mode.*")
        child.sendline('\r')

        child.expect("Do you want to remove gsc?.*")
        child.sendline('\r')
        child.interact()
        child.close()
        verboseHandle.printConsoleInfo("Adabas undeployed successfully!!")
                    

    logger.info("undeployFeeders() : end")
    return feederMsg

def getProcessingUnitList(managerHost,isSecure=False,username=None,password=None):
    logger.info("getProcessingUnitList() : start")
    logger.debug("managerHost = >"+str(managerHost))
    if(isSecure==True and username is not None and password is not None):
        response = requests.get('http://' + managerHost + ':8090/v2/pus',auth = HTTPBasicAuth(username, password))
    else:
        response = requests.get('http://' + managerHost + ':8090/v2/pus')
    logger.debug("getProcessingUnitList() response: "+str(logger.debug("response")))
    if response.status_code == 200:
        puList = json.loads(response.text)


    logger.info("getProcessingUnitList() : end")
    return puList


def getServiceListFromConsul():
    logger.info("getServiceListFromConsul() : start")
    consulHost = getNBServerHost()
    consulServiceList = []
    response = requests.get('http://' + str(consulHost) + ':8500/v1/catalog/services')
    if response.status_code == 200:
        services = json.loads(response.text)
        for service in services:
            if(len(str(service))>0):
                consulServiceList.append(str(service))
    logger.debug("consulServiceList : "+str(consulServiceList))
    logger.info("getServiceListFromConsul() : end")
    return consulServiceList


def displayPus(puList):
    logger.info("displayPus() : start")
    headers = [Fore.YELLOW + "Name" + Fore.RESET,
                Fore.YELLOW + "Type" + Fore.RESET,
                Fore.YELLOW + "State" + Fore.RESET,
                ]

    data = [] 
    if(len(puList)>0):
        for pu in puList:
            name = pu['name']
            processingUnitType = pu['processingUnitType']
            
            status = pu['status']
            if(str(status)=='intact'):
                dataArray = [Fore.GREEN + str(name) + Fore.RESET,
                Fore.GREEN + str(processingUnitType) + Fore.RESET,
                Fore.GREEN + str(status)+ Fore.RESET,
                ]
            else:
                dataArray = [Fore.GREEN + str(name) + Fore.RESET,
                Fore.GREEN + str(processingUnitType) + Fore.RESET,
                Fore.RED + str(status)+ Fore.RESET,
                ]
                
            data.append(dataArray)  

    printTabular(None, headers, data)
    logger.info("displayPus() : end")
    
 

def printSuccessSummary(puList):
    logger.info("printSuccessSummary() : start")
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleWarning("***Summary***")
    displayPus(puList)
    
    print(Fore.GREEN+"All processing units are intact"+Fore.RESET)
    print(Fore.GREEN+"Tier storage location is not full."+
            Fore.RESET)
    validateSpaceParitions = readValuefromAppConfig("app.space.shutdown.validateTierSpacePartitions")
    logger.info("validateSpaceParitions => "+str(validateSpaceParitions))
    if(validateSpaceParitions is not None and validateSpaceParitions!='None' and validateSpaceParitions == True):
        
        print(Fore.GREEN+"All primary partitions are stable."+
            Fore.RESET)
    
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    logger.info("printSuccessSummary() : end")


def validateTierStorageFreeSpace(managerHost,tierSpace,isSecure=False,username=None,password=None):
    logger.info("validateTierStorageFreeSpace() : start")
    verboseHandle.printConsoleInfo("Validating Tier Storage location.............")
    headers = {'Accept': 'application/json'}

    url = f"http://{managerHost}:8090/v2/spaces/{tierSpace}/instances"
    if(isSecure==True and username is not None and password is not None):
        response = requests.get(url, headers=headers, auth = HTTPBasicAuth(username, password), verify=False)
    else:
        response = requests.get(url, headers=headers, verify=False)
    spaceHosts = config_get_space_hosts_list()
    logger.debug("spaceHosts : "+str(spaceHosts))
    hostList = []
    for item in response.json():
        spaceHost = item['hostId']
        if (hostList.__contains__(spaceHost)==False):
            hostList.append(spaceHost)


    #print("hostList =>"+str(hostList));
    for host in hostList:   
        tierStorageLocation = "/dbagigadata/tiered-storage"
        #print("tierStorageLocation==="+str(tierStorageLocation))
        checkFileSizeCmd = "df -ha "+tierStorageLocation
        fileSizeOutput = executeRemoteCommandAndGetOutput(host, 'root', checkFileSizeCmd)
        device, size, used, available, percent, mountpoint = \
        fileSizeOutput.split("\n")[1].split()
        strPercent = str(percent)
        #print("strPercent=>"+strPercent)
        strPercent = strPercent[:-1]
        #print("strPercent=> 2=> "+strPercent+"..............")
        intPercent = int(str(strPercent))
        isValid = True
        logger.info("intPercent() :"+str(intPercent))
        if(intPercent > 90):
            isValid =  False
            break
    logger.info("isValid :"+str(isValid))    
    logger.info("validateTierStorageFreeSpace() : end")
    return isValid
     
 
def getContainerIdForInstance(managerHost,instanceId,isSecure=False,username=None,password=None):
    logger.info("mapInstancesContainers() : start")
    if(isSecure==True and username is not None and password is not None):
        response = requests.get("http://"+managerHost+":8090/v2/containers",auth = HTTPBasicAuth(username, password))
    else:
        response = requests.get("http://"+managerHost+":8090/v2/containers")
    jsonContainers = json.loads(response.text)
    
    for container in jsonContainers:
        containerId = container['id']
        instancesList = container['instances']
        if(len(instancesList)>0):
            #dict[str(instancesList[0])]=containerId
            if(str(instancesList[0]) == str(instanceId)):
                return containerId
    
    logger.info("mapInstancesContainers() : end")
    return dict


def validatePUStatus(puList):
    logger.info("validatePUStatus() : start")
    verboseHandle.printConsoleInfo("Validating PU status.............")
    isValid = True
    try:
        if(len(puList)>0):
            for pu in puList:
                status = pu['status']
                if(status != 'intact'):
                    isValid =  False
                    break
            
            
        else:
            logger.info("Processing units not found")
        logger.info("isValid : "+str(isValid))
        logger.info("validatePUStatus() : end")   
    except ExecError as e:
        handleException(e)    
        return False    
    return isValid
    
def getManagerHost():
    managerNodes = config_get_manager_node()
    logger.info("getManagerHost() : start")  
    managerHost=""
    status=""
    try:
        logger.info("managerNodes :"+str(managerNodes))
        for node in managerNodes:
            status = getSpaceServerStatus(os.getenv(node.ip))
            if(status=="ON"):
                managerHost = str(os.getenv(node.ip))
                break;
        logger.info("managerHost : "+str(managerHost))  
        logger.info("getManagerHost() : end")  
        return managerHost      
    except Exception as e:
        handleException(e)


def getNBServerHost():
    logger.info("getManagerHost() : start")
    
    nodeList = config_get_nb_list()
    logger.debug("nodeList : "+str(nodeList))
    nodes=""
    for node in nodeList:
        if(str(node.role).casefold().__contains__('applicative')):
            if(len(nodes)==0):
                nodes = os.getenv(node.ip)
                break;
    logger.info("nodes : "+str(nodes))
    logger.info("getManagerHost() : end")
    return str(nodes)

def validateBeforeShutdown(managerHost,puList,tierSpace,isSecure=False,username=None,password=None):
    logger.info("validateBeforeShutdown() :  start")
    errMsg = ''
    validPUState = validatePUStatus(puList)
    
    validTierStorageSpace = validateTierStorageFreeSpace(managerHost,tierSpace,isSecure,username,password)
    #print("validTierStorageSpace ="+str(validTierStorageSpace))
    #print("validPUState ="+str(validPUState))
    if(validPUState==False):
        errMsg = "Processing units are not Intact"
    if(validTierStorageSpace==False):
        errMsg = "Tier storage location does not have enough space"
       
      
    logger.info("validateBeforeShutdown() :  end")
    return errMsg

def validateTierSpace(managerHost,tierSpace,isSecure=False,username=None,password=None):
    logger.info("validateTierSpace() :  start")
    verboseHandle.printConsoleInfo("Validating Tier Space Partitions.............")
    errMsg = ''
      
    count = 0
    isPrimaryStable = True

        
    totalPrimaryCount = getAllObjPrimaryCount(managerHost, tierSpace,isSecure,username,password)
    verboseHandle.printConsoleInfo("Verifying primary count.........")
    while(count < 3):
        print("totalPrimaryCount -> "+str(totalPrimaryCount))
        count+=1
        tempPrimaryCount, totalPrimaryCount =totalPrimaryCount, getAllObjPrimaryCount(managerHost, tierSpace,isSecure,username,password)
        if(tempPrimaryCount != totalPrimaryCount):
            isPrimaryStable = False
        else: 
            isPrimaryStable = True

        time.sleep(5)

    if(isPrimaryStable == False):
        errMsg = "Primary partitions are not stable\n"
    
    verboseHandle.printConsoleInfo("Validating Primary and Backup count.........")
    isPrimaryBackupSame = verifyPrimaryBackupObjCount(managerHost, tierSpace,isSecure,username,password)
    
    if(isPrimaryBackupSame == False):
        errMsg += "Primary and Backup records are not same\n"
                
    logger.info("validateBeforeShutdown() :  end")
    return errMsg



def checkSpaceStatus(managerHost,isSecure=False,username=None,password=None):

    allSpaceURL = 'http://' + managerHost + ':8090/v2/spaces' 
    allPUsURL = 'http://' + managerHost + ':8090/v2/pus'
    
    spaceList = []
    if(isSecure==True and username is not None and password is not None):
        response1 = requests.get(allSpaceURL,auth = HTTPBasicAuth(username, password))
    else:
        response1 = requests.get(allSpaceURL)
    if response1.status_code == 200:
        spaceList = json.loads(response1.text)

    intactSpaceList = []
    print("intactSpaceList=>"+str(len(intactSpaceList)))
    with Spinner():
        verboseHandle.printConsoleInfo("Waiting for space to be intact..........")
        while(len(spaceList) != len(intactSpaceList)):
            #verboseHandle.printConsoleInfo("Waiting for space to be intact..........")
            intactSpaceList = []
            if(isSecure==True and username is not None and password is not None):
                response = requests.get(allPUsURL,auth = HTTPBasicAuth(username, password))
            else:
                response = requests.get(allPUsURL)
            if response.status_code == 200:
                puList = json.loads(response.text)
                for pu in puList:
                    name = pu['name']
                    processingUnitType = pu['processingUnitType']
                    status = pu['status']
                    if(str(processingUnitType).casefold()=="stateful" and str(status).casefold()=="intact"):
                        intactSpaceList.append(pu)
    logger.info("reloadSpaces() : end")
    return True  


    
    
    #except Exception as e:
    #    logger.error("error occurred in shutdownServers()")

def checkSpacePrimaryStatus(managerHost,isSecure=False,username=None,password=None):

    tierStorageSpace = readValuefromAppConfig("app.tieredstorage.pu.spacename")
    spaceName = readValuefromAppConfig("app.spacejar.space.name")

    strSpaceMaxPartitions = readValuefromAppConfig("app.spacejar.pu.partitions")
    spaceMaxPartitions = int(strSpaceMaxPartitions)

    strTierSpaceMaxPartitions = readValuefromAppConfig("app.tieredstorage.gsc.partitions")
    tierSpaceMaxPartitions = int(strTierSpaceMaxPartitions)
    
    isAllTierPrimariesUp = False
    isAllSpacePrimariesUp = False
    with Spinner():
        verboseHandle.printConsoleInfo("waiting for all primary partitions of Tier storage space..")
        while(isAllTierPrimariesUp == False):
            isAllTierPrimariesUp = checkSpacePrimaryParitions(managerHost,tierStorageSpace,tierSpaceMaxPartitions,isSecure, username,password)
    
    with Spinner():
        verboseHandle.printConsoleInfo("waiting for all primary partitions of space..")
        while(isAllSpacePrimariesUp == False):
            isAllSpacePrimariesUp = checkSpacePrimaryParitions(managerHost,spaceName,spaceMaxPartitions,isSecure, username,password)

    print(bcolors.BLUE + bcolors.BOLD + "All primary partitions of space are up!"+bcolors.RESET)
    
def checkSpacePrimaryParitions(managerHost,spaceName, maxPartitions,isSecure=False,username=None,password=None):
    
    
    if(len(spaceName)>0):
        spacePrimaryParitions = []
        spacePrimaryList = []
        for i in range(maxPartitions):
            i += 1;
            tempPartitionId = spaceName+"~"+str(i)+"_1"
            spacePrimaryParitions.append(tempPartitionId)

        spaceURL = 'http://' + managerHost + ':8090/v2/spaces/'+spaceName
        if(isSecure==True and username is not None and password is not None):
            response = requests.get(spaceURL,auth = HTTPBasicAuth(username, password))
        else:
            response = requests.get(spaceURL)
        if(response.status_code == 200):
            spaceDetails = json.loads(response.text)
            instanceList = spaceDetails['instancesIds']
            #print("spacePrimaryList=>"+str(spacePrimaryList))
            for instanceId in instanceList:
                if(spacePrimaryParitions.__contains__(str(instanceId)) and instanceId not in spacePrimaryList):
                    spacePrimaryList.append(instanceId)
                
                #print("2.   spacePrimaryList=>"+str(spacePrimaryList))
                if(len(spacePrimaryParitions) == len(spacePrimaryList)):
                    return True

                            
def deployTierSpace(isSecure=False):
    logger.info("deployTierSpace(): start")
    verboseHandle.printConsoleInfo("deploying TierSpace..............")
    cmd = "python3 scripts/odsx_tieredstorage_deploy.py"
    if(isSecure==True):
        cmd = "python3 scripts/odsx_security_tieredstorage_deploy.py"
    child = pexpect.spawn(cmd)
    child.expect(".*Are you sure want to proceed.*")
    child.sendline('\r')
    child.interact()
    child.close()
    verboseHandle.printConsoleInfo("TierSpace deployed successfully..............")
    logger.info("deployTierSpace(): end")

def deploySpace(isSecure=False):
    
    logger.info("deploySpace() : start")
    verboseHandle.printConsoleInfo("deploying space..............")
    cmd = "python3 scripts/odsx_space_createspacewithjar.py"
    if(isSecure==True):
        cmd = "python3 scripts/odsx_security_space_createspacewithjar.py"
    child = pexpect.spawn(cmd)
    child.expect(".*Are you sure want to proceed.*")
    child.sendline('\r')
    child.interact()
    child.close()
    verboseHandle.printConsoleInfo("Space is deployed successfully!!")
    logger.info("deploySpace() : end")

def deployFeeders(isSecure=False):
    logger.info("deployFeeders() : start")
    verboseHandle.printConsoleInfo("deploying db2 feeders..............")

    cmd = "python3 scripts/odsx_dataengine_db2-feeder_install-deploy.py"
    if(isSecure==True):
        cmd = "python3 scripts/odsx_security_dataengine_db2-feeder_install-deploy.py"
    child = pexpect.spawn(cmd)
 
    child.expect(".*Are you sure want to proceed.*")
    child.sendline('\r')

    child.interact()
    child.close()
    verboseHandle.printConsoleInfo("db2 feeders are deployed successfully!!")

    verboseHandle.printConsoleInfo("deploying mssql feeders..............")
    cmd = "python3 scripts/odsx_dataengine_mssql-feeder_install-deploy.py"
    if(isSecure==True):
        cmd = "python3 scripts/odsx_security_dataengine_mssql-feeder_install-deploy.py"
    child = pexpect.spawn(cmd)
    child.expect(".*Do you want to create GSC.*")
    child.sendline('\r')

    child.expect(".*Are you sure want to proceed.*")
    child.sendline('\r')

    child.interact()
    child.close()
    verboseHandle.printConsoleInfo("ms-sql feeders are deployed successfully!!")

    """
    verboseHandle.printConsoleInfo("deploying adabas feeders..............")
    cmd = "python3 scripts/odsx_dataengine_mq-connector_adabas-service_install.py"
    if(isSecure==True):
        cmd = "python3 scripts/ods_security_dataengine_mq-connector_adabas-service_install.py"
    child = pexpect.spawn(cmd)
    child.expect(".*Do you want to create GSC.*")
    child.sendline('\r')

    child.expect(".*Are you sure want to proceed.*")
    child.sendline('\r')
    child.interact()
    child.close()
    verboseHandle.printConsoleInfo("adabas feeders are deployed successfully!!")
    """
    """
    verboseHandle.printConsoleInfo("deploying kafka feeders..............")
    cmd = "python3 scripts/odsx_dataengine_mq-connector_kafka-consumer_deploy.py"
    if(isSecure==True):
        cmd = "python3 scripts/odsx_security_dataengine_mq-connector_kafka-consumer_deploy.py"
    child = pexpect.spawn(cmd)
    child.expect(".*Do you want to create GSC.*")
    child.sendline('\r')

    child.expect(".*Are you sure want to proceed.*")
    child.sendline('\r')
    child.interact()
    child.close()     
    verboseHandle.printConsoleInfo("kafka feeders are deployed successfully!!")
    """
    logger.info("deployFeeders() : end")

def deployPU(managerHost,puname,isSecure=False,username=None,password=None):

    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    data = {
        "resource": ""+puname+"",
        "name": ""+puname+".jar"
    }

    if(isSecure==True and username is not None and password is not None):
        response = requests.post('http://' + managerHost + ':8090/v2/pus'
                        ,auth = HTTPBasicAuth(username, password)
                        , data=json.dumps(data)
                        , headers=headers)
    else:
        response = requests.post('http://' + managerHost + ':8090/v2/pus'
                        , data=json.dumps(data)
                        , headers=headers)
    logger.debug("getProcessingUnitList() response: "+str(logger.debug("response")))
    if response.status_code == 202:
        return True
    

def startSpaceServers(user,isSecure=False):
    spaceHosts = config_get_space_hosts_list()
    for host in spaceHosts:
        spaceHost = os.getenv(host)
        argsString='scripts/odsx_servers_space_start.py m --host '+spaceHost+' -u '+user
        if(isSecure==True):
            argsString='scripts/odsx_security_servers_space_start.py m --host '+spaceHost+' -u '+user
        logger.info(argsString)
        os.system('python3 scripts/servers_manager_scriptbuilder.py '+argsString)
    