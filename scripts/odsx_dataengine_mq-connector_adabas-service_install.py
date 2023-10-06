#!/usr/bin/env python3

import os

from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValueByConfigObj, getYamlFilePathInsideFolder
from utils.ods_cluster_config import config_get_dataIntegration_nodes, config_get_influxdb_node
from utils.ods_scp import scp_upload
from utils.ods_ssh import connectExecuteSSH
from utils.odsx_keypress import userInputWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
clusterHosts = []

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

class obj_type_dictionary(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

def getDIServerHostList():
    nodeList = config_get_dataIntegration_nodes()
    nodes = ""
    count=0  # Only 3 Kafka host we will configure
    for node in nodeList:
        # if(str(node.role).casefold() == 'server'):
        if count <3:
            if (len(nodes) == 0):
                nodes = os.getenv(node.ip)
            else:
                nodes = nodes + ',' + os.getenv(node.ip)
        count=count+1
    return nodes


def displaySummary():
    logger.info("displaySummary()")
    #verboseHandle.printConsoleInfo("----------------------------------------------------------------")
    verboseHandle.printConsoleWarning("-----------------------*****Summary****-------------------------")
    verboseHandle.printConsoleInfo("Enter target directory to install mq-connector         : "+str(targetDir))
    verboseHandle.printConsoleInfo("MQ-Connector will going to install on hosts ["+str(kafkahostConfig)+"] ")
    verboseHandle.printConsoleInfo("Enter source adabas .jar file path including file name : "+str(sourceAdabasJarFile))
    verboseHandle.printConsoleInfo("keystore.jks file source : "+str(sourceKeyStoreFile))
    verboseHandle.printConsoleInfo("keystore.jks file target : "+str(targetDir)+"/keystore.jks")
    verboseHandle.printConsoleInfo("Enter mq hostname        : "+str(mqHostname))
    verboseHandle.printConsoleInfo("Enter mq channel         : "+str(mqChannel))
    verboseHandle.printConsoleInfo("Enter mq qmanager        : "+str(mqManager))
    verboseHandle.printConsoleInfo("Enter mq queueName       : "+str(queueName))
    verboseHandle.printConsoleInfo("Enter mq sslChipherSuite : "+str(sslChipherSuite))
    verboseHandle.printConsoleInfo("Enter mq port            : "+str(mqPort))
    verboseHandle.printConsoleInfo("----------------------------------------------------------------")

def getInputParam(kafkaHosts):
    logger.info("getInputParam()")
    numMQhostToInstall=''
    confirmMQHosts=''
    hostConfig=''
    global kafkahostConfig
    global targetDir
    global sourceAdabasJarFile
    global targetAdabasJarFile
    global mqHostname
    global mqChannel
    global mqManager
    global queueName
    global sslChipherSuite
    global mqPort
    global sourceKeyStoreFile
    kafkahostConfig = kafkaHosts
    sourceAdabasJarFile=''
    targetAdabasJarFile=''
    dbaGigaDir=str(readValueByConfigObj("app.giga.path"))
    targetDir = str(readValueByConfigObj("app.dataengine.mq.adabas.targetDir")).replace('[','').replace(']','').replace("'","").replace(', ',',').replace("/dbagiga/",dbaGigaDir)
    #verboseHandle.printConsoleWarning("MQ-Connector will going to install on hosts ["+str(kafkaHosts)+"] ")
    #targetDirConfirm = str(userInputWrapper(Fore.YELLOW+"Enter target directory to install mq-connector : ["+targetDir+"] : "))
    #if(len(str(targetDirConfirm))==0):
    targetDirConfirm=targetDir

    sourceConfig = str(getYamlFilePathInsideFolder(".mq-connector.adabas.jars.jarFile")).replace('[','').replace(']','').replace("'","").replace(', ',',')
    #print(Fore.YELLOW+"Enter source adabas .jar file path including file name ["+str(sourceConfig)+"] : "+Fore.RESET)
    #if(len(str(sourceAdabasJarFile))==0):
    sourceAdabasJarFile=sourceConfig
    #verboseHandle.printConsoleWarning("Target path will be "+targetDir+"/"+(os.path.basename(sourceAdabasJarFile)))
    targetAdabasJarFile = targetDirConfirm+"/"+(os.path.basename(sourceAdabasJarFile))

    mqHostnameConfig = str(readValueByConfigObj("app.dataengine.mq.adabas.mqHostname")).replace('[','').replace(']','').replace("'","").replace(', ',',')
    #print(Fore.YELLOW+"Enter mq hostname ["+mqHostnameConfig+"] : "+Fore.RESET)
    #if(len(str(mqHostname))==0):
    mqHostname=mqHostnameConfig
    #set_value_in_property_file("app.dataengine.mq.adabas.mqHostname",mqHostname)

    mqChannelConfig = str(readValueByConfigObj("app.dataengine.mq.adabas.channel")).replace('[','').replace(']','').replace("'","").replace(', ',',')
    #print(Fore.YELLOW+"Enter mq channel ["+mqChannelConfig+"] : "+Fore.RESET)
    #if(len(str(mqChannel))==0):
    mqChannel = mqChannelConfig
    #set_value_in_property_file("app.dataengine.mq.adabas.channel",mqChannel)

    mqManagerConfig = str(readValueByConfigObj("app.dataengine.mq.adabas.manager")).replace('[','').replace(']','').replace("'","").replace(', ',',')
    #print(Fore.YELLOW+"Enter mq qmanager ["+mqManagerConfig+"] : "+Fore.RESET)
    #if(len(str(mqManager))==0):
    mqManager = mqManagerConfig
    #set_value_in_property_file("app.dataengine.mq.adabas.manager",mqManager)

    queueNameConfig = str(readValueByConfigObj("app.dataengine.mq.adabas.queuename")).replace('[','').replace(']','').replace("'","").replace(', ',',')
    #print(Fore.YELLOW+"Enter mq queueName ["+queueNameConfig+"] : "+Fore.RESET)
    #if(len(str(queueName))==0):
    queueName = queueNameConfig
    #set_value_in_property_file("app.dataengine.mq.adabas.queuename",queueName)

    sslChipherSuiteConfig = str(readValueByConfigObj("app.dataengine.mq.adabas.sslChipherSuite")).replace('[','').replace(']','').replace("'","").replace(', ',',')
    #print(Fore.YELLOW+"Enter mq sslChipherSuite ["+sslChipherSuiteConfig+"] : "+Fore.RESET)
    #if(len(str(sslChipherSuite))==0):
    sslChipherSuite = sslChipherSuiteConfig
    #set_value_in_property_file("app.dataengine.mq.adabas.sslChipherSuite",sslChipherSuite)

    mqPortConfig =  str(readValueByConfigObj("app.dataengine.mq.adabas.port")).replace('[','').replace(']','').replace("'","").replace(', ',',')
    #print(Fore.YELLOW+"Enter mq port ["+mqPortConfig+"] : "+Fore.RESET)
    #if(len(str(mqPort))==0):
    mqPort = mqPortConfig
    #set_value_in_property_file("app.dataengine.mq.adabas.port",mqPort)

    sourceKeyStoreFile = str(getYamlFilePathInsideFolder(".mq-connector.adabas.config.keystore")).replace('[','').replace(']','').replace("'","").replace(', ',',')

    displaySummary()
    return kafkaHosts

def buildTarFileToLocalMachine():
    logger.info("buildTarFileToLocalMachine :")

    cmd = 'tar -cvf install/install.tar install'#+sourceInstallerDirectory # Creating .tar file on Pivot machine
    with Spinner():
        status = os.system(cmd)
        logger.info("Creating tar file status : " + str(status))

def buildUploadInstallTarToServer(host):
    logger.info("buildUploadInstallTarToServer(): start host :" + str(host))
    user='root'
    try:
        with Spinner():
            logger.info("hostip ::" + str(host) + " user :" + str(user))
            scp_upload(host, user, 'install/install.tar', '/root')
    except Exception as e:
        handleException(e)

def getConnectionStr(hostConfig):
    logger.info("getConnectionStr()")
    connectionStr=''
    for host in hostConfig.split(','):
        connectionStr=connectionStr+host+':2181,'
    connectionStr= connectionStr[:-1]
    logger.info("connectionStr :"+str(connectionStr))
    return connectionStr

def getBootstrapAddress(hostConfig):
    logger.info("getBootstrapAddress()")
    bootstrapAddress=''
    for host in hostConfig.split(','):
        bootstrapAddress=bootstrapAddress+host+':9092,'
    bootstrapAddress=bootstrapAddress[:-1]
    logger.info("getBootstrapAddress : "+str(bootstrapAddress))
    return bootstrapAddress

def getInfluxdbHost():
    host=''
    nodeList = config_get_influxdb_node()
    for host in nodeList:
        host = os.getenv(host.ip)
    return host

def proceedForInstallation(hostConfig):
    logger.info("proceedForInstallation()")
    confirmInstallation=str(userInputWrapper(Fore.YELLOW+"Are you sure want to proceed for Installation on hosts ["+hostConfig+"] ? (y/n) [y] : "))
    if(len(str(confirmInstallation))==0):
        buildTarFileToLocalMachine()
        hostList = hostConfig.split(',')
        connectionStr = getConnectionStr(hostConfig)
        bootstrapAddress = getBootstrapAddress(hostConfig)
        influxdbhost = str(getInfluxdbHost())
        if(len(influxdbhost)==0):
            verboseHandle.printConsoleWarning("No influxdb configuration found.")

        dbaGigaLogPath=str(readValueByConfigObj("app.gigalog.path"))
        dbaGigaDir=str(readValueByConfigObj("app.giga.path"))
        additionalParam = ""+targetDir+' '+hostConfig+' '+connectionStr+' '+bootstrapAddress+' '+os.path.basename(sourceAdabasJarFile)
        additionalParam = additionalParam+' '+mqHostname+' '+mqChannel+' '+mqManager+' '+queueName+' '+sslChipherSuite+' '+mqPort+' '+influxdbhost +' '+dbaGigaLogPath+' '+dbaGigaDir
        print(additionalParam)
        logger.info("additionalParam : "+str(additionalParam))
        user='root'
        for host in hostList:
            logger.info("Proceeding for host :"+str(host))
            buildUploadInstallTarToServer(host)
            print(sourceAdabasJarFile+' '+sourceKeyStoreFile)
            scp_upload(host, user, sourceAdabasJarFile, '/root')
            scp_upload(host, user,sourceKeyStoreFile , '/root')
            verboseHandle.printConsoleInfo("Proceeding installation for host :"+str(host))
            commandToExecute = "scripts/dataengine_list_mq-connector_adabasservice_install.sh"
            logger.info("Additinal Param:" + additionalParam + " cmdToExec:" + commandToExecute + " Host:" + str(
                host) + " User:" + str(user))
            with Spinner():
                outputShFile = connectExecuteSSH(host, user, commandToExecute, additionalParam)
                print(outputShFile)
                logger.info("outputShFile kafka : " + str(outputShFile))

            #config_add_dataEngine_node(host, host, "dataEngine", "mq-connector", "")
            verboseHandle.printConsoleInfo("Installation of mq-connector done on host :"+str(host))

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> MQ-Connector -> Adabas Service -> Install')
    try:
        nodes = getDIServerHostList()
        logger.info("DI / kafka host found :"+str(nodes))
        if(len(nodes)>0):
            hostConfig = getInputParam(nodes)
            if(str(hostConfig)!='99'):
                proceedForInstallation(hostConfig)
        else:
            logger.info("No kafka servers configurations found. Please install kafka servers first.")
            verboseHandle.printConsoleInfo("No kafka servers configurations found. Please install kafka servers first.")
    except Exception as e:
        handleException(e)