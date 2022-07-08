#!/usr/bin/env python3

import os, time, requests,json, subprocess, glob,sqlite3
from colorama import Fore
from scripts.logManager import LogManager
from utils.odsx_print_tabular_data import printTabular
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_validation import getSpaceServerStatus
from utils.ods_app_config import readValuefromAppConfig,readValueByConfigObj
from utils.odsx_db2feeder_utilities import getMSSQLQueryStatusFromSqlLite
from utils.odsx_db2feeder_utilities import getPasswordByHost, getUsernameByHost
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

def displayMSSQLFeederShFiles():
    logger.info("startMSSQLFeeder()")
    global fileNameDict
    global sourceMSSQLFeederShFilePath
    global fileNamePuNameDict
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)
    sourceMSSQLFeederShFilePath = str(str(sourceInstallerDirectory+".mssql.scripts.").replace('.','/'))
    logger.info("sourceDB2FeederShFilePath: "+str(sourceMSSQLFeederShFilePath))
    counter=1
    directory = os.getcwd()
    os.chdir(sourceMSSQLFeederShFilePath)
    fileNameDict = host_dictionary_obj()
    fileNamePuNameDict = host_dictionary_obj()
    headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
               Fore.YELLOW+"Name of mssql-feeder file"+Fore.RESET
               ]
    dataTable=[]
    for file in glob.glob("load_*.sh"):
        os.chdir(directory)
        dataArray = [Fore.GREEN+str(counter)+Fore.RESET,
                     Fore.GREEN+str(file)+Fore.RESET]
        dataTable.append(dataArray)
        fileNameDict.add(str(counter),str(file))
        puName = str(file).replace('load','').replace('.sh','').casefold()
        puName = 'mssqlfeeder'+puName
        fileNamePuNameDict.add(str(puName),str(file))
        counter=counter+1
    logger.info("fileNameDict : "+str(fileNameDict))
    logger.info("fileNamePuNameDict : "+str(fileNamePuNameDict))
    #printTabular(None,headers,dataTable)

def listDeployed(managerHost):
    logger.info("listDeployed()")
    global gs_space_dictionary_obj
    try:
        db_file = str(readValueByConfigObj("app.dataengine.mssql-feeder.sqlite.dbfile")).replace('"','').replace(' ','')
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
                   Fore.YELLOW+"Status"+Fore.RESET
                   ]
        gs_space_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_dictionary_obj : "+str(gs_space_dictionary_obj))
        counter=0
        dataTable=[]
        for data in jsonArray:
            hostId=''
            response2 = requests.get("http://"+str(managerHost)+":8090/v2/pus/"+str(data["name"])+"/instances",auth = HTTPBasicAuth(username, password))
            jsonArray2 = json.loads(response2.text)
            queryStatus = str(getMSSQLQueryStatusFromSqlLite(str(data["name"]))).replace('"','')
            for data2 in jsonArray2:
                hostId=data2["hostId"]
            if(len(str(hostId))==0):
                hostId="N/A"
            if(str(data["name"]).__contains__('mssql')):
                dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                             Fore.GREEN+data["name"]+Fore.RESET,
                             Fore.GREEN+str(hostId)+Fore.RESET,
                             Fore.GREEN+str(data["sla"]["zones"])+Fore.RESET,
                             Fore.GREEN+str(queryStatus)+Fore.RESET,
                             Fore.GREEN+data["status"]+Fore.RESET
                             ]
                logger.info("UPDATE mssql_host_port SET host='"+str(hostId)+"' where feeder_name like '%"+str(data["name"])+"%' ")
                mycursor = cnx.execute("UPDATE mssql_host_port SET host='"+str(hostId)+"' where feeder_name like '%"+str(data["name"])+"%' ")
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
    inputChoice = str(input(Fore.YELLOW+"Enter [1] For individual start \n[Enter] For all \n[99] For exit : "+Fore.RESET))
    if(str(inputChoice)=='99'):
        return
    if(str(inputChoice)=='1'):
        inputNumberToStart = str(input(Fore.YELLOW+"Enter serial number to start mssql-feeder : "+Fore.RESET))
        if(len(str(inputNumberToStart))==0):
            inputNumberToStart = str(input(Fore.YELLOW+"Enter serial number to start mssql-feeder : "+Fore.RESET))
        proceedToStartMSSQLFeeder(inputNumberToStart)
    if(len(str(inputChoice))==0):
        elements = len(fileNameDict)
        for i in range (1,elements+1):
            proceedToStartMSSQLFeeder(str(i))

def sqlLiteGetHostAndPortByFileName(puName):
    logger.info("sqlLiteGetHostAndPortByFileName() shFile : "+str(puName))
    try:
        db_file = str(readValueByConfigObj("app.dataengine.mssql-feeder.sqlite.dbfile")).replace('"','').replace(' ','')
        cnx = sqlite3.connect(db_file)
        logger.info("Db connection obtained."+str(cnx))
        logger.info("SQL : SELECT host,port,file FROM mssql_host_port where feeder_name like '%"+str(puName)+"%' ")
        mycursor = cnx.execute("SELECT host,port,file FROM mssql_host_port where feeder_name like '%"+str(puName)+"%' ")
        myresult = mycursor.fetchall()
        cnx.close()
        for row in myresult:
            logger.info("host : "+str(row[0]))
            logger.info("port : "+str(row[1]))
            logger.info("file : "+str(row[2]))
            return str(row[0])+','+str(row[1])+','+str(row[2])
    except Exception as e:
        handleException(e)

def proceedToStartMSSQLFeeder(fileNumberToStart):
    logger.info("proceedToStartMSSQLFeeder()")
    #shFileName = fileNameDict.get(str(fileNumberToStart))
    puName = gs_space_dictionary_obj.get(str(fileNumberToStart))
    print(puName)
    shFileName = fileNamePuNameDict.get(str(puName))
    hostAndPort = str(sqlLiteGetHostAndPortByFileName(puName)).split(',')
    print("hostAndPort"+str(hostAndPort))
    host = str(hostAndPort[0])
    port = str(hostAndPort[1])
    shFileName = str(hostAndPort[2])
    cmd = str(sourceMSSQLFeederShFilePath)+'/'+shFileName+' '+host+" "+port
    logger.info("cmd : "+str(cmd))
    print(cmd)
    os.system(cmd)
    #output = executeLocalCommandAndGetOutput(cmd)
    #print(output)

if __name__ == '__main__':
    logger.info("odsx_security_dataengine_mssql-feeder_start")
    verboseHandle.printConsoleWarning("Menu -> DataEngine -> MSSQL-Feeder -> Start")
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
            displayMSSQLFeederShFiles()
            gs_space_dictionary_obj = listDeployed(managerHost)
            if(len(str(gs_space_dictionary_obj))>2):
                inputParam()
            else:
                logger.info("No feeder found.")
                verboseHandle.printConsoleInfo("No feeder found.")
        else:
            logger.info("No manager status ON.")
            verboseHandle.printConsoleInfo("No manager status ON.")
    except Exception as e:
        verboseHandle.printConsoleError("Eror in odsx_mssql-feeder_start : "+str(e))
        handleException(e)
