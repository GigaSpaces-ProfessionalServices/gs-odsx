#!/usr/bin/env python3

import os, subprocess, sqlite3, json, requests
from datetime import datetime
from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValueByConfigObj, readValuefromAppConfig, set_value_in_property_file
from utils.ods_cluster_config import config_get_manager_node, config_get_influxdb_node
from utils.ods_manager import getManagerInfo
from utils.ods_ssh import executeRemoteCommandAndGetOutput,executeLocalCommandAndGetOutput
import re

from utils.odsx_db2feeder_utilities import getPasswordByHost, getUsernameByHost

app_config_interval_key = 'app.retentionmanager.scheduler.interval'
app_config_time_key = 'app.retentionmanager.scheduler.time'
app_config_space_key = 'app.retentionmanager.space'
app_retentionmanager_sqlite_dbfile = 'app.retentionmanager.sqlite.dbfile'

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
serviceName =  'retention-manager.service'


def validateObjectType(input):
    logger.info("validateObjectType()")
    regX = "^[a-z]+(\.[a-z0-9]+)*$"
    pattern = re.compile(regX)
    result = pattern.match(input)
    #print(str(result))
    if(str(result)!='None'):
        return True
    logger.info("Exiting validateObjectType()")
    return False

def isTimeFormat(input):
    try:
        datetime.strptime(input, '%H:%M')
        return True
    except ValueError:
        return False


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


def getManagerHost():

    logger.info("getManagerHost()")
    managerNodes = config_get_manager_node()
    managerHost=""
    try:
        logger.info("getManagerHost() : managerNodes :"+str(managerNodes))
        for node in managerNodes:
            managerHost = os.getenv(node.ip)
            break;
    except Exception as e:
        handleException(e)
    
    return managerHost

def getInfluxHost():
    nodeList = config_get_influxdb_node()
    nodes=""
    for node in nodeList:
        if(len(nodes)==0):
            nodes = node.ip
            break;
        else:
            nodes = nodes+','+node.ip
    return nodes
    
def setupOrReloadService(spaceName,schedulerInterval,managerServer,dbLocation,retentionJar):
    
    influxHost = getInfluxHost()
    scheduler_minute = '0'
    scheduler_hour = '\*'
    scheduler_config = ''
    scheduler_interval = 600000
    
    appId = str(readValuefromAppConfig("app.space.security.appId")).replace('"','')
    safeId = str(readValuefromAppConfig("app.space.security.safeId")).replace('"','')
    objectId = str(readValuefromAppConfig("app.space.security.objectId")).replace('"','')
    logger.info("appId : "+appId+" safeID : "+safeId+" objectID : "+objectId)

    profile = str(readValuefromAppConfig("app.setup.profile"))
    if(profile is not None and len(profile)>0 and profile.casefold=="security"):
        username = str(getUsernameByHost(managerServer,appId,safeId,objectId))
        password = str(getPasswordByHost(managerServer,appId,safeId,objectId))


        managerInfo = getManagerInfo(True,username,password)
        lookupGroup = str(managerInfo['lookupGroups'])
        
    else:
        managerInfo = getManagerInfo()
        lookupGroup = str(managerInfo['lookupGroups'])
        


    isSchedulerTimeBase = ":" in schedulerInterval
    if(isSchedulerTimeBase==True):
        scheduler_minute=schedulerInterval.split(":")[1]
        scheduler_hour=schedulerInterval.split(":")[0]
        scheduler_config='timely'
        set_value_in_property_file(app_config_time_key,str(schedulerInterval))
        set_value_in_property_file(app_config_interval_key,'')
    else:
        scheduler_interval=int(schedulerInterval) * 60000
        scheduler_interval = str(scheduler_interval)
        scheduler_config='interval'
        set_value_in_property_file(app_config_interval_key,str(schedulerInterval))
        set_value_in_property_file(app_config_time_key,'')
    dbaGigaLogPath=str(readValueByConfigObj("app.gigalog.path"))

    args = spaceName+" "+managerServer+" "+dbLocation+" "+influxHost
    args+= " "+scheduler_config+" "+str(scheduler_interval)+" "+scheduler_minute+" "+scheduler_hour+" "+retentionJar+" "+lookupGroup +" "+dbaGigaLogPath

    commandToExecute = "scripts/retentionmanager_service_setup.sh "+args
    logger.info("Command "+commandToExecute)
    try:
        with Spinner():
            os.system(commandToExecute)
        
            os.system('sudo systemctl daemon-reload')
        
            logger.info("setupOrReloadService() completed")

    except Exception as e:
        logger.error("error occurred in setupService()")
    
    logger.info("setupService() : end")

def validateRetentionPolicy(retention_policy):
    logger.info("validateRetentionPolicy()")
    regX = "^([1-9]|[1-9][0-9]|[1-9][0-9][0-9]|1000)[dMy]{1}$"   #Allow any number between 1-1000 followed by d/M/y
    pattern = re.compile(regX)
    result = pattern.match(retention_policy)
    #print(str(result))
    if(str(result)!='None'):
        return True
    logger.info("Exiting validateRetentionPolicy()")
    return False

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


    