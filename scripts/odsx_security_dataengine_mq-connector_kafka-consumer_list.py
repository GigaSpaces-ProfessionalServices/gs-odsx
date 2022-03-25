#!/usr/bin/env python3

import os, time, requests,json
from colorama import Fore
from scripts.logManager import LogManager
from utils.odsx_print_tabular_data import printTabular
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_validation import getSpaceServerStatus
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_ssh import executeRemoteCommandAndGetOutput
from requests.auth import HTTPBasicAuth

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

def listDeployed(managerHost):
    global gs_space_dictionary_obj
    try:
        logger.info("managerHost :"+str(managerHost))
        response = requests.get("http://"+str(managerHost)+":8090/v2/pus/",auth = HTTPBasicAuth(username,password))
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Resources on cluster:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Name"+Fore.RESET,
                   Fore.YELLOW+"Host"+Fore.RESET,
                   Fore.YELLOW+"Zone"+Fore.RESET,
                   Fore.YELLOW+"processingUnitType"+Fore.RESET,
                   Fore.YELLOW+"Status"+Fore.RESET
                   ]
        gs_space_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_dictionary_obj : "+str(gs_space_dictionary_obj))
        counter=0
        dataTable=[]
        for data in jsonArray:
            hostId=''
            response2 = requests.get("http://"+str(managerHost)+":8090/v2/pus/"+str(data["name"])+"/instances",auth = HTTPBasicAuth(username,password))
            jsonArray2 = json.loads(response2.text)
            for data2 in jsonArray2:
                hostId=data2["hostId"]
            if(len(str(hostId))==0):
               hostId="N/A"
            if(str(data["name"]).casefold().__contains__('adabasconsumer')):
                dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                             Fore.GREEN+data["name"]+Fore.RESET,
                             Fore.GREEN+str(hostId)+Fore.RESET,
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

def getUsernameByHost(managerHost):
    logger.info("getUsernameByHost()")
    cmdToExecute = '/opt/CARKaim/sdk/clipasswordsdk GetPassword -p AppDescs.AppID='+appId+' -p Query="Safe='+safeId+';Folder=;Object='+objectId+';" -o PassProps.UserName'
    logger.info("cmdToExecute : "+str(cmdToExecute))
    output = executeRemoteCommandAndGetOutput(managerHost,"root",cmdToExecute)
    output=str(output).replace('\n','')
    logger.info("Username : "+output)
    return output

def getPasswordByHost(managerHost):
    logger.info("getPasswordByHost()")
    cmdToExecute = '/opt/CARKaim/sdk/clipasswordsdk GetPassword -p AppDescs.AppID='+appId+' -p Query="Safe='+safeId+';Folder=;Object='+objectId+';" -o Password'
    logger.info("cmdToExecute : "+str(cmdToExecute))
    output = executeRemoteCommandAndGetOutput(managerHost,"root",cmdToExecute)
    output=str(output).replace('\n','')
    logger.info("Password : "+output)
    return  output

if __name__ == '__main__':
    logger.info("odsx_security_mq-connector_kafka-consumer_undeploy")
    verboseHandle.printConsoleWarning("Menu -> Security -> MQ-Connector -> Kafka consumer -> List")
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
        logger.info("managerNodes: main"+str(managerNodes))
        if(len(str(managerNodes))>0):
            managerHost = getManagerHost(managerNodes)
            username = str(getUsernameByHost(managerHost))
            password = str(getPasswordByHost(managerHost))
            listDeployed(managerHost)
    except Exception as e:
        verboseHandle.printConsoleError("Eror in odsx_tieredstorage_undeployed : "+str(e))
        logger.error("Exception in tieredStorage_undeployed.py"+str(e))
        handleException(e)