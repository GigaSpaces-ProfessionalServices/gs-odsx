#!/usr/bin/env python3

import os, time, requests,json,mysql, mysql.connector, subprocess, sqlite3
from colorama import Fore
from scripts.logManager import LogManager
from utils.odsx_print_tabular_data import printTabular
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_validation import getSpaceServerStatus
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


def listDeployed(managerHost):
    logger.info("listDeployed()")
    global gs_space_dictionary_obj
    try:
        logger.info("managerHost :"+str(managerHost))
        response = requests.get("http://"+str(managerHost)+":8090/v2/pus/")
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
            response2 = requests.get("http://"+str(managerHost)+":8090/v2/pus/"+str(data["name"])+"/instances")
            jsonArray2 = json.loads(response2.text)
            queryStatus = str(getQueryStatusFromSqlLite(str(data["name"]))).replace('"','')
            for data2 in jsonArray2:
                hostId=data2["hostId"]
            if(len(str(hostId))==0):
               hostId="N/A"
            if(str(data["name"]).__contains__('db2')):
                dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                             Fore.GREEN+data["name"]+Fore.RESET,
                             Fore.GREEN+str(hostId)+Fore.RESET,
                             Fore.GREEN+str(data["sla"]["zones"])+Fore.RESET,
                             Fore.GREEN+str(queryStatus)+Fore.RESET,
                             Fore.GREEN+data["status"]+Fore.RESET
                             ]
                gs_space_dictionary_obj.add(str(counter+1),str(data["name"]))
                counter=counter+1
                dataTable.append(dataArray)
        printTabular(None,headers,dataTable)
        return gs_space_dictionary_obj
    except Exception as e:
        handleException(e)

if __name__ == '__main__':
    logger.info("odsx_dataengine_list_db2-feeder_list")
    verboseHandle.printConsoleWarning("Menu -> DataEngine -> List -> DB2-Feeder -> List")
    try:
        managerNodes = config_get_manager_node()
        logger.info("managerNodes: main"+str(managerNodes))
        if(len(str(managerNodes))>0):
            managerHost = getManagerHost(managerNodes)
            listDeployed(managerHost)
    except Exception as e:
        handleException(e)