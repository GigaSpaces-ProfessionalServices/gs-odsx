#!/usr/bin/env python3

import logging
import os
import time
from pathlib import Path

import json
import requests
from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_tieredstorage_updatecachepolicy import handleException
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig, getYamlFilePathInsideFolder
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_scp import scp_upload
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_keypress import userInputWithEscWrapper, userInputWrapper
from utils.odsx_print_tabular_data import printTabular
from utils.odsx_print_tabular_data import printTabularGrid, printTabularGridWrap

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

# TieredStorage log file configuration  ---Starts
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

loggerTiered = setup_logger(os.path.basename(__file__), 'logs/tieredstorage_updatecachepolicy_trace.log')
# TieredStorage log file configuration  ---Ends

timeToSleepForRestart = 30
requestHeader = {'Content-type': 'application/json', 'Accept': 'text/plain'}
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

def listSpacesOnServer(managerHost):
    logger.info("listSpacesOnServer : managerNodes :"+str(managerHost))
    global gs_space_host_dictionary_obj
    try:
        logger.info("managerHost :"+str(managerHost))
        response = requests.get("http://"+str(managerHost)+":8090/v2/spaces")
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

def displayOnlyGSC():
    logger.info("displayOnlyGSC()")
    try:
        response = requests.get("http://"+managerHost+":8090/v2/spaces/"+str(spaceName)+"/instances")
        logger.info("response.text : "+str(response.text))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Instances on cluster:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"ID"+Fore.RESET,
                   Fore.YELLOW+"containerId"+Fore.RESET,
                   Fore.YELLOW+"mode"+Fore.RESET
                   ]
        counter=0
        coupleNumber=0
        backupCounter=0
        primaryCounter=0
        global containerIdHostDict
        global backupContainerDict
        global primaryContainerDict
        global backupSpaceIdDict
        global primarySpaceIdDict
        global spaceIdContainerIdDict
        global spaceIdResponseCodeDict
        global srNoSpaceIdDict
        containerIdHostDict = host_dictionary_obj()
        backupContainerDict = host_dictionary_obj()
        primaryContainerDict = host_dictionary_obj()
        backupSpaceIdDict = host_dictionary_obj()
        primarySpaceIdDict = host_dictionary_obj()
        spaceIdContainerIdDict = host_dictionary_obj()
        spaceIdResponseCodeDict = host_dictionary_obj()
        srNoSpaceIdDict = host_dictionary_obj()
        dataTable=[]
        for data in jsonArray:
            if((counter+1)%2==0): # To display containers based on couple instead of each incremental
                dataArray = [
                    Fore.GREEN+str('')+Fore.RESET,
                    Fore.GREEN+str(data["id"])+Fore.RESET,
                    Fore.GREEN+str(data["containerId"])+Fore.RESET,
                    Fore.GREEN+str(data["mode"])+Fore.RESET
                ]

            else:
                coupleNumber = coupleNumber+1
                dataArray = [
                    Fore.GREEN+str(coupleNumber)+Fore.RESET,
                    Fore.GREEN+str(data["id"])+Fore.RESET,
                    Fore.GREEN+str(data["containerId"])+Fore.RESET,
                    Fore.GREEN+str(data["mode"])+Fore.RESET
                ]
            counter=counter+1
            dataTable.append(dataArray)
            if(str(data["mode"]).__contains__("BACKUP")):
                backupCounter=backupCounter+1
                backupContainerDict.add(str(backupCounter),str(data["containerId"]))
                backupSpaceIdDict.add(str(backupCounter),str(data["id"]))
            if(str(data["mode"]).__contains__("PRIMARY")):
                primaryCounter=primaryCounter+1
                primaryContainerDict.add(str(primaryCounter),str(data["containerId"]))
                primarySpaceIdDict.add(str(primaryCounter),str(data["id"]))

            containerIdHostDict.add(str(counter),str(data["containerId"]))
            spaceIdContainerIdDict.add(str(data["id"]),str(data["containerId"]))
            srNoSpaceIdDict.add(str(counter),str(data["id"]))
        logger.info("backup containers :"+str(backupContainerDict))
        logger.info("primary containers :"+str(primaryContainerDict))
        logger.info("container DICT :"+str(containerIdHostDict))
        logger.info("spaceIdContainerIdDict :"+str(spaceIdContainerIdDict))
        logger.info("srNoSpaceIdDict :"+str(srNoSpaceIdDict))
        logger.info("backupSpaceIdDict :"+str(backupSpaceIdDict))
        logger.info("primarySpaceIdDict :"+str(primarySpaceIdDict))
        printTabularGrid(None,headers,dataTable)
    except Exception as e:
        handleException(e)

def listUpdatedGSCStatus(display):
    logger.info("getUpdatedGSCStatus()")
    try:
        response = requests.get("http://"+managerHost+":8090/v2/spaces/"+str(spaceName)+"/instances")
        logger.info("getUpdatedGSCStatus() :response.text : "+str(response.text))
        jsonArray = json.loads(response.text)
        if(display=='true'):
            verboseHandle.printConsoleWarning("Instances on cluster:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"ID"+Fore.RESET,
                   Fore.YELLOW+"containerId"+Fore.RESET,
                   Fore.YELLOW+"mode"+Fore.RESET,
                   Fore.YELLOW+"Status"+Fore.RESET,
                   Fore.YELLOW+"Description"+Fore.RESET
                   ]
        counter=0
        coupleNumber=0
        dataTable=[]

        for data in jsonArray:
            updatedStatus = 'NONE'
            updatedDescription='NONE'
            if(spaceIdResponseCodeDict.__contains__(str(data["id"]))):
                spaceIdResponseCode = spaceIdResponseCodeDict.get(str(data["id"]))
                #if(str(spaceIdResponseCode).isdigit()):
                updatedStatus = validateResponse(spaceIdResponseCode)
                updatedDescription = validateResponseGetDescription(spaceIdResponseCode)
                #else:
                #    updatedDescription= spaceIdResponseCodeDict.get(str(data["id"]))
            if((counter+1)%2==0): # To display containers based on couple instead of each incremental
                dataArray = [
                    Fore.GREEN+str('')+Fore.RESET,
                    Fore.GREEN+str(data["id"])+Fore.RESET,
                    Fore.GREEN+str(data["containerId"])+Fore.RESET,
                    Fore.GREEN+str(data["mode"])+Fore.RESET,
                    Fore.GREEN+str(updatedStatus)+Fore.RESET,
                    Fore.GREEN+str(updatedDescription)+Fore.RESET
                ]
            else:
                coupleNumber = coupleNumber+1
                dataArray = [
                    Fore.GREEN+str(coupleNumber)+Fore.RESET,
                    Fore.GREEN+str(data["id"])+Fore.RESET,
                    Fore.GREEN+str(data["containerId"])+Fore.RESET,
                    Fore.GREEN+str(data["mode"])+Fore.RESET,
                    Fore.GREEN+str(updatedStatus)+Fore.RESET,
                    Fore.GREEN+str(updatedDescription)+Fore.RESET
                ]
            counter=counter+1
            dataTable.append(dataArray)
        printTabularGridWrap(None,headers,dataTable)
    except Exception as e:
        handleException(e)


def confirmAndProceedForAll():
    logger.info("confirmAndProceedForAll()")
    try:
        confirmRollingUpdate = str(userInputWrapper(Fore.YELLOW+"Are you sure want to proceed for rolling update all SrNo ? (y/n) [y]: "+Fore.RESET))
        if(len(str(confirmRollingUpdate))==0 ):
            confirmRollingUpdate = 'y'
        logger.info("confirmRollingUpdate : "+str(confirmRollingUpdate)) # instead of serial number couple need to be restarted.
        logger.info("confirmAndProceedForAll() :backupContainerDict :"+str(backupContainerDict))
        if(confirmRollingUpdate=='y'):
            copyFilesFromODSXToSpaceServer()
            for srno,containerID in backupContainerDict.items():
                print("Procceed for SrNo : "+srno)
                proceedForBackupRollingUpdate(srno)
    except Exception as e:
        handleException(e)

def validateResponse(responseCode):
    logger.info("validateResponse() "+str(responseCode))
    try:
        response = requests.get("http://"+managerHost+":8090/v2/requests/"+str(responseCode))
        jsonData = json.loads(response.text)
        logger.info("response : "+str(jsonData))
        return str(jsonData["status"])
    except Exception as e:
        handleException(e)

def validateResponseGetDescription(responseCode):
    logger.info("validateResponse() "+str(responseCode))
    try:
        response = requests.get("http://"+managerHost+":8090/v2/requests/"+str(responseCode))
        jsonData = json.loads(response.text)
        logger.info("response : "+str(jsonData))
        return str(jsonData["description"])
    except Exception as e:
        handleException(e)

def updateSpaceIdContainerID():
    logger.info("updateSpaceIdContainerID()")
    try:
        backupCounter=0
        primaryCounter=0
        response = requests.get("http://"+managerHost+":8090/v2/spaces/"+str(spaceName)+"/instances")
        logger.info("response.text : "+str(response.text))
        jsonArray = json.loads(response.text)
        for data in jsonArray:
            spaceIdContainerIdDict[str(data["id"])]=str(data["containerId"])
            if(str(data["mode"]).__contains__("BACKUP")):
                backupCounter=backupCounter+1
                backupSpaceIdDict[(str(backupCounter))]=str(data["id"])
            if(str(data["mode"]).__contains__("PRIMARY")):
                primaryCounter=primaryCounter+1
                primarySpaceIdDict[(str(primaryCounter))]=str(data["id"])

    except Exception as e:
        handleException(e)

def proceedForNewBackUpRollingUpdate(gscNumberToBeRollingUpdate):
    logger.info("proceedForNewBackUpRollingUpdate()")
    try:
        with Spinner():
            time.sleep(5)
        updateSpaceIdContainerID()
        spaceIdToBeRestarted = str(backupSpaceIdDict.get(str(gscNumberToBeRollingUpdate)))
        containerIdToBeRestarted = str(spaceIdContainerIdDict.get(str(spaceIdToBeRestarted)))
        logger.info("Space ID to be restarted : "+str(spaceIdToBeRestarted)+" ContainerId :"+str(containerIdToBeRestarted))
        #verboseHandle.printConsoleInfo("Space ID to be restarted : "+str(spaceIdToBeRestarted)+" ContainerId :"+str(containerIdToBeRestarted))
        verboseHandle.printConsoleInfo("Space ID to be restarted : "+str(spaceIdToBeRestarted)+"  ContainerId : "+str(containerIdToBeRestarted))
        loggerTiered.info("Space ID to be restarted : "+str(spaceIdToBeRestarted)+"  ContainerId : "+str(containerIdToBeRestarted))
        newbackUpRestartresponse = requests.post("http://"+str(managerHostConfig)+":8090/v2/containers/"+str(containerIdToBeRestarted)+"/restart",headers=requestHeader)
        with Spinner():
            time.sleep(5)
        logger.info("newbackUpRestartresponse.content : "+str(newbackUpRestartresponse.content))
        backUPResponseCode = str(newbackUpRestartresponse.content.decode('utf-8'))
        logger.info("backUPResponseCode : "+str(backUPResponseCode))
        status = validateResponse(backUPResponseCode)
        with Spinner():
            while(status.casefold() != 'successful'):
                time.sleep(2)
                status = validateResponse(backUPResponseCode)
                logger.info("spaceID Restart :"+str(spaceIdToBeRestarted)+" status :"+str(status))
                #verboseHandle.printConsoleInfo("spaceID Restart :"+str(spaceIdToBeRestarted)+" status :"+str(status))
                verboseHandle.printConsoleInfo("SpaceID Restart        : "+str(spaceIdToBeRestarted)+"                Status : "+str(status))
                loggerTiered.info("SpaceID Restart        : "+str(spaceIdToBeRestarted)+"                Status : "+str(status))
        verboseHandle.printConsoleInfo(" SpaceID Restart        : "+str(spaceIdToBeRestarted)+"                  Status : "+str(status))
        loggerTiered.info("SpaceID Restart        : "+str(spaceIdToBeRestarted)+"                  Status : "+str(status))
        with Spinner():
            verboseHandle.printConsoleInfo("Waiting for partition become healthy..."+str(restartContainerSleeptime)+"s")
            loggerTiered.info("Waiting for partition become healthy..."+str(restartContainerSleeptime)+"s")
            time.sleep(int(restartContainerSleeptime))
        spaceIdResponseCodeDict[str(spaceIdToBeRestarted)]=str(backUPResponseCode)
        updateSpaceIdContainerID()
        logger.info("updated After Restart : spaceIdContainerIdDict"+str(spaceIdContainerIdDict))
        logger.info("updated After Restart : backupIdDict"+str(backupSpaceIdDict))
        logger.info("updated After Restart : primaryIdDict"+str(primarySpaceIdDict))
        logger.info("updated After Restart : spaceIdResponseCodeDict"+str(spaceIdResponseCodeDict))
    except Exception as e:
        handleException(e)

def proceedForDemotePrimaryContainer(gscNumberToBeRollingUpdate):
    logger.info("proceedForDemotePrimaryContainer() : "+str(gscNumberToBeRollingUpdate))
    try:
        logger.info("Primary SpaceID Dict : demote : "+str(primarySpaceIdDict))
        spaceIdToBeDemoted = str(primarySpaceIdDict.get(str(gscNumberToBeRollingUpdate)))
        logger.info("Demoting : "+str(spaceIdToBeDemoted))
        #verboseHandle.printConsoleInfo("Demoting : "+str(spaceIdToBeDemoted))
        verboseHandle.printConsoleInfo(" Demoting                : "+str(spaceIdToBeDemoted))
        loggerTiered.info(" Demoting                : "+str(spaceIdToBeDemoted))
        maxSuspendTime = readValuefromAppConfig("app.tieredstorage.demote.maxsuspendtime")
        logger.info("maxSuspendTime : "+str(maxSuspendTime))
        primaryDemoteResponse = requests.post("http://"+str(managerHostConfig)+":8090/v2/spaces/"+str(spaceName)+"/instances/"+str(spaceIdToBeDemoted)+"/demote?maxSuspendTime="+str(maxSuspendTime),headers=requestHeader)
        primaryDemoteResponseCode = str(primaryDemoteResponse.content.decode('utf-8'))
        with Spinner():
            time.sleep(5)

        status = validateResponse(primaryDemoteResponseCode)
        with Spinner():
            while(status.casefold() != 'successful'):
                time.sleep(2)
                status = validateResponse(primaryDemoteResponseCode)
                #verboseHandle.printConsoleInfo("Demote :"+str(spaceIdToBeDemoted)+" Status :"+str(status))
                verboseHandle.printConsoleInfo("Demote                  : "+str(spaceIdToBeDemoted)+"                  Status : "+str(status))
                loggerTiered.info("Demote                  : "+str(spaceIdToBeDemoted)+"                  Status : "+str(status))
        #verboseHandle.printConsoleInfo("Demote :"+str(spaceIdToBeDemoted)+" Status :"+str(status))
        verboseHandle.printConsoleInfo(" Demote                  : "+str(spaceIdToBeDemoted)+"                  Status : "+str(status))
        loggerTiered.info("Demote                  : "+str(spaceIdToBeDemoted)+"                  Status : "+str(status))
        with Spinner():
            verboseHandle.printConsoleInfo("Waiting for partition become healthy..."+str(demoteSleeptime)+"s")
            loggerTiered.info("Waiting for partition become healthy..."+str(demoteSleeptime)+"s")
            time.sleep(int(demoteSleeptime))
        spaceIdResponseCodeDict[str(spaceIdToBeDemoted)]=str(primaryDemoteResponseCode)
        updateSpaceIdContainerID()
        logger.info("updated After Demote : spaceIdContainerIdDict :"+str(spaceIdContainerIdDict))
        proceedForNewBackUpRollingUpdate(gscNumberToBeRollingUpdate)

    except Exception as e:
        handleException(e)

def proceedForBackupRollingUpdate(gscNumberToBeRollingUpdate):
    logger.info("proceedForBackupRollingUpdate()")
    try:
        with Spinner():
            time.sleep(5)
        updateSpaceIdContainerID()
        logger.info("restartContainerSleeptime :"+str(restartContainerSleeptime)+" :: demoteSleeptime "+str(demoteSleeptime))
        loggerTiered.info("restartContainerSleeptime :"+str(restartContainerSleeptime)+" :: demoteSleeptime "+str(demoteSleeptime))
        logger.info("RollingUpdate SrNo number : "+gscNumberToBeRollingUpdate)
        loggerTiered.info("RollingUpdate SrNo number : "+gscNumberToBeRollingUpdate)
        verboseHandle.printConsoleInfo("RollingUpdate SrNo number: "+gscNumberToBeRollingUpdate)
        backupSpaceId = str(backupSpaceIdDict.get(str(gscNumberToBeRollingUpdate)))
        logger.info("backupSpaceId : "+str(backupSpaceId))
        #verboseHandle.printConsoleInfo("backupSpaceId : "+str(backupSpaceId))
        verboseHandle.printConsoleInfo("backupSpaceId            : "+str(backupSpaceId))
        loggerTiered.info("backupSpaceId            : "+str(backupSpaceId))
        backupContainerId = spaceIdContainerIdDict.get(str(backupSpaceId))
        logger.info("backupContainerId : "+str(backupContainerId))
        #verboseHandle.printConsoleInfo("backupContainerId :"+str(backupContainerId))
        verboseHandle.printConsoleInfo("backupContainerId        : "+str(backupContainerId))
        loggerTiered.info("backupContainerId        : "+str(backupContainerId))
        backUpIndividualGSCRestartresponse = requests.post("http://"+str(managerHostConfig)+":8090/v2/containers/"+str(backupContainerId)+"/restart",headers=requestHeader)
        logger.info("backUpIndividualGSCRestartresponse : "+str(backUpIndividualGSCRestartresponse.content))
        backUPRestartResponseCode = str(backUpIndividualGSCRestartresponse.content.decode('utf-8'))
        status = validateResponse(backUPRestartResponseCode)
        with Spinner():
            while(status.casefold() != 'successful'):
                time.sleep(2)
                status = validateResponse(backUPRestartResponseCode)
                #verboseHandle.printConsoleInfo("Backup :"+str(backupSpaceId)+" Restart Status :"+str(status))
                verboseHandle.printConsoleInfo("Backup                  : "+str(backupSpaceId)+"          Restart Status : "+str(status))
                loggerTiered.info("Backup                  : "+str(backupSpaceId)+"          Restart Status : "+str(status))
                logger.info("Backup : "+str(backupSpaceId)+" Status : "+str(status))
        #verboseHandle.printConsoleInfo("Backup :"+str(backupSpaceId)+" Restart Status :"+str(status))
        verboseHandle.printConsoleInfo(" Backup                  : "+str(backupSpaceId)+"          Restart Status : "+str(status))
        loggerTiered.info("Backup                  : "+str(backupSpaceId)+"          Restart Status : "+str(status))
        with Spinner():
            verboseHandle.printConsoleInfo("Waiting for partition become healthy..."+str(restartContainerSleeptime)+"s")
            loggerTiered.info("Waiting for partition become healthy..."+str(restartContainerSleeptime)+"s")
            time.sleep(int(restartContainerSleeptime))
        updateSpaceIdContainerID()
        spaceIdResponseCodeDict[str(backupSpaceId)]=str(backUPRestartResponseCode)
        logger.info("updated After Backup Restart : spaceIdContainerIdDict"+str(spaceIdContainerIdDict))
        logger.info("updated After Backup Restart : spaceIdResponseCodeDict"+str(spaceIdResponseCodeDict))
        proceedForDemotePrimaryContainer(gscNumberToBeRollingUpdate)
    except Exception as e:
        handleException(e)


def confirmAndProceedForIndividualRestartGSC():
    logger.info("confirmAndProceedForIndividualRestartGSC()")
    try:
        gscNumberToBeRestarted = str(userInputWrapper(Fore.YELLOW+"Enter SrNo number to be rolling update : "+Fore.RESET))
        while(len(str(gscNumberToBeRestarted))==0 ):
            gscNumberToBeRestarted = str(userInputWrapper(Fore.YELLOW+"Enter SrNo number to be rolling update : "+Fore.RESET))
        logger.info("gscNumberToBeRestarted : "+str(gscNumberToBeRestarted)) # instead of serial number couple need to be restarted.
        confirmRestart = str(userInputWrapper(Fore.YELLOW+"Are you sure want to rolling update for Sr No "+str(gscNumberToBeRestarted)+" (y/n) [y] : "+Fore.RESET))
        if(len(str(confirmRestart))==0):
            confirmRestart='y'
        logger.info("confirmRestart :"+str(confirmRestart))
        if(len(str(confirmRestart))==0 or confirmRestart=='y'):
            copyFilesFromODSXToSpaceServer()
            if(str(gscNumberToBeRestarted).__contains__(',')):
                for srno in gscNumberToBeRestarted.split(','):
                    proceedForBackupRollingUpdate(srno)
            else:
                proceedForBackupRollingUpdate(gscNumberToBeRestarted)

    except Exception as e:
        handleException(e)

def inputParams():
    logger.info("inputParams()")
    global restartContainerSleeptime
    global demoteSleeptime
    try:
        restartcontainerSleeptimeConfig = str(readValuefromAppConfig("app.tieredstorage.restartcontainer.sleeptime")).replace('"','')
        restartContainerSleeptime = str(userInputWrapper(Fore.YELLOW+"Enter restart container sleeptime ["+restartcontainerSleeptimeConfig+"]: "))
        if(len(str(restartContainerSleeptime))==0):
            restartContainerSleeptime = restartcontainerSleeptimeConfig
        logger.info("restartcontainerSleeptime : "+str(restartContainerSleeptime))


        demoteSleeptimeConfig = str(readValuefromAppConfig("app.tieredstorage.demote.sleeptime")).replace('"','')
        demoteSleeptime = str(userInputWrapper(Fore.YELLOW+"Enter demote sleeptime ["+demoteSleeptimeConfig+"]: "))
        if(len(str(demoteSleeptime))==0):
            demoteSleeptime = demoteSleeptimeConfig
        logger.info("demoteSleeptimeConfig : "+str(demoteSleeptimeConfig))

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
    logger.info("ips :"+str(ips))
    tieredCriteriaConfigFilePathError = str(getYamlFilePathInsideFolder(".object.config.ddlparser.ts.bck.currentTs")).replace('"','')
    logger.info("tieredCriteriaConfigFilePathError : "+str(tieredCriteriaConfigFilePathError))
    tieredCriteriaConfigFilePath=""
    tieredCriteriaConfigFilePathBck = str(getYamlFilePathInsideFolder(".object.config.ddlparser.ts.bck.previousTs")).replace('"','')
    logger.info("tieredCriteriaConfigFilePathBck : "+str(tieredCriteriaConfigFilePathBck))
    if(tieredCriteriaConfigFilePathBck.__contains__('.bck')):
        tieredCriteriaConfigFilePath = tieredCriteriaConfigFilePathBck.replace(".bck","")
    logger.info("tieredCriteriaConfigFilePath : "+str(tieredCriteriaConfigFilePath))
    #rename .bck to original file
    cmd = "mv "+str(tieredCriteriaConfigFilePathError)+" "+str(tieredCriteriaConfigFilePathError)+".err; mv "+str(tieredCriteriaConfigFilePathBck)+" "+str(tieredCriteriaConfigFilePath)
    logger.info("cmd : "+str(cmd))
    status = os.system(cmd)
    logger.info("status : "+str(status))
    dbaGigaDir=str(readValuefromAppConfig("app.giga.path"))
    tieredCriteriaConfigFilePathTarget = str(readValuefromAppConfig("app.tieredstorage.criteria.filepath.target")).replace('"','').replace("/dbagiga/",dbaGigaDir)
    logger.info(" ips : "+str(ips)+" tieredCriteriaConfigFilePath :"+str(tieredCriteriaConfigFilePath)+" tieredCriteriaConfigFilePathTarget : "+str(tieredCriteriaConfigFilePathTarget))
    if(copyFile(ips, tieredCriteriaConfigFilePath, tieredCriteriaConfigFilePathTarget)):
        logger.info("File copied successfully.. taking backup of source file")
        #cmd = "cp "+str(tieredCriteriaConfigFilePath)+" "+str(tieredCriteriaConfigFilePath)
        #set_value_in_property_file('app.tieredstorage.criteria.filepath',str(tieredCriteriaConfigFilePath))
        #status = os.system(cmd)
        #logger.info("status : "+str(status))
        #logger.info("mv status :"+str(status))


def listGSC(managerHost):
    global managerHostConfig
    global spaceNumber
    global spaceName
    managerHostConfig = managerHost
    try:
        spaceNumber = str(userInputWrapper(Fore.YELLOW+"Enter space number to get details :"+Fore.RESET))
        while(len(str(spaceNumber))==0 or (not spaceNumber.isdigit())):
            spaceNumber = str(userInputWrapper(Fore.YELLOW+"Enter space number to get details :"+Fore.RESET))
        logger.info("spaceNumber : "+str(spaceNumber))
        logger.info("SpaceName = "+str(gs_space_host_dictionary_obj.get(str(spaceNumber))))
        spaceName = str(gs_space_host_dictionary_obj.get(str(spaceNumber)))
        logger.info("listGSC for manager:"+str(managerHost))

        displayOnlyGSC()

        typeOfRestart=''
        #typeOfRestart = str(userInputWrapper("[1] For individual GSC restart \n[Enter] For all GSCs \n[99] For Exit. \nEnter your choice : "))
        while(str(typeOfRestart)!='99'):
            typeOfRestart = str(userInputWithEscWrapper(Fore.YELLOW+"[1] For List \n[2] For SrNo rolling update \n[Enter] For rolling update all \n[99] For Exit. \nEnter your choice : "+Fore.RESET))
            logger.info("typeOfRestart : "+str(typeOfRestart))
            if(len(str(typeOfRestart))==0):
                #confirmParamAndRestartGSC()
                #inputParams()
                confirmAndProceedForAll()
            elif(str(typeOfRestart)=='1'):
                display='true'
                listUpdatedGSCStatus(display)
            elif(str(typeOfRestart)=='2'):
                #inputParams()
                confirmAndProceedForIndividualRestartGSC()
            elif(str(typeOfRestart)=='99'):
                return
        return
    except Exception as e:
        handleException(e)

if __name__ == '__main__':
    logger.info("odsx_tieredstorage_rollback")
    verboseHandle.printConsoleWarning("Menu -> TieredStorage -> Rollback")
    try:
        managerNodes = config_get_manager_node()
        if(len(str(managerNodes))>0):
            logger.info("managerNodes: main"+str(managerNodes))
            spaceNodes = config_get_space_hosts()
            logger.info("spaceNodes: main"+str(spaceNodes))
            managerHost = getManagerHost(managerNodes)
            logger.info("managerHost : "+str(managerHost))
            if(len(str(managerHost))>0):
                logger.info("Manager Host :"+str(managerHost))
                global sourceFile
                sourceFile = str(getYamlFilePathInsideFolder(".object.config.ddlparser.ts.bck.currentTs")).replace('"','')
                logger.info("sourceFile : "+str(sourceFile))
                global backupCriteriaFile
                backupCriteriaFile = str(getYamlFilePathInsideFolder(".object.config.ddlparser.ts.bck.previousTs")).replace('"','')
                logger.info("backupFile : "+str(backupCriteriaFile))
                if(Path(backupCriteriaFile).is_file()):
                    logger.info("File exist"+str(backupCriteriaFile))
                    confirm = str(userInputWrapper(Fore.YELLOW+"Using "+str(backupCriteriaFile)+" for rolling instead of current "+str(sourceFile)+" please approve [y/n] : "+Fore.RESET))
                    if(confirm=='y' or len(str(confirm))==0):
                        gs_space_host_dictionary_obj = listSpacesOnServer(managerHost)
                        logger.info(" gs_space_host_dictionary_obj :"+str(len(gs_space_host_dictionary_obj)))
                        if(len(gs_space_host_dictionary_obj)>0):
                            listGSC(managerHost)
                        else:
                            verboseHandle.printConsoleInfo("No space found.")
                        #listGSC(managerHost)
                else:
                    logger.info("File does not exist : "+str(backupCriteriaFile))
                    verboseHandle.printConsoleInfo("File does not exist : "+str(backupCriteriaFile))
            else:
                logger.info("Please check manager server status.")
                verboseHandle.printConsoleInfo("Please check manager server status.")
        else:
            logger.info("No Manager configuration found please check.")
            verboseHandle.printConsoleInfo("No Manager configuration found please check.")
    except Exception as e:
        verboseHandle.printConsoleError("Eror in odsx_tieredstorage_rollback : "+str(e))
        logger.error("Exception in tieredStorage_rollback.py"+str(e))
        handleException(e)