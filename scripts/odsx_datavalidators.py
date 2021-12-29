#!/usr/bin/env python3

import os.path, argparse, sys
from scripts.logManager import LogManager
from colorama import Fore
from utils.odsx_print_tabular_data import printTabular
from utils.ods_cluster_config import config_get_manager_node, config_get_space_hosts, config_get_nb_list, \
    config_get_grafana_list, config_get_influxdb_node
from utils.ods_validation import getSpaceServerStatus
import requests, json, subprocess
from utils.ods_ssh import executeRemoteCommandAndGetOutput, executeRemoteCommandAndGetOutputPython36
from subprocess import Popen, PIPE
from scripts.spinner import Spinner
from utils.ods_validation import isValidHost, getTelnetStatus

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR


class host_dictionary_obj(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value


def getPort(dataSource):
    if (dataSource == 'gigaspaces'):
        return '4174'

    if (dataSource == 'mysql'):
        return '3306'

    if (dataSource == 'db2'):
        return '446'

    if (dataSource == 'ms-sql'):
        return '1433'


def doValidate():
    verboseHandle.printConsoleWarning('')
    headers = [Fore.YELLOW + "Sr Num" + Fore.RESET,
               Fore.YELLOW + "Test Name" + Fore.RESET
               ]
    data = []
    dataArray = [Fore.GREEN + "1" + Fore.RESET,
                 Fore.GREEN + "Measure" + Fore.RESET
                 ]
    data.append(dataArray)

    dataArray = [Fore.GREEN + "2" + Fore.RESET,
                 Fore.GREEN + "Compare" + Fore.RESET
                 ]
    data.append(dataArray)

    dataArray = [Fore.GREEN + "3" + Fore.RESET,
                 Fore.GREEN + "List of scheduled tests" + Fore.RESET
                 ]
    data.append(dataArray)

    printTabular(None, headers, data)
    verboseHandle.printConsoleWarning('');
    testType = str(input("Select test name (1/2/3) [1]: "))
    if (len(str(testType)) == 0):
        testType = '1'

    verboseHandle.printConsoleWarning('');
    if testType == '1':
        test = str(input("Test type (avg/count/min/max/lastvalue) [count]: "))
        if (len(str(test)) == 0):
            test = 'count'
        dataSource1Type = str(input("DataSource Type (gigaspaces/ms-sql/db2/mysql) [gigaspaces]: "))
        if (len(str(dataSource1Type)) == 0):
            dataSource1Type = 'gigaspaces'
        dataSource1HostIp = str(input("DataSource Host Ip [localhost]: "))
        if (len(str(dataSource1HostIp)) == 0):
            dataSource1HostIp = 'localhost'
        dataSource1Port = str(input("DataSource Port [" + getPort(dataSource1Type) + "]: "))
        if (len(str(dataSource1Port)) == 0):
            dataSource1Port = getPort(dataSource1Type)
        username1 = str(input("User name []: "))
        if (len(str(username1)) == 0):
            username1 = ''
        password1 = str(input("Password []: "))
        if (len(str(password1)) == 0):
            password1 = ''
        schemaName1 = str(input("Schema Name [demo]: "))
        if (len(str(schemaName1)) == 0):
            schemaName1 = 'demo'

        tableName1 = str(input("Table Name : "))
        if (len(str(tableName1)) == 0):
            tableName1 = '0'
        fieldName1 = str(input("Field Name : "))
        if (len(str(fieldName1)) == 0):
            fieldName1 = 'demo'
        if test != 'lastvalue':
            whereCondition = str(input("Where Condition [''] : "))
            if (len(str(whereCondition)) == 0):
                whereCondition = ''
        executionTime = str(input("Execution time delay (in minutes) [0]: "))
        if (len(str(executionTime)) == 0):
            executionTime = '0'

        verboseHandle.printConsoleWarning('');

        # http://localhost:7890/compare/avg?dataSource1Type=gigaspaces&dataSource1HostIp=localhost&dataSource1Port=414&schemaName1=demo&dataSource2Type=gigaspaces&dataSource2HostIp=localhost&dataSource2Port=4174&schemaName2=demo2&tableName=com.mycompany.app.Person&fieldName=salary
        managerHostConfig = 'localhost'
        if test == 'lastvalue':
            response = requests.get(
                "http://" + managerHostConfig + ":7890/query/"+tableName1+"/"+fieldName1 + "?dataSourceType=" + dataSource1Type
                + "&dataSourceHostIp=" + dataSource1HostIp + "&dataSourcePort=" + dataSource1Port
                + "&username=" + username1 + "&password=" + password1
                + "&schemaName=" + schemaName1 + "&executionTime=" + executionTime
                )
        else:
            response = requests.get(
                "http://" + managerHostConfig + ":7890/measure/" + test + "?dataSourceType=" + dataSource1Type
                + "&dataSourceHostIp=" + dataSource1HostIp + "&dataSourcePort=" + dataSource1Port
                + "&username=" + username1 + "&password=" + password1
                + "&schemaName=" + schemaName1 + "&tableName=" + tableName1
                + "&fieldName=" + fieldName1 + "&executionTime=" + executionTime
                + "&whereCondition="+whereCondition)

        logger.info(str(response.status_code))
        jsonArray = json.loads(response.text)

        verboseHandle.printConsoleWarning("")
        verboseHandle.printConsoleWarning("------------------------------------------------------------")
        # verboseHandle.printConsoleInfo("Test Result:  "+jsonArray["response"])
        if jsonArray["response"] == 'scheduled':
            verboseHandle.printConsoleInfo("Test is " + jsonArray["response"])
        elif jsonArray["response"].startswith('FAIL') :
            verboseHandle.printConsoleError("Test Result: " + jsonArray["response"])
        else:
            verboseHandle.printConsoleInfo("Test Result: " + jsonArray["response"])
        verboseHandle.printConsoleWarning("------------------------------------------------------------")

    elif testType == '2':
        test = str(input("Test type (avg/count/min/max) [count]: "))
        if (len(str(test)) == 0):
            test = 'count'
        dataSource1Type = str(input("DataSource1 Type (gigaspaces/ms-sql/db2/mysql) [gigaspaces]: "))
        if (len(str(dataSource1Type)) == 0):
            dataSource1Type = 'gigaspaces'
        dataSource1HostIp = str(input("DataSource1 Host Ip [localhost]: "))
        if (len(str(dataSource1HostIp)) == 0):
            dataSource1HostIp = 'localhost'
        dataSource1Port = str(input("DataSource1 Port [" + getPort(dataSource1Type) + "]: "))
        if (len(str(dataSource1Port)) == 0):
            dataSource1Port = getPort(dataSource1Type)
        username1 = str(input("User name1 []: "))
        if (len(str(username1)) == 0):
            username1 = ''
        password1 = str(input("Password1 []: "))
        if (len(str(password1)) == 0):
            password1 = ''
        schemaName1 = str(input("Schema Name 1 [demo]: "))
        if (len(str(schemaName1)) == 0):
            schemaName1 = 'demo'

        tableName1 = str(input("Table Name1 : "))
        if (len(str(tableName1)) == 0):
            tableName1 = '0'
        fieldName1 = str(input("Field Name1 : "))
        if (len(str(fieldName1)) == 0):
            fieldName1 = 'demo'

        verboseHandle.printConsoleWarning('');
        dataSource2Type = str(input("DataSource2 Type (gigaspaces/ms-sql/db2/mysql) [gigaspaces]: "))
        if (len(str(dataSource2Type)) == 0):
            dataSource2Type = 'gigaspaces'
        dataSource2HostIp = str(input("DataSource2 Host Ip [localhost]: "))
        if (len(str(dataSource2HostIp)) == 0):
            dataSource2HostIp = 'localhost'
        dataSource2Port = str(input("DataSource2 Port [" + getPort(dataSource2Type) + "]: "))
        if (len(str(dataSource2Port)) == 0):
            dataSource2Port = getPort(dataSource2Type)
        username2 = str(input("User name2 []: "))
        if (len(str(username2)) == 0):
            username2 = ''
        password2 = str(input("Password2 []: "))
        if (len(str(password2)) == 0):
            password2 = ''
        schemaName2 = str(input("Schema Name 2 [demo]: "))
        if (len(str(schemaName2)) == 0):
            schemaName2 = 'demo'

        tableName2 = str(input("Table Name2 : "))
        if (len(str(tableName2)) == 0):
            tableName2 = '0'
        fieldName2 = str(input("Field Name2 : "))
        if (len(str(fieldName2)) == 0):
            fieldName2 = 'demo'

        whereCondition = str(input("Where Condition [''] : "))
        if (len(str(whereCondition)) == 0):
            whereCondition = ''
        executionTime = str(input("Execution time delay (in minutes) [0]: "))
        if (len(str(executionTime)) == 0):
            executionTime = '0'

        # http://localhost:7890/compare/avg?dataSource1Type=gigaspaces&dataSource1HostIp=localhost&dataSource1Port=414&schemaName1=demo&dataSource2Type=gigaspaces&dataSource2HostIp=localhost&dataSource2Port=4174&schemaName2=demo2&tableName=com.mycompany.app.Person&fieldName=salary
        managerHostConfig = 'localhost'
        response = requests.get(
            "http://" + managerHostConfig + ":7890/compare/" + test + "?dataSource1Type=" + dataSource1Type
            + "&dataSource1HostIp=" + dataSource1HostIp + "&dataSource1Port=" + dataSource1Port
            + "&username1=" + username1 + "&password1=" + password1
            + "&schemaName1=" + schemaName1 + "&tableName1=" + tableName1
            + "&fieldName1=" + fieldName1 + "&dataSource2Type=" + dataSource2Type
            + "&dataSource2HostIp=" + dataSource2HostIp + "&dataSource2Port=" + dataSource2Port
            + "&username2=" + username2 + "&password2=" + password2
            + "&schemaName2=" + schemaName2 + "&tableName2=" + tableName2
            + "&fieldName2=" + fieldName2 + "&executionTime=" + executionTime
            + "&whereCondition="+whereCondition)

        logger.info(str(response.status_code))
        jsonArray = json.loads(response.text)

        verboseHandle.printConsoleWarning("")
        verboseHandle.printConsoleWarning("------------------------------------------------------------")
        if jsonArray["response"] == 'scheduled':
            verboseHandle.printConsoleInfo("Test is " + jsonArray["response"])
        elif jsonArray["response"] != 'PASS':
            verboseHandle.printConsoleError("Test Result:  " + jsonArray["response"])
        else:
            verboseHandle.printConsoleInfo("Test Result:  " + jsonArray["response"])
        verboseHandle.printConsoleWarning("------------------------------------------------------------")

    elif testType == '3':

        managerHostConfig = 'localhost'
        response = requests.get("http://" + managerHostConfig + ":7890/scheduledtasks")
        logger.info(str(response.status_code))
        jsonArray = json.loads(response.text)
        response = json.loads(jsonArray["response"])
        # print("response "+response)
        # print("response2 "+response[0])
        # print(isinstance(response, list))

        headers = [Fore.YELLOW + "Request Id" + Fore.RESET,
                   Fore.YELLOW + "Test Name" + Fore.RESET,
                   Fore.YELLOW + "Test Details" + Fore.RESET,
                   Fore.YELLOW + "Status/Result" + Fore.RESET
                   ]
        data = []
        counter = 1
        if response:
            for task in response:
                #print(task)
                if task["dbProperties"]["testType"] == "Measure":
                    testDetail = "Measurement:" + task["dbProperties"]["test"]+", Field:" + task["dbProperties"]["fieldName"]+", Table:" + task["dbProperties"]["tableName"]
                    testDetail2= "'"+task["dbProperties"]["test"] +"' of '"+task["dbProperties"]["fieldName"] +"' FROM '"+ task["dbProperties"]["tableName"]+"'"
                else:
                    testDetail = "Measurement:" + task["dbProperties"]["test"]+", Field:" + task["dbProperties"]["fieldName1"]+", Table:" + task["dbProperties"]["tableName1"]
                    testDetail2= "'"+task["dbProperties"]["test"] +"' of '"+task["dbProperties"]["fieldName1"] +"' FROM '"+ task["dbProperties"]["tableName1"] +"'"

                if task["dbProperties"]["whereCondition"] != "":
                    testDetail2 += " WHERE " + task["dbProperties"]["whereCondition"]

                status = Fore.GREEN + task["result"] + Fore.RESET
                if task["result"].startswith('FAIL') :
                    status = Fore.RED + task["result"] + Fore.RESET

                dataArray = [Fore.GREEN + str(task["id"]) + Fore.RESET,
                             Fore.GREEN + task["dbProperties"]["testType"] + Fore.RESET,
                             Fore.GREEN + testDetail2 + Fore.RESET,
                             status
                             ]
                data.append(dataArray)
                counter = counter + 1

        printTabular(None, headers, data)

    else:
        verboseHandle.printConsoleWarning("Invalid option")


if __name__ == '__main__':
    logger.info("odsx - validators")
    verboseHandle.printConsoleWarning('Menu -> Data Validators')
    verboseHandle.printConsoleWarning('');
    try:
        # with Spinner():
        doValidate()
    except Exception as e:
        logger.error("Exception in Menu->Validators" + str(e))
        verboseHandle.printConsoleError("Exception in Menu->Validators" + str(e))
