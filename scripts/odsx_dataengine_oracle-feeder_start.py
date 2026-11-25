#!/usr/bin/env python3

import glob
import json
import os
import re
import requests
import sqlite3
import subprocess
import sys
import socket
from datetime import date, timedelta

from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_app_config import readValueByConfigObj
from utils.ods_cluster_config import config_get_manager_node
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_keypress import userInputWithEscWrapper, userInputWrapper
from utils.odsx_print_tabular_data import printTabular
from utils.odsx_db2feeder_utilities import getOracleQueryStatusFromSqlLite

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

def displayOracleFeederShFiles():
    logger.info("startOracleFeeder()")
    global fileNameDict
    global sourceOracleFeederShFilePath
    global fileNamePuNameDict
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)
    sourceOracleFeederShFilePath = str(str(sourceInstallerDirectory+".oracle.scripts.").replace('.','/'))
    logger.info("sourceDB2FeederShFilePath: "+str(sourceOracleFeederShFilePath))
    counter=1
    directory = os.getcwd()
    os.chdir(sourceOracleFeederShFilePath)
    fileNameDict = host_dictionary_obj()
    fileNamePuNameDict = host_dictionary_obj()
    headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
               Fore.YELLOW+"Name of oracle-feeder file"+Fore.RESET
               ]
    dataTable=[]
    for file in sorted(glob.glob("load_*.sh"), key=str.casefold):
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
        response = requests.get("http://"+str(managerHost)+":8090/v2/pus")
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
        jsonArray = json.loads(response.text)
        if isinstance(jsonArray, list): jsonArray = sorted(jsonArray, key=lambda pu: str(pu.get('name', '')).casefold())
        verboseHandle.printConsoleWarning("Resources on cluster:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Name"+Fore.RESET,
                   Fore.YELLOW+"Host"+Fore.RESET,
                   Fore.YELLOW+"Zone"+Fore.RESET,
                   Fore.YELLOW+"Query Status"+Fore.RESET,
                   Fore.YELLOW+"Status"+Fore.RESET,
                   Fore.YELLOW+"Condition"+Fore.RESET,
                   ]
        gs_space_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_dictionary_obj : "+str(gs_space_dictionary_obj))
        counter=0
        dataTable=[]
        flag = False
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
        sourceOracleFeederShFilePath = str(sourceInstallerDirectory+".oracle.scripts.").replace('.','/')
        for i in jsonArray:
            if(str(i['name']).__contains__("oraclefeeder")):
                flag = True
        if(len(jsonArray) == 0 or flag == False):

            logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)

            os.chdir(sourceOracleFeederShFilePath)

            for file in sorted(glob.glob("load_*.sh"), key=str.casefold):
                os.chdir(sourceOracleFeederShFilePath)
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
                            puName = 'oraclefeeder_'+puName
                            conditionDate = "-"
                        # global mySubString
                        # mySubString = myString[
                        #               myString.find(startString) + len(startString):myString.find(endString)]
                        # puName = 'oraclefeeder_'+puName
                        # conditionDate = getFormattedDate(mySubString)
                        dataArray = [Fore.GREEN + str(counter + 1) + Fore.RESET,
                                     Fore.GREEN + puName + Fore.RESET,
                                     Fore.GREEN + str("-") + Fore.RESET,
                                     Fore.GREEN + str("-") + Fore.RESET,
                                     Fore.GREEN + str("-") + Fore.RESET,
                                     Fore.GREEN + "Undeployed" + Fore.RESET,
                                     Fore.GREEN + str(conditionDate) + Fore.RESET,
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
                if (str(data["name"]).__contains__("oraclefeeder")):
                    os.getcwd()
                    os.chdir(sourceOracleFeederShFilePath)
                    dataArray = None
                    for file in sorted(glob.glob("load_*.sh"), key=str.casefold):
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
                                        # puName = 'oraclefeeder_'+puName
                                        conditionDate = getFormattedDate(mySubString)
                                    else:
                                        conditionDate = "-"
                                    dataArray = [Fore.GREEN + str(counter + 1) + Fore.RESET,
                                                 Fore.GREEN + data["name"] + Fore.RESET,
                                                 Fore.GREEN + str(hostId) + Fore.RESET,
                                                 Fore.GREEN + str(data["sla"]["zones"]) + Fore.RESET,
                                                 Fore.GREEN + str(queryStatus) + Fore.RESET,
                                                 Fore.GREEN + data["status"] + Fore.RESET,
                                                 Fore.GREEN + str(conditionDate) + Fore.RESET
                                                 ]
                    if dataArray is None:
                        # no matching load_*.sh (or no curl line in it): still show the feeder,
                        # so every Sr No. on screen matches gs_space_dictionary_obj
                        logger.info("No load script found for "+str(data["name"]))
                        verboseHandle.printConsoleError("No load script found for "+str(data["name"]))
                        dataArray = [Fore.GREEN + str(counter + 1) + Fore.RESET,
                                     Fore.GREEN + data["name"] + Fore.RESET,
                                     Fore.GREEN + str(hostId) + Fore.RESET,
                                     Fore.GREEN + str(data["sla"]["zones"]) + Fore.RESET,
                                     Fore.GREEN + str(queryStatus) + Fore.RESET,
                                     Fore.GREEN + data["status"] + Fore.RESET,
                                     Fore.RED + "no load script" + Fore.RESET
                                     ]
                    logger.info("UPDATE oracle_host_port SET host = ? WHERE feeder_name = ? | params: host="+str(hostId)+", feeder_name="+str(data["name"]))
                    mycursor = cnx.execute("UPDATE oracle_host_port SET host = ? WHERE feeder_name = ?", (str(hostId), str(data["name"])))
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
        inputNumberToStart = str(userInputWrapper(Fore.YELLOW+"Enter serial number to start oracle-feeder : "+Fore.RESET))
        if(len(str(inputNumberToStart))==0):
            inputNumberToStart = str(userInputWrapper(Fore.YELLOW+"Enter serial number to start oracle-feeder : "+Fore.RESET))
        puName = gs_space_dictionary_obj.get(str(inputNumberToStart))
        if(puName is None):
            verboseHandle.printConsoleError("Invalid serial number : "+str(inputNumberToStart))
            return
        confirmStart = str(userInputWrapper(Fore.YELLOW+"Do you want to start "+str(puName)+" y/N [N]: "+Fore.RESET))
        if(confirmStart.casefold()!='y' and confirmStart.casefold()!='yes'):
            verboseHandle.printConsoleInfo("Skipped starting "+str(puName))
            return
        proceedToStartOracleFeeder(inputNumberToStart)
    if(len(str(inputChoice))==0):
        confirmAll = str(userInputWrapper(Fore.YELLOW+"Do you want to start all feeders y/N [N]: "+Fore.RESET))
        if(confirmAll.casefold()!='y' and confirmAll.casefold()!='yes'):
            return
        for puName in list(gs_space_dictionary_obj.values()):
            proceedToStartOracleFeederWithName(puName)

def sqlLiteGetHostAndPortByFileName(puName):
    logger.info("sqlLiteGetHostAndPortByFileName() shFile : "+str(puName))
    try:
        db_file = str(readValueByConfigObj("app.dataengine.oracle-feeder.sqlite.dbfile")).replace('"','').replace(' ','')
        cnx = sqlite3.connect(db_file)
        logger.info("Db connection obtained."+str(cnx))
        logger.info("SQL : SELECT host,port,file FROM oracle_host_port WHERE feeder_name = ? | params: feeder_name="+str(puName))
        mycursor = cnx.execute("SELECT host,port,file FROM oracle_host_port WHERE feeder_name = ?", (str(puName),))
        myresult = mycursor.fetchall()
        cnx.close()
        for row in myresult:
            logger.info("host : "+str(row[0]))
            logger.info("port : "+str(row[1]))
            logger.info("file : "+str(row[2]))
            return str(row[0])+','+str(row[1])+','+str(row[2])
    except Exception as e:
        handleException(e)

def proceedToStartOracleFeeder(fileNumberToStart):
    logger.info("proceedToStartOracleFeeder()")
    #shFileName = fileNameDict.get(str(fileNumberToStart))
    puName = gs_space_dictionary_obj.get(str(fileNumberToStart))
    print(puName)
    proceedToStartOracleFeederWithName(puName)
    #shFileName = fileNamePuNameDict.get(str(puName))
    #hostAndPort = str(sqlLiteGetHostAndPortByFileName(puName)).split(',')
    #print("hostAndPort"+str(hostAndPort))
    #host = str(hostAndPort[0])
    #port = str(hostAndPort[1])
    #shFileName = str(hostAndPort[2])
    #host=str(socket.gethostbyaddr(host).__getitem__(2)[0])
    #cmd = str(sourceOracleFeederShFilePath)+'/'+shFileName+' '+host+" "+port
    #logger.info("cmd : "+str(cmd))
    #print(cmd)
    #os.system(cmd)

    #output = executeLocalCommandAndGetOutput(cmd)
    #print(output)

def getLoadScriptName(puName):
    return str(puName).replace('oraclefeeder_', 'load_').casefold() + '.sh'

def hasLoadScript(puName):
    # same match as the "no load script" Condition column in listDeployed()
    loadName = getLoadScriptName(puName)
    for path in glob.glob(os.path.join(str(sourceOracleFeederShFilePath), "load_*.sh")):
        if os.path.basename(path).casefold() == loadName:
            return True
    return False

def proceedToStartOracleFeederWithName(puName):
    logger.info("proceedToStartOracleFeederWithName()")
    if not hasLoadScript(puName):
        logger.info("No load script for "+str(puName)+" : "+getLoadScriptName(puName))
        verboseHandle.printConsoleError("No load script for "+str(puName)+" ("+getLoadScriptName(puName)+"), skipping")
        return
    #shFileName = fileNameDict.get(str(fileNumberToStart))
    print(puName)
    shFileName = fileNamePuNameDict.get(str(puName))
    hostAndPort = str(sqlLiteGetHostAndPortByFileName(puName)).split(',')
    print("hostAndPort"+str(hostAndPort))
    host = str(hostAndPort[0])
    port = str(hostAndPort[1])
    shFileName = str(hostAndPort[2])
    host=str(socket.gethostbyaddr(host).__getitem__(2)[0])
    scriptPath = str(sourceOracleFeederShFilePath)+'/'+shFileName
    if not os.path.isfile(scriptPath):
        logger.info("No load script for "+str(puName)+" : "+scriptPath)
        verboseHandle.printConsoleError("No load script for "+str(puName)+" ("+scriptPath+"), skipping")
        return
    cmd = str(sourceOracleFeederShFilePath)+'/'+shFileName+' '+host+" "+port
    logger.info("cmd : "+str(cmd))
    print(cmd)
    os.system(cmd)

if __name__ == '__main__':
    logger.info("odsx_dataengine_oracle-feeder_start")
    verboseHandle.printConsoleWarning("Menu -> DataEngine -> Oracle-Feeder -> Start")
    try:
        managerHost=''
        managerNodes = config_get_manager_node()
        managerHost = getManagerHost(managerNodes);
        if(len(str(managerHost))>0):
            displayOracleFeederShFiles()
            gs_space_dictionary_obj = listDeployed(managerHost)
            if(len(str(gs_space_dictionary_obj))>2):
                if len(sys.argv) > 1 and sys.argv[1] != "m":
                    proceedToStartOracleFeederWithName(sys.argv[1])
                else:
                    inputParam()
            else:
                logger.info("No feeder found.")
                verboseHandle.printConsoleInfo("No feeder found.")
        else:
            logger.info("No manager status ON.")
            verboseHandle.printConsoleInfo("No manager status ON.")
    except Exception as e:
        verboseHandle.printConsoleError("Eror in odsx_oracle-feeder_start : "+str(e))
        handleException(e)
