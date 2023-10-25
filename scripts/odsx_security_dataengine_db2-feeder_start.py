#!/usr/bin/env python3

import glob
import json
import os
import re
import requests
import sqlite3
import subprocess
import sys
from datetime import date, timedelta

from colorama import Fore
from requests.auth import HTTPBasicAuth

from scripts.logManager import LogManager
from utils.ods_app_config import readValueByConfigObj, readValuefromAppConfig
from utils.ods_cluster_config import config_get_manager_node
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_db2feeder_utilities import getPasswordByHost, getUsernameByHost
from utils.odsx_db2feeder_utilities import getQueryStatusFromSqlLite
from utils.odsx_keypress import userInputWithEscWrapper, userInputWrapper
from utils.odsx_print_tabular_data import printTabular

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

def executeLocalCommandAndGetOutput(commandToExecute):
    logger.info("executeLocalCommandAndGetOutput() cmd :" + str(commandToExecute))
    cmd = commandToExecute
    cmdArray = cmd.split(" ")
    process = subprocess.Popen(cmdArray, stdout=subprocess.PIPE)
    out, error = process.communicate()
    out = out.decode()
    return str(out).replace('\n', '')

def displayDB2FeederShFiles():
    logger.info("startDB2Feeder()")
    global fileNameDict
    global sourceDB2FeederShFilePath
    global fileNamePuNameDict
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)
    sourceDB2FeederShFilePath = str(str(sourceInstallerDirectory+".db2.scripts.").replace('.','/'))
    logger.info("sourceDB2FeederShFilePath: "+str(sourceDB2FeederShFilePath))
    counter=1
    directory = os.getcwd()
    os.chdir(sourceDB2FeederShFilePath)
    fileNameDict = host_dictionary_obj()
    fileNamePuNameDict = host_dictionary_obj()
    headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
               Fore.YELLOW+"Name of db2-feeder file"+Fore.RESET
               ]
    dataTable=[]
    for file in glob.glob("load_*.sh"):
        os.chdir(directory)
        dataArray = [Fore.GREEN+str(counter)+Fore.RESET,
                     Fore.GREEN+str(file)+Fore.RESET]
        dataTable.append(dataArray)
        fileNameDict.add(str(counter),str(file))
        puName = str(file).replace('load','').replace('.sh','').casefold()
        puName = 'db2feeder'+puName
        fileNamePuNameDict.add(str(puName),str(file))
        counter=counter+1
    logger.info("fileNameDict : "+str(fileNameDict))
    logger.info("fileNamePuNameDict : "+str(fileNamePuNameDict))
    #printTabular(None,headers,dataTable)

def getFormattedDate(mySubString):
    mySubString = mySubString.replace("%20", " ")
    startDate = ""
    endDate = ""
    if re.search('current|date', mySubString.casefold()):
        startDate = date.today().strftime('%d/%m/%Y')
    if(re.search('days', mySubString.casefold())):
        dates = mySubString.split('-')[-1]
        num = [int(x) for x in dates.split() if x.isdigit()]
        endDate = date.today()-timedelta(days=num[0])
        endDate = endDate.strftime('%d/%m/%Y')
    if ( len(str(startDate)) == 0 or len(str(endDate)) == 0):
        conditionDate = mySubString
    else:
        conditionDate = mySubString.split('=')[0]+"='"+str(endDate)+"'"
    return conditionDate

def listDeployed(managerHost):
    logger.info("listDeployed()")
    global gs_space_dictionary_obj
    try:
        dbaGigaWorkPath=str(readValueByConfigObj("app.gigawork.path"))
        db_file = str(readValueByConfigObj("app.dataengine.db2-feeder.sqlite.dbfile")).replace("/dbagigawork",dbaGigaWorkPath).replace('"','').replace(' ','')
        cnx = sqlite3.connect(db_file)

        logger.info("managerHost :"+str(managerHost))
        response = requests.get("http://"+str(managerHost)+":8090/v2/pus/",auth = HTTPBasicAuth(username, password))
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Resources on cluster:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Name"+Fore.RESET,
                   Fore.YELLOW+"Host"+Fore.RESET,
                   Fore.YELLOW+"Zone"+Fore.RESET,
                   Fore.YELLOW+"Query Status"+Fore.RESET,
                   Fore.YELLOW+"Status"+Fore.RESET,
                   Fore.YELLOW+"Condition"+Fore.RESET
                   ]
        gs_space_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_dictionary_obj : "+str(gs_space_dictionary_obj))
        counter=0
        dataTable=[]
        # for data in jsonArray:
        #     hostId=''
        #     response2 = requests.get("http://"+str(managerHost)+":8090/v2/pus/"+str(data["name"])+"/instances",auth = HTTPBasicAuth(username, password))
        #     jsonArray2 = json.loads(response2.text)
        #     queryStatus = str(getQueryStatusFromSqlLite(str(data["name"]))).replace('"','')
        #     for data2 in jsonArray2:
        #         hostId=data2["hostId"]
        #     if(len(str(hostId))==0):
        #         hostId="N/A"
        #     if(str(data["name"]).__contains__('db2')):
        #         dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
        #                      Fore.GREEN+data["name"]+Fore.RESET,
        #                      Fore.GREEN+str(hostId)+Fore.RESET,
        #                      Fore.GREEN+str(data["sla"]["zones"])+Fore.RESET,
        #                      Fore.GREEN+str(queryStatus)+Fore.RESET,
        #                      Fore.GREEN+data["status"]+Fore.RESET
        #                      ]
        #         logger.info("UPDATE db2_host_port SET host='"+str(hostId)+"' where feeder_name like '%"+str(data["name"])+"%' ")
        #         mycursor = cnx.execute("UPDATE db2_host_port SET host='"+str(hostId)+"' where feeder_name like '%"+str(data["name"])+"%' ")
        #         logger.info("query result:"+str(mycursor.rowcount))

        flag = False
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
        for i in jsonArray:
            if(str(i["name"]).__contains__("db2")):
                flag = True
        if(len(jsonArray) == 0 or flag == False):

            logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)
            directory = os.getcwd()
            sourceDB2FeederShFilePathConfig = str(sourceInstallerDirectory+".db2.scripts.").replace('.','/')
            os.chdir(sourceDB2FeederShFilePathConfig)

            for file in glob.glob("load_*.sh"):
                os.chdir(directory)
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
                            endString = "&exclude-columns="
                            if(myString.find(startString) != -1):
                                mySubString = myString[
                                              myString.find(startString) + len(startString):myString.find(endString)]
                                puName = 'db2feeder_'+puName
                                conditionDate = getFormattedDate(mySubString)
                            else:
                                puName = 'db2feeder_'+puName
                                conditionDate = "-"
                            dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                                         Fore.GREEN+str(puName)+Fore.RESET,
                                         Fore.GREEN+str("-")+Fore.RESET,
                                         Fore.GREEN+str("-")+Fore.RESET,
                                         Fore.GREEN+str("-")+Fore.RESET,
                                         Fore.GREEN+str("Undeployed")+Fore.RESET,
                                         Fore.GREEN+str(conditionDate)+Fore.RESET
                                         ]
                    counter=counter+1
                    dataTable.append(dataArray)
        else:

            for data in jsonArray:
                hostId=''
                response2 = requests.get("http://"+str(managerHost)+":8090/v2/pus/"+str(data["name"])+"/instances",auth = HTTPBasicAuth(username, password))
                jsonArray2 = json.loads(response2.text)
                queryStatus = str(getQueryStatusFromSqlLite(str(data["name"]))).replace('"','')
                for data2 in jsonArray2:
                    hostId=data2["hostId"]
                if(len(str(hostId))==0):
                    hostId="N/A"
                if(str(data["name"]).__contains__('db2')):
                    os.getcwd()
                    sourceDB2FeederShFilePathConfig = str(sourceInstallerDirectory+".db2.scripts.").replace('.','/')
                    os.chdir(sourceDB2FeederShFilePathConfig)
                    for file in glob.glob("load_*.sh"):
                        puName = str(str(data["name"])).replace('db2feeder_','load_').casefold()
                        puName= puName+".sh"
                        if(file.casefold() == puName):
                            file = open(file, "r")
                            for line in file:
                                if (line.startswith("curl")):
                                    myString = line
                                    startString = '&condition='
                                    endString = '&exclude'
                                    if(myString.find(startString) != -1):
                                        mySubString = myString[
                                                      myString.find(startString) + len(startString):myString.find(endString)]
                                        # puName = 'db2feeder_'+puName
                                        conditionDate = getFormattedDate(mySubString)
                                    else:
                                        conditionDate = "-"
                                    # mySubString=myString[myString.find(startString)+len(startString):myString.find(endString)]
                                    # conditionDate = getFormattedDate(mySubString)
                                    dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                                                 Fore.GREEN+data["name"]+Fore.RESET,
                                                 Fore.GREEN+str(hostId)+Fore.RESET,
                                                 Fore.GREEN+str(data["sla"]["zones"])+Fore.RESET,
                                                 Fore.GREEN+str(queryStatus)+Fore.RESET,
                                                 Fore.GREEN+data["status"]+Fore.RESET,
                                                 Fore.GREEN+str(conditionDate)+Fore.RESET
                                                 ]
                    logger.info("UPDATE db2_host_port SET host='"+str(hostId)+"' where feeder_name like '%"+str(data["name"])+"%' ")
                    mycursor = cnx.execute("UPDATE db2_host_port SET host='"+str(hostId)+"' where feeder_name like '%"+str(data["name"])+"%' ")
                    logger.info("query result:"+str(mycursor.rowcount))

                    gs_space_dictionary_obj.add(str(counter+1),str(data["name"]))
                    counter=counter+1
                    dataTable.append(dataArray)
        cnx.commit()
        cnx.close()
        printTabular(None,headers,dataTable)
        return gs_space_dictionary_obj
    except Exception as e:
        handleException(e)

def inputParam():
    logger.info("inputParam()")
    inputNumberToStart =''
    inputChoice=''
    inputChoice = str(userInputWithEscWrapper(Fore.YELLOW+"Enter [1] For individual start \n[Enter] For all \n[99] For exit : "+Fore.RESET))
    if(str(inputChoice)=='99'):
        return
    if(str(inputChoice)=='1'):
        inputNumberToStart = str(userInputWrapper(Fore.YELLOW+"Enter serial number to start db2-feeder : "+Fore.RESET))
        if(len(str(inputNumberToStart))==0):
            inputNumberToStart = str(userInputWrapper(Fore.YELLOW+"Enter serial number to start db2-feeder : "+Fore.RESET))
        proceedToStartDB2Feeder(inputNumberToStart)
    if(len(str(inputChoice))==0):
        elements = len(fileNameDict)
        for i in range (1,elements+1):
            proceedToStartDB2Feeder(str(i))

def sqlLiteGetHostAndPortByFileName(puName):
    logger.info("sqlLiteGetHostAndPortByFileName() shFile : "+str(puName))
    try:
        dbaGigaWorkPath=str(readValueByConfigObj("app.gigawork.path"))
        db_file = str(readValueByConfigObj("app.dataengine.db2-feeder.sqlite.dbfile")).replace("/dbagigawork",dbaGigaWorkPath).replace('"','').replace(' ','')
        cnx = sqlite3.connect(db_file)
        logger.info("Db connection obtained."+str(cnx))
        logger.info("SELECT host,port,file FROM db2_host_port where feeder_name like '%"+str(puName)+"%' ")
        mycursor = cnx.execute("SELECT host,port,file FROM db2_host_port where feeder_name like '%"+str(puName)+"%' ")
        myresult = mycursor.fetchall()
        cnx.close()
        for row in myresult:
            logger.info("host : "+str(row[0]))
            logger.info("port : "+str(row[1]))
            logger.info("file : "+str(row[2]))
            return str(row[0])+','+str(row[1])+','+str(row[2])
    except Exception as e:
        handleException(e)

def proceedToStartDB2FeederWithName(puName):
    logger.info("proceedToStartDB2FeederWithName()")
    #shFileName = fileNameDict.get(str(fileNumberToStart))
    print(puName)
    shFileName = fileNamePuNameDict.get(str(puName))
    hostAndPort = str(sqlLiteGetHostAndPortByFileName(puName)).split(',')
    print("hostAndPort"+str(hostAndPort))
    host = str(hostAndPort[0])
    port = str(hostAndPort[1])
    shFileName = str(hostAndPort[2])
    cmd = str(sourceDB2FeederShFilePath)+'/'+shFileName+' '+host+" "+port
    logger.info("cmd : "+str(cmd))
    print(cmd)
    os.system(cmd)
def proceedToStartDB2Feeder(fileNumberToStart):
    logger.info("proceedToStartDB2Feeder()")
    #shFileName = fileNameDict.get(str(fileNumberToStart))
    puName = gs_space_dictionary_obj.get(str(fileNumberToStart))
    print(puName)
    shFileName = fileNamePuNameDict.get(str(puName))
    hostAndPort = str(sqlLiteGetHostAndPortByFileName(puName)).split(',')
    print("hostAndPort"+str(hostAndPort))
    host = str(hostAndPort[0])
    port = str(hostAndPort[1])
    shFileName = str(hostAndPort[2])
    cmd = str(sourceDB2FeederShFilePath)+'/'+shFileName+' '+host+" "+port
    logger.info("cmd : "+str(cmd))
    print(cmd)
    os.system(cmd)
    #output = executeLocalCommandAndGetOutput(cmd)
    #print(output)

if __name__ == '__main__':
    logger.info("odsx_dataengine_db2-feeder_start")
    verboseHandle.printConsoleWarning("Menu -> DataEngine -> DB2-Feeder -> Start")
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
        managerHost=''
        managerNodes = config_get_manager_node()
        managerHost = getManagerHost(managerNodes);
        if(len(str(managerHost))>0):
            username = str(getUsernameByHost(managerHost,appId,safeId,objectId))
            password = str(getPasswordByHost(managerHost,appId,safeId,objectId))
            displayDB2FeederShFiles()
            gs_space_dictionary_obj = listDeployed(managerHost)
            if(len(str(gs_space_dictionary_obj))>2):
                if len(sys.argv) > 1 and sys.argv[1] != "m":
                    proceedToStartDB2FeederWithName(sys.argv[1])
                else:
                    inputParam()
            else:
                logger.info("No feeder found.")
                verboseHandle.printConsoleInfo("No feeder found.")
        else:
            logger.info("No manager status ON.")
            verboseHandle.printConsoleInfo("No manager status ON.")
    except Exception as e:
        verboseHandle.printConsoleError("Eror in odsx_db2-feeder_start : "+str(e))
        handleException(e)
