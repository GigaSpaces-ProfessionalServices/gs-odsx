#!/usr/bin/env python3

import logging
import os
import signal
import sqlite3

import json
import requests
from colorama import Fore
from requests.auth import HTTPBasicAuth

from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig, readValueByConfigObj
from utils.ods_cleanup import signal_handler
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_scp import scp_upload
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_db2feeder_utilities import getPasswordByHost, getUsernameByHost
from utils.odsx_print_tabular_data import printTabular
from utils.odsx_print_tabular_data import printTabularGrid

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

ll = []

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

dbaGigaLogPath=str(readValueByConfigObj("app.gigalog.path"))
if not os.path.exists(dbaGigaLogPath+'/tieredstorage/'):
    os.makedirs(dbaGigaLogPath+'/tieredstorage/')
    loggerTiered = setup_logger(os.path.basename(__file__), dbaGigaLogPath+'/tieredstorage/tieredstorage_updatecachepolicy_trace.log')

else:
    loggerTiered = setup_logger(os.path.basename(__file__), dbaGigaLogPath+'/tieredstorage/tieredstorage_updatecachepolicy_trace.log')
    # loggerTiered = setup_logger(os.path.basename(__file__), 'logs/tieredstorage_updatecachepolicy_trace.log')

# loggerTiered = setup_logger(os.path.basename(__file__), 'logs/tieredstorage_updatecachepolicy_trace.log')
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

def getNumberOfSpaceInstances():
    spaceInstanceNumber = len(config_get_space_hosts());
    return spaceInstanceNumber

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

def getTieredStorageSpaces():
    logger.info("getTieredStorageSpaces()")
    #check for Tiered storage space
    tieredSpace = []
    try:
        responseTiered = requests.get("http://"+str(managerHost)+":8090/v2/internal/spaces/utilization",auth = HTTPBasicAuth(username,password))
        logger.info("Response status of spaces/utilization : "+str(responseTiered.status_code)+" content : "+str(responseTiered.content))
        jsonArrayTiered = json.loads(responseTiered.text)
        for data in jsonArrayTiered:
            if(data["tiered"]==True):
                tieredSpace.append(str(data["name"]))
        logger.info("tieresSpaces : "+str(tieredSpace))
    except Exception as e:
        handleException(e)
    return tieredSpace

def listSpacesOnServer(managerHost):
    logger.info("listSpacesOnServer : managerNodes :"+str(managerHost))
    global gs_space_host_dictionary_obj
    global gs_service_dictionary_obj
    try:
        tieredSpaces = getTieredStorageSpaces()
        logger.info("managerHost :"+str(managerHost))
        response = requests.get("http://"+str(managerHost)+":8090/v2/spaces",auth = HTTPBasicAuth(username,password))
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
        gs_service_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_host_dictionary_obj : "+str(gs_space_host_dictionary_obj))
        logger.info("gs_service_dictionary_obj : "+str(gs_service_dictionary_obj))
        counter=0
        dataTable=[]
        for data in jsonArray:
            if(tieredSpaces.__contains__(str(data["name"]))):
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
                gs_service_dictionary_obj.add(str(counter+1),str(data["processingUnitName"]))
                counter=counter+1
                dataTable.append(dataArray)
        printTabular(None,headers,dataTable)
        return gs_space_host_dictionary_obj
    except Exception as e:
        handleException(e)

def statusList(spaceID):
    try:
        db_file = str(readValueByConfigObj("app.tieredstorage.updatecachepolicy.sqlite.dbfile")).replace('"','').replace(' ','')
        cnx = sqlite3.connect(db_file)
        mycursor = cnx.execute("SELECT status FROM db2_updatecachepolicy_status where spaceID='"+str(spaceID)+"'")
        myresult = mycursor.fetchone()
        cnx.close()
        if myresult is not None:
            return myresult[0]

    except Exception as e:
        handleException(e)


def displayOnlyGSC():
    logger.info("displayOnlyGSC()")
    try:
        response = requests.get("http://"+managerHost+":8090/v2/spaces/"+str(spaceName)+"/instances",auth = HTTPBasicAuth(username,password))
        logger.info("response.text : "+str(response.text))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Instances on cluster:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"ID"+Fore.RESET,
                   Fore.YELLOW+"containerId"+Fore.RESET,
                   Fore.YELLOW+"mode"+Fore.RESET,
                   Fore.YELLOW+"status"+Fore.RESET
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
        updatedStatus = 'NONE'
        for data in jsonArray:
            updatedStatus = statusList(str(data["id"]))
            if((counter+1)%2==0): # To display containers based on couple instead of each incremental
                dataArray = [
                    Fore.GREEN+str('')+Fore.RESET,
                    Fore.GREEN+str(data["id"])+Fore.RESET,
                    Fore.GREEN+str(data["containerId"])+Fore.RESET,
                    Fore.GREEN+str(data["mode"])+Fore.RESET,
                    Fore.GREEN+str(updatedStatus)+Fore.RESET
                ]

            else:
                coupleNumber = coupleNumber+1
                dataArray = [
                    Fore.GREEN+str(coupleNumber)+Fore.RESET,
                    Fore.GREEN+str(data["id"])+Fore.RESET,
                    Fore.GREEN+str(data["containerId"])+Fore.RESET,
                    Fore.GREEN+str(data["mode"])+Fore.RESET,
                    Fore.GREEN+str(updatedStatus)+Fore.RESET
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

def validateResponse(responseCode):
    logger.info("validateResponse() "+str(responseCode))
    try:
        response = requests.get("http://"+managerHost+":8090/v2/requests/"+str(responseCode),auth = HTTPBasicAuth(username,password))
        jsonData = json.loads(response.text)
        logger.info("response : "+str(jsonData))
        return str(jsonData["status"])
    except Exception as e:
        handleException(e)

def validateResponseGetDescription(responseCode):
    logger.info("validateResponse() "+str(responseCode))
    try:
        response = requests.get("http://"+managerHost+":8090/v2/requests/"+str(responseCode),auth = HTTPBasicAuth(username,password))
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
        response = requests.get("http://"+managerHost+":8090/v2/spaces/"+str(spaceName)+"/instances",auth = HTTPBasicAuth(username,password))
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

def getSpaceCurrentStatus():
    logger.info("getSpaceCurrentStatus()")
    try:
        serviceName = gs_service_dictionary_obj.get(spaceNumber)
        logger.info("Getting status URL : http://"+str(managerHost)+":8090/v2/pus/"+str(serviceName))
        response = requests.get("http://"+str(managerHost)+":8090/v2/pus/"+str(serviceName),auth = HTTPBasicAuth(username,password))
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
        jsonArray = json.loads(response.text)
        logger.info("status : "+str(jsonArray["status"]))
        return str(jsonArray["status"])
    except Exception as e:
        handleException(e)

def inputParams():
    logger.info("inputParams()")
    #global restartContainerSleeptime
    #global demoteSleeptime
    try:
        '''
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
        '''
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

def createDB2EntryInSqlLite():
    logger.info("createDB2EntryInSqlLite()")
    try:
        db_file = str(readValueByConfigObj("app.tieredstorage.updatecachepolicy.sqlite.dbfile")).replace('"','').replace(' ','')
        cnx = sqlite3.connect(db_file)
        cnx.execute("CREATE TABLE IF NOT EXISTS db2_updatecachepolicy_status (spaceID VARCHAR(50), hostId VARCHAR(50), status VARCHAR(50))")
        cnx.commit()
        logger.info("query result for create:"+str(cnx))
        cnx.close()
    except Exception as e:
        handleException(e)

def listGSC(managerHost):
    global managerHostConfig
    global spaceNumber
    global spaceName
    managerHostConfig = managerHost
    try:
        from utils.odsx_keypress import userInputWrapper
        spaceNumber = str(userInputWrapper(Fore.YELLOW+"Enter space number to get details :"+Fore.RESET))
        while(len(str(spaceNumber))==0 or (not spaceNumber.isdigit())):
            from utils.odsx_keypress import userInputWrapper
            spaceNumber = str(userInputWrapper(Fore.YELLOW+"Enter space number to get details :"+Fore.RESET))
        logger.info("spaceNumber : "+str(spaceNumber))
        logger.info("SpaceName = "+str(gs_space_host_dictionary_obj.get(str(spaceNumber))))
        spaceName = str(gs_space_host_dictionary_obj.get(str(spaceNumber)))
        logger.info("listGSC for manager:"+str(managerHost))

        displayOnlyGSC()
        return
    except Exception as e:
        handleException(e)

if __name__ == '__main__':
    logger.info("odsx_security_tieredstorage_updatecachepolicy")
    loggerTiered.info("Updatecachepolicy")
    verboseHandle.printConsoleWarning("Menu -> TieredStorage -> Update cache policy -> Show")
    username = ""
    password = ""
    appId=""
    safeId=""
    objectId=""
    signal.signal(signal.SIGINT, signal_handler)
    try:
        appId = str(readValuefromAppConfig("app.space.security.appId")).replace('"','')
        safeId = str(readValuefromAppConfig("app.space.security.safeId")).replace('"','')
        objectId = str(readValuefromAppConfig("app.space.security.objectId")).replace('"','')
        logger.info("appId : "+appId+" safeID : "+safeId+" objectID : "+objectId)
        managerNodes = config_get_manager_node()
        if(len(str(managerNodes))>0):
            logger.info("managerNodes: main"+str(managerNodes))
            spaceNodes = config_get_space_hosts()
            logger.info("spaceNodes: main"+str(spaceNodes))
            managerHost = getManagerHost(managerNodes)
            logger.info("managerHost : "+str(managerHost))
            if(len(str(managerHost))>0):
                username = str(getUsernameByHost(managerHost,appId,safeId,objectId))
                password =  str(getPasswordByHost(managerHost,appId,safeId,objectId))
                logger.info("Manager Host :"+str(managerHost))
                gs_space_host_dictionary_obj = listSpacesOnServer(managerHost)
                logger.info(" gs_space_host_dictionary_obj :"+str(len(gs_space_host_dictionary_obj)))
                if(len(gs_space_host_dictionary_obj)>0):
                    createDB2EntryInSqlLite()
                    listGSC(managerHost)
                else:
                    verboseHandle.printConsoleInfo("No space found.")
                #confirmParamAndRestartGSC()
            else:
                logger.info("Please check manager server status.")
                verboseHandle.printConsoleInfo("Please check manager server status.")
        else:
            logger.info("No Manager configuration found please check.")
            verboseHandle.printConsoleInfo("No Manager configuration found please check.")
    except Exception as e:
        #verboseHandle.printConsoleError("Eror in odsx_tieredstorage_updatecachepolicy : "+str(e))
        logger.error("Exception in tieredStorage_updatecachepolicy.py"+str(e))
        handleException(e)
