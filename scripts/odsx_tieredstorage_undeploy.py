#!/usr/bin/env python3

import os, time
from colorama import Fore
from scripts.logManager import LogManager
import requests, json, math
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_print_tabular_data import printTabular
from utils.ods_ssh import executeRemoteShCommandAndGetOutput,executeRemoteCommandAndGetOutput
from scripts.spinner import Spinner

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
            status = getSpaceServerStatus(node.ip)
            if(status=="ON"):
                managerHost = node.ip
        return managerHost
    except Exception as e:
        handleException(e)

def getTieredStorageSpaces():
    logger.info("getTieredStorageSpaces()")
    #check for Tiered storage space
    responseTiered = requests.get("http://"+str(managerHost)+":8090/v2/internal/spaces/utilization")
    logger.info("Response status of spaces/utilization : "+str(responseTiered.status_code)+" content : "+str(responseTiered.content))
    jsonArrayTiered = json.loads(responseTiered.text)
    tieredSpace = []
    for data in jsonArrayTiered:
        if(data["tiered"]==True):
            tieredSpace.append(str(data["serviceName"]))
    logger.info("tieresSpace : "+str(tieredSpace))
    return tieredSpace

def listUndeployedPUsOnServer(managerHost):
    logger.info("listUndeployedPUsOnServer()")
    global gs_pu_dictionary_obj
    try:
        logger.info("managerHost :"+str(managerHost))
        response = requests.get("http://"+str(managerHost)+":8090/v2/pus/undeployed")
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
        puSrNumber = str(input("Enter PU number to remove :"))
        while(len(str(puSrNumber))==0 or (not puSrNumber.isdigit())):
            puSrNumber = str(input("Enter PU number to remove :"))
        logger.info("puSrNumber :"+str(puSrNumber))
        spaceTobeUndeploy = gs_pu_dictionary_obj.get(puSrNumber)
        logger.info("spaceTobeUndeploy :"+str(spaceTobeUndeploy))
        logger.info("managerHost :"+managerHost)
        response = requests.delete("http://"+managerHost+":8090/v2/pus/undeployed/"+str(spaceTobeUndeploy))
        verboseHandle.printConsoleInfo(str(response.status_code))
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
        if(response.status_code==200):
            logger.info("PU :"+str(spaceTobeUndeploy)+" has been undeployed.")
            verboseHandle.printConsoleInfo("PU :"+str(spaceTobeUndeploy)+" has been undeployed.")
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

            response = requests.delete("http://"+managerHost+":8090/v2/pus/undeployed/"+str(spaceTobeUndeploy))
            verboseHandle.printConsoleInfo(str(response.status_code))
            logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
            if(response.status_code==200):
                logger.info("PU :"+str(spaceTobeUndeploy)+" has been undeployed.")
                verboseHandle.printConsoleInfo("PU :"+str(spaceTobeUndeploy)+" has been undeployed.")
            else:
                logger.info("PU :"+str(spaceTobeUndeploy)+" has not been undeployed.")
                verboseHandle.printConsoleInfo("PU :"+str(spaceTobeUndeploy)+" has not been undeployed.")
    except Exception as e:
        handleException(e)

def getUserInput(managerHost):
    logger.info("getUserInput()")
    try:
        typeOfRemove = str(input(Fore.YELLOW+"[1] For individual undeployed PU\n[Enter] For all above undeployed PUs \n[99] For exist. :"+Fore.RESET))
        print(typeOfRemove)
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
    try:
        logger.info("managerHost :"+str(managerHost))
        response = requests.get("http://"+str(managerHost)+":8090/v2/pus/")
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Resources on cluster:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Name"+Fore.RESET,
                   Fore.YELLOW+"Resource"+Fore.RESET,
                   Fore.YELLOW+"Zone"+Fore.RESET,
                   Fore.YELLOW+"processingUnitType"+Fore.RESET,
                   Fore.YELLOW+"Status"+Fore.RESET
                   ]
        gs_space_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_dictionary_obj : "+str(gs_space_dictionary_obj))
        counter=0
        dataTable=[]
        tieredSpaces = getTieredStorageSpaces()
        for data in jsonArray:
            if(tieredSpaces.__contains__(str(data["name"]))):
                dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                             Fore.GREEN+data["name"]+Fore.RESET,
                             Fore.GREEN+data["resource"]+Fore.RESET,
                             Fore.GREEN+str(data["sla"]["zones"])+Fore.RESET,
                             Fore.GREEN+data["processingUnitType"]+Fore.RESET,
                             Fore.GREEN+data["status"]+Fore.RESET
                            ]
                gs_space_dictionary_obj.add(str(counter+1),str(data["name"]))
                counter=counter+1
                dataTable.append(dataArray)
        printTabular(None,headers,dataTable)
        return gs_space_dictionary_obj
    except Exception as e:
        handleException(e)

def proceedForAllUndeploy(managerHost):
    logger.info("proceedForAllUndeploy()")
    try:
        for key,value in gs_space_dictionary_obj.items():
            logger.info(str(key)+" : "+str(value))
            spaceTobeUndeploy = gs_space_dictionary_obj.get(str(key))
            print(spaceTobeUndeploy)

            #response = requests.delete("http://"+managerHost+":8090/v2/pus/"+str(spaceTobeUndeploy))
            logger.info("managerHost All: "+str(managerHost)+" drainMode: "+str(drainMode)+" drainTimeout: "+str(drainTimeout))
            logger.info("URL DrainMode : http://"+str(managerHost)+":8090/v2/pus/"+str(spaceTobeUndeploy)+"?drainMode="+str(drainMode)+"&drainTimeout="+str(drainTimeout))
            response = requests.delete("http://"+str(managerHost)+":8090/v2/pus/"+str(spaceTobeUndeploy)+"?drainMode="+str(drainMode)+"&drainTimeout="+str(drainTimeout))
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
                verboseHandle.printConsoleInfo(" Undeploy  : "+str(spaceTobeUndeploy)+"   Status : "+str(status))

            else:
                logger.info("PU :"+str(spaceTobeUndeploy)+" has not been undeploy.")
                verboseHandle.printConsoleInfo("PU :"+str(spaceTobeUndeploy)+" has not been undeploy.")
    except Exception as e:
        handleException(e)

def proceedToUndeployPU(managerHost):
    logger.info("proceedToUndeployPU()")
    try:
        typeOfRemove = str(input(Fore.YELLOW+"[1] For individual undeploy PU\n[Enter] For all above PUs \n[99] For exist. :"+Fore.RESET))
        logger.info("typeOfRemove : "+str(typeOfRemove))

        if(typeOfRemove=='1'):
            spaceNumberTobeRemove = str(input(Fore.YELLOW+"Enter space / pu number to be remove : "+Fore.RESET))
            while(len(str(spaceNumberTobeRemove))==0 or (not spaceNumberTobeRemove.isdigit())):
                spaceNumberTobeRemove = str(input(Fore.YELLOW+"Enter space / pu number to be remove : "+Fore.RESET))
            logger.info("spaceNumberTobeRemove :"+str(spaceNumberTobeRemove))
            spaceTobeUndeploy = gs_space_dictionary_obj.get(spaceNumberTobeRemove)

            proceedForInputParams()

            confirmToRemoveSpace = str(input(Fore.YELLOW+"Are you sure want to remove "+str(spaceTobeUndeploy)+" ? (y/n) [y] :"))
            logger.info("confirmToRemoveSpace : "+str(confirmToRemoveSpace))
            if(len(str(confirmToRemoveSpace))==0):
                confirmToRemoveSpace='y'
            if(confirmToRemoveSpace=='y'):
                #response = requests.delete("http://"+managerHost+":8090/v2/pus/"+str(spaceTobeUndeploy))
                logger.info("managerHost undeploy: "+str(managerHost)+" drainMode: "+str(drainMode)+" drainTimeout: "+str(drainTimeout))
                logger.info("URL DrainMode :   http://"+str(managerHost)+":8090/v2/pus/"+str(spaceTobeUndeploy)+"?drainMode="+str(drainMode)+"&drainTimeout="+str(drainTimeout))
                response = requests.delete("http://"+managerHost+":8090/v2/pus/"+str(spaceTobeUndeploy)+"?drainMode="+str(drainMode)+"&drainTimeout="+str(drainTimeout))
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
                    verboseHandle.printConsoleInfo(" Undeploy  : "+str(spaceTobeUndeploy)+"   Status : "+str(status))
            else:
                    logger.info("PU :"+str(spaceTobeUndeploy)+" has not been undeployed.")
                    verboseHandle.printConsoleInfo("PU :"+str(spaceTobeUndeploy)+" has not been undeployed.")
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
        response = requests.get("http://"+managerHost+":8090/v2/requests/"+str(responseCode))
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
    drainModeConfirm = str(input(Fore.YELLOW+"Enter drain mode ["+str(drainMode)+"] :" +Fore.RESET))
    if(len(str(drainModeConfirm))>0):
        drainMode = drainModeConfirm
    logger.info("drainMode : "+str(drainMode))

    drainTimeout = readValuefromAppConfig("app.tieredstorage.drainTimeout")
    drainTimeoutConfirm = str(input(Fore.YELLOW+"Enter drain mode timeout ["+str(drainTimeout)+"] : "+Fore.RESET))
    if(len(str(drainTimeoutConfirm))>0):
        drainTimeout = drainTimeoutConfirm
    logger.info("drainTimeout : "+str(drainTimeout))

def printProgressBar(i,max,postText):
    logger.info("printProgressBar()")
    n_bar =10 #size of progress bar
    j= i/max
    print('\r')
    print(f"[{'=' * int(n_bar * j):{n_bar}s}] {int(100 * j)}%  {postText}")


def removeGSC(managerHost):
    logger.info("removeGSC()")
    zoneToDeleteGSC = str(input(Fore.YELLOW+"Enter the zone to delete GSC : "+Fore.RESET))
    while(len(str(zoneToDeleteGSC))==0):
        zoneToDeleteGSC = str(input(Fore.YELLOW+"Enter the zone to delete GSC : "+Fore.RESET))
    logger.info("zoneToDeleteGSC : "+str(zoneToDeleteGSC))
    confirmRemoveGSC = str(input(Fore.YELLOW+"Are you sure want to remove GSCs under zone ["+str(zoneToDeleteGSC)+"] ? (y/n) [y] :"))
    if(len(str(confirmRemoveGSC))==0):
        confirmRemoveGSC='y'
    if(confirmRemoveGSC=='y'):
        cmd = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh container kill --zones "+str(zoneToDeleteGSC)
        logger.info("cmd : "+str(cmd))
        print(str(cmd))
        with Spinner():
            output = executeRemoteCommandAndGetOutput(managerHost, 'root', cmd)
            print(output)

    '''
    response = requests.get("http://"+managerHost+":8090/v2/containers")
    jsonArray = json.loads(response.text)
    sizeJsonArray = (len(jsonArray))
    i=1
    percentage=0
    for data in jsonArray:
        response = requests.delete("http://"+managerHost+":8090/v2/containers/"+str(data["id"]))
        if(response.status_code==202):
            print("GSC ID "+str(data["id"])+" deleted")
        printProgressBar(i,sizeJsonArray,"Completed.")
        i=i+1
    '''

if __name__ == '__main__':
    logger.info("odsx_tieredstorage_undeploy")
    verboseHandle.printConsoleWarning("Menu -> TieredStorage -> Undeploy")
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
                gs_space_dictionary_obj = listDeployed(managerHost)
                if(len(gs_space_dictionary_obj)>0):
                    proceedToUndeployPU(managerHost)
                else:
                    logger.info("No space/pu found.")
                    verboseHandle.printConsoleInfo("No space/pu found.")
                #with Spinner():
                #    time.sleep(30)
                gs_pu_dictionary_obj = listUndeployedPUsOnServer(managerHost)
                if(len(gs_pu_dictionary_obj)>0):
                    getUserInput(managerHost)
                    gscRemove = str(input(Fore.YELLOW+"Do you want to remove gsc? (y/n) [y]:"+Fore.RESET))
                    if(len(str(gscRemove))==0):
                        gscRemove='y'
                    if(gscRemove=='y'):
                        managerHost = getManagerHost(managerNodes)
                        removeGSC(managerHost)
                else:
                    logger.info("No space/pu undeployed found.")
                    verboseHandle.printConsoleInfo("No space/pu undeployed found.")
                #confirmParamAndRestartGSC()
            else:
                logger.info("Please check manager server status.")
                verboseHandle.printConsoleInfo("Please check manager server status.")
        else:
            logger.info("No Manager configuration found please check.")
            verboseHandle.printConsoleInfo("No Manager configuration found please check.")
    except Exception as e:
        verboseHandle.printConsoleError("Eror in odsx_tieredstorage_undeployed : "+str(e))
        logger.error("Exception in tieredStorage_undeployed.py"+str(e))
        handleException(e)