#!/usr/bin/env python3

import os
import time
import sqlite3

import json
import requests
from colorama import Fore
from requests.auth import HTTPBasicAuth

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_app_config import readValueByConfigObj
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_ssh import executeRemoteCommandAndGetOutput
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_keypress import userInputWithEscWrapper, userInputWrapper
from utils.odsx_print_tabular_data import printTabular
from utils.odsx_db2feeder_utilities import getOracleQueryStatusFromSqlLite, getUsernameByHost, getPasswordByHost

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


def listUndeployedPUsOnServer(managerHost):
    logger.info("listUndeployedPUsOnServer()")
    global gs_pu_dictionary_obj
    try:
        logger.info("managerHost :"+str(managerHost))
        response = requests.get("http://"+str(managerHost)+":8090/v2/pus/undeployed",auth = HTTPBasicAuth(username, password))
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Persist resources on cluster:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Name"+Fore.RESET
                   ]
        gs_pu_dictionary_obj = host_dictionary_obj()
        logger.info("gs_pu_dictionary_obj : "+str(gs_pu_dictionary_obj))
        counter=0
        dataTable=[]
        for data in jsonArray:
            dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                         Fore.GREEN+data["name"]+Fore.RESET]
            gs_pu_dictionary_obj.add(str(counter+1),str(data["name"]))
            counter=counter+1
            dataTable.append(dataArray)
        printTabular(None,headers,dataTable)
        return gs_pu_dictionary_obj
    except Exception as e:
        handleException(e)

def proceedForIndividualUndeployed(managerHost):
    logger.info("proceedForIndividualUndeployed()")
    try:
        puSrNumber = str(userInputWrapper("Enter PU number to remove :"))
        while(len(str(puSrNumber))==0 or (not puSrNumber.isdigit())):
            puSrNumber = str(userInputWrapper("Enter PU number to remove :"))
        logger.info("puSrNumber :"+str(puSrNumber))
        spaceTobeUndeploy = gs_pu_dictionary_obj.get(puSrNumber)
        logger.info("spaceTobeUndeploy :"+str(spaceTobeUndeploy))
        logger.info("managerHost :"+managerHost)
        response = requests.delete("http://"+managerHost+":8090/v2/pus/undeployed/"+str(spaceTobeUndeploy),auth = HTTPBasicAuth(username, password))
        verboseHandle.printConsoleInfo(str(response.status_code))
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
        if(response.status_code==200):
            logger.info("PU :"+str(spaceTobeUndeploy)+" has been undeployed.")
            verboseHandle.printConsoleInfo("PU :"+str(spaceTobeUndeploy)+" has been undeployed.")
            deleteOracleEntryFromSqlLite(spaceTobeUndeploy)
        else:
            logger.info("PU :"+str(spaceTobeUndeploy)+" has not been undeployed.")
            verboseHandle.printConsoleInfo("PU :"+str(spaceTobeUndeploy)+" has not been undeployed.")
    except Exception as e:
        handleException(e)

def proceedForAllUndeployed(managerHost):
    logger.info("proceedForAllUndeployed()")
    try:
        for key,value in gs_pu_dictionary_obj.items():
            logger.info(str(key)+" : "+str(value))
            spaceTobeUndeploy = gs_pu_dictionary_obj.get(str(key))
            print(spaceTobeUndeploy)

            response = requests.delete("http://"+managerHost+":8090/v2/pus/undeployed/"+str(spaceTobeUndeploy),auth = HTTPBasicAuth(username, password))
            verboseHandle.printConsoleInfo(str(response.status_code))
            logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
            if(response.status_code==200):
                logger.info("PU :"+str(spaceTobeUndeploy)+" has been undeployed.")
                verboseHandle.printConsoleInfo("PU :"+str(spaceTobeUndeploy)+" has been undeployed.")
                deleteOracleEntryFromSqlLite(spaceTobeUndeploy)
            else:
                logger.info("PU :"+str(spaceTobeUndeploy)+" has not been undeployed.")
                verboseHandle.printConsoleInfo("PU :"+str(spaceTobeUndeploy)+" has not been undeployed.")
    except Exception as e:
        handleException(e)

def deleteOracleEntryFromSqlLite(puName):
    logger.info("deleteOracleEntryFromSqlLite()")
    try:
        db_file = str(readValueByConfigObj("app.dataengine.oracle-feeder.sqlite.dbfile")).replace('"','').replace(' ','')
        logger.info("db_file :"+str(db_file))
        cnx = sqlite3.connect(db_file)
        logger.info("SQL : DELETE FROM oracle_host_port where feeder_name like '%"+str(puName)+"%'")
        cnx.execute("DELETE FROM oracle_host_port where feeder_name like '%"+str(puName)+"%'")
        cnx.commit()
        cnx.close()
    except Exception as e:
        handleException(e)

def getUserInput(managerHost):
    logger.info("getUserInput()")
    try:
        typeOfRemove = str(userInputWithEscWrapper(Fore.YELLOW+"[1] For individual undeployed PU\n[Enter] For all above undeployed PUs \n[99] For exist. :"+Fore.RESET))
        #print(typeOfRemove)
        logger.info("typeOfRemove : "+str(typeOfRemove))
        if(typeOfRemove=='1'):
            proceedForIndividualUndeployed(managerHost)
        elif(str(typeOfRemove)=='99'):
            print("99")
            logger.info("99")
            return
        elif(len(str(typeOfRemove))==0):
            proceedForAllUndeployed(managerHost)
    except Exception as e:
        handleException(e)


def listDeployed(managerHost):
    global gs_space_dictionary_obj
    global gs_pu_zone_dictionary_obj
    try:
        logger.info("managerHost :"+str(managerHost))
        response = requests.get("http://"+str(managerHost)+":8090/v2/pus/",auth = HTTPBasicAuth(username, password))
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Resources on cluster:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Name"+Fore.RESET,
                   Fore.YELLOW+"Resource"+Fore.RESET,
                   Fore.YELLOW+"Zone"+Fore.RESET,
                   Fore.YELLOW+"processingUnitType"+Fore.RESET
                   ]
        gs_space_dictionary_obj = host_dictionary_obj()
        gs_pu_zone_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_dictionary_obj : "+str(gs_space_dictionary_obj))
        counter=0
        dataTable=[]
        for data in jsonArray:
            queryStatus = str(getOracleQueryStatusFromSqlLite(str(data["name"]))).replace('"','')
            if(str(data["name"]).__contains__('oracle')):
                dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                             Fore.GREEN+data["name"]+Fore.RESET,
                             Fore.GREEN+data["resource"]+Fore.RESET,
                             Fore.GREEN+str(data["sla"]["zones"])+Fore.RESET,
                             Fore.GREEN+str(queryStatus)+Fore.RESET
                             ]
                gs_space_dictionary_obj.add(str(counter+1),str(data["name"]))
                gs_pu_zone_dictionary_obj.add(str(counter+1),str(data["sla"]["zones"]))
                counter=counter+1
                dataTable.append(dataArray)
        logger.info("gs_pu_zone_dictionary_obj : "+str(gs_pu_zone_dictionary_obj))
        printTabular(None,headers,dataTable)
        return gs_space_dictionary_obj
    except Exception as e:
        handleException(e)

def proceedForAllUndeploy(managerHost):
    logger.info("proceedForAllUndeploy()")
    try:
        counter=1
        gscRemove=''
        for key,value in gs_space_dictionary_obj.items():
            logger.info(str(key)+" : "+str(value))
            spaceTobeUndeploy = gs_space_dictionary_obj.get(str(key))
            logger.info("spaceTobeUndeploy : "+str(spaceTobeUndeploy))

            #response = requests.delete("http://"+managerHost+":8090/v2/pus/"+str(spaceTobeUndeploy))
            logger.info("managerHost All: "+str(managerHost)+" drainMode: "+str(drainMode)+" drainTimeout: "+str(drainTimeout))
            logger.info("URL DrainMode : http://"+str(managerHost)+":8090/v2/pus/"+str(spaceTobeUndeploy)+"?drainMode="+str(drainMode)+"&drainTimeout="+str(drainTimeout))
            response = requests.delete("http://"+str(managerHost)+":8090/v2/pus/"+str(spaceTobeUndeploy)+"?drainMode="+str(drainMode)+"&drainTimeout="+str(drainTimeout),auth = HTTPBasicAuth(username, password))
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
                        logger.info("UndeployAll :"+str(spaceTobeUndeploy)+"   Status :"+str(status))
                        #verboseHandle.printConsoleInfo("spaceID Restart :"+str(spaceIdToBeRestarted)+" status :"+str(status))
                        verboseHandle.printConsoleInfo("Undeploy  : "+str(spaceTobeUndeploy)+"   Status : "+str(status))
                deleteOracleEntryFromSqlLite(spaceTobeUndeploy)
                verboseHandle.printConsoleInfo(" Undeploy  : "+str(spaceTobeUndeploy)+"   Status : "+str(status))
            else:
                logger.info("PU :"+str(spaceTobeUndeploy)+" has not been undeploy.")
                verboseHandle.printConsoleInfo("PU :"+str(spaceTobeUndeploy)+" has not been undeploy.")
            if(len(gscRemove)==0):
                gscRemove = str(userInputWrapper(Fore.YELLOW+"Do you want to remove gsc? (y/n) [y]:"+Fore.RESET))
            if(len(str(gscRemove))==0):
                gscRemove='y'
            if(gscRemove=='y'):
                managerHost = getManagerHost(managerNodes)
                removeGSC(managerHost,str(counter),'all')
            counter=counter+1
    except Exception as e:
        handleException(e)

def proceedToUndeployPU(managerHost):
    logger.info("proceedToUndeployPU()")
    try:
        global spaceNumberTobeRemove
        typeOfRemove = str(userInputWrapper(Fore.YELLOW+"[1] For individual undeploy PU\n[Enter] For all above PUs \n[99] For exist. :"+Fore.RESET))
        logger.info("typeOfRemove : "+str(typeOfRemove))

        if(typeOfRemove=='1'):
            spaceNumberTobeRemove = str(userInputWrapper(Fore.YELLOW+"Enter space / pu number to be remove : "+Fore.RESET))
            while(len(str(spaceNumberTobeRemove))==0 or (not spaceNumberTobeRemove.isdigit())):
                spaceNumberTobeRemove = str(userInputWrapper(Fore.YELLOW+"Enter space / pu number to be remove : "+Fore.RESET))
            logger.info("spaceNumberTobeRemove :"+str(spaceNumberTobeRemove))
            spaceTobeUndeploy = gs_space_dictionary_obj.get(spaceNumberTobeRemove)

            proceedForInputParams()

            confirmToRemoveSpace = str(userInputWrapper(Fore.YELLOW+"Are you sure want to remove "+str(spaceTobeUndeploy)+" ? (y/n) [y] :"))
            logger.info("confirmToRemoveSpace : "+str(confirmToRemoveSpace))
            if(len(str(confirmToRemoveSpace))==0):
                confirmToRemoveSpace='y'
            if(confirmToRemoveSpace=='y'):
                #response = requests.delete("http://"+managerHost+":8090/v2/pus/"+str(spaceTobeUndeploy))
                logger.info("managerHost undeploy: "+str(managerHost)+" drainMode: "+str(drainMode)+" drainTimeout: "+str(drainTimeout))
                logger.info("URL DrainMode :   http://"+str(managerHost)+":8090/v2/pus/"+str(spaceTobeUndeploy)+"?drainMode="+str(drainMode)+"&drainTimeout="+str(drainTimeout))
                response = requests.delete("http://"+managerHost+":8090/v2/pus/"+str(spaceTobeUndeploy)+"?drainMode="+str(drainMode)+"&drainTimeout="+str(drainTimeout),auth = HTTPBasicAuth(username, password))
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
                            logger.info("Undeploy :"+str(spaceTobeUndeploy)+"   Status :"+str(status))
                            #verboseHandle.printConsoleInfo("spaceID Restart :"+str(spaceIdToBeRestarted)+" status :"+str(status))
                            verboseHandle.printConsoleInfo("Undeploy  : "+str(spaceTobeUndeploy)+"   Status : "+str(status))
                    deleteOracleEntryFromSqlLite(spaceTobeUndeploy)
                    verboseHandle.printConsoleInfo(" Undeploy  : "+str(spaceTobeUndeploy)+"   Status : "+str(status))
                    proceedForPersistUndeploy()

            gscRemove = str(userInputWrapper(Fore.YELLOW+"Do you want to remove gsc? (y/n) [y]:"+Fore.RESET))
            if(len(str(gscRemove))==0):
                gscRemove='y'
            if(gscRemove=='y'):
                managerHost = getManagerHost(managerNodes)
                removeGSC(managerHost,spaceNumberTobeRemove,'')
        elif(typeOfRemove=='99'):
            logger.info("99")
            return
        elif(len(str(typeOfRemove))==0):
            proceedForInputParams()
            proceedForAllUndeploy(managerHost)
    except Exception as e:
        handleException(e)

def validateResponse(responseCode):
    logger.info("validateResponse() "+str(responseCode))
    try:
        response = requests.get("http://"+managerHost+":8090/v2/requests/"+str(responseCode),auth = HTTPBasicAuth(username, password))
        jsonData = json.loads(response.text)
        logger.info("response : "+str(jsonData))
        return str(jsonData["status"])
    except Exception as e:
        handleException(e)

def proceedForInputParams():
    logger.info("proceedForInputParams()")
    global drainMode
    global drainTimeout

    #drainMode = "ATTEMPT"
    drainMode = readValuefromAppConfig("app.tieredstorage.drainmode")
    drainModeConfirm = str(userInputWrapper(Fore.YELLOW+"Enter drain mode ["+str(drainMode)+"] :" +Fore.RESET))
    if(len(str(drainModeConfirm))>0):
        drainMode = drainModeConfirm
    logger.info("drainMode : "+str(drainMode))

    drainTimeout = readValuefromAppConfig("app.tieredstorage.drainTimeout")
    drainTimeoutConfirm = str(userInputWrapper(Fore.YELLOW+"Enter drain mode timeout ["+str(drainTimeout)+"] : "+Fore.RESET))
    if(len(str(drainTimeoutConfirm))>0):
        drainTimeout = drainTimeoutConfirm
    logger.info("drainTimeout : "+str(drainTimeout))

def removeGSC(managerHost,spaceNumberTobeRemove,flag):
    logger.info("removeGSC()")
    logger.info(str(spaceNumberTobeRemove)+" :: "+str(gs_pu_zone_dictionary_obj))
    zoneToRemove =gs_pu_zone_dictionary_obj.get(str(spaceNumberTobeRemove))
    zoneToRemove = str(zoneToRemove).replace("'","").replace(']','').replace('[','')
    zoneToDeleteGSC=''
    if(str(flag)!='all'):
        zoneToDeleteGSC = str(userInputWrapper(Fore.YELLOW+"Enter the zone to delete GSC ["+str(zoneToRemove)+"] : "+Fore.RESET))
        if(len(zoneToDeleteGSC)==0):
            zoneToDeleteGSC=zoneToRemove
        logger.info("zoneToDeleteGSC : "+str(zoneToDeleteGSC))
        confirmRemoveGSC = str(userInputWrapper(Fore.YELLOW+"Are you sure want to remove GSCs under zone ["+str(zoneToDeleteGSC)+"] ? (y/n) [y] :"))
        if(len(str(confirmRemoveGSC))==0):
            confirmRemoveGSC='y'
    else:
        zoneToDeleteGSC = zoneToRemove
        confirmRemoveGSC='y'
    if(confirmRemoveGSC=='y'):
        cmd = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh --username="+username+" --password="+password+" container kill --zones "+str(zoneToDeleteGSC)
        logger.info("cmd : "+str(cmd))
        verboseHandle.printConsoleInfo("Killing container of zone : "+str(zoneToDeleteGSC))
        with Spinner():
            output = executeRemoteCommandAndGetOutput(managerHost, 'root', cmd)
            print(output)

def proceedForPersistUndeploy():
    gs_pu_dictionary_obj = listUndeployedPUsOnServer(managerHost)
    if(len(gs_pu_dictionary_obj)>0):
        getUserInput(managerHost)
    else:
        logger.info("No space/pu undeployed found.")
        verboseHandle.printConsoleInfo("No space/pu undeployed found.")

if __name__ == '__main__':
    logger.info("odsx_dataengine_oracle-feeder_undeploy")
    verboseHandle.printConsoleWarning("Menu -> DataEngine -> Oracle-Feeder -> Stop-UnDeploy")
    username = ""
    password = ""

    try:
        managerNodes = config_get_manager_node()
        if(len(str(managerNodes))>0):
            logger.info("managerNodes: main"+str(managerNodes))
            spaceNodes = config_get_space_hosts()
            logger.info("spaceNodes: main"+str(spaceNodes))
            managerHost = getManagerHost(managerNodes)
            logger.info("managerHost : "+str(managerHost))
            if(len(str(managerHost))>0):
                username = str(getUsernameByHost())
                password = str(getPasswordByHost())
                managerHostConfig = str(userInputWrapper(Fore.YELLOW+"Proceeding with manager host ["+managerHost+"] : "+Fore.RESET))
                if(len(str(managerHostConfig))>0):
                    managerHost = managerHostConfig
                logger.info("Manager Host :"+str(managerHost))
                gs_space_dictionary_obj = listDeployed(managerHost)
                if(len(gs_space_dictionary_obj)>0):
                    proceedToUndeployPU(managerHost)
                else:
                    logger.info("No space/pu found.")
                    verboseHandle.printConsoleInfo("No space/pu found.")
            else:
                logger.info("Please check manager server status.")
                verboseHandle.printConsoleInfo("Please check manager server status.")
        else:
            logger.info("No Manager configuration found please check.")
            verboseHandle.printConsoleInfo("No Manager configuration found please check.")
    except Exception as e:
        handleException(e)
