#!/usr/bin/env python3

import os
import socket

import requests
import sqlite3
from scripts.logManager import LogManager
from utils.ods_app_config import readValueByConfigObj
from utils.odsx_db2feeder_utilities import executeLocalCommandAndGetOutput

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

def getGilboaQueryStatusFromSqlLite(feederName):
    logger.info("getQueryStatusFromSqlLite() shFile : "+str(feederName))
    try:
        db_file = str(readValueByConfigObj("app.dataengine.gilboa-feeder.sqlite.dbfile")).replace('"','').replace(' ','')
        cnx = sqlite3.connect(db_file)
        logger.info("Db connection obtained."+str(cnx))
        logger.info("CREATE TABLE IF NOT EXISTS gilboa_host_port (file VARCHAR(50), feeder_name VARCHAR(50), host VARCHAR(50), port varchar(10))")
        cnx.execute("CREATE TABLE IF NOT EXISTS gilboa_host_port (file VARCHAR(50), feeder_name VARCHAR(50), host VARCHAR(50), port varchar(10))")
        cnx.commit()
        logger.info("SQL : SELECT host,port FROM gilboa_host_port where feeder_name like '%"+str(feederName)+"%' ")
        mycursor = cnx.execute("SELECT host,port FROM gilboa_host_port where feeder_name like '%"+str(feederName)+"%' ")
        myresult = mycursor.fetchall()
        cnx.close()
        host = ''
        port = ''
        output='gilboa db is empty or no matching record found'
        for row in myresult:
            logger.info("host : "+str(row[0]))
            host = str(row[0])
            host = str(socket.gethostbyaddr(host).__getitem__(2)[0])
            logger.info("port : "+str(row[1]))
            port = str(row[1])
            cmd = "curl -X POST http://"+host+":"+port+"/table-feed/actions_count?table-name=dbo.Portal_Calendary_View&base-column=v_timestamp"
            logger.info("cmd : "+str(cmd))
            output = executeLocalCommandAndGetOutput(cmd)
            output = "predicated count : "+str(output)
            logger.info("Output ::"+str(output))
        return output
    except Exception as e:
        handleException(e)

def sqlLiteGetHostAndPortByFileName():
    puName="gilboafeeder"
    logger.info("sqlLiteGetHostAndPortByFileName() shFile : "+str(puName))
    try:
        db_file = str(readValueByConfigObj("app.dataengine.gilboa-feeder.sqlite.dbfile")).replace('"','').replace(' ','')
        cnx = sqlite3.connect(db_file)
        logger.info("Db connection obtained."+str(cnx))
        logger.info("SQL : SELECT host,port,file FROM gilboa_host_port where feeder_name like '%"+str(puName)+"%' ")
        mycursor = cnx.execute("SELECT host,port,file FROM gilboa_host_port where feeder_name like '%"+str(puName)+"%' ")
        myresult = mycursor.fetchall()
        cnx.close()
        for row in myresult:
            logger.info("host : "+str(row[0]))
            logger.info("port : "+str(row[1]))
            logger.info("file : "+str(row[2]))
            gilboaSyncChangeCount(str(row[0]),str(row[1]))
    except Exception as e:
        handleException(e)

def getData():
    data = {
        "table-name": "dbo.Portal_Calendary_View",
        "base-column": "v_timestamp"
    }
    return data
def gilboaSyncChangeCount(host,port):
    logger.info("count for gilboa sync changes")
    response = requests.post('http://' + host + ':'+port+'/table-feed/actions_count',params=getData(),
                            headers={'Accept': 'application/json'})
    verboseHandle.printConsoleInfo("Count in memory : " + response.text)

if __name__ == '__main__':
    logger.info("odsx_dataengine_gilboa-feeder_predicted-ops")
    verboseHandle.printConsoleWarning("Menu -> DataEngine  -> Gilboa -> Update -> Predicted Operation")
    try:
        puName="gilboafeeder"
        verboseHandle.printConsoleInfo(getGilboaQueryStatusFromSqlLite(puName))
        #sqlLiteGetHostAndPortByFileName()
    except Exception as e:
        verboseHandle.printConsoleError("Error in odsx_dataengine_gilboa-feeder_predicted-ops : "+str(e))
        handleException(e)
