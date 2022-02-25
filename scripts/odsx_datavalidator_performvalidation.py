#!/usr/bin/env python3

import os.path, argparse, sys
from scripts.logManager import LogManager
from colorama import Fore

from scripts.odsx_datavalidator_list import getDataValidationHost
from utils.odsx_print_tabular_data import printTabular
from utils.ods_cluster_config import config_get_dataValidation_nodes
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
    testType = str(input("Enter test sr number [1]: "))
    if (len(str(testType)) == 0):
        testType = '1'

    dataValidationNodes = config_get_dataValidation_nodes()
    dataValidationHost = getDataValidationHost(dataValidationNodes)
    logger.info("dataValidationHost : "+str(dataValidationHost))

    if str(dataValidationHost) == "":
        verboseHandle.printConsoleError("")
        verboseHandle.printConsoleError("Failed to connect to the Data validation server. Please check that it is running.")
        return

    #dataValidatorServiceHost = str(input("Data validator service host ["+str(dataValidationHost)+"]: "))
    #if (len(str(dataValidatorServiceHost)) == 0):
    #    dataValidatorServiceHost = dataValidationHost

    dataValidatorServiceHost = dataValidationHost

    verboseHandle.printConsoleWarning('');
    if testType == '1':
        verboseHandle.printConsoleWarning('Existing Measurements:');
        resultCount = printmeasurementtable(dataValidatorServiceHost)

        registernew = 'yes'
        if resultCount > 0:
            registernew = str(input("Do you want to register new measurement (yes/no) [no]: "))
            if (len(str(registernew)) == 0):
                registernew = 'no'
        else:
            verboseHandle.printConsoleWarning("No measurement available. Please register one")

        if registernew == 'yes':
            test = str(input("Test type (count/avg/min/max/sum) [count]: "))
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

            verboseHandle.printConsoleWarning('');
            data ={
                "test": test,
                "dataSourceType": dataSource1Type,
                "dataSourceHostIp": dataSource1HostIp,
                "dataSourcePort": dataSource1Port,
                "username": username1,
                "password": password1,
                "schemaName": schemaName1,
                "tableName": tableName1,
                "fieldName": fieldName1,
                "whereCondition": whereCondition
            }
            headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
            response = requests.post("http://"+dataValidatorServiceHost+":7890/measurement/register"
                                     ,data=json.dumps(data)
                                     ,headers=headers)

            logger.info(str(response.status_code))
            jsonArray = json.loads(response.text)

            verboseHandle.printConsoleWarning("")
            verboseHandle.printConsoleWarning("------------------------------------------------------------")
            verboseHandle.printConsoleInfo("Test Result:  "+jsonArray["response"])
            verboseHandle.printConsoleWarning("------------------------------------------------------------")
        else:  # Run existing measurement
            verboseHandle.printConsoleWarning('');
            measurementId = str(input("Select measurement by id to run [1]: "))
            if (len(str(measurementId)) == 0):
                measurementId = '1')
            while(measurementId not in measurementids):
                print(Fore.YELLOW +"Please select  measurement from above list"+Fore.RESET) 
                measurementId = str(input("Select measurement by id to run [1]:"))
            executionTime = str(input("Execution time delay (in minutes) [0]: "))
            if (len(str(executionTime)) == 0):
                executionTime = '0'

            response = requests.get(
                "http://" + dataValidatorServiceHost + ":7890/measurement/run/"+measurementId+"?executionTime="+executionTime)

            logger.info(str(response.status_code))
            jsonArray = json.loads(response.text)

            verboseHandle.printConsoleWarning("")
            verboseHandle.printConsoleWarning("------------------------------------------------------------")
            # verboseHandle.printConsoleInfo("Test Result:  "+jsonArray["response"])
            if jsonArray["response"] == 'scheduled':
                verboseHandle.printConsoleInfo("Test is " + jsonArray["response"])
            elif jsonArray["response"].startswith('FAIL'):
                verboseHandle.printConsoleError("Test Result: " + jsonArray["response"])
            else:
                verboseHandle.printConsoleInfo("Test Result: " + jsonArray["response"])
            verboseHandle.printConsoleWarning("------------------------------------------------------------")
    elif testType == '2':
        resultCount = printmeasurementtable(dataValidatorServiceHost)
        if resultCount > 0:
            measurementIdA = str(input("Select 1st measurement Id for comparison : "))
            if (len(str(measurementIdA)) == 0):
                measurementIdA = '1'
            while(measurementIdA not in measurementids):
               print(Fore.YELLOW +"Please select  1st measurement Id  from above list"+Fore.RESET) 
               measurementIdA = str(input("Select 1st measurement Id for comparison : "))
            measurementIdB = str(input("Select 2nd measurement Id for comparison : "))
            if (len(str(measurementIdB)) == 0):
                measurementIdB = '1'
            while(measurementIdB not in measurementids):
              print(Fore.YELLOW +"Please select  2nd measurement Id  from above list"+Fore.RESET) 
              measurementIdB = str(input("Select 2nd measurement Id for comparison : "))

            executionTime = str(input("Execution time delay (in minutes) [0]: "))
            if (len(str(executionTime)) == 0):
                executionTime = '0'

            # http://localhost:7890/compare/avg?dataSource1Type=gigaspaces&dataSource1HostIp=localhost&dataSource1Port=414&schemaName1=demo&dataSource2Type=gigaspaces&dataSource2HostIp=localhost&dataSource2Port=4174&schemaName2=demo2&tableName=com.mycompany.app.Person&fieldName=salary
            response = requests.get(
                "http://" + dataValidatorServiceHost + ":7890/compare/" + measurementIdA+"/"+measurementIdB
                 + "?executionTime=" + executionTime)

            if response.status_code == 200:
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
        else:
            verboseHandle.printConsoleInfo("No measurement available.Please Register first.")


    elif testType == '22':
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
        response = requests.get(
            "http://" + dataValidatorServiceHost + ":7890/compare/" + test + "?dataSource1Type=" + dataSource1Type
            + "&dataSource1HostIp=" + dataSource1HostIp + "&dataSource1Port=" + dataSource1Port
            + "&username1=" + username1 + "&password1=" + password1
            + "&schemaName1=" + schemaName1 + "&tableName1=" + tableName1
            + "&fieldName1=" + fieldName1 + "&dataSource2Type=" + dataSource2Type
            + "&dataSource2HostIp=" + dataSource2HostIp + "&dataSource2Port=" + dataSource2Port
            + "&username2=" + username2 + "&password2=" + password2
            + "&schemaName2=" + schemaName2 + "&tableName2=" + tableName2
            + "&fieldName2=" + fieldName2 + "&executionTime=" + executionTime
            + "&whereCondition=" + whereCondition)

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
        response = requests.get("http://" + dataValidatorServiceHost + ":7890/scheduledtasks")
        logger.info(str(response.status_code))
        jsonArray = json.loads(response.text)
        response = json.loads(jsonArray["response"])
        # print("response "+response)
        # print("response2 "+response[0])
        # print(isinstance(response, list))

        headers = [Fore.YELLOW + "Request Id" + Fore.RESET,
                   Fore.YELLOW + "Test Name" + Fore.RESET,
                   Fore.YELLOW + "Test Details" + Fore.RESET,
                  # Fore.YELLOW + "Datasource Details" + Fore.RESET,
                   Fore.YELLOW + "Status/Result" + Fore.RESET
                   ]
        data = []
        counter = 1
        if response:
            for task in response:
                # print(task)
                # if task["type"] == "Measure":
                # testDetail = "Measurement:" + task["measurementList"][0]["type"]+", Field:" + task["measurementList"][0]["fieldName"]+", Table:" + task["measurementList"][0]["tableName"]
                testDetail = "'" + task["measurementList"][0]["type"] + "' of '" + task["measurementList"][0][
                    "fieldName"] + "' FROM '" + task["measurementList"][0]["tableName"] + "'"
                # else:
                #    testDetail = "Measurement:" + task["measurementList"][0]["type"]+", Field:" + task["measurementList"][0]["fieldName"]+", Table:" + task["measurementList"][0]["tableName"]
                #    testDetail2= "'"+task["measurementList"][0]["type"] +"' of '"+task["measurementList"][0]["fieldName"] +"' FROM '"+ task["measurementList"][0]["tableName"] +"'"

                if task["measurementList"][0]["whereCondition"] != "":
                    testDetail += " WHERE " + task["measurementList"][0]["whereCondition"]

                dataSouceDetail=""
                if task["type"] == "Measure":
                    dataSouceDetail+=" | "+task["measurementList"][0]["dataSourceType"] \
                                +"(space="+task["measurementList"][0]["schemaName"]\
                                +", host="+task["measurementList"][0]["dataSourceHostIp"]+")"
                else:
                    dataSouceDetail+=" | "+task["measurementList"][0]["dataSourceType"] \
                                +"(space="+task["measurementList"][0]["schemaName"] \
                                +", host="+task["measurementList"][0]["dataSourceHostIp"]+")"
                    dataSouceDetail+=" | "+task["measurementList"][1]["dataSourceType"] \
                                +"(space="+task["measurementList"][1]["schemaName"] \
                                +", host="+task["measurementList"][1]["dataSourceHostIp"]+")"

                status = Fore.GREEN + task["result"] + Fore.RESET
                if task["result"].startswith('FAIL'):
                    status = Fore.RED + task["result"] + Fore.RESET

                dataArray = [Fore.GREEN + str(task["id"]) + Fore.RESET,
                             Fore.GREEN + task["type"] + Fore.RESET,
                             Fore.GREEN + testDetail + Fore.RESET,
                            # Fore.GREEN + dataSouceDetail + Fore.RESET,
                             status
                             ]
                data.append(dataArray)
                counter = counter + 1

        printTabular(None, headers, data)

    else:
        verboseHandle.printConsoleWarning("Invalid option")

measurementids=[]
def printmeasurementtable(dataValidatorServiceHost):

    try:
        response = requests.get("http://" + dataValidatorServiceHost + ":7890/measurement/list")
    except:
        print("An exception occurred")

    if response.status_code == 200:
        #logger.info(str(response.status_code))
        jsonArray = json.loads(response.text)
        response = json.loads(jsonArray["response"])
        # print("response2 "+response[0])
        # print(isinstance(response, list))

        headers = [Fore.YELLOW + "Measurement Id" + Fore.RESET,
                   Fore.YELLOW + "Measurement Datasource" + Fore.RESET,
                   Fore.YELLOW + "Measurement Query" + Fore.RESET
                   ]
        data = []
        if response:
            for measurement in response:
                #print(measurement)
                queryDetail= "'"+measurement["type"] +"' of '"+measurement["fieldName"] +"' FROM '"+ measurement["tableName"]+"'"
                if measurement["whereCondition"] != "":
                    queryDetail += " WHERE " + measurement["whereCondition"]

                dataArray = [Fore.GREEN + str(measurement["id"]) + Fore.RESET,
                             Fore.GREEN + measurement["dataSourceType"] +"(schema="+measurement["schemaName"]+", host="+measurement["dataSourceHostIp"]+")" + Fore.RESET,
                             Fore.GREEN + queryDetail + Fore.RESET
                             ]
                data.append(dataArray)
                measurementids.append(str(measurement["id"]) )
        printTabular(None, headers, data)
        verboseHandle.printConsoleWarning('');
        return len(response)
    return 0


if __name__ == '__main__':
    logger.info("MENU -> Data Validator -> Perform Validation")
    verboseHandle.printConsoleWarning('MENU -> Data Validator -> Perform Validation')
    verboseHandle.printConsoleWarning('');
    try:
        # with Spinner():
        doValidate()
    except Exception as e:
        logger.error("Exception in Menu->Validators" + str(e))
        verboseHandle.printConsoleError("Exception in Menu->Validators" + str(e))
