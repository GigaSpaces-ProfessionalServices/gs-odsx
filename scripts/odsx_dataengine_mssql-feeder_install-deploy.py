#!/usr/bin/env python3

import os,time,subprocess,requests, json, math, glob, sqlite3
from utils.ods_app_config import set_value_in_property_file,readValueByConfigObj
from utils.ods_cluster_config import config_get_dataIntegration_nodes,config_add_dataEngine_node
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from utils.ods_app_config import readValuefromAppConfig, set_value_in_property_file
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_print_tabular_data import printTabular
from scripts.spinner import Spinner
from utils.ods_ssh import executeRemoteCommandAndGetOutput

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
            nodes = node.ip
        else:
            nodes = nodes + ',' + node.ip
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
            status = getSpaceServerStatus(node.ip)
            if(status=="ON"):
                managerHost = node.ip
        return managerHost
    except Exception as e:
        handleException(e)

def listDeployed(managerHost):
    global gs_space_dictionary_obj
    try:
        logger.info("managerHost :"+str(managerHost))
        response = requests.get("http://"+str(managerHost)+":8090/v2/pus/")
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
            if(str(data["name"]).casefold().__contains__("mssqlfeeder") or str(data["processingUnitType"]).casefold().__contains__("stateful")):
                dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                             Fore.GREEN+data["name"]+Fore.RESET,
                             Fore.GREEN+data["resource"]+Fore.RESET,
                             Fore.GREEN+str(data["sla"]["zones"])+Fore.RESET,
                             Fore.GREEN+data["processingUnitType"]+Fore.RESET,
                             Fore.GREEN+data["status"]+Fore.RESET
                             ]
                gs_space_dictionary_obj.add(str(counter+1),str(data["name"]))
                counter=counter+1
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
            status = getSpaceServerStatus(node.ip)
            logger.info("Ip :"+str(node.ip)+"Status : "+str(status))
            if(status=="ON"):
                managerHost = node.ip;
        logger.info("managerHost :"+managerHost)
        response = requests.get("http://"+managerHost+":8090/v2/spaces")
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
            status = getSpaceServerStatus(node.ip)
            if(status=="ON"):
                managerHostConfig = node.ip;
        logger.info("managerHostConfig : "+str(managerHostConfig))
        response = requests.get('http://'+managerHostConfig+':8090/v2/hosts', headers={'Accept': 'application/json'})
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
            if(gs_host_details_obj.__contains__(str(node.name)) or (str(node.name) in gs_host_details_obj.values())):
                space_dict_obj.add(str(counter+1),node.name)
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


def proceedToCreateGSC(zoneGSC):
    logger.info("proceedToCreateGSC()")
    for host in spaceNodes:
        commandToExecute = "cd; home_dir=$(pwd); source $home_dir/setenv.sh;$GS_HOME/bin/gs.sh container create --count="+str(numberOfGSC)+" --zone="+str(zoneGSC)+" --memory="+str(memoryGSC)+" --vm-option=-Djava.security.krb5.conf=/etc/krb5.conf --vm-option=-Djava.security.auth.login.config=/dbagiga/gs_config/SQLJDBCDriver.conf "+str(host.ip)+" | grep -v JAVA_HOME"
        verboseHandle.printConsoleInfo("Creating container count : "+str(numberOfGSC)+" zone="+str(zoneGSC)+" memory="+str(memoryGSC)+" host="+str(host.ip))
        logger.info(commandToExecute)
        with Spinner():
            output = executeRemoteCommandAndGetOutput(managerHost, 'root', commandToExecute)
            print(output)
            logger.info("Output:"+str(output))

def createGSCInputParam():
    logger.info("createGSCInputParam()")
    global numberOfGSC
    global memoryGSC

    numberOfGSC = str(input(Fore.YELLOW+"Enter number of GSCs per host [1] : "+Fore.RESET))
    while(len(str(numberOfGSC))==0):
        numberOfGSC=1
    logger.info("numberOfGSC :"+str(numberOfGSC))

    memoryGSC = str(input(Fore.YELLOW+"Enter memory of GSC [1g] : "+Fore.RESET))
    while(len(str(memoryGSC))==0):
        memoryGSC='1g'

def updateAndCopyJarFileFromSourceToShFolder(puName):
    global filePrefix
    logger.info("updateAndCopyJarFileFromSourceToShFolder()")
    #sourceDB2FeederShFilePath = '/home/ec2-user/db2-feeder'
    #sourceDB2JarFilePath = '/home/ec2-user/db2feeder-1.0.0.jar'
    head , tail = os.path.split(sourceMSSQLJarFilePath)
    fileName= str(tail).replace('.jar','')
    filePrefix = fileName
    targetJarFile=sourceMSSQLFeederShFilePath+fileName+puName+'.jar'
    cmd = "cp "+sourceMSSQLJarFilePath+' '+sourceMSSQLFeederShFilePath+fileName+puName+'.jar'
    logger.info("cmd : "+str(cmd))
    home = executeLocalCommandAndGetOutput(cmd)
    logger.info("home: "+str(home))
    return targetJarFile

def uploadFileRest(managerHostConfig):
    try:
        logger.info("uploadFileRest : managerHostConfig : "+str(managerHostConfig))
        directory = os.getcwd()
        os.chdir(sourceMSSQLFeederShFilePath)
        for file in glob.glob("load_*.sh"):
            os.chdir(directory)
            puName = str(file).replace('load','').replace('.sh','').casefold()
            pathOfSourcePU = updateAndCopyJarFileFromSourceToShFolder(puName)
            #print("pathOfSourcePU : "+str(pathOfSourcePU))
            #print("jarName :"+jarName)
            zoneGSC = 'mssql_'+puName
            verboseHandle.printConsoleWarning("Proceeding for : "+pathOfSourcePU)
            logger.info("url : "+"curl -X PUT -F 'file=@"+str(pathOfSourcePU)+"' http://"+managerHostConfig+":8090/v2/pus/resources")
            logger.info("url : "+"curl -X PUT -F 'file=@"+str(pathOfSourcePU)+"' http://"+managerHostConfig+":8090/v2/pus/resources")
            status = os.system("curl -X PUT -F 'file=@"+str(pathOfSourcePU)+"' http://"+managerHostConfig+":8090/v2/pus/resources")
            print("\n")
            logger.info("status : "+str(status))
    except Exception as e:
        handleException(e)

def getDataPUREST(resource,resourceName,zoneOfPU,restPort):
    backUpRequired=0
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
            "mssql.server" : ""+mssqlServer+"",
            "feeder.writeBatchSize" : ""+feederWriteBatchSize+"",
            "space.name" : ""+spaceName+"",
            "feeder.sleepAfterWriteInMillis" : ""+feederSleepAfterWrite+""
        }
    }
    #print(data)
    return data

def validateResponseGetDescription(responseCode):
    logger.info("validateResponse() "+str(responseCode))
    response = requests.get("http://"+managerHost+":8090/v2/requests/"+str(responseCode))
    jsonData = json.loads(response.text)
    logger.info("response : "+str(jsonData))
    if(str(jsonData["status"]).__contains__("failed")):
        return "Status :"+str(jsonData["status"])+" Description:"+str(jsonData["error"])
    else:
        return "Status :"+str(jsonData["status"])+" Description:"+str(jsonData["description"])

def sqlLiteCreateTableDB():
    logger.info("sqlLiteCreateTableDB()")
    try:
        db_file = str(readValueByConfigObj("app.dataengine.mssql-feeder.sqlite.dbfile")).replace('"','').replace(' ','')
        logger.info("dbFile : "+str(db_file))
        cnx = sqlite3.connect(db_file)
        logger.info("Db connection obtained."+str(cnx)+" Sqlite V: "+str(sqlite3.version))
        cnx.execute("DROP TABLE IF EXISTS mssql_host_port")
        cnx.execute("CREATE TABLE mssql_host_port (file VARCHAR(50), feeder_name VARCHAR(50), host VARCHAR(50), port varchar(10))")
        cnx.commit()
        cnx.close()
    except Exception as e:
        handleException(e)

def createMSSQLEntryInSqlLite(puName, file, restPort):
    logger.info("createMSSQLEntryInSqlLite()")
    try:
        response = requests.get("http://"+str(managerHost)+":8090/v2/pus/"+str(puName)+"/instances")
        jsonArray = json.loads(response.text)
        logger.info("response : "+str(jsonArray))
        hostId = ''
        for data in jsonArray:
            hostId = str(data["hostId"])
        db_file = str(readValueByConfigObj("app.dataengine.mssql-feeder.sqlite.dbfile")).replace('"','').replace(' ','')
        cnx = sqlite3.connect(db_file)
        cnx.execute("INSERT INTO mssql_host_port (file, feeder_name, host, port) VALUES ('"+str(file)+"', '"+str(puName)+"','"+str(hostId)+"','"+str(restPort)+"')")
        cnx.commit()
        cnx.close()
    except Exception as e:
        handleException(e)

def proceedToDeployPU():
    global restPort
    try:
        logger.info("proceedToDeployPU()")
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        logger.info("url : "+"http://"+managerHost+":8090/v2/pus")
        sqlLiteCreateTableDB()
        directory = os.getcwd()
        os.chdir(sourceMSSQLFeederShFilePath)
        #os.system("pwd")
        restPort = 8014
        for file in glob.glob("load_*.sh"):
            restPort = restPort+1
            os.chdir(directory)
            puName = str(file).replace('load_','').replace('.sh','').casefold()
            zoneGSC = 'mssql_'+puName
            logger.info("filePrefix : "+filePrefix)
            resource = filePrefix+'_'+puName+'.jar'
            puName = 'mssqlfeeder_'+puName
            if(confirmCreateGSC=='y'):
                proceedToCreateGSC(zoneGSC)
            verboseHandle.printConsoleInfo("Resource : "+resource+" : rest.port : "+str(restPort))
            data = getDataPUREST(resource,puName,zoneGSC,str(restPort))
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
                while(retryCount>0 or (not str(status).casefold().__contains__('successful')) or (not str(status).casefold().__contains__('failed'))):
                    status = validateResponseGetDescription(deployResponseCode)
                    verboseHandle.printConsoleInfo("Response :"+str(status))
                    retryCount = retryCount-1
                    time.sleep(2)
                    if(str(status).casefold().__contains__('successful')):
                        time.sleep(2)
                        createMSSQLEntryInSqlLite(puName,file,restPort)
                        cmd = "rm -f "+sourceMSSQLFeederShFilePath+resource
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
    verboseHandle.printConsoleInfo("------------------------------------------------------------")
    verboseHandle.printConsoleInfo("***Summary***")
    if(confirmCreateGSC=='y'):
        verboseHandle.printConsoleInfo("Enter number of GSCs per host :"+str(numberOfGSC))
        verboseHandle.printConsoleInfo("Enter memory of GSC [1g] :"+memoryGSC)
        #verboseHandle.printConsoleInfo("Enter -Dpipeline.config.location source : "+dPipelineLocationSource)
        #verboseHandle.printConsoleInfo("Enter -Dpipeline.config.location target : "+dPipelineLocationTarget)
    verboseHandle.printConsoleInfo("Enter mssql.server : "+str(mssqlServer))
    verboseHandle.printConsoleInfo("Enter feeder.writeBatchSize : "+str(feederWriteBatchSize))
    verboseHandle.printConsoleInfo("Enter feeder.sleepAfterWriteInMillis :"+str(feederSleepAfterWrite))
    verboseHandle.printConsoleInfo("Enter source file path of mssql-feeder .jar file including file name : "+str(sourceMSSQLJarFilePath))
    verboseHandle.printConsoleInfo("Enter source file path of mssql-feeder *.sh file : "+str(sourceMSSQLFeederShFilePath))

def proceedToDeployPUInputParam(managerHost):
    logger.info("proceedToDeployPUInputParam()")

    global sourceMSSQLJarFilePath
    sourceMSSQLJarFileConfig = str(readValueByConfigObj("app.dataengine.mssql-feeder.jar"))
    sourceMSSQLJarFilePath = str(input(Fore.YELLOW+"Enter source file path of mssql-feeder .jar file including file name ["+sourceMSSQLJarFileConfig+"] : "+Fore.RESET))
    if(len(str(sourceMSSQLJarFilePath))==0):
        sourceMSSQLJarFilePath = sourceMSSQLJarFileConfig
    set_value_in_property_file("app.dataengine.mssql-feeder.jar",sourceMSSQLJarFilePath)

    global sourceMSSQLFeederShFilePath
    sourceMSSQLFeederShFilePathConfig = str(readValueByConfigObj("app.dataengine.mssql-feeder.filePath.shFile"))
    sourceMSSQLFeederShFilePath = str(input(Fore.YELLOW+"Enter source file path (directory) of *.sh file ["+sourceMSSQLFeederShFilePathConfig+"] : "+Fore.RESET))
    if(len(str(sourceMSSQLFeederShFilePath))==0):
        sourceMSSQLFeederShFilePath = sourceMSSQLFeederShFilePathConfig
    lastChar = str(sourceMSSQLFeederShFilePath[-1])
    logger.info("last char:"+str(lastChar))
    if(lastChar!='/'):
        sourceMSSQLFeederShFilePath = sourceMSSQLFeederShFilePath+'/'
    set_value_in_property_file("app.dataengine.mssql-feeder.filePath.shFile",sourceMSSQLFeederShFilePath)

    uploadFileRest(managerHost)

    global partition
    partition='1'

    global maxInstancesPerMachine
    maxInstancesPerMachine = '1'
    logger.info("maxInstancePerVM Of PU :"+str(maxInstancesPerMachine))

    global spaceName
    spaceName = str(input(Fore.YELLOW+"Enter space.name [bllspace] : "+Fore.RESET))
    if(len(str(spaceName))==0):
        spaceName='bllspace'

    global mssqlServer
    mssqlServerConfig = str(readValueByConfigObj("app.dataengine.mssql-feeder.mssql.server"))
    mssqlServer = str(input(Fore.YELLOW+"Enter mssql.server ["+mssqlServerConfig+"]: "+Fore.RESET))
    if(len(str(mssqlServer))==0):
        mssqlServer = mssqlServerConfig
    set_value_in_property_file("app.dataengine.mssql-feeder.mssql.server",mssqlServer)

    global feederWriteBatchSize
    feederWriteBatchSize = str(input(Fore.YELLOW+"Enter feeder.writeBatchSize [10000] :"+Fore.RESET))
    if(len(feederWriteBatchSize)==0):
        feederWriteBatchSize='10000'

    global feederSleepAfterWrite
    feederSleepAfterWrite = str(input(Fore.YELLOW+"Enter feeder.sleepAfterWriteInMillis [500] :"+Fore.RESET))
    if(len(feederSleepAfterWrite)==0):
        feederSleepAfterWrite='500'

    displaySummaryOfInputParam()

    finalConfirm = str(input(Fore.YELLOW+"Are you sure want to proceed ? (y/n) [y] :"+Fore.RESET))
    if(len(str(finalConfirm))==0):
        finalConfirm='y'
    if(finalConfirm=='y'):
        logger.info("mq connector kafka consumer confirmCreateGSC "+confirmCreateGSC)
        proceedToDeployPU()
    else:
        return

if __name__ == '__main__':
    logger.info("odsx_dataengine_mssql-feeder_install")
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> MSSQL-Feeder -> Install-Deploy')
    try:
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
                    listSpacesOnServer(managerNodes)
                    listDeployed(managerHost)
                    space_dict_obj = displaySpaceHostWithNumber(managerNodes,spaceNodes)
                    if(len(space_dict_obj)>0):
                        confirmCreateGSC = str(input(Fore.YELLOW+"Do you want to create GSC ? (y/n) [y] : "))
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