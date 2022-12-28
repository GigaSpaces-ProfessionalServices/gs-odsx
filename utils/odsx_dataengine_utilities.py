#!/usr/bin/env python3
import glob
import os, subprocess, sqlite3, json, requests
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_app_config import readValueByConfigObj, readValuefromAppConfig, getYamlFilePathInsideFolder
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

def getmssqlFeederList():
    global mssqlFeederList
    mssqlFeederList=[]
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    os.getcwd()
    sourceMSSQLFeederShFilePath = str(sourceInstallerDirectory + ".mssql.scripts.").replace('.', '/')
    os.chdir(sourceMSSQLFeederShFilePath)
    for file in glob.glob("load_*.sh"):
        puName = str(file).replace('load_','').replace('.sh','').casefold()
        mssqlFeederList.append('mssqlfeeder_'+puName)

def getdbFeederList():
    global dbFeederList
    dbFeederList=[]
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    os.getcwd()
    sourceMSSQLFeederShFilePath = str(sourceInstallerDirectory + ".db2.scripts.").replace('.', '/')
    os.chdir(sourceMSSQLFeederShFilePath)
    for file in glob.glob("load_*.sh"):
        puName = str(file).replace('load_','').replace('.sh','').casefold()
        dbFeederList.append('db2feeder_'+puName)

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
        getmssqlFeederList()
        getdbFeederList()
        if (len(jsonArray) == 0):
            sourceDB2FeederShFilePathConfig = str(sourceInstallerDirectory+".db2.scripts.").replace('.','/')
            os.chdir(sourceDB2FeederShFilePathConfig)
            for file in glob.glob("load_*.sh"):
                puName = str(file).replace('load_','').replace('.sh','').casefold()
                puName = 'db2feeder_'+puName
                if(str(puName).__contains__('db2')):
                    dbFeederList.remove(puName)
                    dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                                         Fore.GREEN+str(puName)+Fore.RESET,
                                         Fore.GREEN+str("-")+Fore.RESET,
                                         Fore.GREEN+str("-")+Fore.RESET,
                                         # Fore.GREEN+str("-")+Fore.RESET,
                                         Fore.GREEN+str("Undeployed")+Fore.RESET,
                                         ]
                    counter=counter+1
                    dataTable.append(dataArray)
            os.getcwd()
            sourceMSSQLFeederShFilePath = str(sourceInstallerDirectory + ".mssql.scripts.").replace('.', '/')
            os.chdir(sourceMSSQLFeederShFilePath)
            for file in glob.glob("load_*.sh"):
                os.chdir(sourceMSSQLFeederShFilePath)
                puName = str(file).replace('load_', '').replace('.sh', '').casefold()
                puName = 'mssqlfeeder_'+puName
                mssqlFeederList.remove(puName)
                dataArray1 = [Fore.GREEN + str(counter + 1) + Fore.RESET,
                                     Fore.GREEN + puName + Fore.RESET,
                                     Fore.GREEN + str("-") + Fore.RESET,
                                     Fore.GREEN + str("-") + Fore.RESET,
                                     # Fore.GREEN + str("-") + Fore.RESET,
                                     Fore.GREEN + "Undeployed" + Fore.RESET,
                                     ]
                counter = counter + 1
                dataTable.append(dataArray1)

            os.getcwd()
            dPipelineSourceConfig = str(getYamlFilePathInsideFolder(".mq-connector.adabas.config.pipeline")).replace('[','').replace(']','').replace("'","").replace(', ',',')
            filename = os.path.basename(dPipelineSourceConfig)
            if(len(str(filename)) != 0):
                    resourceName = str(readValueByConfigObj("app.dataengine.mq.kafka.consumer.pu.name"))
                    dataArray1 = [Fore.GREEN + str(counter + 1) + Fore.RESET,
                                         Fore.GREEN + resourceName + Fore.RESET,
                                         Fore.GREEN + str("-") + Fore.RESET,
                                         Fore.GREEN + str("-") + Fore.RESET,
                                         # Fore.GREEN + str("-") + Fore.RESET,
                                         Fore.GREEN + "Undeployed" + Fore.RESET,
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
                if(dbFeederList.__contains__(str(data["name"]))):
                    dbFeederList.remove(str(data["name"]))
                dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                             Fore.GREEN+data["name"]+Fore.RESET,
                             Fore.GREEN+str(hostId)+Fore.RESET,
                             Fore.GREEN+str(data["sla"]["zones"])+Fore.RESET,
                             Fore.GREEN+data["status"]+Fore.RESET
                             ]
                gs_space_dictionary_obj.add(str(counter+1),str(data["name"]))
                counter=counter+1
                dataTable.append(dataArray)

            # For Kafka - Consumer

            if(str(data["name"]).casefold().__contains__('adabasconsumer')):
                dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                             Fore.GREEN+data["name"]+Fore.RESET,
                             Fore.GREEN+str(hostId)+Fore.RESET,
                             Fore.GREEN+str(data["sla"]["zones"])+Fore.RESET,
                             # Fore.GREEN+str("-")+Fore.RESET,
                             Fore.GREEN+data["status"]+Fore.RESET
                             ]
                gs_space_dictionary_obj.add(str(counter+1),str(data["name"]))
                counter=counter+1
                dataTable.append(dataArray)
            # For MS-SQL-Feeder

            if(str(data["name"]).__contains__('mssql')):
                if(mssqlFeederList.__contains__(str(data["name"]))):
                    mssqlFeederList.remove(str(data["name"]))
                dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                             Fore.GREEN+data["name"]+Fore.RESET,
                             Fore.GREEN+str(hostId)+Fore.RESET,
                             Fore.GREEN+str(data["sla"]["zones"])+Fore.RESET,
                             # Fore.GREEN+str(queryStatus)+Fore.RESET,
                             Fore.GREEN+data["status"]+Fore.RESET
                             ]
                gs_space_dictionary_obj.add(str(counter+1),str(data["name"]))
                counter=counter+1
                dataTable.append(dataArray)

        logger.info("getAllFeeders() : end")
        mssqlFlag = False
        db2Flag = False
        adabsFlag = False
        if (len(mssqlFeederList) != 0 and len(jsonArray) != 0):
            for puName in mssqlFeederList:
                if(str(puName).__contains__('mssql')):
                    dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                                 Fore.GREEN+str(puName)+Fore.RESET,
                                 Fore.GREEN+str("-")+Fore.RESET,
                                 Fore.GREEN+str("-")+Fore.RESET,
                                 # Fore.GREEN+str("-")+Fore.RESET,
                                 Fore.GREEN+str("Undeployed")+Fore.RESET,
                                 ]
                    counter=counter+1
                    dataTable.append(dataArray)
        if (len(dbFeederList) != 0 and len(jsonArray) != 0):
            for puName in dbFeederList:
                if(str(puName).__contains__('db2')):
                    dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                                 Fore.GREEN+str(puName)+Fore.RESET,
                                 Fore.GREEN+str("-")+Fore.RESET,
                                 Fore.GREEN+str("-")+Fore.RESET,
                                 # Fore.GREEN+str("-")+Fore.RESET,
                                 Fore.GREEN+str("Undeployed")+Fore.RESET,
                                 ]
                    counter=counter+1
                    dataTable.append(dataArray)
        # for i in jsonArray:
        if not(str(jsonArray).__contains__("mssql")):
                mssqlFlag = True
        # for i in jsonArray:
        if not(str(jsonArray).__contains__("db2")):
                db2Flag = True
        # for i in jsonArray:
        if not(str(jsonArray).casefold().__contains__('adabasconsumer')):
                adabsFlag = True
        # if(db2Flag == True and len(jsonArray) != 0):
        #     sourceDB2FeederShFilePathConfig = str(sourceInstallerDirectory+".db2.scripts.").replace('.','/')
        #     os.chdir(sourceDB2FeederShFilePathConfig)
        #     for file in glob.glob("load_*.sh"):
        #         puName = str(file).replace('load_','').replace('.sh','').casefold()
        #         puName = 'db2feeder_'+puName
        #         if(str(puName).__contains__('db2')):
        #             dbFeederList.remove(puName)
        #             dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
        #                          Fore.GREEN+str(puName)+Fore.RESET,
        #                          Fore.GREEN+str("-")+Fore.RESET,
        #                          Fore.GREEN+str("-")+Fore.RESET,
        #                          # Fore.GREEN+str("-")+Fore.RESET,
        #                          Fore.GREEN+str("Undeployed")+Fore.RESET,
        #                          ]
        #             counter=counter+1
        #             dataTable.append(dataArray)
        # if(mssqlFlag == True and len(jsonArray) != 0):
        #     os.getcwd()
        #     sourceMSSQLFeederShFilePath = str(sourceInstallerDirectory + ".mssql.scripts.").replace('.', '/')
        #     os.chdir(sourceMSSQLFeederShFilePath)
        #     for file in glob.glob("load_*.sh"):
        #         os.chdir(sourceMSSQLFeederShFilePath)
        #         puName = str(file).replace('load_', '').replace('.sh', '').casefold()
        #         puName = 'mssqlfeeder_'+puName
        #         dataArray1 = [Fore.GREEN + str(counter + 1) + Fore.RESET,
        #                       Fore.GREEN + puName + Fore.RESET,
        #                       Fore.GREEN + str("-") + Fore.RESET,
        #                       Fore.GREEN + str("-") + Fore.RESET,
        #                       # Fore.GREEN + str("-") + Fore.RESET,
        #                       Fore.GREEN + "Undeployed" + Fore.RESET,
        #                       ]
        #         counter = counter + 1
        #         dataTable.append(dataArray1)
        if(adabsFlag == True and len(jsonArray) != 0):
            os.getcwd()
            dPipelineSourceConfig = str(getYamlFilePathInsideFolder(".mq-connector.adabas.config.pipeline")).replace('[','').replace(']','').replace("'","").replace(', ',',')
            filename = os.path.basename(dPipelineSourceConfig)
            if(len(str(filename)) != 0):
                resourceName = str(readValueByConfigObj("app.dataengine.mq.kafka.consumer.pu.name"))
                counter = counter + 1
                dataArray1 = [Fore.GREEN + str(counter) + Fore.RESET,
                              Fore.GREEN + resourceName + Fore.RESET,
                              Fore.GREEN + str("-") + Fore.RESET,
                              Fore.GREEN + str("-") + Fore.RESET,
                              # Fore.GREEN + str("-") + Fore.RESET,
                              Fore.GREEN + "Undeployed" + Fore.RESET,
                              ]

                dataTable.append(dataArray1)
        mssqlFeederList.clear()
        dbFeederList.clear()
        return dataTable

    except Exception as e:
        handleException(e)