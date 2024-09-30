import argparse
import glob
import os
import socket
import sqlite3
import subprocess
import sys
import time
import json
from datetime import datetime

import requests

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import getYamlFilePathInsideFolder, readValuefromAppConfig, \
    readValueByConfigObj
from utils.ods_cluster_config import config_get_manager_node
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_db2feeder_utilities import getPortNotExistInOracleFeeder, getPasswordByHost, getUsernameByHost
from utils.odsx_keypress import userInputWithEscWrapper, userInputWrapper
from utils.odsx_objectmanagement_utilities import getPivotHost
from requests.auth import HTTPBasicAuth

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


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

def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    parser.add_argument('-dryrun', '--dryrun',
                        help='Dry run flag',
                        default='false', action='store_true')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])

def replace_or_add_column_in_ddl(file_path, passedColumn, updatedColumnDef):
    lines_replaced = False

    # Read the file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    parts = ''.join(lines).rsplit(',', 1)
    modified_sql = f"{parts[0]},\n{updatedColumnDef},{parts[1]}"
    #modified_sql = parts[0] + updatedColumnDef + ')' + (parts[1] if len(parts) > 1 else '')
    # Process the lines
    lines_replaced = False
    with open(file_path, 'w') as file:
        for line in lines:
            fileColumnName = line.split(" ")[0]
            if fileColumnName in passedColumn:
                file.write(updatedColumnDef + ',\n')
                lines_replaced = True
            else:
                file.write(line)

        # If no line was replaced, add new line before the last line
        #if not lines_replaced and len(lines) > 0:
            # Insert new line before the last line
            #file.write(updatedColumnDef + '\n')
            #file.writelines(lines[-1:])  # Re-write the last line
            # file.write(modified_sql)
    with open(file_path, 'w') as file:
        if not lines_replaced:
            file.write(modified_sql)

def validateResponse(responseCode):
    logger.info("validateResponse() "+str(responseCode))
    try:
        response = requests.get("http://"+managerHost+":8090/v2/requests/"+str(responseCode),auth = HTTPBasicAuth(username, password))
        jsonData = json.loads(response.text)
        logger.info("response : "+str(jsonData))
        return str(jsonData["status"])
    except Exception as e:
        handleException(e)

def deleteOracleEntryFromSqlLite(puName):
    logger.info("deleteOracleEntryFromSqlLite()")
    try:
        db_file = str(readValueByConfigObj("app.dataengine.oracle-feeder.sqlite.dbfile")).replace('"','').replace(' ','')
        logger.info("db_file :"+str(db_file))
        cnx = sqlite3.connect(db_file)
        logger.info("SQL : DELETE FROM oracle_host_port where feeder_name like '%"+str(puName)+"%'")
        cnx.execute("DELETE FROM oracle_host_port where feeder_name like '%"+str(puName)+"%'")
        cnx.commit()
        cnx.close()
    except Exception as e:
        handleException(e)

def proceedForPersistUndeploy(spaceTobeUndeploy):
    response = requests.delete("http://"+managerHost+":8090/v2/pus/undeployed/"+str(spaceTobeUndeploy),auth = HTTPBasicAuth(username, password))
    logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
    if(response.status_code==200):
        logger.info("PU :"+str(spaceTobeUndeploy)+" has been undeployed.")
        verboseHandle.printConsoleInfo("PU :"+str(spaceTobeUndeploy)+" has been undeployed.")
       # deleteOracleEntryFromSqlLite(spaceTobeUndeploy)
    else:
        logger.info("PU :"+str(spaceTobeUndeploy)+" has not been undeployed.")
        verboseHandle.printConsoleInfo("PU :"+str(spaceTobeUndeploy)+" has not been undeployed.")

def feeder_undeploy(puTobeUndeploy):
    drainMode = readValuefromAppConfig("app.tieredstorage.drainmode")
    drainTimeout = readValuefromAppConfig("app.tieredstorage.drainTimeout")
    response = requests.delete("http://"+managerHost+":8090/v2/pus/"+str(puTobeUndeploy)+"?drainMode="+str(drainMode)+"&drainTimeout="+str(drainTimeout),auth = HTTPBasicAuth(username, password))
    logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
    if(response.status_code==202):
        undeployResponseCode = str(response.content.decode('utf-8'))
        logger.info("backUPResponseCode : "+str(undeployResponseCode))

        status = validateResponse(undeployResponseCode)
        with Spinner():
            while(status.casefold() != 'successful'):
                time.sleep(2)
                status = validateResponse(undeployResponseCode)
                logger.info("Undeploy :"+str(puTobeUndeploy)+"   Status :"+str(status))
                #verboseHandle.printConsoleInfo("spaceID Restart :"+str(spaceIdToBeRestarted)+" status :"+str(status))
                verboseHandle.printConsoleInfo("Undeploy  : "+str(puTobeUndeploy)+"   Status : "+str(status))
        deleteOracleEntryFromSqlLite(puTobeUndeploy)
        verboseHandle.printConsoleInfo(" Undeploy  : "+str(puTobeUndeploy)+"   Status : "+str(status))
        proceedForPersistUndeploy(puTobeUndeploy)

def newInstallOracleFeeder(tableName):
    global newInstall
    newInstall=[]
    directory = os.getcwd()
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    sourceOracleFeederShFilePath = str(sourceInstallerDirectory + ".oracle.scripts.").replace('.', '/')
    os.chdir(sourceOracleFeederShFilePath)
    os.chdir(directory)
    fileName= "load_"+tableName+".sh"
    global activefeeder
    activefeeder=[]
    exitsFeeder = fileName.replace('load','oraclefeeder').replace('.sh','').casefold()
    activefeeder.append(exitsFeeder)

def executeLocalCommandAndGetOutput(commandToExecute):
    logger.info("executeLocalCommandAndGetOutput() cmd :" + str(commandToExecute))
    cmd = commandToExecute
    cmdArray = cmd.split(" ")
    process = subprocess.Popen(cmdArray, stdout=subprocess.PIPE)
    out, error = process.communicate()
    out = out.decode()
    return str(out).replace('\n', '')

def updateAndCopyJarFileFromSourceToShFolder(puName):
    global filePrefix
    logger.info("updateAndCopyJarFileFromSourceToShFolder()")
    head , tail = os.path.split(sourceOracleJarFilePath)
    fileName= str(tail).replace('.jar','')
    filePrefix = fileName
    targetJarFile=sourceOracleFeederShFilePath+fileName+"_"+puName+'.jar'
    userCMD = os.getlogin()
    if userCMD == 'ec2-user':
        cmd = "sudo cp "+sourceOracleJarFilePath+' '+sourceOracleFeederShFilePath+fileName+"_"+puName+'.jar'
    else:
        cmd = "cp "+sourceOracleJarFilePath+' '+sourceOracleFeederShFilePath+fileName+"_"+puName+'.jar'
    logger.info("cmd : "+str(cmd))
    home = executeLocalCommandAndGetOutput(cmd)
    logger.info("home: "+str(home))
    return targetJarFile

def uploadFileRest(managerHostConfig,feederName):
    try:
        logger.info("uploadFileRest : managerHostConfig : "+str(managerHostConfig))
        directory = os.getcwd()
        os.chdir(sourceOracleFeederShFilePath)

        #puName = str(file).replace('load','').replace('.sh','').casefold()
        pathOfSourcePU = updateAndCopyJarFileFromSourceToShFolder(feederName)
        zoneGSC = 'oracle_'+feederName
        logger.info("url : "+"curl -X PUT -F 'file=@"+str(pathOfSourcePU)+"' http://"+managerHostConfig+":8090/v2/pus/resources")
        cmdToExecute = "curl -X PUT -F 'file=@"+str(pathOfSourcePU)+"' http://"+managerHostConfig+":8090/v2/pus/resources -u "+username+":"+password+""
        status = os.system(cmdToExecute)
        logger.info("status : "+str(status))

    except Exception as e:
        handleException(e)

def validateResponseGetDescription(responseCode):
    logger.info("validateResponse() "+str(responseCode))
    response = requests.get("http://"+managerHost+":8090/v2/requests/"+str(responseCode),auth = HTTPBasicAuth(username, password))
    jsonData = json.loads(response.text)
    logger.info("response : "+str(jsonData))
    if(str(jsonData["status"]).__contains__("failed")):
        return "Status :"+str(jsonData["status"])+" Description:"+str(jsonData["error"])
    else:
        return "Status :"+str(jsonData["status"])+" Description:"+str(jsonData["description"])

def createOracleEntryInSqlLite(puName, file, restPort):
    logger.info("createOracleEntryInSqlLite()")
    try:
        response = requests.get("http://"+str(managerHost)+":8090/v2/pus/"+str(puName)+"/instances",auth = HTTPBasicAuth(username, password))
        jsonArray = json.loads(response.text)
        logger.info("response : "+str(jsonArray))
        hostId = ''
        for data in jsonArray:
            hostId = str(data["hostId"])
        db_file = str(readValueByConfigObj("app.dataengine.oracle-feeder.sqlite.dbfile")).replace('"','').replace(' ','')
        cnx = sqlite3.connect(db_file)
        cnx.execute("INSERT INTO oracle_host_port (file, feeder_name, host, port) VALUES ('"+str(file)+"', '"+str(puName)+"','"+str(hostId)+"','"+str(restPort)+"')")
        cnx.commit()
        cnx.close()
    except Exception as e:
        handleException(e)

def getDataPUREST(resource,resourceName,zoneOfPU,restPort,managerHost):
    backUpRequired=0
    oracleHost = str(readValueByConfigObj("app.dataengine.oracle-feeder.oracle.server")).replace('"','').replace(' ','')
    oracleUser = str(readValueByConfigObj("app.dataengine.oracle-feeder.oracle.username")).replace('"','').replace(' ','')
    oraclePassword = str(readValueByConfigObj("app.dataengine.oracle-feeder.oracle.password")).replace('"','').replace(' ','')
    oracleDatabase = str(readValueByConfigObj("app.dataengine.oracle-feeder.oracle.databasename")).replace('"','').replace(' ','')
    spaceName = str(readValueByConfigObj("app.dataengine.oracle-feeder.space.name"))
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

def sqlLiteCreateTableDB():
    logger.info("sqlLiteCreateTableDB()")
    try:
        db_file = str(readValueByConfigObj("app.dataengine.oracle-feeder.sqlite.dbfile")).replace('"','').replace(' ','')
        logger.info("dbFile : "+str(db_file))
        cnx = sqlite3.connect(db_file)
        logger.info("Db connection obtained."+str(cnx)+" Sqlite V: "+str(sqlite3.version))
        #cnx.execute("DROP TABLE IF EXISTS db2_host_port")
        cnx.execute("CREATE TABLE IF NOT EXISTS oracle_host_port (file VARCHAR(50), feeder_name VARCHAR(50), host VARCHAR(50), port varchar(10))")
        cnx.commit()
        cnx.close()
    except Exception as e:
        handleException(e)

def proceedToDeployPU(feederName):
    global restPort
    try:
        logger.info("proceedToDeployPU()")
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        logger.info("url : "+"http://"+managerHost+":8090/v2/pus")
        sqlLiteCreateTableDB()
        directory = os.getcwd()
        os.chdir(sourceOracleFeederShFilePath)
        restPort = str(readValueByConfigObj("app.dataengine.oracle-feeder.rest.port")).replace('"','').replace(' ','')

        logger.info("Resport : "+str(restPort))
        file = feederName
        os.chdir(directory)
        exitsFeeder = str(file).replace('load','oraclefeeder').replace('.sh','').casefold()
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
        data = getDataPUREST(resource,puName,zoneGSC,str(restPort),managerHost)
        logger.info("data of payload :"+str(data))

        response = requests.post("http://"+managerHost+":8090/v2/pus",data=json.dumps(data),headers=headers,auth = HTTPBasicAuth(username, password))
        deployResponseCode = str(response.content.decode('utf-8'))
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

def proceedToDeployPUInputParam(tableName):
    logger.info("proceedToDeployPUInputParam()")

    global sourceOracleJarFilePath
    sourceOracleJarFileConfig = str(getYamlFilePathInsideFolder(".oracle.jars.oracleJarFile"))
    sourceOracleJarFilePath = sourceOracleJarFileConfig

    global sourceOracleFeederShFilePath
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)
    sourceOracleFeederShFilePathConfig = str(sourceInstallerDirectory+".oracle.scripts.").replace('.','/')

    sourceOracleFeederShFilePath = sourceOracleFeederShFilePathConfig
    lastChar = str(sourceOracleFeederShFilePath[-1])
    logger.info("last char:"+str(lastChar))
    if(lastChar!='/'):
        sourceOracleFeederShFilePath = sourceOracleFeederShFilePath+'/'
    #set_value_in_property_file("app.dataengine.oracle-feeder.filePath.shFile",sourceOracleFeederShFilePath)

    #uploadFileRest(managerHost)
    newInstallOracleFeeder(tableName)
    global partition
    partition='1'

    global maxInstancesPerMachine
    maxInstancesPerMachine = '1'
    logger.info("maxInstancePerVM Of PU :"+str(maxInstancesPerMachine))

    global oracleServer
    oracleServerConfig = str(readValueByConfigObj("app.dataengine.oracle-feeder.oracle.server"))
    oracleServer = oracleServerConfig
    global feederWriteBatchSize
    feederWriteBatchSize = str(readValueByConfigObj("app.dataengine.oracle-feeder.writeBatchSize"))

    global feederSleepAfterWrite
    feederSleepAfterWrite = str(readValueByConfigObj("app.dataengine.oracle-feeder.sleepAfterWriteInMillis"))
    if(len(feederSleepAfterWrite)==0):
        feederSleepAfterWrite='500'

    uploadFileRest(managerHost,tableName)
    proceedToDeployPU(tableName)

def sqlLiteGetHostAndPortByFileName(puName):
    logger.info("sqlLiteGetHostAndPortByFileName() shFile : "+str(puName))
    try:
        db_file = str(readValueByConfigObj("app.dataengine.oracle-feeder.sqlite.dbfile")).replace('"','').replace(' ','')
        cnx = sqlite3.connect(db_file)
        logger.info("Db connection obtained."+str(cnx))
        logger.info("SQL : SELECT host,port,file FROM oracle_host_port where feeder_name = '"+str(puName)+"' ")
        mycursor = cnx.execute("SELECT host,port,file FROM oracle_host_port where feeder_name = '"+str(puName)+"' ")
        myresult = mycursor.fetchall()
        cnx.close()
        for row in myresult:
            logger.info("host : "+str(row[0]))
            logger.info("port : "+str(row[1]))
            logger.info("file : "+str(row[2]))
            return str(row[0])+','+str(row[1])+','+str(row[2])
    except Exception as e:
        handleException(e)


def proceedToStartOracleFeederWithName(puName):
    logger.info("proceedToStartOracleFeederWithName()")
    hostAndPort = str(sqlLiteGetHostAndPortByFileName(puName)).split(',')
    host = str(hostAndPort[0])
    port = str(hostAndPort[1])
    shFileName = str(hostAndPort[2])
    host=str(socket.gethostbyaddr(host).__getitem__(2)[0])
    cmd = str(sourceOracleFeederShFilePath)+'/'+"load_"+shFileName.upper()+'.sh '+host+" "+port
    logger.info("cmd : "+str(cmd))
    os.system(cmd)

def recreateType():
    #Back up the old DDL file
    ddlFilename = tableName + ".ddl"
    tableListfilePath = str(getYamlFilePathInsideFolder(".object.config.ddlparser.ddlBatchFileName")).replace("//", "/")
    ddlAndPropertiesBasePath = os.path.dirname(tableListfilePath) + "/"
    timestamp = time.time()
    filename_suffix = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d_%H-%M-%S')
    os.system("cp " +ddlAndPropertiesBasePath+"/"+ ddlFilename + " " +ddlAndPropertiesBasePath+"/"+ ddlFilename + ".backup." + filename_suffix)
    #Copy the new DDL file to the server
    updatedColumnDef = str(userInputWithEscWrapper("modified ddl column (Ex. BZ00_TOKEN	DECIMAL(11, 0)	NOT NULL) :"))
    #add or remove the column from ddl file based on above value
    columnName = updatedColumnDef.split(" ")[0]
    replace_or_add_column_in_ddl(ddlAndPropertiesBasePath+"/"+ ddlFilename, columnName, updatedColumnDef)
    wantToAddIndex = str(userInputWithEscWrapper("Do you want to add index (y/n) [n] ?"))
    if wantToAddIndex == 'y':
        os.system("cp " +ddlAndPropertiesBasePath+"/batchIndexes.txt" + " " +ddlAndPropertiesBasePath+"/batchIndexes.txt" + ".backup." + filename_suffix)
        addedIndex = str(userInputWithEscWrapper("modified index (Ex. STUD.TA_PERSON  SHEM_MISHP_ENG  ORDERED :"))
        with open(ddlAndPropertiesBasePath+"/batchIndexes.txt", 'a') as file:
            file.write(addedIndex)

    #Drop the appropriate table/type
    objectMgmtHost = getPivotHost()
    data = {
        "type": "" + tableName + ""
    }
    response = requests.post('http://' + objectMgmtHost + ':7001/unregistertype', data=data,
                             headers={'Accept': 'application/json'})
    if (response.text == "success"):
        verboseHandle.printConsoleInfo("Object is removed successfully!!")
    else:
        verboseHandle.printConsoleError("Error in removing object.")
    data = {
        "tableName": "" + tableName + ""
    }
    response = requests.post('http://' + objectMgmtHost + ':7001/registertype/single', data=data,
                             headers={'Accept': 'application/json'})
    #Create appropriate table/type based on the new ddl
    if (response.text == "success"):
        verboseHandle.printConsoleInfo("Object is registered successfully!!")
    elif (response.text == "duplicate"):
        verboseHandle.printConsoleError("Object is already registered.")
    else:
        verboseHandle.printConsoleError("Error in registering object.")


    #Run the indexes
    response = requests.post('http://' + objectMgmtHost + ':7001/index/addinbatch',
                             headers={'Accept': 'application/json'})
    logger.info("indexes response : "+str(response))
    verboseHandle.printConsoleInfo("Added indexes")

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle-Feeder -> Schema change')
    global username
    global password
    global tableName
    global sourceOracleFeederShFilePath
    tableName = str(userInputWithEscWrapper("DDL filename :"))
    recreateType()
    #Redeploy the appropriate feeder that fills the table
    global managerHost
    managerHost=''
    for node in config_get_manager_node():
        status = getSpaceServerStatus(os.getenv(node.ip))
        logger.info("Ip :"+str(os.getenv(node.ip))+"Status : "+str(status))
        if(status=="ON"):
            managerHost = os.getenv(node.ip)
            break
    username = str(getUsernameByHost())
    password = str(getPasswordByHost())
    tableName = str(tableName).split(".")[1].lower()
    puName = "oraclefeeder_" + tableName
    feeder_undeploy(puName)
    proceedToDeployPUInputParam(tableName)
    #Start the feeder
    proceedToStartOracleFeederWithName(puName)
