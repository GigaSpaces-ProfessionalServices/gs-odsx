#!/usr/bin/env python3

import glob
import json
import os
import requests
import subprocess
import time

from colorama import Fore
from requests.auth import HTTPBasicAuth

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValueByConfigObj, getYamlFilePathInsideFolder, getYamlFileNamesInsideFolderList
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_ssh import executeRemoteCommandAndGetOutput
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_db2feeder_utilities import getPasswordByHost, getUsernameByHost
from utils.odsx_keypress import userInputWrapper
from utils.odsx_print_tabular_data import printTabular

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
clusterHosts = []
confirmCreateGSC=''

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR


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

class host_dictionary_obj(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

def executeLocalCommandAndGetOutput(commandToExecute):
    logger.info("executeLocalCommandAndGetOutput() cmd :" + str(commandToExecute))
    cmd = commandToExecute
    cmdArray = cmd.split(" ")
    process = subprocess.Popen(cmdArray, stdout=subprocess.PIPE)
    out, error = process.communicate()
    out = out.decode()
    return str(out).replace('\n', '')

def getBootstrapAddress(hostConfig):
    logger.info("getBootstrapAddress()")
    bootstrapAddress=''
    for host in hostConfig.split(','):
        bootstrapAddress=bootstrapAddress+host+':9092,'
    bootstrapAddress=bootstrapAddress[:-1]
    logger.info("getBootstrapAddress : "+str(bootstrapAddress))
    return bootstrapAddress

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

def listDeployed(managerHost):
    global gs_space_dictionary_obj
    global activefeeder
    activefeeder=[]
    try:
        logger.info("managerHost :"+str(managerHost))
        response = requests.get("http://"+str(managerHost)+":8090/v2/pus/", auth=HTTPBasicAuth(username, password))
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
        for data in jsonArray:
            if(str(data["name"]).casefold().__contains__("notifier")):
                dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                             Fore.GREEN+data["name"]+Fore.RESET,
                             Fore.GREEN+data["resource"]+Fore.RESET,
                             Fore.GREEN+str(data["sla"]["zones"])+Fore.RESET,
                             Fore.GREEN+data["processingUnitType"]+Fore.RESET,
                             Fore.GREEN+data["status"]+Fore.RESET
                             ]
                gs_space_dictionary_obj.add(str(counter+1),str(data["name"]))
                activefeeder.append(str(data["name"]))
                counter=counter+1
                dataTable.append(dataArray)
        printTabular(None,headers,dataTable)
        return gs_space_dictionary_obj
    except Exception as e:
        handleException(e)

def listSpacesOnServer(managerNodes):
    try:
        logger.info("listSpacesOnServer : managerNodes :"+str(managerNodes))
        managerHost=''
        for node in managerNodes:
            status = getSpaceServerStatus(os.getenv(node.ip))
            logger.info("Ip :"+str(os.getenv(node.ip))+"Status : "+str(status))
            if(status=="ON"):
                managerHost = os.getenv(node.ip);
        logger.info("managerHost :"+managerHost)
        response = requests.get("http://"+managerHost+":8090/v2/spaces", auth=HTTPBasicAuth(username, password))
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Existing spaces on cluster:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Name"+Fore.RESET,
                   Fore.YELLOW+"PU Name"+Fore.RESET
                   ]
        gs_space_host_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_host_dictionary_obj : "+str(gs_space_host_dictionary_obj))
        counter=0
        dataTable=[]
        for data in jsonArray:
            dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                         Fore.GREEN+data["name"]+Fore.RESET,
                         Fore.GREEN+data["processingUnitName"]+Fore.RESET
                         ]
            gs_space_host_dictionary_obj.add(str(counter+1),str(data["name"]))
            counter=counter+1
            dataTable.append(dataArray)
        #printTabular(None,headers,dataTable)
        return gs_space_host_dictionary_obj
    except Exception as e:
        handleException(e)

def get_gs_host_details(managerNodes):
    try:
        logger.info("get_gs_host_details() : managerNodes :"+str(managerNodes))
        for node in managerNodes:
            status = getSpaceServerStatus(os.getenv(node.ip))
            if(status=="ON"):
                managerHostConfig = os.getenv(node.ip)
        logger.info("managerHostConfig : "+str(managerHostConfig))
        response = requests.get('http://'+managerHostConfig+':8090/v2/hosts', headers={'Accept': 'application/json'}, auth=HTTPBasicAuth(username, password))
        logger.info("response status of host :"+str(managerHostConfig)+" status :"+str(response.status_code))
        jsonArray = json.loads(response.text)
        gs_servers_host_dictionary_obj = host_dictionary_obj()
        for data in jsonArray:
            gs_servers_host_dictionary_obj.add(str(data['name']),str(data['address']))
        logger.info("gs_servers_host_dictionary_obj : "+str(gs_servers_host_dictionary_obj))
        return gs_servers_host_dictionary_obj
    except Exception as e:
        handleException(e)

def displaySpaceHostWithNumber(managerNodes, spaceNodes):
    try:
        logger.info("displaySpaceHostWithNumber() managerNodes :"+str(managerNodes)+" spaceNodes :"+str(spaceNodes))
        gs_host_details_obj = get_gs_host_details(managerNodes)
        logger.info("gs_host_details_obj : "+str(gs_host_details_obj))
        counter = 0
        space_dict_obj = host_dictionary_obj()
        logger.info("space_dict_obj : "+str(space_dict_obj))
        for node in spaceNodes:
            if(gs_host_details_obj.__contains__(str(os.getenv(node.name))) or (str(os.getenv(node.name)) in gs_host_details_obj.values())):
                space_dict_obj.add(str(counter+1),os.getenv(node.name))
                counter=counter+1
        logger.info("space_dict_obj : "+str(space_dict_obj))
        headers = [Fore.YELLOW+"No"+Fore.RESET,
                   Fore.YELLOW+"Host"+Fore.RESET]
        dataTable=[]
        for data in range (1,len(space_dict_obj)+1):
            dataArray = [Fore.GREEN+str(data)+Fore.RESET,
                         Fore.GREEN+str(space_dict_obj.get(str(data)))+Fore.RESET]
            dataTable.append(dataArray)
        return space_dict_obj
    except Exception as e:
        handleException(e)


def proceedToCreateGSC(zoneGSC,newGSCCount):
    logger.info("proceedToCreateGSC()")
    idx = newGSCCount % len(spaceNodes)
    host = spaceNodes[idx]
    commandToExecute = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh --username="+username+" --password="+password+" container create --count="+str(numberOfGSC)+" --zone="+str(zoneGSC)+" --memory="+str(memoryGSC)+" "+str(os.getenv(host.ip))+" | grep -v JAVA_HOME"
    verboseHandle.printConsoleInfo("Creating container count : "+str(numberOfGSC)+" zone="+str(zoneGSC)+" memory="+str(memoryGSC)+" host="+str(os.getenv(host.ip)))
    logger.info(commandToExecute)
    with Spinner():
        output = executeRemoteCommandAndGetOutput(managerHost, 'root', commandToExecute)
        print(output)
        logger.info("Output:"+str(output))

def createGSCInputParam():
    logger.info("createGSCInputParam()")
    global numberOfGSC
    global memoryGSC

    numberOfGSC = str(readValuefromAppConfig("app.dataengine.notifier.gscpercluster"))
    logger.info("numberOfGSC :"+str(numberOfGSC))
    memoryGSC = str(readValuefromAppConfig("app.dataengine.notifier.gsc.memory"))

def uploadFileRest(managerHostConfig):
    try:
        logger.info("uploadFileRest : managerHostConfig : "+str(managerHostConfig))
        pathOfSourcePU=str(getYamlFilePathInsideFolder(".notifier.jars.notifierPersonalJarFile"))
        verboseHandle.printConsoleWarning("Proceeding for 1 : "+pathOfSourcePU)
        status = os.system("curl -X PUT -F 'file=@"+str(pathOfSourcePU)+"' http://"+managerHostConfig+":8090/v2/pus/resources -u "+username+":"+password+"")
        print("\n")
        logger.info("status : "+str(status))
        pathOfSourcePU=str(getYamlFilePathInsideFolder(".notifier.jars.notifierMessageJarFile"))
        verboseHandle.printConsoleWarning("Proceeding for 2 : "+pathOfSourcePU)
        status = os.system("curl -X PUT -F 'file=@"+str(pathOfSourcePU)+"' http://"+managerHostConfig+":8090/v2/pus/resources -u "+username+":"+password+"")
        print("\n")
        logger.info("status : "+str(status))
    except Exception as e:
        handleException(e)

def getDataPUREST(resource,resourceName,zoneOfPU):
    data={
        "resource": ""+resource+"",
        "topology": {
            "instances": 1,
        },
        "sla": {
            "zones": [
                ""+zoneOfPU+""
            ],
        },
        "name": ""+resourceName+"",
        "maxInstancesPerMachine": int(maxInstancesPerMachine),
        "contextProperties": {
            "minPort" : "8113",
            "maxPort" : "8311",
            "apiPushUri" : "https://apigwit.tau.ac.il/test/os/v1/OSPushNotification/SendPushNotification",
            "space.name" : ""+spaceName+"",
            "lookup.locators" : ""+managerHost+""
        }
    }
    #print(data)
    return data

def validateResponseGetDescription(responseCode):
    logger.info("validateResponse() "+str(responseCode))
    response = requests.get("http://"+managerHost+":8090/v2/requests/"+str(responseCode), auth=HTTPBasicAuth(username, password))
    jsonData = json.loads(response.text)
    logger.info("response : "+str(jsonData))
    if(str(jsonData["status"]).__contains__("failed")):
        return "Status :"+str(jsonData["status"])+" Description:"+str(jsonData["error"])
    else:
        return "Status :"+str(jsonData["status"])+" Description:"+str(jsonData["description"])

def checkResponse(data):
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    response = requests.post("http://"+managerHost+":8090/v2/pus",data=json.dumps(data),headers=headers, auth=HTTPBasicAuth(username, password))
    deployResponseCode = str(response.content.decode('utf-8'))
    print("deployResponseCode : "+str(deployResponseCode))
    logger.info("deployResponseCode :"+str(deployResponseCode))

    status = validateResponseGetDescription(deployResponseCode)
    logger.info("response.status_code :"+str(response.status_code))
    logger.info("response.content :"+str(response.content) )
    if(response.status_code==202):
        logger.info("Response :"+str(status))
        retryCount=5
        with Spinner():
            while(retryCount>0 or (not str(status).casefold().__contains__('successful')) or (not str(status).casefold().__contains__('failed'))):
                status = validateResponseGetDescription(deployResponseCode)
                verboseHandle.printConsoleInfo("Response :"+str(status))
                retryCount = retryCount-1
                time.sleep(2)
                if(str(status).casefold().__contains__('successful')):
                    logger.info("status : "+str(status))
                    break
                elif(str(status).casefold().__contains__('failed')):
                    break
    else:
        logger.info("Unable to deploy 1 :"+str(status))
        verboseHandle.printConsoleInfo("Unable to deploy 1 : "+str(status))

def proceedToDeployPU():
    try:
        logger.info("proceedToDeployPU()")
        #logger.info("url : "+"http://"+managerHost+":8090/v2/pus", auth=HTTPBasicAuth(username, password))
        newGSCCount=0
        resource = str(getYamlFileNamesInsideFolderList(".notifier.jars.notifierPersonalJarFile"))
        if(confirmCreateGSC=='y'):
            proceedToCreateGSC('personal_message_notifier',newGSCCount)
            newGSCCount=newGSCCount+1
            proceedToCreateGSC('group_message_notifier',newGSCCount)
        puName = "personal_message_notifier_service"
        data = getDataPUREST(resource,puName,'personal_message_notifier')
        logger.info("data of payload2 :"+str(data))
        checkResponse(data)
        resource = str(getYamlFileNamesInsideFolderList(".notifier.jars.notifierMessageJarFile"))
        puName = "group_message_notifier_service"
        data = getDataPUREST(resource,puName,'group_message_notifier')
        logger.info("data of payload2 :"+str(data))
        checkResponse(data)
    except Exception as e :
        handleException(e)

def displaySummaryOfInputParam():
    logger.info("displaySummaryOfInputParam()")
    verboseHandle.printConsoleInfo("------------------------------------------------------------")
    verboseHandle.printConsoleInfo("***Summary***")
    if(confirmCreateGSC=='y'):
        verboseHandle.printConsoleInfo("Enter number of GSCs per cluster :"+str(numberOfGSC))
        verboseHandle.printConsoleInfo("Enter memory of GSC :"+memoryGSC)
    verboseHandle.printConsoleInfo("Enter source file path of notifier personal jar file including file name : "+str(getYamlFilePathInsideFolder(".notifier.jars.notifierPersonalJarFile")))
    verboseHandle.printConsoleInfo("Enter source file path of notifier message jar file including file name : "+str(getYamlFilePathInsideFolder(".notifier.jars.notifierMessageJarFile")))

def proceedToDeployPUInputParam(managerHost):
    logger.info("proceedToDeployPUInputParam()")
    global partition
    partition='1'
    global spaceName
    spaceName = str(readValueByConfigObj("app.dataengine.notifier.space.name"))

    global maxInstancesPerMachine
    maxInstancesPerMachine = '1'
    logger.info("maxInstancePerVM Of PU :"+str(maxInstancesPerMachine))
    displaySummaryOfInputParam()
    finalConfirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to proceed ? (y/n) [y] :"+Fore.RESET))
    if(len(str(finalConfirm))==0):
        finalConfirm='y'
    if(finalConfirm=='y'):
        uploadFileRest(managerHost)
        proceedToDeployPU()
    else:
        return

if __name__ == '__main__':
    logger.info("odsx_dataengine_notifier_install")
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Notifier -> Install-Deploy')
    username = ""
    password = ""
    try:
        managerNodes = config_get_manager_node()
        logger.info("managerNodes: main"+str(managerNodes))
        if(len(str(managerNodes))>0):
            username = str(getUsernameByHost())
            password = str(getPasswordByHost())

            spaceNodes = config_get_space_hosts()
            logger.info("spaceNodes: main"+str(spaceNodes))
            managerHost = getManagerHost(managerNodes)
            logger.info("managerHost : main"+str(managerHost))
            if(len(str(managerHost))>0):
                listSpacesOnServer(managerNodes)
                listDeployed(managerHost)
                space_dict_obj = displaySpaceHostWithNumber(managerNodes,spaceNodes)
                if(len(space_dict_obj)>0):
                    confirmCreateGSC = str(readValuefromAppConfig("app.dataengine.notifier.gsc.create"))
                    if(len(str(confirmCreateGSC))==0 or confirmCreateGSC=='y'):
                        confirmCreateGSC='y'
                        createGSCInputParam()
                    proceedToDeployPUInputParam(managerHost)
                else:
                    logger.info("Please check space server.")
                    verboseHandle.printConsoleInfo("Please check space server.")
            else:
                logger.info("Please check manager server status.")
                verboseHandle.printConsoleInfo("Please check manager server status.")
        else:
            logger.info("No Manager configuration found please check.")
            verboseHandle.printConsoleInfo("No Manager configuration found please check.")
    except Exception as e:
        handleException(e)
