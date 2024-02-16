#!/usr/bin/env python3
import glob
import json
import os
import re
import requests
import sqlite3
from colorama import Fore
from datetime import date, timedelta

from requests.auth import HTTPBasicAuth

from scripts.logManager import LogManager
from utils.ods_app_config import readValueByConfigObj
from utils.ods_cluster_config import config_get_manager_node
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_db2feeder_utilities import getOracleQueryStatusFromSqlLite, getPasswordByHost, getUsernameByHost
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
        response = requests.get("http://"+str(managerHost)+":8090/v2/pus/",auth = HTTPBasicAuth(username, password))
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Resources on cluster:")
        headers = [Fore.YELLOW + "Sr No." + Fore.RESET,
                   Fore.YELLOW + "Name" + Fore.RESET,
                   Fore.YELLOW + "Host" + Fore.RESET,
                   Fore.YELLOW + "Zone" + Fore.RESET,
                   Fore.YELLOW + "Query Status" + Fore.RESET,
                   Fore.YELLOW + "Status" + Fore.RESET,
                   Fore.YELLOW + "Condition" + Fore.RESET
                   ]
        gs_space_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_dictionary_obj : " + str(gs_space_dictionary_obj))
        counter = 0
        dataTable = []
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
        sourceOracleFeederShFilePath = str(sourceInstallerDirectory + ".oracle.scripts.").replace('.', '/')
        flag = False
        for i in jsonArray:
            if (str(i['name']).__contains__("oracle")):
                flag = True

        logger.info("sourceInstallerDirectory:" + sourceInstallerDirectory)
        sourceOracleFeederShFilePath = str(sourceInstallerDirectory + ".oracle.scripts.").replace('.', '/')
        os.chdir(sourceOracleFeederShFilePath)

        deployedPUNames = []
        if (len(jsonArray) > 0):

            for data in jsonArray:
                hostId = ''
                response2 = requests.get(
                    "http://" + str(managerHost) + ":8090/v2/pus/" + str(data["name"]) + "/instances",auth = HTTPBasicAuth(username, password))
                jsonArray2 = json.loads(response2.text)
                queryStatus = str(getOracleQueryStatusFromSqlLite(str(data["name"]))).replace('"', '')
                for data2 in jsonArray2:
                    hostId = data2["hostId"]
                if (len(str(hostId)) == 0):
                    hostId = "N/A"
                if (str(data["name"]).__contains__('oracle')):
                    os.getcwd()
                    os.chdir(sourceOracleFeederShFilePath)
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
                                    if(myString.find(startString) != -1):
                                        mySubString = myString[
                                                      myString.find(startString) + len(startString):myString.find(endString)]
                                        # puName = 'oraclefeeder_'+puName
                                        conditionDate = getFormattedDate(mySubString)
                                    else:
                                        conditionDate = "-"
                                    deployedPUNames.append(data["name"])
                                    dataArray = [Fore.GREEN + str(counter + 1) + Fore.RESET,
                                                 Fore.GREEN + data["name"] + Fore.RESET,
                                                 Fore.GREEN + str(hostId) + Fore.RESET,
                                                 Fore.GREEN + str(data["sla"]["zones"]) + Fore.RESET,
                                                 Fore.GREEN + str(queryStatus) + Fore.RESET,
                                                 Fore.GREEN + data["status"] + Fore.RESET,
                                                 Fore.GREEN + str(conditionDate) + Fore.RESET
                                                 ]
                    logger.info("UPDATE oracle_host_port SET host='" + str(hostId) + "' where feeder_name like '%" + str(
                        data["name"]) + "%' ")
                    mycursor = cnx.execute(
                        "UPDATE oracle_host_port SET host='" + str(hostId) + "' where feeder_name like '%" + str(
                            data["name"]) + "%' ")
                    logger.info("query result:" + str(mycursor.rowcount))

                    gs_space_dictionary_obj.add(str(counter + 1), str(data["name"]))
                    counter = counter + 1
                    dataTable.append(dataArray)

        for file in glob.glob("load_*.sh"):
            os.chdir(sourceOracleFeederShFilePath)
            puName = str(file).replace('load_', '').replace('.sh', '').casefold()
            file = open(file, "r")
            puName = 'oraclefeeder_'+puName
            if puName in deployedPUNames:
                continue
            for line in file:
                if (line.startswith("curl")):
                    #puName = 'oraclefeeder_'+puName
                    myString = line
                    startString = '&condition='
                    endString = "&exclude-columns="
                    # mySubString = myString[
                    #               myString.find(startString) + len(startString):myString.find(endString)]

                    if(myString.find(startString) != -1):
                        mySubString = myString[
                                    myString.find(startString) + len(startString):myString.find(endString)]
                        #puName = 'oraclefeeder_'+puName
                        conditionDate = getFormattedDate(mySubString)
                    else:
                        #puName = 'oraclefeeder_'+puName
                        conditionDate = "-"
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

        cnx.commit()
        cnx.close()

        printTabular(None, headers, dataTable)
        return gs_space_dictionary_obj
    except Exception as e:
        handleException(e)

if __name__ == '__main__':
    logger.info("odsx_dataengine_oracle-feeder_list")
    verboseHandle.printConsoleWarning("Menu -> DataEngine -> Oracle-Feeder -> List")
    username = ""
    password = ""

    try:
        managerNodes = config_get_manager_node()
        logger.info("managerNodes: main"+str(managerNodes))
        if(len(str(managerNodes))>0):
            username = str(getUsernameByHost())
            password = str(getPasswordByHost())
            managerHost = getManagerHost(managerNodes)
            listDeployed(managerHost)
    except Exception as e:
        handleException(e)