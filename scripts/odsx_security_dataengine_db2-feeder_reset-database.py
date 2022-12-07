#!/usr/bin/env python3

import os
import sqlite3

from scripts.logManager import LogManager
from utils.ods_app_config import readValueByConfigObj

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


def sqlLiteDeleteTableDb2Feeder():
    logger.info("sqlLiteDeleteTableDb2Feeder() ")
    try:
        db_file = str(readValueByConfigObj("app.dataengine.db2-feeder.sqlite.dbfile")).replace('"','').replace(' ','')
        cnx = sqlite3.connect(db_file)
        logger.info("Db connection obtained."+str(cnx))
        logger.info("DELETE FROM db2_host_port")
        cnx.execute("DELETE FROM db2_host_port")
        verboseHandle.printConsoleInfo("Table : db2_host_port reseted.")
        cnx.commit()
        cnx.close()
    except Exception as e:
        handleException(e)

if __name__ == '__main__':
    logger.info("odsx_security_dataengine_db2-feeder_reset")
    verboseHandle.printConsoleWarning("Menu -> DataEngine -> DB2-Feeder -> Reset")
    try:
        sqlLiteDeleteTableDb2Feeder()
    except Exception as e:
        verboseHandle.printConsoleError("Eror in odsx_db2-feeder_reset : "+str(e))
        handleException(e)
