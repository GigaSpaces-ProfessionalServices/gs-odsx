#!/usr/bin/env python3

import os, subprocess, sqlite3, json, requests
from datetime import datetime
from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValueByConfigObj, set_value_in_property_file
from utils.ods_cluster_config import config_get_manager_node, config_get_influxdb_node
from utils.ods_ssh import executeRemoteCommandAndGetOutput,executeLocalCommandAndGetOutput
import re

app_config_interval_key = 'app.retentionmanager.scheduler.interval'
app_config_time_key = 'app.retentionmanager.scheduler.time'
app_config_space_key = 'app.retentionmanager.space'
app_retentionmanager_sqlite_dbfile = 'app.retentionmanager.sqlite.dbfile'

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


def getPivotHost():
    hostname = os.getenv("pivot1")
    return hostname;





def handleException(e):
    logger.info("handleException()")
    trace = []
    tb = e.__traceback__e
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

def getLocalHostName():
    localIP=""
    try:
        localIP = executeLocalCommandAndGetOutput("curl --silent --connect-timeout 2 http://169.254.169.254/latest/meta-data/public-ipv4")
        localIP = str(localIP)
       
    except Exception as e:
        logger.error("error in getting public ip of pivot machine")

    if(str(localIP)=='b\'\''):
        localIP = executeLocalCommandAndGetOutput("hostname")

    localIP = str(localIP)
    localIP = localIP[1:]
    localIP = localIP.replace("'","")
    #print(localIP)
    return localIP;


    