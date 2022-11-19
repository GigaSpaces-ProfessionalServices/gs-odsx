#!/usr/bin/env python3
import glob
import os, subprocess, sqlite3, json, requests
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_app_config import readValueByConfigObj, readValuefromAppConfig
from utils.ods_cluster_config import config_get_manager_node
from utils.ods_ssh import executeRemoteCommandAndGetOutput
from utils.ods_validation import getSpaceServerStatus
from requests.auth import HTTPBasicAuth

from utils.odsx_db2feeder_utilities import getMSSQLQueryStatusFromSqlLite, getPasswordByHost, getQueryStatusFromSqlLite, getUsernameByHost

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

def getAllFeeders():
    logger.info("getAllFeeders() : start")

    profile=str(readValuefromAppConfig("app.setup.profile"))
    managerNodes = config_get_manager_node()
    global gs_space_dictionary_obj
    managerHost = getManagerHost(managerNodes)
    if profile=='security':
        appId = str(readValuefromAppConfig("app.space.security.appId")).replace('"','')
        safeId = str(readValuefromAppConfig("app.space.security.safeId")).replace('"','')
        objectId = str(readValuefromAppConfig("app.space.security.objectId")).replace('"','')
        logger.info("appId : "+appId+" safeID : "+safeId+" objectID : "+objectId)
        username = str(getUsernameByHost(managerHost,appId,safeId,objectId))
        password = str(getPasswordByHost(managerHost,appId,safeId,objectId))

    try:
        response=""
        logger.info("managerHost :"+str(managerHost))
        if profile == 'security':
            response = requests.get("http://"+str(managerHost)+":8090/v2/pus/",auth = HTTPBasicAuth(username, password))
        else:
            response = requests.get("http://"+str(managerHost)+":8090/v2/pus/")
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
        jsonArray = json.loads(response.text)
        #verboseHandle.printConsoleWarning("Resources on cluster:")
        
        gs_space_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_dictionary_obj : "+str(gs_space_dictionary_obj))
        counter=0
        dataTable=[]
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))

        if (len(jsonArray) == 0):
            sourceDB2FeederShFilePathConfig = str(sourceInstallerDirectory+".db2.scripts.").replace('.','/')
            os.chdir(sourceDB2FeederShFilePathConfig)
            for file in glob.glob("load_*.sh"):
                puName = str(file).replace('load_','').replace('.sh','').casefold()
                puName = 'db2feeder_'+puName
                if(str(puName).__contains__('db2')):
                    os.chdir(sourceDB2FeederShFilePathConfig)
                    puName = str(file).replace('load_', '').replace('.sh', '').casefold()
                    file = open(file, "r")
                    for line in file:
                        if (line.startswith("curl")):
                            myString = line
                            startString = '&condition='
                            endString = "'&exclude-columns="
                            global mySubString
                            mySubString = myString[
                                          myString.find(startString) + len(startString):myString.find(endString)]
                            puName = 'db2feeder_'+puName
                            dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                                         Fore.GREEN+str(puName)+Fore.RESET,
                                         Fore.GREEN+str("-")+Fore.RESET,
                                         Fore.GREEN+str("-")+Fore.RESET,
                                         Fore.GREEN+str("-")+Fore.RESET,
                                         Fore.GREEN+str("Undeployed")+Fore.RESET,
                                         Fore.GREEN+str(mySubString)+Fore.RESET
                                         ]
                    counter=counter+1
                    dataTable.append(dataArray)

            os.getcwd()
            sourceMSSQLFeederShFilePath = str(sourceInstallerDirectory + ".mssql.scripts.").replace('.', '/')
            os.chdir(sourceMSSQLFeederShFilePath)
            for file in glob.glob("load_*.sh"):
                os.chdir(sourceMSSQLFeederShFilePath)
                puName = str(file).replace('load_', '').replace('.sh', '').casefold()
                file = open(file, "r")
                for line in file:
                    if (line.startswith("curl")):
                        myString = line
                        startString = '&condition='
                        endString = "'&exclude-columns="
                        mySubString = myString[
                                      myString.find(startString) + len(startString):myString.find(endString)]
                        puName = 'mssqlfeeder_'+puName
                        dataArray1 = [Fore.GREEN + str(counter + 1) + Fore.RESET,
                                     Fore.GREEN + puName + Fore.RESET,
                                     Fore.GREEN + str("-") + Fore.RESET,
                                     Fore.GREEN + str("-") + Fore.RESET,
                                     Fore.GREEN + str("-") + Fore.RESET,
                                     Fore.GREEN + "Undeployed" + Fore.RESET,
                                     Fore.GREEN + str(mySubString) + Fore.RESET,
                                     ]
                counter = counter + 1
                dataTable.append(dataArray1)
        for data in jsonArray:
            hostId=''
            if profile == 'security':
                response2 = requests.get("http://"+str(managerHost)+":8090/v2/pus/"+str(data["name"])+"/instances",auth = HTTPBasicAuth(username, password))
            else:
                response2 = requests.get("http://"+str(managerHost)+":8090/v2/pus/"+str(data["name"])+"/instances")
            jsonArray2 = json.loads(response2.text)
            queryStatus = str(getQueryStatusFromSqlLite(str(data["name"]))).replace('"','')
            for data2 in jsonArray2:
                hostId=data2["hostId"]
            if(len(str(hostId))==0):
                hostId="N/A"
            if(str(data["name"]).__contains__('db2')):
                directory = os.getcwd()
                sourceDB2FeederShFilePathConfig = str(sourceInstallerDirectory+".db2.scripts.").replace('.','/')
                os.chdir(sourceDB2FeederShFilePathConfig)

                for file in glob.glob("load_*.sh"):
                    os.chdir(directory)
                    puName = str(file).replace('load_','').replace('.sh','').casefold()
                    puName = 'db2feeder_'+puName
                    if(str(puName).__contains__('db2')):
                        os.chdir(sourceDB2FeederShFilePathConfig)
                        file = open(file, "r")
                        for line in file:
                            if (line.startswith("curl")):
                                myString = line
                                startString = '&condition='
                                endString = "'&exclude-columns="
                                mySubString = myString[
                                              myString.find(startString) + len(startString):myString.find(endString)]
                                dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                                             Fore.GREEN+data["name"]+Fore.RESET,
                                             Fore.GREEN+str(hostId)+Fore.RESET,
                                             Fore.GREEN+str(data["sla"]["zones"])+Fore.RESET,
                                             Fore.GREEN+str(queryStatus)+Fore.RESET,
                                             Fore.GREEN+data["status"]+Fore.RESET,
                                             Fore.GREEN + str(mySubString) + Fore.RESET
                                             ]
                                gs_space_dictionary_obj.add(str(counter+1),str(data["name"]))
                counter=counter+1
                dataTable.append(dataArray)
            # if not(str(data["name"]).__contains__('db2')):
            #     directory = os.getcwd()
            #     sourceDB2FeederShFilePathConfig = str(sourceInstallerDirectory+".db2.scripts.").replace('.','/')
            #     os.chdir(sourceDB2FeederShFilePathConfig)
            #
            #     for file in glob.glob("load_*.sh"):
            #         os.chdir(directory)
            #         puName = str(file).replace('load_','').replace('.sh','').casefold()
            #         # puName = 'db2feeder_'+puName
            #         if(str(puName).__contains__('db2')):
            #             os.chdir(sourceDB2FeederShFilePathConfig)
            #             puName = str(file).replace('load_', '').replace('.sh', '').casefold()
            #             file = open(file, "r")
            #             for line in file:
            #                 if (line.startswith("curl")):
            #                     myString = line
            #                     startString = '&condition='
            #                     endString = "'&exclude-columns="
            #                     mySubString = myString[
            #                                   myString.find(startString) + len(startString):myString.find(endString)]
            #                     puName = 'db2feeder_'+puName
            #                     dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
            #                                  Fore.GREEN+str(puName)+Fore.RESET,
            #                                  Fore.GREEN+str("-")+Fore.RESET,
            #                                  Fore.GREEN+str("-")+Fore.RESET,
            #                                  Fore.GREEN+str("-")+Fore.RESET,
            #                                  Fore.GREEN+str("Undeployed")+Fore.RESET,
            #                                  Fore.GREEN+str(mySubString)+Fore.RESET
            #                                  ]
            #         counter=counter+1
            #         dataTable.append(dataArray)
            #
        # For Kafka - Consumer
        
            if(str(data["name"]).casefold().__contains__('adabasconsumer')):
                dataArray = [Fore.GREEN+str(counter)+Fore.RESET,
                             Fore.GREEN+data["name"]+Fore.RESET,
                             Fore.GREEN+str(hostId)+Fore.RESET,
                             Fore.GREEN+str(data["sla"]["zones"])+Fore.RESET,
                             Fore.GREEN+str("-")+Fore.RESET,
                             Fore.GREEN+data["status"]+Fore.RESET,
                             Fore.GREEN + str("-") + Fore.RESET
                             ]
                gs_space_dictionary_obj.add(str(counter+1),str(data["name"]))
                counter=counter+1
                dataTable.append(dataArray)

            # if not(str(data["name"]).__contains__('adabasconsumer')):
            #     dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
            #                  Fore.GREEN+data["name"]+Fore.RESET,
            #                  Fore.GREEN+str(hostId)+Fore.RESET,
            #                  Fore.GREEN+str(data["sla"]["zones"])+Fore.RESET,
            #                  Fore.GREEN+str(queryStatus)+Fore.RESET,
            #                  Fore.GREEN+str("Undeployed")+Fore.RESET,
            #                  Fore.GREEN + str("-") + Fore.RESET
            #                  ]
            #     counter=counter+1
            #     dataTable.append(dataArray)
            #
        # For MS-SQL-Feeder

            if (str(data["name"]).__contains__('mssql')):
                os.getcwd()
                sourceMSSQLFeederShFilePath = str(sourceInstallerDirectory + ".mssql.scripts.").replace('.', '/')
                os.chdir(sourceMSSQLFeederShFilePath)
                for file in glob.glob("load_*.sh"):
                    puName = str(str(data["name"])).replace('mssqlfeeder_', 'load_').casefold()
                    puName = puName + ".sh"
                    if (file.casefold() == puName):
                        file = open(file, "r")
                        for line in file:
                            if (line.startswith("curl")):
                                myString = line
                                startString = '&condition='
                                endString = "'&exclude-columns="
                                mySubString = myString[myString.find(startString) + len(startString):myString.find(
                                    endString)]
                                dataArray = [Fore.GREEN + str(counter + 1) + Fore.RESET,
                                             Fore.GREEN + data["name"] + Fore.RESET,
                                             Fore.GREEN + str(hostId) + Fore.RESET,
                                             Fore.GREEN + str(data["sla"]["zones"]) + Fore.RESET,
                                             Fore.GREEN + str(queryStatus) + Fore.RESET,
                                             Fore.GREEN + data["status"] + Fore.RESET,
                                             Fore.GREEN + str(mySubString) + Fore.RESET
                                             ]
                            gs_space_dictionary_obj.add(str(counter+1),str(data["name"]))
                counter=counter+1
                dataTable.append(dataArray)
            # if not(str(data["name"]).__contains__('mssql')):
            #     sourceMSSQLFeederShFilePath = str(sourceInstallerDirectory + ".mssql.scripts.").replace('.', '/')
            #     os.chdir(sourceMSSQLFeederShFilePath)
            #
            #     for file in glob.glob("load_*.sh"):
            #         os.chdir(sourceMSSQLFeederShFilePath)
            #         puName = str(file).replace('load_', '').replace('.sh', '').casefold()
            #         file = open(file, "r")
            #         for line in file:
            #             if (line.startswith("curl")):
            #                 myString = line
            #                 startString = '&condition='
            #                 endString = "'&exclude-columns="
            #                 mySubString = myString[
            #                               myString.find(startString) + len(startString):myString.find(endString)]
            #                 puName = 'mssqlfeeder_'+puName
            #                 dataArray1 = [Fore.GREEN + str(counter + 1) + Fore.RESET,
            #                               Fore.GREEN + puName + Fore.RESET,
            #                               Fore.GREEN + str("-") + Fore.RESET,
            #                               Fore.GREEN + str("-") + Fore.RESET,
            #                               Fore.GREEN + str("-") + Fore.RESET,
            #                               Fore.GREEN + "Undeployed" + Fore.RESET,
            #                               Fore.GREEN + str(mySubString) + Fore.RESET,
            #                               ]
            #         counter = counter + 1
            #         dataTable.append(dataArray1)
        logger.info("getAllFeeders() : end")
        return dataTable
        
    except Exception as e:
        handleException(e)