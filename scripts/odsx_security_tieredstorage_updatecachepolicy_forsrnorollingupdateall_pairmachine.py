#!/usr/bin/env python3

import json
import logging
import os
import signal
import sqlite3
import time
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime as dt

import requests
from colorama import Fore
from requests.auth import HTTPBasicAuth

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig, set_value_yaml_config, \
    readValueFromYaml, getYamlFilePathInsideFolder, readValueByConfigObj
from utils.ods_cleanup import signal_handler
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_scp import scp_upload
from utils.ods_ssh import executeRemoteCommandAndGetOutput
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_db2feeder_utilities import getPasswordByHost, getUsernameByHost
from utils.odsx_keypress import userInputWrapper
from utils.odsx_print_tabular_data import printTabular
from utils.odsx_print_tabular_data import printTabularGrid, printTabularGridWrap

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


if not os.path.exists('/dbagigalogs/tieredstorage/'):
    os.makedirs('/dbagigalogs/tieredstorage/')
else:
    loggerTiered = setup_logger(os.path.basename(__file__),
                                '/dbagigalogs/tieredstorage/tieredstorage_updatecachepolicy_trace.log')
    loggerTiered = setup_logger(os.path.basename(__file__), 'logs/tieredstorage_updatecachepolicy_trace.log')

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


def dataContainerREST(host, zone, memory):
    logger.info("dataContainerREST()")
    data = {
        "vmArguments": [
            "-Xms" + memory + " -Xmx" + memory
        ],
        "memory": memory,
        "zone": zone,
        "host": host
    }
    return data


def get_gs_host_details(managerNodes):
    try:
        logger.info("get_gs_host_details() : managerNodes :" + str(managerNodes))
        for node in managerNodes:
            status = getSpaceServerStatus(os.getenv(node.ip))
            if (status == "ON"):
                managerHostConfig = os.getenv(node.ip);
        logger.info("managerHostConfig : " + str(managerHostConfig))
        response = requests.get('http://' + managerHostConfig + ':8090/v2/hosts',
                                headers={'Accept': 'application/json'}, auth=HTTPBasicAuth(username, password))
        logger.info("response status of host :" + str(managerHostConfig) + " status :" + str(response.status_code))
        jsonArray = json.loads(response.text)
        gs_servers_host_dictionary_obj = host_dictionary_obj()
        for data in jsonArray:
            gs_servers_host_dictionary_obj.add(str(data['name']), str(data['address']))
        logger.info("gs_servers_host_dictionary_obj : " + str(gs_servers_host_dictionary_obj))
        return gs_servers_host_dictionary_obj
    except Exception as e:
        handleException(e)


def createGSC(host):
    try:
        gs_host_details_obj = get_gs_host_details(managerNodes)
        logger.info("gs_host_details_obj : " + str(gs_host_details_obj))
        counter = 0
        space_dict_obj = host_dictionary_obj()
        memoryGSC = str(readValuefromAppConfig("app.spacejar.creategsc.gscmemory"))
        numberOfGSC = 1 #str(readValuefromAppConfig("app.spacejar.creategsc.gsczone"))
        #numberOfGSC = numberOfGSC/2
        zoneGSC = str(readValuefromAppConfig("app.space.gsc.zone"))
        for node in spaceNodes:
            if (gs_host_details_obj.__contains__(str(os.getenv(node.name))) or (
                    str(os.getenv(node.name)) in gs_host_details_obj.values())):
                space_dict_obj.add(str(counter + 1), os.getenv(node.name))
                counter = counter + 1
        print(space_dict_obj)
        #for i in range(1, len(space_dict_obj) + 1):
        #host = space_dict_obj.get(str(i))
        cmd = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh --username=" + username + " --password=" + password + " container create --zone " + str(
            zoneGSC) + " --count " + str(numberOfGSC) + " --memory " + str(memoryGSC) + " " + str(host) + ""
        logger.info("cmd 161 : " + str(cmd))
        print("cmd : " + str(cmd))
        with Spinner():
            output = executeRemoteCommandAndGetOutput(host, 'root', cmd)
            print("163: host : "+str(host))
            verboseHandle.printConsoleInfo(str(output))
    except Exception as e:
        handleException(e)

def insertDB2EntryInSqlLite(spaceID, hostId, status):
    # print("createDB2EntryInSqlLite()")
    try:
        db_file = str(readValueByConfigObj("app.tieredstorage.updatecachepolicy.sqlite.dbfile")).replace('"',
                                                                                                         '').replace(
            ' ', '')
        cnx = sqlite3.connect(db_file)
        cnx.execute("INSERT INTO db2_updatecachepolicy_status (spaceID, hostId, status) VALUES ('" + str(
            spaceID) + "', '" + str(hostId) + "','" + str(status) + "')")
        cnx.commit()
        # print("query result for insert:"+str(cnx))
        cnx.close()
    except Exception as e:
        handleException(e)

def applyCachePolicyAndReadData():
    data = json.dumps({
        "partialMemberName": str(spaceName)+"_container",
        "spaceName": str(spaceName),
        "isBackup": "false"
    })
    spaceServers = config_get_space_hosts()
    for spacehost in spaceServers:
        print(">>>str(os.getenv(spacehost.ip)) : "+str(os.getenv(spacehost.ip)) +", data "+str(data))
        response = requests.post(
            "http://" + str(os.getenv(spacehost.ip)) + ":7002/policy/update",headers={'Content-type': 'application/json'}, data=data)
        print("applied update cache policy response 196 : "+str(response.text))
        response = requests.get(
            "http://" + str(os.getenv(spacehost.ip)) + ":7002/policy/read",headers={'Content-type': 'application/json'}, data=data)
        print("read cache policy response 612 : "+str(response.text))

def truncateInSqlLite():
    # print("truncateInSqlLite()")
    try:
        db_file = str(readValueByConfigObj("app.tieredstorage.updatecachepolicy.sqlite.dbfile")).replace('"',
                                                                                                         '').replace(
            ' ', '')
        cnx = sqlite3.connect(db_file)
        cnx.execute("DELETE FROM db2_updatecachepolicy_status ")
        cnx.commit()
        # print("query result for insert:"+str(cnx))
        cnx.close()
    except Exception as e:
        handleException(e)

def createDB2EntryInSqlLite():
    # logger.info("createDB2EntryInSqlLite()")
    try:
        db_file = str(readValueByConfigObj("app.tieredstorage.updatecachepolicy.sqlite.dbfile")).replace('"',
                                                                                                         '').replace(
            ' ', '')
        cnx = sqlite3.connect(db_file)
        cnx.execute(
            "CREATE TABLE IF NOT EXISTS db2_updatecachepolicy_status (spaceID VARCHAR(50), hostId VARCHAR(50), status VARCHAR(50))")
        cnx.commit()
        logger.info("query result for create:" + str(cnx))
        cnx.close()
    except Exception as e:
        handleException(e)


def updateDB2EntryInSqlLite(spaceID, status):
    # print("updateDB2EntryInSqlLite()")
    try:
        db_file = str(readValueByConfigObj("app.tieredstorage.updatecachepolicy.sqlite.dbfile")).replace('"',
                                                                                                         '').replace(
            ' ', '')
        cnx = sqlite3.connect(db_file)
        mycursor = cnx.execute(
            "UPDATE db2_updatecachepolicy_status SET status='" + str(status) + "' where spaceID='" + str(
                spaceID) + "' ")
        logger.info("query result for update:" + str(mycursor.rowcount))

        # cnx.execute("INSERT INTO db2_updatecachepolicy_status (spaceID, hostId, status) VALUES ('"+str(spaceID)+"', '"+str(hostId)+"','"+str(status)+"')")
        cnx.commit()
        cnx.close()
    except Exception as e:
        handleException(e)


def getNumberOfSpaceInstances():
    spaceInstanceNumber = len(config_get_space_hosts());
    return spaceInstanceNumber


def getManagerHost(managerNodes):
    managerHost = ""
    try:
        logger.info("getManagerHost() : managerNodes :" + str(managerNodes))
        for node in managerNodes:
            status = getSpaceServerStatus(os.getenv(node.ip))
            if (status == "ON"):
                managerHost = os.getenv(node.ip)
        return managerHost
    except Exception as e:
        handleException(e)


def getTieredStorageSpaces():
    logger.info("getTieredStorageSpaces()")
    # check for Tiered storage space
    tieredSpace = []
    try:
        responseTiered = requests.get("http://" + str(managerHost) + ":8090/v2/internal/spaces/utilization",
                                      auth=HTTPBasicAuth(username, password))
        logger.info("Response status of spaces/utilization : " + str(responseTiered.status_code) + " content : " + str(
            responseTiered.content))
        jsonArrayTiered = json.loads(responseTiered.text)
        for data in jsonArrayTiered:
            if (data["tiered"] == True):
                tieredSpace.append(str(data["name"]))
        logger.info("tieresSpaces : " + str(tieredSpace))
    except Exception as e:
        handleException(e)
    return tieredSpace


def listSpacesOnServer(managerHost):
    logger.info("listSpacesOnServer : managerNodes :" + str(managerHost))
    global gs_space_host_dictionary_obj
    global gs_service_dictionary_obj
    try:
        tieredSpaces = getTieredStorageSpaces()
        logger.info("managerHost :" + str(managerHost))
        response = requests.get("http://" + str(managerHost) + ":8090/v2/spaces",
                                auth=HTTPBasicAuth(username, password))
        logger.info("response status of host :" + str(managerHost) + " status :" + str(response.status_code))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Existing spaces on cluster:")
        headers = [Fore.YELLOW + "Sr No." + Fore.RESET,
                   Fore.YELLOW + "Name" + Fore.RESET,
                   Fore.YELLOW + "PU Name" + Fore.RESET,
                   Fore.YELLOW + "Partition" + Fore.RESET,
                   Fore.YELLOW + "Backup Partition" + Fore.RESET
                   ]
        gs_space_host_dictionary_obj = host_dictionary_obj()
        gs_service_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_host_dictionary_obj : " + str(gs_space_host_dictionary_obj))
        logger.info("gs_service_dictionary_obj : " + str(gs_service_dictionary_obj))
        counter = 0
        dataTable = []
        for data in jsonArray:
            if (tieredSpaces.__contains__(str(data["name"]))):
                if (str(data["topology"]["backupsPerPartition"]) == "1"):
                    isBackup = "YES"
                if (str(data["topology"]["backupsPerPartition"]) == "0"):
                    isBackup = "NO"
                dataArray = [Fore.GREEN + str(counter + 1) + Fore.RESET,
                             Fore.GREEN + data["name"] + Fore.RESET,
                             Fore.GREEN + data["processingUnitName"] + Fore.RESET,
                             Fore.GREEN + str(data["topology"]["partitions"]) + Fore.RESET,
                             Fore.GREEN + isBackup + Fore.RESET
                             ]
                gs_space_host_dictionary_obj.add(str(counter + 1), str(data["name"]))
                gs_service_dictionary_obj.add(str(counter + 1), str(data["processingUnitName"]))
                counter = counter + 1
                dataTable.append(dataArray)
        printTabular(None, headers, dataTable)
        return gs_space_host_dictionary_obj
    except Exception as e:
        handleException(e)


def displayOnlyGSC():
    logger.info("displayOnlyGSC()")
    try:
        response = requests.get("http://" + managerHost + ":8090/v2/spaces/" + str(spaceName) + "/instances",
                                auth=HTTPBasicAuth(username, password))
        logger.info("response.text : " + str(response.text))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Instances on cluster:")
        headers = [Fore.YELLOW + "Sr No." + Fore.RESET,
                   Fore.YELLOW + "ID" + Fore.RESET,
                   Fore.YELLOW + "containerId" + Fore.RESET,
                   Fore.YELLOW + "mode" + Fore.RESET
                   ]
        counter = 0
        coupleNumber = 0
        backupCounter = 0
        primaryCounter = 0
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
        dataTable = []
        for data in jsonArray:
            if ((counter + 1) % 2 == 0):  # To display containers based on couple instead of each incremental
                dataArray = [
                    Fore.GREEN + str('') + Fore.RESET,
                    Fore.GREEN + str(data["id"]) + Fore.RESET,
                    Fore.GREEN + str(data["containerId"]) + Fore.RESET,
                    Fore.GREEN + str(data["mode"]) + Fore.RESET
                ]

            else:
                coupleNumber = coupleNumber + 1
                dataArray = [
                    Fore.GREEN + str(coupleNumber) + Fore.RESET,
                    Fore.GREEN + str(data["id"]) + Fore.RESET,
                    Fore.GREEN + str(data["containerId"]) + Fore.RESET,
                    Fore.GREEN + str(data["mode"]) + Fore.RESET
                ]
            counter = counter + 1
            dataTable.append(dataArray)
            if (str(data["mode"]).__contains__("BACKUP")):
                backupCounter = backupCounter + 1
                backupContainerDict.add(str(backupCounter), str(data["containerId"]))
                backupSpaceIdDict.add(str(backupCounter), str(data["id"]))
            if (str(data["mode"]).__contains__("PRIMARY")):
                primaryCounter = primaryCounter + 1
                primaryContainerDict.add(str(primaryCounter), str(data["containerId"]))
                primarySpaceIdDict.add(str(primaryCounter), str(data["id"]))

            containerIdHostDict.add(str(counter), str(data["containerId"]))
            spaceIdContainerIdDict.add(str(data["id"]), str(data["containerId"]))
            srNoSpaceIdDict.add(str(counter), str(data["id"]))
        logger.info("backup containers :" + str(backupContainerDict))
        logger.info("primary containers :" + str(primaryContainerDict))
        logger.info("container DICT :" + str(containerIdHostDict))
        logger.info("spaceIdContainerIdDict :" + str(spaceIdContainerIdDict))
        logger.info("srNoSpaceIdDict :" + str(srNoSpaceIdDict))
        logger.info("backupSpaceIdDict :" + str(backupSpaceIdDict))
        logger.info("primarySpaceIdDict :" + str(primarySpaceIdDict))
        printTabularGrid(None, headers, dataTable)
    except Exception as e:
        handleException(e)


def listUpdatedGSCStatus(display):
    logger.info("getUpdatedGSCStatus()")
    try:
        response = requests.get("http://" + managerHost + ":8090/v2/spaces/" + str(spaceName) + "/instances",
                                auth=HTTPBasicAuth(username, password))
        logger.info("getUpdatedGSCStatus() :response.text : " + str(response.text))
        jsonArray = json.loads(response.text)
        if (display == 'true'):
            verboseHandle.printConsoleWarning("Instances on cluster:")
        headers = [Fore.YELLOW + "Sr No." + Fore.RESET,
                   Fore.YELLOW + "ID" + Fore.RESET,
                   Fore.YELLOW + "containerId" + Fore.RESET,
                   Fore.YELLOW + "mode" + Fore.RESET,
                   Fore.YELLOW + "Status" + Fore.RESET,
                   Fore.YELLOW + "Description" + Fore.RESET
                   ]
        counter = 0
        coupleNumber = 0
        dataTable = []

        for data in jsonArray:
            updatedStatus = 'NONE'
            updatedDescription = 'NONE'
            if (spaceIdResponseCodeDict.__contains__(str(data["id"]))):
                spaceIdResponseCode = spaceIdResponseCodeDict.get(str(data["id"]))
                # if(str(spaceIdResponseCode).isdigit()):
                updatedStatus = validateResponse(spaceIdResponseCode)
                updatedDescription = validateResponseGetDescription(spaceIdResponseCode)
                # else:
                #    updatedDescription= spaceIdResponseCodeDict.get(str(data["id"]))
            if ((counter + 1) % 2 == 0):  # To display containers based on couple instead of each incremental
                dataArray = [
                    Fore.GREEN + str('') + Fore.RESET,
                    Fore.GREEN + str(data["id"]) + Fore.RESET,
                    Fore.GREEN + str(data["containerId"]) + Fore.RESET,
                    Fore.GREEN + str(data["mode"]) + Fore.RESET,
                    Fore.GREEN + str(updatedStatus) + Fore.RESET,
                    Fore.GREEN + str(updatedDescription) + Fore.RESET
                ]
            else:
                coupleNumber = coupleNumber + 1
                dataArray = [
                    Fore.GREEN + str(coupleNumber) + Fore.RESET,
                    Fore.GREEN + str(data["id"]) + Fore.RESET,
                    Fore.GREEN + str(data["containerId"]) + Fore.RESET,
                    Fore.GREEN + str(data["mode"]) + Fore.RESET,
                    Fore.GREEN + str(updatedStatus) + Fore.RESET,
                    Fore.GREEN + str(updatedDescription) + Fore.RESET
                ]
            counter = counter + 1
            dataTable.append(dataArray)
        printTabularGridWrap(None, headers, dataTable)
    except Exception as e:
        handleException(e)


def confirmAndProceedForAll():
    logger.info("confirmAndProceedForAll()")
    try:
        confirmRollingUpdate = str(userInputWrapper(
            Fore.YELLOW + "Are you sure want to proceed for rolling update all SrNo ? (y/n) [y]: " + Fore.RESET))
        if (len(str(confirmRollingUpdate)) == 0):
            confirmRollingUpdate = 'y'
        logger.info("confirmRollingUpdate : " + str(
            confirmRollingUpdate))  # instead of serial number couple need to be restarted.
        logger.info("confirmAndProceedForAll() :backupContainerDict :" + str(primaryContainerDict))
        if (confirmRollingUpdate == 'y'):
            copyFilesFromODSXToSpaceServer()
            start_time = time.time()
            # newList = primaryContainerIDList()
            label = True
            global ll
            for partitionId in range(1, len(primaryContainerDict) + 1):
                ll.append(partitionId)
            while label == True:
                dict_obj = host_dictionary_obj()
                for partitionId in ll:
                    primarySpaceId = primarySpaceIdDict.get(str(partitionId))
                    # print("   back up space id     "+str(primarySpaceId))
                    primaryContainerId = spaceIdContainerIdDict.get(str(primarySpaceId))
                    dict_obj.add(partitionId, primaryContainerId)
                # print(" dict object    "+str(dict_obj))
                print("dict_obj : "+str(dict_obj))
                new_list = host_dictionary_obj()
                for item in dict_obj:
                    stripped = dict_obj.get(item).split('~', 1)[0]
                    if not stripped in list(new_list.values()):
                        new_list.add(item, stripped)
                partitionIdList = list(new_list.keys())
                print(" Restarting partitons are :   " + str(partitionIdList))
                loggerTiered.info(" Restarting partitons are :  " + str(partitionIdList))

                numberOfSpaceInstances = getNumberOfSpaceInstances()
                with ThreadPoolExecutor(numberOfSpaceInstances) as executor:
                    for partitionId in range(1, len(primaryContainerDict) + 1):
                        if partitionId in partitionIdList:
                            ll.remove(partitionId)
                            print("partitionId : 492 : "+str(partitionId))
                            executor.submit(proceedForBackupRollingUpdate1, str(partitionId))
                if (len(ll) == 0):
                    label = False
            end_time = time.time()

            # print(f'Total time to run multithreads: {end_time - start_time:2f}s')

    except Exception as e:

        handleException(e)


def validateResponse(responseCode):
    logger.info("validateResponse() " + str(responseCode))
    #try:
#        response = requests.get("http://" + managerHost + ":8090/v2/requests/" + str(responseCode),
#                                auth=HTTPBasicAuth(username, password))
    response = requests.get("http://" + managerHost + ":8090/v2/pus",
                            auth=HTTPBasicAuth(username, password))
    jsonData = json.loads(response.text)
    resourceNameToCheck = str(readValuefromAppConfig("app.tieredstorage.pu.name"))
    for data in jsonData:
        puName=data["name"]
        if puName == resourceNameToCheck and data["status"] == "intact":
            time.sleep(5)
            return "successful"

    return "inprogress"
'''        logger.info("response : " + str(jsonData))
        print("response 508 : " + str(jsonData))
        if len(jsonData) == 0:
            return "successful"
        if 'status' in jsonData:
            if jsonData["status"] == 'running':
                return "successful"
        if 'status' in jsonData[0]:
            if jsonData[0]["status"] == 'running':
                return "successful"
        return jsonData
        #return str(jsonData[0]["status"])
        '''
    #except Exception as e:
    #    handleException(e)

def validateResponseGetDescriptionOrg(responseCode):
    logger.info("validateResponse() "+str(responseCode))
    #print(username+" : "+password)
    response = requests.get("http://"+managerHost+":8090/v2/requests/"+str(responseCode),auth = HTTPBasicAuth(username, password))
    jsonData = json.loads(response.text)
    logger.info("response : "+str(jsonData))
    if(str(jsonData["status"]).__contains__("failed")):
        return "Status :"+str(jsonData["status"])+" Description:"+str(jsonData["error"])
    else:
        return "Status :"+str(jsonData["status"])+" Description:"+str(jsonData["description"])
def validateResponseGetDescription(responseCode):
    logger.info("validateResponse() " + str(responseCode))
    try:
        response = requests.get("http://" + managerHost + ":8090/v2/requests/" + str(responseCode),
                                auth=HTTPBasicAuth(username, password))
        jsonData = json.loads(response.text)
        logger.info("response : " + str(jsonData))
        return str(jsonData["description"])
    except Exception as e:
        handleException(e)


def updateSpaceIdContainerID():
    logger.info("updateSpaceIdContainerID()")
    try:
        backupCounter = 0
        primaryCounter = 0
        response = requests.get("http://" + managerHost + ":8090/v2/spaces/" + str(spaceName) + "/instances",
                                auth=HTTPBasicAuth(username, password))
        logger.info("response.text : " + str(response.text))
        jsonArray = json.loads(response.text)
        print("jsonArray : "+str(jsonArray))
        for data in jsonArray:
            spaceIdContainerIdDict[str(data["id"])] = str(data["containerId"])
            if (str(data["mode"]).__contains__("BACKUP")):
                backupCounter = backupCounter + 1
                backupSpaceIdDict[(str(backupCounter))] = str(data["id"])
            if (str(data["mode"]).__contains__("PRIMARY")):
                primaryCounter = primaryCounter + 1
                primarySpaceIdDict[(str(primaryCounter))] = str(data["id"])
        print("primarySpaceIdDict : " +str(primarySpaceIdDict))
        print("backupSpaceIdDict : " +str(backupSpaceIdDict))
    except Exception as e:
        handleException(e)


def getSpaceCurrentStatus():
    logger.info("getSpaceCurrentStatus()")
    try:
        serviceName = gs_service_dictionary_obj.get(spaceNumber)
        logger.info("Getting status URL : http://" + str(managerHost) + ":8090/v2/pus/" + str(serviceName))
        response = requests.get("http://" + str(managerHost) + ":8090/v2/pus/" + str(serviceName),
                                auth=HTTPBasicAuth(username, password))
        logger.info("response status of host :" + str(managerHost) + " status :" + str(
            response.status_code) + " Content: " + str(response.content))
        jsonArray = json.loads(response.text)
        logger.info("status : " + str(jsonArray["status"]))
        return str(jsonArray["status"])
    except Exception as e:
        handleException(e)


def proceedForNewBackUpRollingUpdate(gscNumberToBeRollingUpdate,isUpdate):
    logger.info("proceedForNewBackUpRollingUpdate()")
    try:
        with Spinner():
            time.sleep(5)
        print("proceedForNewBackUpRollingUpdate -> gscNumberToBeRollingUpdate : " + str(gscNumberToBeRollingUpdate))
        updateSpaceIdContainerID()
        spaceIdToBeRestarted = str(primarySpaceIdDict.get(str(gscNumberToBeRollingUpdate)))
        containerIdToBeRestarted = str(spaceIdContainerIdDict.get(str(spaceIdToBeRestarted)))
        logger.info("Space ID to be restarted : " + str(spaceIdToBeRestarted) + " ContainerId :" + str(
            containerIdToBeRestarted))
        # verboseHandle.printConsoleInfo("Space ID to be restarted : "+str(spaceIdToBeRestarted)+" ContainerId :"+str(containerIdToBeRestarted))

        if isUpdate:
            data = json.dumps({
                "partialMemberName": str(spaceName)+"_container",
                "spaceName": str(spaceName),
                "isBackup": "false"
            })
            print("str(containerIdToBeRestarted).split[0] : "+str(containerIdToBeRestarted).split("~",1)[0] +", data "+str(data))
            print(backupSpaceIdDict)
            print(spaceIdContainerIdDict)
            response = requests.post(
               "http://" + str(containerIdToBeRestarted).split("~",1)[0] + ":7002/policy/update",headers={'Content-type': 'application/json'}, data=data)
            print("applied update cache policy response 609 : "+str(response.text))
            response = requests.get(
                "http://" + str(containerIdToBeRestarted).split("~",1)[0] + ":7002/policy/read",headers={'Content-type': 'application/json'}, data=data)
            print("read cache policy response 612 : "+str(response.text))

        else:
            spaceIdToBeRestarted = str(backupSpaceIdDict.get(str(gscNumberToBeRollingUpdate)))
            containerIdToBeRestarted = str(spaceIdContainerIdDict.get(str(spaceIdToBeRestarted)))
            insertDB2EntryInSqlLite(str(spaceIdToBeRestarted), str("backupContainerId"), "pending")
            verboseHandle.printConsoleInfo(
                "Space ID to be restarted : " + str(spaceIdToBeRestarted) + "  ContainerId : " + str(
                    containerIdToBeRestarted))
            loggerTiered.info("Space ID to be restarted : " + str(spaceIdToBeRestarted) + "  ContainerId : " + str(
                containerIdToBeRestarted))
            #newbackUpRestartresponse = requests.post(
            #    "http://" + str(managerHostConfig) + ":8090/v2/containers/" + str(containerIdToBeRestarted) + "/restart",
            #    headers=requestHeader, auth=HTTPBasicAuth(username, password))
           # response = requests.get("http://"+managerHost+":8090/v2/containers")
          #  jsonArray = json.loads(response.text)
           # for data in jsonArray:
            #    response = requests.delete("http://"+managerHost+":8090/v2/containers/"+str(data["id"]),headers=requestHeader, auth=HTTPBasicAuth(username, password))
            response = requests.delete("http://"+managerHost+":8090/v2/containers/"+str(containerIdToBeRestarted),headers=requestHeader, auth=HTTPBasicAuth(username, password))
            verboseHandle.printConsoleInfo("Deleted container 590 "+str(containerIdToBeRestarted))
            #data = json.dumps({
            #    "partialMemberName": str(spaceName)+"_container",
            #    "spaceName": str(spaceName),
            #    "isBackup": "false"
            #})
            hostips = getSpaceNodeIps()
            #for hostip in hostips:
            #response = requests.post(
             #   "http://" + str(containerIdToBeRestarted).split("~",1)[0] + ":7002/policy/update",headers={'Content-type': 'application/json'}, data=data)
            #print("applied update cache policy response 613 : "+str(response.text))

            print("proceedForNewBackUpRollingUpdate : ")
            createGSC(str(containerIdToBeRestarted).split("~",1)[0])
            #logger.info("newbackUpRestartresponse.content : " + str(newbackUpRestartresponse.content))
            response = requests.get("http://"+managerHost+":8090/v2/requests",auth = HTTPBasicAuth(username,password))
            jsonArray = json.loads(response.text)
            backUPResponseCode=""
            if(len(jsonArray)>1):
                jsonArray = json.loads(response.text)
                backUPResponseCode=jsonArray[0]["id"]
            #backUPResponseCode = str(newbackUpRestartresponse.content.decode('utf-8'))
            logger.info("backUPResponseCode : " + str(backUPResponseCode))
            status = validateResponse(backUPResponseCode)
            with Spinner():
                while (status.casefold() != 'successful'):
                    time.sleep(2)
                    status = validateResponse(backUPResponseCode)
                    logger.info("spaceID Restart :" + str(spaceIdToBeRestarted) + " status :" + str(status))
                    # verboseHandle.printConsoleInfo("spaceID Restart :"+str(spaceIdToBeRestarted)+" status :"+str(status))
                    updateDB2EntryInSqlLite(str(spaceIdToBeRestarted), str(status))
                    verboseHandle.printConsoleInfo(
                        "SpaceID Restart        : " + str(spaceIdToBeRestarted) + "                Status : " + str(status))
                    loggerTiered.info(
                        "SpaceID Restart        : " + str(spaceIdToBeRestarted) + "                Status : " + str(status))
            verboseHandle.printConsoleInfo(
                " SpaceID Restart        : " + str(spaceIdToBeRestarted) + "                  Status : " + str(status))
            loggerTiered.info(
                "SpaceID Restart        : " + str(spaceIdToBeRestarted) + "                  Status : " + str(status))

            with Spinner():
                status = 'intact'
                time.sleep(5)
                while (status != str(getSpaceCurrentStatus())):
                    verboseHandle.printConsoleInfo(
                        "Waiting for partition become healthy. Current status : " + str(getSpaceCurrentStatus()))
                    loggerTiered.info("Waiting for partition become. Current status " + getSpaceCurrentStatus())
                    time.sleep(3)
                verboseHandle.printConsoleInfo("Final status : " + str(getSpaceCurrentStatus()))
                updateDB2EntryInSqlLite(str(spaceIdToBeRestarted), str(getSpaceCurrentStatus()))
                logger.info("Final status : " + str(getSpaceCurrentStatus()))
                time.sleep(2)
            spaceIdResponseCodeDict[str(spaceIdToBeRestarted)] = str(backUPResponseCode)
            updateSpaceIdContainerID()
            logger.info("updated After Restart : spaceIdContainerIdDict" + str(spaceIdContainerIdDict))
            logger.info("updated After Restart : backupIdDict" + str(backupSpaceIdDict))
            logger.info("updated After Restart : primaryIdDict" + str(primarySpaceIdDict))
            logger.info("updated After Restart : spaceIdResponseCodeDict" + str(spaceIdResponseCodeDict))
    except Exception as e:
        handleException(e)


def proceedForDemotePrimaryContainer(gscNumberToBeRollingUpdate):
    logger.info("proceedForDemotePrimaryContainer() : " + str(gscNumberToBeRollingUpdate))
    try:
        logger.info("Primary SpaceID Dict : demote : " + str(primarySpaceIdDict))
        spaceIdToBeDemoted = str(primarySpaceIdDict.get(str(gscNumberToBeRollingUpdate)))
        logger.info("Demoting : " + str(spaceIdToBeDemoted))
        # verboseHandle.printConsoleInfo("Demoting : "+str(spaceIdToBeDemoted))
        verboseHandle.printConsoleInfo(" Demoting                : " + str(spaceIdToBeDemoted))
        loggerTiered.info("Demoting                : " + str(spaceIdToBeDemoted))
        insertDB2EntryInSqlLite(str(spaceIdToBeDemoted), str("backupContainerId"), "pending")
        maxSuspendTime = readValuefromAppConfig("app.tieredstorage.demote.maxsuspendtime")
        logger.info("maxSuspendTime : " + str(maxSuspendTime))
        primaryDemoteResponse = requests.post(
            "http://" + str(managerHostConfig) + ":8090/v2/spaces/" + str(spaceName) + "/instances/" + str(
                spaceIdToBeDemoted) + "/demote?maxSuspendTime=" + str(maxSuspendTime), headers=requestHeader,
            auth=HTTPBasicAuth(username, password))
        primaryDemoteResponseCode = str(primaryDemoteResponse.content.decode('utf-8'))
        with Spinner():
            time.sleep(5)

        status = validateResponse(primaryDemoteResponseCode)
        verboseHandle.printConsoleInfo("primaryDemoteResponseCode :" + str(primaryDemoteResponseCode))
        with Spinner():
            while (status.casefold() != 'successful'):
                time.sleep(2)
                status = validateResponse(primaryDemoteResponseCode)
                updateDB2EntryInSqlLite(str(spaceIdToBeDemoted), str(status))
                # verboseHandle.printConsoleInfo("Demote :"+str(spaceIdToBeDemoted)+" Status :"+str(status))
                verboseHandle.printConsoleInfo(
                    "Demote                  : " + str(spaceIdToBeDemoted) + "                  Status : " + str(
                        status))
                loggerTiered.info(
                    "Demote                  : " + str(spaceIdToBeDemoted) + "                  Status : " + str(
                        status))
        # verboseHandle.printConsoleInfo("Demote :"+str(spaceIdToBeDemoted)+" Status :"+str(status))
        verboseHandle.printConsoleInfo(
            " Demote                  : " + str(spaceIdToBeDemoted) + "                  Status : " + str(status))
        loggerTiered.info(
            "Demote                  : " + str(spaceIdToBeDemoted) + "                  Status : " + str(status))
        with Spinner():
            status = 'intact'
            time.sleep(5)
            while (status != str(getSpaceCurrentStatus())):
                verboseHandle.printConsoleInfo(
                    "Waiting for partition become healthy. Current status : " + str(getSpaceCurrentStatus()))
                loggerTiered.info("Waiting for partition become healthy. Current status " + getSpaceCurrentStatus())
                time.sleep(3)
            verboseHandle.printConsoleInfo("Final status : " + str(getSpaceCurrentStatus()))
            updateDB2EntryInSqlLite(str(spaceIdToBeDemoted), str(getSpaceCurrentStatus()))
            logger.info("Final status : " + str(getSpaceCurrentStatus()))
            time.sleep(2)
        spaceIdResponseCodeDict[str(spaceIdToBeDemoted)] = str(primaryDemoteResponseCode)
        updateSpaceIdContainerID()
        logger.info("updated After Demote : spaceIdContainerIdDict :" + str(spaceIdContainerIdDict))
#        proceedForNewBackUpRollingUpdate(gscNumberToBeRollingUpdate, True)
        proceedForNewBackUpRollingUpdate(gscNumberToBeRollingUpdate, False)

    except Exception as e:
        handleException(e)
def uploadFileRest(managerHostConfig):
    try:
        logger.info("uploadFileRest : managerHostConfig : "+str(managerHostConfig))
        global pathOfSourcePU
        pathOfSourcePU = ".gs.jars.ts.tieredStorageBuild"
        pathOfSourcePU = str(getYamlFilePathInsideFolder(pathOfSourcePU)).replace('"','')
        logger.info("pathOfSourcePU :"+str(pathOfSourcePU))
        #logger.info("Upload url : "+"curl -X PUT -F 'file=@"+str(pathOfSourcePU)+"' http://"+managerHostConfig+":8090/v2/pus/resources")
        #status = os.system("curl -X PUT -F 'file=@"+str(pathOfSourcePU)+"' http://"+managerHostConfig+":8090/v2/pus/resources -u "+username+":"+password+"")
        #logger.info("status : "+str(status))
    except Exception as e:
        handleException(e)

def dataPuREST(resource,resourceName,zone,partition,maxInstancesPerMachine,backUpRequired):
    logger.info("dataPuREST()")
    try:
        global slaProperties
        slaProperties = str(readValuefromAppConfig("app.tieredstorage.pu.autogenerated-instance-sla"))
        logger.info("slaProperties :"+str(slaProperties))

        global tieredCriteriaConfigFilePathTarget
        tieredCriteriaConfigFilePathTarget = str(readValuefromAppConfig("app.tieredstorage.criteria.filepath.target")).replace('"','')
        logger.info("filePath.target :"+str(tieredCriteriaConfigFilePathTarget))

        global spacePropertyConfigFilePath
        spacePropertyConfigFilePath = str(getYamlFilePathInsideFolder(".gs.config.ts.spaceproperty")).replace('"','')
        logger.info("app.space.property.filePath :"+str(spacePropertyConfigFilePath))
        logger.info("spacePropertyConfigFilePath :"+str(spacePropertyConfigFilePath))

        global spacePropertyConfigFilePathTarget
        spacePropertyConfigFilePathTarget = str(readValuefromAppConfig("app.space.property.filePath.target")).replace('"','')
        logger.info("app.space.property.filePath.target :"+str(spacePropertyConfigFilePathTarget))

        global spaceNameCfg
        spaceNameCfg = str(readValuefromAppConfig("app.tieredstorage.pu.spacename"))
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
                "space.name" : ""+spaceNameCfg+""
            }
        }

        return data
    except Exception as e:
        handleException(e)
def proceedForTieredStorageDeployment(managerHostConfig):
    logger.info("proceedForTieredStorageDeployment()")
    try:
        print("\n")
        head , tail = os.path.split(pathOfSourcePU)
        logger.info("tail :"+str(tail))
        global resource
        resource = str(tail)
        logger.info("resource :"+str(resource))
        global resourceName
        resourceName = str(readValuefromAppConfig("app.tieredstorage.pu.name"))
        logger.info("nameOfPU :"+str(resourceName))
        global partition
        partition = str(readValuefromAppConfig("app.tieredstorage.gsc.partitions"))
        logger.info("Enter partition required :"+str(partition))

        global zoneOfPU
        zoneOfPU = str(readValuefromAppConfig("app.tieredstorage.pu.zone"))
        logger.info("Zone Of PU :"+str(zoneOfPU))

        global maxInstancesPerMachine
        maxInstancesPerMachine = str(readValuefromAppConfig("app.tieredstorage.pu.maxInstancesPerMachine"))
        logger.info("maxInstancePerVM Of PU :"+str(maxInstancesPerMachine))

        global backUpRequired
        global backUpRequiredStr
        backUpRequired = str(readValuefromAppConfig("app.tieredstorage.pu.backuprequired"))
        if(len(str(backUpRequired))==0 or backUpRequired=='y'):
            backUpRequired=1
        if(str(backUpRequired)=='n'):
            backUpRequired=0
        data = dataPuREST(resource,resourceName,zoneOfPU,partition,maxInstancesPerMachine,backUpRequired)

        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        logger.info("url : "+"http://"+managerHostConfig+":8090/v2/pus")
        logger.info("dJson Paylod : "+str(data))
        response = requests.post("http://"+managerHostConfig+":8090/v2/pus",data=json.dumps(data),headers=headers,auth = HTTPBasicAuth(username, password))
        deployResponseCode = str(response.content.decode('utf-8'))
        verboseHandle.printConsoleInfo("deployResponseCode : "+str(deployResponseCode))
        logger.info("deployResponseCode :"+str(deployResponseCode))

        status = validateResponseGetDescriptionOrg(deployResponseCode)
        logger.info("response.status_code :"+str(response.status_code))
        logger.info("response.content :"+str(response.content) )
        if(response.status_code==202):
            logger.info("Response :"+str(status))
            retryCount=5
            while(retryCount>0 or (not str(status).casefold().__contains__('successful')) or (not str(status).casefold().__contains__('failed'))):
                status = validateResponseGetDescriptionOrg(deployResponseCode)
                verboseHandle.printConsoleInfo("Response :"+str(status))
                retryCount = retryCount-1
                time.sleep(2)
                if(str(status).casefold().__contains__('successful')):
                    serviceName = 'object-management.service'
                    os.system('sudo systemctl daemon-reload')
                    os.system('systemctl stop '+serviceName)
                    os.system('systemctl start '+serviceName)
                    return
                elif(str(status).casefold().__contains__('failed')):
                    return

        else:
            logger.info("Unable to deploy :"+str(status))
            verboseHandle.printConsoleInfo("Unable to deploy : "+str(status))
    except Exception as e:
        handleException(e)
def redeploySpace():
    drainMode = readValuefromAppConfig("app.tieredstorage.drainmode")
    drainTimeout = readValuefromAppConfig("app.tieredstorage.drainTimeout")
    spacePUName = readValuefromAppConfig("app.spacejar.pu.name")

    response = requests.delete("http://"+str(managerHost)+":8090/v2/pus/"+str(spacePUName)+"?drainMode="+str(drainMode)+"&drainTimeout="+str(drainTimeout),auth = HTTPBasicAuth(username,password))
    verboseHandle.printConsoleInfo(str(response.status_code))
    logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
    if(response.status_code==202):
        undeployResponseCode = str(response.content.decode('utf-8'))
        logger.info("backUPResponseCode : "+str(undeployResponseCode))
        status = validateResponse(undeployResponseCode)
        with Spinner():
            while(status.casefold() != 'successful'):
                time.sleep(2)
                status = validateResponse(undeployResponseCode)
                logger.info("UndeployAll :"+str(spacePUName)+"   Status :"+str(status))
                verboseHandle.printConsoleInfo("Undeploy  : "+str(spacePUName)+"   Status : "+str(status))
        verboseHandle.printConsoleInfo(" Undeploy  : "+str(spaceName)+"   Status : "+str(status))
        time.sleep(30)
        uploadFileRest(str(managerHost))
        proceedForTieredStorageDeployment(str(managerHost))
    else:
        logger.info("PU :"+str(spacePUName)+" has not been undeploy.")
        verboseHandle.printConsoleInfo("PU :"+str(spacePUName)+" has not been undeploy.")

def proceedForBackupRollingUpdate1(gscNumberToBeRollingUpdate):
    print(">>>>>>>>")
    applyCachePolicyAndReadData()
    redeploySpace()
    #proceedForBackupRollingUpdate(gscNumberToBeRollingUpdate,True)
    #proceedForBackupRollingUpdate(gscNumberToBeRollingUpdate,False)
def proceedForBackupRollingUpdate(gscNumberToBeRollingUpdate,isUpdate):
    logger.info("proceedForBackupRollingUpdate()")
    print("proceedForBackupRollingUpdate >")
    try:
        with Spinner():
            time.sleep(5)
        print("proceedForBackupRollingUpdate -> gscNumberToBeRollingUpdate : " + str(gscNumberToBeRollingUpdate))
        updateSpaceIdContainerID()
        logger.info("RollingUpdate SrNo number : " + gscNumberToBeRollingUpdate)
        loggerTiered.info("RollingUpdate SrNo number : " + gscNumberToBeRollingUpdate)
        verboseHandle.printConsoleInfo("RollingUpdate SrNo number: " + gscNumberToBeRollingUpdate)
        backupSpaceId = str(backupSpaceIdDict.get(str(gscNumberToBeRollingUpdate)))
        logger.info("backupSpaceId : " + str(backupSpaceId))
        # verboseHandle.printConsoleInfo("backupSpaceId : "+str(backupSpaceId))
        verboseHandle.printConsoleInfo("backupSpaceId            : " + str(backupSpaceId))
        loggerTiered.info("backupSpaceId           : " + str(backupSpaceId))
        backupContainerId = spaceIdContainerIdDict.get(str(backupSpaceId))
        logger.info("backupContainerId : " + str(backupContainerId))
        print("backupContainerId 733 : " + str(backupContainerId))
        # verboseHandle.printConsoleInfo("backupContainerId :"+str(backupContainerId))
        verboseHandle.printConsoleInfo("backupContainerId        : " + str(backupContainerId))
        loggerTiered.info("backupContainerId       : " + str(backupContainerId))
        if isUpdate:
            data = json.dumps({
                "partialMemberName": str(spaceName)+"_container",
                "spaceName": str(spaceName),
                "isBackup": "true"
            })
            print("str(backupContainerId).split[0] : "+str(backupContainerId).split("~",1)[0] +", data "+str(data))
            print(spaceIdContainerIdDict)
            print(backupSpaceIdDict)

            response = requests.post(
                "http://" + str(backupContainerId).split("~",1)[0] + ":7002/policy/update",headers={'Content-type': 'application/json'}, data=data)
            print("applied update cache policy response 751 : "+str(response.text))
            response = requests.get(
                "http://" + str(backupContainerId).split("~",1)[0] + ":7002/policy/read",headers={'Content-type': 'application/json'}, data=data)
            print("read cache policy response 751 : "+str(response.text))
            proceedForNewBackUpRollingUpdate(gscNumberToBeRollingUpdate, True)
        else:
            insertDB2EntryInSqlLite(str(backupSpaceId), str(backupContainerId), "pending")
            #backUpIndividualGSCRestartresponse = requests.post(
            #    "http://" + str(managerHostConfig) + ":8090/v2/containers/" + str(backupContainerId) + "/restart",
            #    headers=requestHeader, auth=HTTPBasicAuth(username, password))
            response = requests.delete("http://"+managerHost+":8090/v2/containers/"+str(backupContainerId),headers=requestHeader, auth=HTTPBasicAuth(username, password))
            verboseHandle.printConsoleInfo("Deleted container 735 "+str(backupContainerId))
            ##data = json.dumps({
             #   "partialMemberName": str(spaceName)+"_container",
             #   "spaceName": str(spaceName),
             #   "isBackup": "true"
            #})
            hostips = getSpaceNodeIps()
            #for hostip in hostips:
            #response = requests.post(
            #    "http://" + str(backupContainerId).split("~",1)[0] + ":7002/policy/update",headers={'Content-type': 'application/json'}, data=data)
            #print("response 751 : "+str(response.text))

            print("proceedForBackupRollingUpdate : ")
            createGSC(str(backupContainerId).split("~",1)[0])
            response = requests.get("http://"+managerHost+":8090/v2/requests",auth = HTTPBasicAuth(username,password))
            jsonArray = json.loads(response.text)
            backUPRestartResponseCode=""
            if(len(jsonArray)>1):
                jsonArray = json.loads(response.text)
                backUPRestartResponseCode=jsonArray[0]["id"]
            #logger.info("backUpIndividualGSCRestartresponse : " + str(backUpIndividualGSCRestartresponse.content))
            #backUPRestartResponseCode = str(backUpIndividualGSCRestartresponse.content.decode('utf-8'))
            status = validateResponse(backUPRestartResponseCode)
            print(">>>>>>>>>>>>>>>")
            print(status)
            print(">>>>>>>>>>>>>>>")
            with Spinner():
                while (status.casefold() != 'successful'):
                    time.sleep(2)
                    status = validateResponse(backUPRestartResponseCode)
                    updateDB2EntryInSqlLite(str(backupSpaceId), str(status))
                    # verboseHandle.printConsoleInfo("Backup :"+str(backupSpaceId)+" Restart Status :"+str(status))
                    verboseHandle.printConsoleInfo(
                        "Backup                  : " + str(backupSpaceId) + "          Restart Status : " + str(status))
                    loggerTiered.info(
                        "Backup                  : " + str(backupSpaceId) + "          Restart Status : " + str(status))
                    logger.info("Backup : " + str(backupSpaceId) + " Status : " + str(status))
            # verboseHandle.printConsoleInfo("Backup :"+str(backupSpaceId)+" Restart Status :"+str(status))
            verboseHandle.printConsoleInfo(
                " Backup                  : " + str(backupSpaceId) + "          Restart Status : " + str(status))
            loggerTiered.info(
                "Backup                  : " + str(backupSpaceId) + "          Restart Status : " + str(status))
            with Spinner():
                status = 'intact'
                time.sleep(5)
                while (status != str(getSpaceCurrentStatus())):
                    verboseHandle.printConsoleInfo(
                        "Waiting for partition become healthy. Current status : " + str(getSpaceCurrentStatus()))
                    loggerTiered.info("Waiting for partition become healthy. Current status " + getSpaceCurrentStatus())
                    time.sleep(3)
                verboseHandle.printConsoleInfo("Final status : " + str(getSpaceCurrentStatus()))
                updateDB2EntryInSqlLite(str(backupSpaceId), str(getSpaceCurrentStatus()))
                logger.info("Final status : " + str(getSpaceCurrentStatus()))
                time.sleep(2)
            updateSpaceIdContainerID()
            spaceIdResponseCodeDict[str(backupSpaceId)] = str(backUPRestartResponseCode)
            logger.info("updated After Backup Restart : spaceIdContainerIdDict" + str(spaceIdContainerIdDict))
            logger.info("updated After Backup Restart : spaceIdResponseCodeDict" + str(spaceIdResponseCodeDict))
            proceedForDemotePrimaryContainer(gscNumberToBeRollingUpdate)
    except Exception as e:
        handleException(e)


def confirmAndProceedForIndividualRestartGSC():
    logger.info("confirmAndProceedForIndividualRestartGSC()")
    try:
        gscNumberToBeRestarted = str(
            userInputWrapper(Fore.YELLOW + "Enter SrNo number to be rolling update : " + Fore.RESET))
        while (len(str(gscNumberToBeRestarted)) == 0):
            gscNumberToBeRestarted = str(
                userInputWrapper(Fore.YELLOW + "Enter SrNo number to be rolling update : " + Fore.RESET))
        logger.info("gscNumberToBeRestarted : " + str(
            gscNumberToBeRestarted))  # instead of serial number couple need to be restarted.
        confirmRestart = str(userInputWrapper(Fore.YELLOW + "Are you sure want to rolling update for Sr No " + str(
            gscNumberToBeRestarted) + " (y/n) [y] : " + Fore.RESET))
        if (len(str(confirmRestart)) == 0):
            confirmRestart = 'y'
        logger.info("confirmRestart :" + str(confirmRestart))
        if (len(str(confirmRestart)) == 0 or confirmRestart == 'y'):
            copyFilesFromODSXToSpaceServer()
            if (str(gscNumberToBeRestarted).__contains__(',')):
                for srno in gscNumberToBeRestarted.split(','):
                    print("srno 820 : "+str(srno))
                    proceedForBackupRollingUpdate(srno, True)
                for srno in gscNumberToBeRestarted.split(','):
                    print("srno 820 : "+str(srno))
                    proceedForBackupRollingUpdate(srno,False)
            else:
                print("gscNumberToBeRestarted 823 : "+str(gscNumberToBeRestarted))
                proceedForBackupRollingUpdate(gscNumberToBeRestarted, True)
                proceedForBackupRollingUpdate(gscNumberToBeRestarted, False)

    except Exception as e:
        handleException(e)


def inputParams():
    logger.info("inputParams()")
    # global restartContainerSleeptime
    # global demoteSleeptime
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
    logger.info("copyFile :" + str(hostips) + " : " + str(srcPath) + " : " + str(destPath))
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
    logger.info("ips : " + str(ips))
    return ips


def copyFilesFromODSXToSpaceServer():
    logger.info("copyFilesFromODSXToSpaceServer()")
    ips = getSpaceNodeIps()
    logger.info("ips: " + str(ips))
    tieredCriteriaConfigFilePath = str(
        getYamlFilePathInsideFolder(".object.config.ddlparser.ddlCriteriaFileName")).replace('"', '')
    logger.info("tieredCriteriaConfigFilePath : " + str(tieredCriteriaConfigFilePath))
    tieredCriteriaConfigFilePathTarget = str(
        readValuefromAppConfig("app.tieredstorage.criteria.filepath.target")).replace('"', '')
    logger.info("tieredCriteriaConfigFilePathTarget : " + str(tieredCriteriaConfigFilePathTarget))
    spacePropertyConfigFilePath = str(getYamlFilePathInsideFolder(".gs.config.ts.spaceproperty")).replace('"', '')
    logger.info("spacePropertyConfigFilePath : " + str(spacePropertyConfigFilePath))
    spacePropertyConfigFilePathTarget = str(readValuefromAppConfig("app.space.property.filePath.target")).replace('"',
                                                                                                                  '')
    logger.info("spacePropertyConfigFilePathTarget : " + str(spacePropertyConfigFilePathTarget))
    logger.info(" ips : " + str(ips) + " tieredCriteriaConfigFilePath :" + str(
        tieredCriteriaConfigFilePath) + " tieredCriteriaConfigFilePathTarget : " + str(
        tieredCriteriaConfigFilePathTarget))
    logger.info(" ips : " + str(ips) + " spacePropertyConfigFilePath :" + str(
        spacePropertyConfigFilePath) + " spacePropertyConfigFilePathTarget : " + str(spacePropertyConfigFilePathTarget))
    if (copyFile(ips, tieredCriteriaConfigFilePath, tieredCriteriaConfigFilePathTarget)):
        logger.info("File copied successfully.. taking backup of source file")
        now = dt.now()
        logger.info("now : " + str(now))
        timeStamp = now.strftime("%Y%m%d%H%M%S")
        logger.info("timeStamp : " + str(timeStamp))
        tieredCriteriaConfigFilePathBckupFile = str(tieredCriteriaConfigFilePath) + ".bck." + str(timeStamp)
        head, tail = os.path.split(tieredCriteriaConfigFilePathBckupFile)
        logger.info("tail :" + str(tail))
        bkpFileName = str(tail)
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
        logger.info("sourceInstallerDirectory:" + sourceInstallerDirectory)
        tieredCriteriaConfigFilePathBckupFile = str(
            sourceInstallerDirectory + ".object.config.ddlparser.ts.bck.").replace('.', '/') + str(bkpFileName)
        print("tieredCriteriaConfigFilePathBckupFile" + str(tieredCriteriaConfigFilePathBckupFile))
        logger.info("tieredCriteriaConfigFilePathBckupFile : " + str(tieredCriteriaConfigFilePathBckupFile))
        userCMD = os.getlogin()
        if userCMD == 'ec2-user':
            cmd = "sudo cp " + str(tieredCriteriaConfigFilePath) + " " + str(tieredCriteriaConfigFilePathBckupFile)
        else:
            cmd = "cp " + str(tieredCriteriaConfigFilePath) + " " + str(tieredCriteriaConfigFilePathBckupFile)
        # print(cmd)
        logger.info("cmd : " + str(cmd))
        # set_value_in_property_file('app.tieredstorage.criteria.filepathbackup.prev',str(readValuefromAppConfig("app.tieredstorage.criteria.filepathbackup")))
        # set_value_in_property_file('app.tieredstorage.criteria.filepathbackup',str(tieredCriteriaConfigFilePathBckupFile))
        set_value_yaml_config('currentTs', str(bkpFileName))
        set_value_yaml_config('previousTs', str(readValueFromYaml(".object.config.ddlparser.ts.bck.currentTs")))
        status = os.system(cmd)
        logger.info("cp status :" + str(status))
    if (copyFile(ips, spacePropertyConfigFilePath, spacePropertyConfigFilePathTarget)):
        logger.info("File spaceproperty copied successfully.. taking backup of source file")
        now = dt.now()
        logger.info("now : " + str(now))
        timeStamp = now.strftime("%Y%m%d%H%M%S")
        logger.info("timeStamp : " + str(timeStamp))
        # spacePropertyConfigFilePathBckupFile = str(spacePropertyConfigFilePath)+".bck."+str(timeStamp)
        # logger.info("spacePropertyConfigFilePathBckupFile : "+str(spacePropertyConfigFilePathBckupFile))
        # cmd = "cp "+str(spacePropertyConfigFilePath)+" "+str(spacePropertyConfigFilePathBckupFile)
        # logger.info("cmd : "+str(cmd))
        # set_value_in_property_file('app.space.property.filepathbackup',str(spacePropertyConfigFilePathBckupFile))
        status = os.system(cmd)
        logger.info("cp status :" + str(status))


def updatecachepolicySummary():
    logger.info("updatecachepolicySummary() ")
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleWarning("***Summary***")
    maxWorker = str(getNumberOfSpaceInstances())
    print(Fore.GREEN + "1. " +
          Fore.GREEN + "Batch max size  = " + Fore.RESET,
          Fore.GREEN + maxWorker + Fore.RESET)
    verboseHandle.printConsoleWarning("------------------------------------------------------------")


def listGSC(managerHost):
    global managerHostConfig
    global spaceNumber
    global spaceName
    managerHostConfig = managerHost
    try:
        spaceNumber = str(userInputWrapper(Fore.YELLOW + "Enter space number to get details :" + Fore.RESET))
        while (len(str(spaceNumber)) == 0 or (not spaceNumber.isdigit())):
            spaceNumber = str(userInputWrapper(Fore.YELLOW + "Enter space number to get details :" + Fore.RESET))
        logger.info("spaceNumber : " + str(spaceNumber))
        logger.info("SpaceName = " + str(gs_space_host_dictionary_obj.get(str(spaceNumber))))
        spaceName = str(gs_space_host_dictionary_obj.get(str(spaceNumber)))
        logger.info("listGSC for manager:" + str(managerHost))

        displayOnlyGSC()
        inputParams()
        truncateInSqlLite()
        updatecachepolicySummary()
        confirmAndProceedForAll()

        return
    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    logger.info("odsx_security_tieredstorage_updatecachepolicy")
    loggerTiered.info("Updatecachepolicy")
    verboseHandle.printConsoleWarning(
        "Menu -> TieredStorage -> Update Cache Policy -> For Srno Rolling Update All -> Pair Machine")
    username = ""
    password = ""
    appId = ""
    safeId = ""
    objectId = ""
    signal.signal(signal.SIGINT, signal_handler)
    try:
        appId = str(readValuefromAppConfig("app.space.security.appId")).replace('"', '')
        safeId = str(readValuefromAppConfig("app.space.security.safeId")).replace('"', '')
        objectId = str(readValuefromAppConfig("app.space.security.objectId")).replace('"', '')
        logger.info("appId : " + appId + " safeID : " + safeId + " objectID : " + objectId)
        managerNodes = config_get_manager_node()
        if (len(str(managerNodes)) > 0):
            logger.info("managerNodes: main" + str(managerNodes))
            spaceNodes = config_get_space_hosts()
            logger.info("spaceNodes: main" + str(spaceNodes))
            managerHost = getManagerHost(managerNodes)
            logger.info("managerHost : " + str(managerHost))
            if (len(str(managerHost)) > 0):
                username = str(getUsernameByHost(managerHost, appId, safeId, objectId))
                password = str(getPasswordByHost(managerHost, appId, safeId, objectId))
                logger.info("Manager Host :" + str(managerHost))
                gs_space_host_dictionary_obj = listSpacesOnServer(managerHost)
                logger.info(" gs_space_host_dictionary_obj :" + str(len(gs_space_host_dictionary_obj)))
                if (len(gs_space_host_dictionary_obj) > 0):
                    createDB2EntryInSqlLite()
                    listGSC(managerHost)
                else:
                    verboseHandle.printConsoleInfo("No space found.")
                # confirmParamAndRestartGSC()
            else:
                logger.info("Please check manager server status.")
                verboseHandle.printConsoleInfo("Please check manager server status.")
        else:
            logger.info("No Manager configuration found please check.")
            verboseHandle.printConsoleInfo("No Manager configuration found please check.")
    except Exception as e:
        # verboseHandle.printConsoleError("Eror in odsx_tieredstorage_updatecachepolicy : "+str(e))
        logger.error("Exception in tieredStorage_updatecachepolicy.py" + str(e))
        handleException(e)
