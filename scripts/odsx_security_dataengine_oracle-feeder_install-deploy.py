#!/usr/bin/env python3

import glob
import json
import os
import requests
import sqlite3
import subprocess
import time

from colorama import Fore
from requests.auth import HTTPBasicAuth

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValueByConfigObj, getYamlFilePathInsideFolder
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_dataIntegration_nodes
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_ssh import executeRemoteCommandAndGetOutput
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_keypress import userInputWrapper
from utils.odsx_print_tabular_data import printTabular
from utils.odsx_db2feeder_utilities import getPortNotExistInOracleFeeder
from utils.odsx_db2feeder_utilities import getPasswordByHost, getUsernameByHost

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
clusterHosts = []
confirmCreateGSC=''

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR


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

class host_dictionary_obj(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

def executeLocalCommandAndGetOutput(commandToExecute):
    logger.info("executeLocalCommandAndGetOutput() cmd :" + str(commandToExecute))
    cmd = commandToExecute
    cmdArray = cmd.split(" ")
    process = subprocess.Popen(cmdArray, stdout=subprocess.PIPE)
    out, error = process.communicate()
    out = out.decode()
    return str(out).replace('\n', '')

def getDIServerHostList():
    nodeList = config_get_dataIntegration_nodes()
    nodes = ""
    for node in nodeList:
        # if(str(node.role).casefold() == 'server'):
        if (len(nodes) == 0):
            nodes = os.getenv(node.ip)
        else:
            nodes = nodes + ',' + os.getenv(node.ip)
    return nodes

def getBootstrapAddress(hostConfig):
    logger.info("getBootstrapAddress()")
    bootstrapAddress=''
    for host in hostConfig.split(','):
        bootstrapAddress=bootstrapAddress+host+':9092,'
    bootstrapAddress=bootstrapAddress[:-1]
    logger.info("getBootstrapAddress : "+str(bootstrapAddress))
    return bootstrapAddress

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

def listDeployed(managerHost):
    global gs_space_dictionary_obj
    global activefeeder
    activefeeder=[]
    deployedPUNames =[]
    try:
        logger.info("managerHost :"+str(managerHost))
        response = requests.get("http://"+str(managerHost)+":8090/v2/pus/",auth = HTTPBasicAuth(username, password))
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Resources on cluster:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Name"+Fore.RESET,
                   Fore.YELLOW+"Resource"+Fore.RESET,
                   Fore.YELLOW+"Zone"+Fore.RESET,
                   Fore.YELLOW+"processingUnitType"+Fore.RESET,
                   Fore.YELLOW+"Status"+Fore.RESET
                   ]
        gs_space_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_dictionary_obj : "+str(gs_space_dictionary_obj))
        counter=0
        dataTable=[]
        for data in jsonArray:
            if(str(data["name"]).casefold().__contains__("oraclefeeder")):
                dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                             Fore.GREEN+data["name"]+Fore.RESET,
                             Fore.GREEN+data["resource"]+Fore.RESET,
                             Fore.GREEN+str(data["sla"]["zones"])+Fore.RESET,
                             Fore.GREEN+data["processingUnitType"]+Fore.RESET,
                             Fore.GREEN+data["status"]+Fore.RESET
                             ]
                deployedPUNames.append(data["name"])
                gs_space_dictionary_obj.add(str(counter+1),str(data["name"]))
                activefeeder.append(str(data["name"]))
                counter=counter+1
                dataTable.append(dataArray)

        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
        sourceOracleFeederShFilePath = str(sourceInstallerDirectory + ".oracle.scripts.").replace('.', '/')
        directory = os.getcwd()
        os.chdir(sourceOracleFeederShFilePath)
        for file in glob.glob("load_*.sh"):
            os.chdir(directory)
            puName = str(file).replace('load_', '').replace('.sh', '').casefold()
            puName = 'oraclefeeder_'+puName
            if puName in deployedPUNames:
                continue

            dataArray = [Fore.GREEN + str(counter + 1) + Fore.RESET,
                            Fore.GREEN + puName + Fore.RESET,
                            Fore.GREEN + str("-") + Fore.RESET,
                            Fore.GREEN + str("-") + Fore.RESET,
                            Fore.GREEN + str("-") + Fore.RESET,
                            Fore.GREEN + "Undeployed" + Fore.RESET,
                        ]
            counter = counter + 1
            dataTable.append(dataArray)

        printTabular(None,headers,dataTable)
        return gs_space_dictionary_obj
    except Exception as e:
        handleException(e)

def listSpacesOnServer(managerNodes):
    try:
        logger.info("listSpacesOnServer : managerNodes :"+str(managerNodes))
        managerHost=''
        for node in managerNodes:
            status = getSpaceServerStatus(os.getenv(node.ip))
            logger.info("Ip :"+str(os.getenv(node.ip))+"Status : "+str(status))
            if(status=="ON"):
                managerHost = os.getenv(node.ip);
        logger.info("managerHost :"+managerHost)
        response = requests.get("http://"+managerHost+":8090/v2/spaces",auth = HTTPBasicAuth(username, password))
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Existing spaces on cluster:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Name"+Fore.RESET,
                   Fore.YELLOW+"PU Name"+Fore.RESET
                   ]
        gs_space_host_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_host_dictionary_obj : "+str(gs_space_host_dictionary_obj))
        counter=0
        dataTable=[]
        for data in jsonArray:
            dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                         Fore.GREEN+data["name"]+Fore.RESET,
                         Fore.GREEN+data["processingUnitName"]+Fore.RESET
                         ]
            gs_space_host_dictionary_obj.add(str(counter+1),str(data["name"]))
            counter=counter+1
            dataTable.append(dataArray)
        #printTabular(None,headers,dataTable)
        return gs_space_host_dictionary_obj
    except Exception as e:
        handleException(e)

def get_gs_host_details(managerNodes):
    try:
        logger.info("get_gs_host_details() : managerNodes :"+str(managerNodes))
        for node in managerNodes:
            status = getSpaceServerStatus(os.getenv(node.ip))
            if(status=="ON"):
                managerHostConfig = os.getenv(node.ip);
        logger.info("managerHostConfig : "+str(managerHostConfig))
        response = requests.get('http://'+managerHostConfig+':8090/v2/hosts', headers={'Accept': 'application/json'},auth = HTTPBasicAuth(username, password))
        logger.info("response status of host :"+str(managerHostConfig)+" status :"+str(response.status_code))
        jsonArray = json.loads(response.text)
        gs_servers_host_dictionary_obj = host_dictionary_obj()
        for data in jsonArray:
            gs_servers_host_dictionary_obj.add(str(data['name']),str(data['address']))
        logger.info("gs_servers_host_dictionary_obj : "+str(gs_servers_host_dictionary_obj))
        return gs_servers_host_dictionary_obj
    except Exception as e:
        handleException(e)

def displaySpaceHostWithNumber(managerNodes, spaceNodes):
    try:
        logger.info("displaySpaceHostWithNumber() managerNodes :"+str(managerNodes)+" spaceNodes :"+str(spaceNodes))
        gs_host_details_obj = get_gs_host_details(managerNodes)
        logger.info("gs_host_details_obj : "+str(gs_host_details_obj))
        counter = 0
        space_dict_obj = host_dictionary_obj()
        logger.info("space_dict_obj : "+str(space_dict_obj))
        for node in spaceNodes:
            if(gs_host_details_obj.__contains__(str(os.getenv(node.name))) or (str(os.getenv(node.name)) in gs_host_details_obj.values())):
                space_dict_obj.add(str(counter+1),os.getenv(node.name))
                counter=counter+1
        logger.info("space_dict_obj : "+str(space_dict_obj))
        #verboseHandle.printConsoleWarning("Space hosts lists")
        headers = [Fore.YELLOW+"No"+Fore.RESET,
                   Fore.YELLOW+"Host"+Fore.RESET]
        dataTable=[]
        for data in range (1,len(space_dict_obj)+1):
            dataArray = [Fore.GREEN+str(data)+Fore.RESET,
                         Fore.GREEN+str(space_dict_obj.get(str(data)))+Fore.RESET]
            dataTable.append(dataArray)
        #printTabular(None,headers,dataTable)
        return space_dict_obj
    except Exception as e:
        handleException(e)


def proceedToCreateGSC(zoneGSC,newGSCCount):
    logger.info("proceedToCreateGSC()")
    idx = newGSCCount % len(spaceNodes)
    host = spaceNodes[idx]
    dbaGigaPath=str(readValuefromAppConfig("app.giga.path"))
    commandToExecute = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh container create --count="+str(numberOfGSC)+" --zone="+str(zoneGSC)+" --memory="+str(memoryGSC)+" --vm-option=-Djava.security.krb5.conf=/etc/krb5.conf --vm-option=-Djava.security.auth.login.config="+dbaGigaPath+"gs_config/SQLJDBCDriver.conf "+str(os.getenv(host.ip))+" | grep -v JAVA_HOME"
    verboseHandle.printConsoleInfo("Creating container count : "+str(numberOfGSC)+" zone="+str(zoneGSC)+" memory="+str(memoryGSC)+" host="+str(os.getenv(host.ip)))
    logger.info(commandToExecute)
    with Spinner():
        output = executeRemoteCommandAndGetOutput(managerHost, 'root', commandToExecute)
        print(output)
        logger.info("Output:"+str(output))

def createGSCInputParam():
    logger.info("createGSCInputParam()")
    global numberOfGSC
    global memoryGSC

    numberOfGSC = str(readValuefromAppConfig("app.dataengine.oracle-feeder.gscpercluster"))
    #str(userInputWrapper(Fore.YELLOW+"Enter number of GSCs per host [1] : "+Fore.RESET))
    #while(len(str(numberOfGSC))==0):
    #    numberOfGSC=1
    logger.info("numberOfGSC :"+str(numberOfGSC))

    memoryGSC = str(readValuefromAppConfig("app.dataengine.oracle-feeder.gsc.memory"))
    #str(userInputWrapper(Fore.YELLOW+"Enter memory of GSC [1g] : "+Fore.RESET))
    #while(len(str(memoryGSC))==0):
    #    memoryGSC='1g'

def updateAndCopyJarFileFromSourceToShFolder(puName):
    global filePrefix
    logger.info("updateAndCopyJarFileFromSourceToShFolder()")
    #sourceDB2FeederShFilePath = '/home/ec2-user/db2-feeder'
    #sourceDB2JarFilePath = '/home/ec2-user/db2feeder-1.0.0.jar'
    head , tail = os.path.split(sourceOracleJarFilePath)
    fileName= str(tail).replace('.jar','')
    filePrefix = fileName
    targetJarFile=sourceOracleFeederShFilePath+fileName+puName+'.jar'
    userCMD = os.getlogin()
    if userCMD == 'ec2-user':
        cmd = "sudo cp "+sourceOracleJarFilePath+' '+sourceOracleFeederShFilePath+fileName+puName+'.jar'
        #print(cmd)
    else:
        cmd = "cp "+sourceOracleJarFilePath+' '+sourceOracleFeederShFilePath+fileName+puName+'.jar'
    logger.info("cmd : "+str(cmd))
    home = executeLocalCommandAndGetOutput(cmd)
    logger.info("home: "+str(home))
    return targetJarFile

def uploadFileRest(managerHostConfig):
    try:
        logger.info("uploadFileRest : managerHostConfig : "+str(managerHostConfig))
        directory = os.getcwd()
        os.chdir(sourceOracleFeederShFilePath)
        for file in glob.glob("load_*.sh"):
            os.chdir(directory)

            exitsFeeder = str(file).replace('load','oraclefeeder').replace('.sh','').casefold()
            if exitsFeeder not in activefeeder:
                puName = str(file).replace('load','').replace('.sh','').casefold()
                pathOfSourcePU = updateAndCopyJarFileFromSourceToShFolder(puName)
                #print("pathOfSourcePU : "+str(pathOfSourcePU))
                #print("jarName :"+jarName)
                zoneGSC = 'oracle_'+puName
                verboseHandle.printConsoleWarning("Proceeding for : "+pathOfSourcePU)
                logger.info("url : "+"curl -X PUT -F 'file=@"+str(pathOfSourcePU)+"' http://"+managerHostConfig+":8090/v2/pus/resources")
                logger.info("url : "+"curl -X PUT -F 'file=@"+str(pathOfSourcePU)+"' http://"+managerHostConfig+":8090/v2/pus/resources")
                status = os.system("curl -X PUT -F 'file=@"+str(pathOfSourcePU)+"' http://"+managerHostConfig+":8090/v2/pus/resources -u "+username+":"+password+"")
                print("\n")
                logger.info("status : "+str(status))
    except Exception as e:
        handleException(e)

def getDataPUREST(resource,resourceName,zoneOfPU,restPort,managerHost):
    backUpRequired=0
    oracleHost = str(readValueByConfigObj("app.dataengine.oracle-feeder.oracle.server")).replace('"','').replace(' ','')
    oracleUser = str(readValueByConfigObj("app.dataengine.oracle-feeder.oracle.username")).replace('"','').replace(' ','')
    oraclePassword = str(readValueByConfigObj("app.dataengine.oracle-feeder.oracle.password")).replace('"','').replace(' ','')
    oracleDatabase = str(readValueByConfigObj("app.dataengine.oracle-feeder.oracle.databasename")).replace('"','').replace(' ','')
    data={
        "resource": ""+resource+"",
        "topology": {
            "instances": 1,
        },
        "sla": {
            "zones": [
                ""+zoneOfPU+""
            ],
        },
        "name": ""+resourceName+"",
        "maxInstancesPerMachine": int(maxInstancesPerMachine),
        "contextProperties": {#"pu.autogenerated-instance-sla" :""+slaProperties+"",
            #"tieredCriteriaConfig.filePath" : ""+tieredCriteriaConfigFilePathTarget+"",
            "rest.port" : ""+restPort+"",
            "rest.locators" : ""+managerHost+"",
            "oracle.host" : ""+oracleHost+"" ,
            "oracle.database" : ""+oracleDatabase+"" ,
            "oracle.user" : ""+oracleUser+"" ,
            "oracle.password" : ""+oraclePassword+"" ,
            "feeder.writeBatchSize" : ""+feederWriteBatchSize+"",
            "space.name" : ""+spaceName+"",
            "feeder.sleepAfterWriteInMillis" : ""+feederSleepAfterWrite+""
        }
    }
    #print(data)
    return data

def validateResponseGetDescription(responseCode):
    logger.info("validateResponse() "+str(responseCode))
    response = requests.get("http://"+managerHost+":8090/v2/requests/"+str(responseCode),auth = HTTPBasicAuth(username, password))
    jsonData = json.loads(response.text)
    logger.info("response : "+str(jsonData))
    if(str(jsonData["status"]).__contains__("failed")):
        return "Status :"+str(jsonData["status"])+" Description:"+str(jsonData["error"])
    else:
        return "Status :"+str(jsonData["status"])+" Description:"+str(jsonData["description"])

def sqlLiteCreateTableDB():
    logger.info("sqlLiteCreateTableDB()")
    try:
        dbaGigaWorkPath=str(readValueByConfigObj("app.gigawork.path"))
        db_file = str(readValueByConfigObj("app.dataengine.oracle-feeder.sqlite.dbfile")).replace("/dbagigawork",dbaGigaWorkPath).replace('"','').replace(' ','')
        logger.info("dbFile : "+str(db_file))
        cnx = sqlite3.connect(db_file)
        logger.info("Db connection obtained."+str(cnx)+" Sqlite V: "+str(sqlite3.version))
        #cnx.execute("DROP TABLE IF EXISTS db2_host_port")
        cnx.execute("CREATE TABLE IF NOT EXISTS oracle_host_port (file VARCHAR(50), feeder_name VARCHAR(50), host VARCHAR(50), port varchar(10))")
        cnx.commit()
        cnx.close()
    except Exception as e:
        handleException(e)

def createOracleEntryInSqlLite(puName, file, restPort):
    logger.info("createOracleEntryInSqlLite()")
    try:
        response = requests.get("http://"+str(managerHost)+":8090/v2/pus/"+str(puName)+"/instances",auth = HTTPBasicAuth(username, password))
        jsonArray = json.loads(response.text)
        logger.info("response : "+str(jsonArray))
        verboseHandle.printConsoleInfo("response : "+str(jsonArray))
        hostId = ''
        for data in jsonArray:
            hostId = str(data["hostId"])
        dbaGigaWorkPath=str(readValueByConfigObj("app.gigawork.path"))
        db_file = str(readValueByConfigObj("app.dataengine.oracle-feeder.sqlite.dbfile")).replace("/dbagigawork",dbaGigaWorkPath).replace('"','').replace(' ','')
        cnx = sqlite3.connect(db_file)
        cnx.execute("INSERT INTO oracle_host_port (file, feeder_name, host, port) VALUES ('"+str(file)+"', '"+str(puName)+"','"+str(hostId)+"','"+str(restPort)+"')")
        cnx.commit()
        cnx.close()
    except Exception as e:
        handleException(e)

def newInstallOracleFeeder():
    global newInstall
    newInstall=[]
    directory = os.getcwd()
    os.chdir(sourceOracleFeederShFilePath)
    for file in glob.glob("load_*.sh"):
        os.chdir(directory)
        exitsFeeder = str(file).replace('load','oraclefeeder').replace('.sh','').casefold()
        if exitsFeeder not in activefeeder:
            newInstall.append(exitsFeeder)

def proceedToDeployPU():
    global restPort
    try:
        logger.info("proceedToDeployPU()")
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        logger.info("url : "+"http://"+managerHost+":8090/v2/pus",auth = HTTPBasicAuth(username, password))
        sqlLiteCreateTableDB()
        directory = os.getcwd()
        os.chdir(sourceOracleFeederShFilePath)
        #os.system("pwd")
        restPort = 8015 #8025
        restPort = restPort+1

        newGSCCount=0
        logger.info("Resport : "+str(restPort))
        for file in glob.glob("load_*.sh"):
            os.chdir(directory)
            exitsFeeder = str(file).replace('load','oraclefeeder').replace('.sh','').casefold()
            if exitsFeeder not in activefeeder:
                puName = str(file).replace('load_','').replace('.sh','').casefold()
                zoneGSC = 'oracle_'+puName
                logger.info("filePrefix : "+filePrefix)
                resource = filePrefix+'_'+puName+'.jar'
                puName = 'oraclefeeder_'+puName
                port = getPortNotExistInOracleFeeder(restPort)
                logger.info("dbPort : "+str(port))
                if(len(str(port))!=0):
                    while(len(str(port))!=0):
                        restPort = int(port)+1
                        port = getPortNotExistInOracleFeeder(restPort)
                    #else:
                    #    dbPort = restPort
                if(confirmCreateGSC=='y'):
                    proceedToCreateGSC(zoneGSC,newGSCCount)
                    newGSCCount=newGSCCount+1
                verboseHandle.printConsoleInfo("Resource : "+resource+" : rest.port : "+str(restPort))
                data = getDataPUREST(resource,puName,zoneGSC,str(restPort),managerHost)
                logger.info("data of payload :"+str(data))

                response = requests.post("http://"+managerHost+":8090/v2/pus",data=json.dumps(data),headers=headers)
                deployResponseCode = str(response.content.decode('utf-8'))
                print("deployResponseCode : "+str(deployResponseCode))
                logger.info("deployResponseCode :"+str(deployResponseCode))

                status = validateResponseGetDescription(deployResponseCode)
                logger.info("response.status_code :"+str(response.status_code))
                logger.info("response.content :"+str(response.content) )
                if(response.status_code==202):
                    logger.info("Response :"+str(status))
                    retryCount=5
                    with Spinner():
                        while(retryCount>0 or (not str(status).casefold().__contains__('successful')) or (not str(status).casefold().__contains__('failed'))):
                            status = validateResponseGetDescription(deployResponseCode)
                            verboseHandle.printConsoleInfo("Response :"+str(status))
                            retryCount = retryCount-1
                            time.sleep(2)
                            if(str(status).casefold().__contains__('successful')):
                                time.sleep(2)
                                createOracleEntryInSqlLite(puName,file,restPort)
                                verboseHandle.printConsoleInfo("Entry : "+str(file)+" puName :"+str(puName))
                                userCMD = os.getlogin()
                                if userCMD == 'ec2-user':
                                    cmd = "sudo rm -f "+sourceOracleFeederShFilePath+resource
                                else:
                                    cmd = "rm -f "+sourceOracleFeederShFilePath+resource
                                logger.info("cmd : "+str(cmd))
                                home = executeLocalCommandAndGetOutput(cmd)
                                break
                            elif(str(status).casefold().__contains__('failed')):
                                break
                else:
                    logger.info("Unable to deploy 1 :"+str(status))
                    verboseHandle.printConsoleInfo("Unable to deploy 1 : "+str(status))
    except Exception as e :
        handleException(e)


def displaySummaryOfInputParam():
    logger.info("displaySummaryOfInputParam()")
    dbaGigaWorkPath=str(readValueByConfigObj("app.gigawork.path"))
    db_file = str(readValueByConfigObj("app.dataengine.oracle-feeder.sqlite.dbfile")).replace("/dbagigawork",dbaGigaWorkPath).replace('"','').replace(' ','')
    verboseHandle.printConsoleInfo("------------------------------------------------------------")
    verboseHandle.printConsoleInfo("***Summary***")
    if(confirmCreateGSC=='y'):
        verboseHandle.printConsoleInfo("Enter number of GSCs per cluster :"+str(numberOfGSC))
        verboseHandle.printConsoleInfo("Enter memory of GSC :"+memoryGSC)
        #verboseHandle.printConsoleInfo("Enter -Dpipeline.config.location source : "+dPipelineLocationSource)
        #verboseHandle.printConsoleInfo("Enter -Dpipeline.config.location target : "+dPipelineLocationTarget)
    verboseHandle.printConsoleInfo("Enter oracle.server : "+str(oracleServer))
    verboseHandle.printConsoleInfo("Enter feeder.writeBatchSize : "+str(feederWriteBatchSize))
    verboseHandle.printConsoleInfo("Enter feeder.sleepAfterWriteInMillis :"+str(feederSleepAfterWrite))
    verboseHandle.printConsoleInfo("Enter sqlite3 db file :"+str(db_file))
    verboseHandle.printConsoleInfo("Enter source file path of oracle-feeder .jar file including file name : "+str(sourceOracleJarFilePath))
    verboseHandle.printConsoleInfo("Enter source file path of oracle-feeder *.sh file : "+str(sourceOracleFeederShFilePath))
    verboseHandle.printConsoleInfo("Enter source file of oracle-feeder *.sh file : "+str(newInstall))

def proceedToDeployPUInputParam(managerHost):
    logger.info("proceedToDeployPUInputParam()")

    global sourceOracleJarFilePath
    sourceOracleJarFileConfig = str(getYamlFilePathInsideFolder(".oracle.jars.oracleJarFile"))
    #print(Fore.YELLOW+"Enter source file path of oracle-feeder .jar file including file name ["+sourceOracleJarFileConfig+"] : "+Fore.RESET)
    #if(len(str(sourceOracleJarFilePath))==0):
    sourceOracleJarFilePath = sourceOracleJarFileConfig
    #set_value_in_property_file("app.dataengine.oracle-feeder.jar",sourceOracleJarFilePath)

    global sourceOracleFeederShFilePath
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)
    sourceOracleFeederShFilePathConfig = str(sourceInstallerDirectory+".oracle.scripts.").replace('.','/')

    #print(Fore.YELLOW+"Enter source file path (directory) of *.sh file ["+sourceOracleFeederShFilePathConfig+"] : "+Fore.RESET)
    #if(len(str(sourceOracleFeederShFilePath))==0):
    sourceOracleFeederShFilePath = sourceOracleFeederShFilePathConfig
    lastChar = str(sourceOracleFeederShFilePath[-1])
    logger.info("last char:"+str(lastChar))
    if(lastChar!='/'):
        sourceOracleFeederShFilePath = sourceOracleFeederShFilePath+'/'
    #set_value_in_property_file("app.dataengine.oracle-feeder.filePath.shFile",sourceOracleFeederShFilePath)

    #uploadFileRest(managerHost)
    newInstallOracleFeeder()
    global partition
    partition='1'

    global maxInstancesPerMachine
    maxInstancesPerMachine = '1'
    logger.info("maxInstancePerVM Of PU :"+str(maxInstancesPerMachine))

    global spaceName
    spaceName = str(readValueByConfigObj("app.dataengine.oracle-feeder.space.name"))
    #print(Fore.YELLOW+"Enter space.name ["+spaceName+"] : "+Fore.RESET)
    #if(len(str(spaceName))==0):
    #    spaceName='bllspace'

    global oracleServer
    oracleServerConfig = str(readValueByConfigObj("app.dataengine.oracle-feeder.oracle.server"))
    #print(Fore.YELLOW+"Enter oracle.server ["+oracleServerConfig+"]: "+Fore.RESET)
    #if(len(str(oracleServer))==0):
    oracleServer = oracleServerConfig
    # set_value_in_property_file("app.dataengine.oracle-feeder.oracle.server",oracleServer)

    global feederWriteBatchSize
    feederWriteBatchSize = str(readValueByConfigObj("app.dataengine.oracle-feeder.writeBatchSize"))
    #print(Fore.YELLOW+"Enter feeder.writeBatchSize ["+feederWriteBatchSize+"] :"+Fore.RESET)
    #if(len(feederWriteBatchSize)==0):
    #    feederWriteBatchSize='10000'

    global feederSleepAfterWrite
    feederSleepAfterWrite = str(readValueByConfigObj("app.dataengine.oracle-feeder.sleepAfterWriteInMillis"))
    #print(Fore.YELLOW+"Enter feeder.sleepAfterWriteInMillis ["+feederSleepAfterWrite+"] :"+Fore.RESET)
    if(len(feederSleepAfterWrite)==0):
        feederSleepAfterWrite='500'

    displaySummaryOfInputParam()
    finalConfirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to proceed ? (y/n) [y] :"+Fore.RESET))
    if(len(str(finalConfirm))==0):
        finalConfirm='y'
    if(finalConfirm=='y'):
        logger.info("mq connector kafka consumer confirmCreateGSC "+confirmCreateGSC)
        uploadFileRest(managerHost)
        proceedToDeployPU()
    else:
        return

if __name__ == '__main__':
    logger.info("odsx_dataengine_oracle-feeder_install")
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle-Feeder -> Install-Deploy')
    username = ""
    password = ""
    appId=""
    safeId=""
    objectId=""
    try:
        appId = str(readValuefromAppConfig("app.space.security.appId")).replace('"','')
        safeId = str(readValuefromAppConfig("app.space.security.safeId")).replace('"','')
        objectId = str(readValuefromAppConfig("app.space.security.objectId")).replace('"','')
        logger.info("appId : "+appId+" safeID : "+safeId+" objectID : "+objectId)
        nodes = getDIServerHostList()
        logger.info("DI / kafka host found :"+str(nodes))
        if(len(nodes)>0):
            managerNodes = config_get_manager_node()
            logger.info("managerNodes: main"+str(managerNodes))
            if(len(str(managerNodes))>0):
                spaceNodes = config_get_space_hosts()
                logger.info("spaceNodes: main"+str(spaceNodes))
                managerHost = getManagerHost(managerNodes)
                #updateAndCopyJarFileFromSourceToShFolder()
                logger.info("managerHost : main"+str(managerHost))
                if(len(str(managerHost))>0):
                    username = str(getUsernameByHost(managerHost,appId,safeId,objectId))
                    password = str(getPasswordByHost(managerHost,appId,safeId,objectId))
                    listSpacesOnServer(managerNodes)
                    listDeployed(managerHost)
                    space_dict_obj = displaySpaceHostWithNumber(managerNodes,spaceNodes)
                    if(len(space_dict_obj)>0):
                        confirmCreateGSC = str(readValuefromAppConfig("app.dataengine.oracle-feeder.gsc.create"))
                        #str(userInputWrapper(Fore.YELLOW+"Do you want to create GSC ? (y/n) [y] : "))
                        if(len(str(confirmCreateGSC))==0 or confirmCreateGSC=='y'):
                            confirmCreateGSC='y'
                            createGSCInputParam()
                        proceedToDeployPUInputParam(managerHost)
                    else:
                        logger.info("Please check space server.")
                        verboseHandle.printConsoleInfo("Please check space server.")
                else:
                    logger.info("Please check manager server status.")
                    verboseHandle.printConsoleInfo("Please check manager server status.")
            else:
                logger.info("No Manager configuration found please check.")
                verboseHandle.printConsoleInfo("No Manager configuration found please check.")
        else:
            logger.info("No kafka servers configurations found. Please install kafka servers first.")
            verboseHandle.printConsoleInfo("No kafka servers configurations found. Please install kafka servers first.")
    except Exception as e:
        handleException(e)
