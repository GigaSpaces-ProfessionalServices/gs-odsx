#!/usr/bin/env python3

import glob
import json
import os
import re
import sys

import requests
import sqlite3
import subprocess
from datetime import date, timedelta

from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig, readValueByConfigObj
from utils.ods_cluster_config import config_get_manager_node
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_keypress import userInputWrapper
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
    #process = subprocess.Popen(cmdArray, stdout=subprocess.PIPE)
    process = subprocess.Popen(cmdArray, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out, error = process.communicate()
    out = out.decode()
    return str(out).replace('\n', '')

def displayMSSQLFeederShFiles():
    logger.info("displayOracleFeederShFiles()")
    global fileNameDict
    global sourceMSSQLFeederShFilePath
    global fileNamePuNameDict
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)
    sourceMSSQLFeederShFilePath = str(str(sourceInstallerDirectory+".oracle.scripts.").replace('.','/'))
    logger.info("sourceOracleFeederShFilePath :"+str(sourceMSSQLFeederShFilePath))
    counter=1
    directory = os.getcwd()
    os.chdir(sourceMSSQLFeederShFilePath)
    fileNameDict = host_dictionary_obj()
    fileNamePuNameDict = host_dictionary_obj()
    headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
               Fore.YELLOW+"Name of oracle-feeder file"+Fore.RESET
               ]
    dataTable=[]
    for file in glob.glob("load_*.sh"):
        os.chdir(directory)
        dataArray = [Fore.GREEN+str(counter)+Fore.RESET,
                     Fore.GREEN+str(file)+Fore.RESET]
        dataTable.append(dataArray)
        fileNameDict.add(str(counter),str(file))
        puName = str(file).replace('load','').replace('.sh','').casefold()
        puName = 'oraclefeeder'+puName
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
        db_file = str(readValueByConfigObj("app.dataengine.oracle-feeder.sqlite.dbfile")).replace('"','').replace(' ','')
        cnx = sqlite3.connect(db_file)

        logger.info("managerHost :"+str(managerHost))
        response = requests.get("http://"+str(managerHost)+":8090/v2/pus/")
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Resources on cluster:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Name"+Fore.RESET,
                   Fore.YELLOW+"Status"+Fore.RESET
                   ]
        gs_space_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_dictionary_obj : "+str(gs_space_dictionary_obj))
        counter=0
        dataTable=[]
        flag = False
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
        sourceMSSQLFeederShFilePath = str(sourceInstallerDirectory+".oracle.scripts.").replace('.','/')
        for i in jsonArray:
            if(str(i['name']).__contains__("oracle")):
                flag = True
        if(len(jsonArray) == 0 or flag == False):

            logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)

            os.chdir(sourceMSSQLFeederShFilePath)

            for file in glob.glob("load_*.sh"):
                os.chdir(sourceMSSQLFeederShFilePath)
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
                            puName = 'oraclefeeder_'+puName
                            conditionDate = getFormattedDate(mySubString)
                        else:
                            conditionDate = "-"
                        dataArray = [Fore.GREEN + str(counter + 1) + Fore.RESET,
                                     Fore.GREEN + puName + Fore.RESET,
                                     Fore.GREEN + str("-") + Fore.RESET
                                     ]
                counter = counter + 1
                dataTable.append(dataArray)
        else:
            for data in jsonArray:
                hostId = ''
                response2 = requests.get(
                    "http://" + str(managerHost) + ":8090/v2/pus/" + str(data["name"]) + "/instances")
                jsonArray2 = json.loads(response2.text)
                queryStatus = str(getOracleQueryStatusFromSqlLite(str(data["name"]))).replace('"', '')
                for data2 in jsonArray2:
                    hostId = data2["hostId"]
                if (len(str(hostId)) == 0):
                    hostId = "N/A"
                if (str(data["name"]).__contains__('oracle')):
                    os.getcwd()
                    os.chdir(sourceMSSQLFeederShFilePath)
                    for file in glob.glob("load_*.sh"):
                        puName = str(str(data["name"])).replace('oraclefeeder_', 'load_').casefold()
                        puName = puName + ".sh"
                        if (file.casefold() == puName):
                            file = open(file, "r")
                            for line in file:
                                if (line.startswith("curl")):
                                    myString = line
                                    startString = '&condition='
                                    endString = "&exclude-columns="
                                    # mySubString = myString[myString.find(startString) + len(startString):myString.find(
                                    #     endString)]
                                    # conditionDate = getFormattedDate(mySubString)
                                    if(myString.find(startString) != -1):
                                        mySubString = myString[
                                                      myString.find(startString) + len(startString):myString.find(endString)]
                                        puName = 'oraclefeeder_'+puName
                                        conditionDate = getFormattedDate(mySubString)
                                    else:
                                        puName = 'oraclefeeder_'+puName
                                        conditionDate = "-"
                                    dataArray = [Fore.GREEN + str(counter + 1) + Fore.RESET,
                                                 Fore.GREEN + data["name"] + Fore.RESET,
                                                 Fore.GREEN + str(queryStatus) + Fore.RESET
                                                 ]
                    logger.info("UPDATE oracle_host_port SET host='"+str(hostId)+"' where feeder_name like '%"+str(data["name"])+"%' ")
                    mycursor = cnx.execute("UPDATE oracle_host_port SET host='"+str(hostId)+"' where feeder_name like '%"+str(data["name"])+"%' ")
                    logger.info("query result:"+str(mycursor.rowcount))

                    gs_space_dictionary_obj.add(str(counter+1),str(data["name"]))
                    counter=counter+1
                    dataTable.append(dataArray)
        cnx.commit()
        cnx.close()

        if len(sys.argv) == 1 or (len(sys.argv)>1 and sys.argv[1] == "m"):
            printTabular(None,headers,dataTable)
        return gs_space_dictionary_obj
    except Exception as e:
        handleException(e)

def inputParam():
    logger.info("inputParam()")
    inputNumberToStatus =''
    inputChoice=''
    #inputChoice = str(userInputWrapper(Fore.YELLOW+"Enter [1] For individual status \n[Enter] For all \n[99] For exit : "+Fore.RESET))
    inputChoice = str(userInputWrapper(Fore.YELLOW+"Enter [1] For individual status \n[99] For exit : "+Fore.RESET))
    if(str(inputChoice)=='99'):
        return
    if(str(inputChoice)=='1'):
        inputNumberToStatus = str(userInputWrapper(Fore.YELLOW+"Enter serial number to status oracle-feeder : "+Fore.RESET))
        if(len(str(inputNumberToStatus))==0):
            inputNumberToStatus = str(userInputWrapper(Fore.YELLOW+"Enter serial number to get status oracle-feeder : "+Fore.RESET))
        proceedToGetStatusMSSQLFeeder(gs_space_dictionary_obj.get(str(inputNumberToStatus)))
    #if(len(str(inputChoice))==0):
    #    elements = len(fileNameDict)
    #    for i in range (1,elements+1):
    #        proceedToGetStatusMSSQLFeeder(gs_space_dictionary_obj.get(str(i)))

def sqlLiteGetHostAndPortByFileName(puName):
    logger.info("sqlLiteGetHostAndPortByFileName() shFile : "+str(puName))
    try:
        db_file = str(readValueByConfigObj("app.dataengine.oracle-feeder.sqlite.dbfile")).replace('"','').replace(' ','')
        cnx = sqlite3.connect(db_file)
        logger.info("Db connection obtained."+str(cnx))
        logger.info("SQL: SELECT host,port FROM oracle_host_port where feeder_name like '%"+str(puName)+"%' ")
        mycursor = cnx.execute("SELECT host,port FROM oracle_host_port where feeder_name like '%"+str(puName)+"%' ")
        myresult = mycursor.fetchall()
        cnx.close()
        for row in myresult:
            logger.info("host : "+str(row[0]))
            logger.info("port : "+str(row[1]))
            return str(row[0])+','+str(row[1])
    except Exception as e:
        handleException(e)

def proceedToGetStatusMSSQLFeeder(puName):
    logger.info("proceedToGetStatusOracleFeeder() " + puName)
    # puName = gs_space_dictionary_obj.get(str(fileNumberToStatus))
    queryStatus = str(getOracleQueryStatusFromSqlLite(puName)).replace('"', '')
    verboseHandle.printConsoleInfo(puName + " : " + queryStatus)

def getOracleQueryStatusFromSqlLite(feederName):
    logger.info("getQueryStatusFromSqlLite() shFile : "+str(feederName))
    try:
        db_file = str(readValueByConfigObj("app.dataengine.oracle-feeder.sqlite.dbfile")).replace('"','').replace(' ','')
        cnx = sqlite3.connect(db_file)
        logger.info("Db connection obtained."+str(cnx))
        logger.info("CREATE TABLE IF NOT EXISTS oracle_host_port (file VARCHAR(50), feeder_name VARCHAR(50), host VARCHAR(50), port varchar(10))")
        cnx.execute("CREATE TABLE IF NOT EXISTS oracle_host_port (file VARCHAR(50), feeder_name VARCHAR(50), host VARCHAR(50), port varchar(10))")
        cnx.commit()
        logger.info("SQL : SELECT host,port FROM oracle_host_port where feeder_name like '%"+str(feederName)+"%' ")
        mycursor = cnx.execute("SELECT host,port FROM oracle_host_port where feeder_name like '%"+str(feederName)+"%' ")
        myresult = mycursor.fetchall()
        cnx.close()
        host = ''
        port = ''
        output='NA'
        for row in myresult:
            logger.info("host : "+str(row[0]))
            host = str(row[0])
            logger.info("port : "+str(row[1]))
            port = str(row[1])
            cmd = "curl "+host+":"+port+"/table-feed/status"
            logger.info("cmd : "+str(cmd))
            output = executeLocalCommandAndGetOutput(cmd);
            logger.info("Output ::"+str(output))
        return output
    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    logger.info("odsx_security_dataengine_oracle-feeder_status")
    verboseHandle.printConsoleWarning("Menu -> DataEngine -> Oracle-Feeder -> Status")
    try:
        managerHost=''
        managerNodes = config_get_manager_node()
        managerHost = getManagerHost(managerNodes);
        if(len(str(managerHost))>0):
            displayMSSQLFeederShFiles()
            gs_space_dictionary_obj = listDeployed(managerHost)
            if(len(str(gs_space_dictionary_obj))>2):
                #print(sys.argv)
                if len(sys.argv) > 1 and sys.argv[1] != "m":
                    proceedToGetStatusMSSQLFeeder(sys.argv[1])
                #else:
                    #inputParam()

            else:
                logger.info("No feeder found.")
                verboseHandle.printConsoleInfo("No feeder found.")
        else:
            logger.info("No manager status ON.")
            verboseHandle.printConsoleInfo("No manager status ON.")
    except Exception as e:
        verboseHandle.printConsoleError("Eror in odsx_data-engine_oracle-feeder_status : "+str(e))
        handleException(e)
