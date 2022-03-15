#!/usr/bin/env python3

import os, subprocess, sqlite3
from scripts.logManager import LogManager
from utils.ods_app_config import readValueByConfigObj
from utils.ods_ssh import executeRemoteCommandAndGetOutput

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

def executeLocalCommandAndGetOutput(commandToExecute):
    logger.info("executeLocalCommandAndGetOutput() cmd :" + str(commandToExecute))
    cmd = commandToExecute
    cmdArray = cmd.split(" ")
    #process = subprocess.Popen(cmdArray, stdout=subprocess.PIPE)
    process = subprocess.Popen(cmdArray, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out, error = process.communicate()
    out = out.decode()
    return str(out).replace('\n', '')

def getQueryStatusFromSqlLite(feederName):
    logger.info("getQueryStatusFromSqlLite() shFile : "+str(feederName))
    try:
        db_file = str(readValueByConfigObj("app.dataengine.db2-feeder.sqlite.dbfile")).replace('"','').replace(' ','')
        cnx = sqlite3.connect(db_file)
        logger.info("Db connection obtained."+str(cnx))
        logger.info("CREATE TABLE IF NOT EXISTS db2_host_port (file VARCHAR(50), feeder_name VARCHAR(50), host VARCHAR(50), port varchar(10))")
        cnx.execute("CREATE TABLE IF NOT EXISTS db2_host_port (file VARCHAR(50), feeder_name VARCHAR(50), host VARCHAR(50), port varchar(10))")
        cnx.commit()
        logger.info("SQL : SELECT host,port FROM db2_host_port where feeder_name like '%"+str(feederName)+"%' ")
        mycursor = cnx.execute("SELECT host,port FROM db2_host_port where feeder_name like '%"+str(feederName)+"%' ")
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

def getUsernameByHost(managerHost,appId,safeId,objectId):
    logger.info("getUsernameByHost()")
    cmdToExecute = '/opt/CARKaim/sdk/clipasswordsdk GetPassword -p AppDescs.AppID='+appId+' -p Query="Safe='+safeId+';Folder=;Object='+objectId+';" -o PassProps.UserName'
    logger.info("cmdToExecute : "+str(cmdToExecute))
    output = executeRemoteCommandAndGetOutput(managerHost,"root",cmdToExecute)
    output=str(output).replace('\n','')
    logger.info("Username : "+output)
    return output

def getPasswordByHost(managerHost,appId,safeId,objectId):
    logger.info("getPasswordByHost()")
    cmdToExecute = '/opt/CARKaim/sdk/clipasswordsdk GetPassword -p AppDescs.AppID='+appId+' -p Query="Safe='+safeId+';Folder=;Object='+objectId+';" -o Password'
    logger.info("cmdToExecute : "+str(cmdToExecute))
    output = executeRemoteCommandAndGetOutput(managerHost,"root",cmdToExecute)
    output=str(output).replace('\n','')
    logger.info("Password : "+output)
    return  output