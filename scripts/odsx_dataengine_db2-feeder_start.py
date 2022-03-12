#!/usr/bin/env python3

import os, time, requests,json, subprocess, glob,sqlite3
from colorama import Fore
from scripts.logManager import LogManager
from utils.odsx_print_tabular_data import printTabular
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_validation import getSpaceServerStatus
from utils.ods_app_config import set_value_in_property_file,readValueByConfigObj

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
    sourceDB2FeederShFilePath = str(readValueByConfigObj("app.dataengine.db2-feeder.filePath.shFile"))
    counter=1
    directory = os.getcwd()
    os.chdir(sourceDB2FeederShFilePath)
    fileNameDict = host_dictionary_obj()
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
        counter=counter+1
    printTabular(None,headers,dataTable)

def inputParam():
    logger.info("inputParam()")
    inputNumberToStart =''
    inputChoice=''
    inputChoice = str(input(Fore.YELLOW+"Enter [1] For individual start \n[Enter] For all \n[99] For exit : "+Fore.RESET))
    if(str(inputChoice)=='99'):
        return
    if(str(inputChoice)=='1'):
        inputNumberToStart = str(input(Fore.YELLOW+"Enter serial number to start db2-feeder : "+Fore.RESET))
        if(len(str(inputNumberToStart))==0):
            inputNumberToStart = str(input(Fore.YELLOW+"Enter serial number to start db2-feeder : "+Fore.RESET))
        proceedToStartDB2Feeder(inputNumberToStart)
    if(len(str(inputChoice))==0):
        elements = len(fileNameDict)
        for i in range (1,elements+1):
            proceedToStartDB2Feeder(str(i))

def sqlLiteGetHostAndPortByFileName(shFileName):
    logger.info("sqlLiteGetHostAndPortByFileName() shFile : "+str(shFileName))
    try:
        db_file = str(readValueByConfigObj("app.dataengine.db2-feeder.sqlite.dbfile")).replace('"','').replace(' ','')
        cnx = sqlite3.connect(db_file)
        logger.info("Db connection obtained."+str(cnx))
        mycursor = cnx.execute("SELECT host,port FROM db2_host_port where file like '%"+str(shFileName)+"%' ")
        myresult = mycursor.fetchall()
        cnx.close()
        for row in myresult:
            logger.info("host : "+str(row[0]))
            logger.info("port : "+str(row[1]))
            return str(row[0])+','+str(row[1])
    except Exception as e:
        handleException(e)

def proceedToStartDB2Feeder(fileNumberToStart):
    logger.info("proceedToStartDB2Feeder()")
    shFileName = fileNameDict.get(str(fileNumberToStart))
    hostAndPort = str(sqlLiteGetHostAndPortByFileName(shFileName)).split(',')
    print("hostAndPort"+str(hostAndPort))
    host = str(hostAndPort[0])
    port = str(hostAndPort[1])
    cmd = str(sourceDB2FeederShFilePath)+'/'+shFileName+' '+host+" "+port
    print(cmd)
    os.system(cmd)
    #output = executeLocalCommandAndGetOutput(cmd)
    #print(output)

if __name__ == '__main__':
    logger.info("odsx_dataengine_db2-feeder_start")
    verboseHandle.printConsoleWarning("Menu -> DataEngine -> DB2-Feeder -> Start")
    try:
        displayDB2FeederShFiles()
        inputParam()
    except Exception as e:
        verboseHandle.printConsoleError("Eror in odsx_db2-feeder_start : "+str(e))
        handleException(e)