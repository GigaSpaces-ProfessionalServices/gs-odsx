#!/usr/bin/env python3

import os
import subprocess
import socket

from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig, getYamlFilePathInsideFolder
from utils.ods_cluster_config import config_get_dataValidation_nodes, config_get_influxdb_node
from utils.ods_scp import scp_upload
from utils.ods_ssh import connectExecuteSSH
from utils.odsx_keypress import userInputWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
clusterHosts=[]
class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR

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

def getDataValidationAgentHostFromEnv():
    logger.info("getDataValidationAgentHostFromEnv()")
    hosts = ''
    dvNodes = config_get_dataValidation_nodes()
    for node in dvNodes:
        if str(node.type).casefold() == 'agent':
            hosts+=str(str(os.getenv(node.ip)))+','
    hosts=hosts[:-1]
    return hosts

def getDataValidationServerHostFromEnv():
    logger.info("getDataValidationServerHostFromEnv()")
    hosts = ''
    dvNodes = config_get_dataValidation_nodes()
    for node in dvNodes:
        if str(node.type).casefold() == 'server':
            hosts+=str(str(os.getenv(node.ip)))+','
    hosts=hosts[:-1]
    return hosts

def getDataValidationAllHostFromEnv():
    logger.info("getDataValidationAllHostFromEnv()")
    hosts = ''
    dvNodes = config_get_dataValidation_nodes()
    for node in dvNodes:
        hosts+=str(os.getenv(str(node.ip)))+','
    hosts=hosts[:-1]
    return hosts

def getInfluxdbHostFromEnv():
    logger.info("getinfluxdbHostFromEnv()")
    hosts = ''
    influxdbNodes = config_get_influxdb_node()
    for node in influxdbNodes:
        hosts+=str(os.getenv(str(node.ip)))+','
    hosts=hosts[:-1]
    return hosts

def installSingle():
    logger.info("installSingle():")
    try:
        global user
        global targetInstallDir
        global sourceDvServerJar
        global logFilepath
        global dbPath
        global influxdbHost
        influxdbHost = getInfluxdbHostFromEnv()
        targetInstallDir=str(readValuefromAppConfig("app.dv.install.target"))
        serverHost = getDataValidationServerHostFromEnv()#str(userInputWrapper(Fore.YELLOW+"Enter host to install Data Validation Server: "+Fore.RESET))
        #while(len(str(serverHost))==0):
        #    serverHost = str(userInputWrapper(Fore.YELLOW+"Enter host to install Data Validation Server: "+Fore.RESET))

        #user = str(userInputWrapper(Fore.YELLOW+"Enter user to connect Data Validation Service servers [root]:"+Fore.RESET))
        #if(len(str(user))==0):
        user="root"
        logger.info(" user: "+str(user))

        dbPath= str(readValuefromAppConfig("app.dv.server.db")) #userInputWrapper(Fore.YELLOW+"Enter db path[/home/gsods/datavalidator.db]: "+Fore.RESET))
        #if(len(str(dbPath))==0):
        #    dbPath='/dbagigawork/sqlite/datavalidator.db'
        logFilepath= str(readValuefromAppConfig("app.dv.server.log")) #userInputWrapper(Fore.YELLOW+"Enter log file path[/home/gsods/datavalidator.log] : "+Fore.RESET))
        #if(len(str(logFilepath))==0):
        #    logFilepath='/dbagigalogs/datavalidator.log'
        sourceDvServerJar = str(getYamlFilePathInsideFolder(".data-validator.jars.serverjar"))

        #open and add properties as per user inputs
        with open('install/data-validation/application.properties', 'w') as f:
         f.write('server.port='+str(readValuefromAppConfig("app.dv.server.port")))
         f.write('\n')
         f.write('logging.file.name='+logFilepath)
         f.write('\n')
         f.write('pathToDataBase='+dbPath)
         f.write('\n')
         f.write('influxDBUrl=http://'+influxdbHost +':'+str(readValuefromAppConfig("app.dv.influxdbport")))   #http://127.0.0.1:8086
         f.write('\n')
         f.write('influxDBUsername='+str(readValuefromAppConfig("app.dv.influxdbusername")))
         f.write('\n')
         f.write('influxDBPassword='+str(readValuefromAppConfig("app.dv.influxdbpassword")))
         f.write('\n')
         f.write('influxDBName='+str(readValuefromAppConfig("app.dv.influxdbname")))
         f.write('\n')
         f.write('envName='+os.getenv('ENV_NAME',default='test'))
         f.write('\n')
         f.write('host='+socket.gethostname())

        verboseHandle.printConsoleInfo("------------------------------------------------------------")
        verboseHandle.printConsoleInfo("***Summary***")
        verboseHandle.printConsoleInfo("server Host : "+serverHost)
        verboseHandle.printConsoleInfo("Server User:  "+user)
        verboseHandle.printConsoleInfo("Target install directory: "+targetInstallDir)
        verboseHandle.printConsoleInfo("db Path: "+dbPath)
        verboseHandle.printConsoleInfo("DataValidation server jar : "+sourceDvServerJar)
        verboseHandle.printConsoleInfo("log File path: "+logFilepath)
        verboseHandle.printConsoleInfo("------------------------------------------------------------")

        confirmInstall = str(userInputWrapper(Fore.YELLOW+"Are you sure want to install Data Validation Service server (y/n) [y]: "+Fore.RESET))
        if(len(str(confirmInstall))==0):
            confirmInstall='y'
        if(confirmInstall=='y'):
            buildTarFileToLocalMachine(serverHost)
            buildUploadInstallTarToServer(serverHost)
            executeCommandForInstall(serverHost,'DataValidation',0,'Server')

    except Exception as e:
        handleException(e)


def buildTarFileToLocalMachine(host):
    logger.info("buildTarFileToLocalMachine :"+str(host))
    cmd = 'tar -cvf install/install.tar install' # Creating .tar file on Pivot machine
    with Spinner():
        status = os.system(cmd)
        logger.info("Creating tar file status : "+str(status))

def buildUploadInstallTarToServer(host):
    logger.info("buildUploadInstallTarToServer(): start host :" +str(host))
    try:
        with Spinner():
            logger.info("hostip ::"+str(host)+" user :"+str(user))
            scp_upload(host, user, 'install/install.tar', targetInstallDir)
    except Exception as e:
        handleException(e)

def executeCommandForInstall(host,type,count,role):
    logger.info("executeCommandForInstall(): start host : "+str(host) +" type : "+str(type))

    try:
        #cmd = "java -version"
        #outputVersion = executeRemoteCommandAndGetOutputPython36(host,user,cmd)
        #print("output java version :"+str(outputVersion))
        commandToExecute="scripts/servers_datavalidation_install.sh"
        additionalParam=sourceInstallerDirectory+' '+targetInstallDir+' '+sourceDvServerJar
        logger.info("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user))
        with Spinner():
            outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
            logger.info("outputShFile : "+str(outputShFile))
            #config_add_dataValidation_node(host, host, role, type)
            #set_value_in_property_file('app.dv.hosts',host)
            verboseHandle.printConsoleInfo("Node has been added :"+str(host))

    except Exception as e:
        handleException(e)

def executeLocalCommandAndGetOutput(commandToExecute):
    logger.info("executeLocalCommandAndGetOutput() cmd :"+str(commandToExecute))
    cmd = commandToExecute
    cmdArray = cmd.split(" ")
    process = subprocess.Popen(cmdArray, stdout=subprocess.PIPE)
    out, error = process.communicate()
    out = out.decode()
    return str(out).replace('\n','')

def validateRPM():
    logger.info("validateRPM()")
    installerArray = []
    cmd = "pwd"
    home = executeLocalCommandAndGetOutput(cmd)
    logger.info("home dir : "+str(home))
    cmd = 'find '+str(sourceInstallerDirectory)+'/jdk/ -name *.rpm -printf "%f\n"' # Creating .tar file on Pivot machine
    javaRpm = executeLocalCommandAndGetOutput(cmd)
    logger.info("javaRpm found :"+str(javaRpm))
    cmd = 'find '+str(home)+'/install/kafka/ -name *.tgz -printf "%f\n"' # Creating .tar file on Pivot machine
    #kafkaZip = executeLocalCommandAndGetOutput(cmd)
    #logger.info("kafkaZip found :"+str(kafkaZip))
    #cmd = 'find '+str(home)+'/install/cr8/ -name *.rpm -printf "%f\n"' # Creating .tar file on Pivot machine
    #cr8Rpm = executeLocalCommandAndGetOutput(cmd)
    #logger.info("cr8Rpm found :"+str(cr8Rpm))
    #cmd = 'find '+str(home)+'/install/cr8/ -name *.gz -printf "%f\n"' # Creating .tar file on Pivot machine
    #localSetupZip = executeLocalCommandAndGetOutput(cmd)
    #logger.info("localSetupZip found :"+str(localSetupZip))
    #cmd = 'find '+str(home)+'/install/telegraf/ -name *.rpm -printf "%f\n"' # Creating .tar file on Pivot machine
    #telegrafRpm = executeLocalCommandAndGetOutput(cmd)
    #logger.info("telegrafRpm found :"+str(telegrafRpm))

    di_installer_dict = obj_type_dictionary()
    di_installer_dict.add('Java',javaRpm)
    #di_installer_dict.add('KafkaZip',kafkaZip)
    #di_installer_dict.add('CR8Rpm',cr8Rpm)
    #di_installer_dict.add('CR8-LocalSetupZip',localSetupZip)
    #di_installer_dict.add('Telegraf',telegrafRpm)

    for name,installer in di_installer_dict.items():
        if(len(str(installer))==0):
            verboseHandle.printConsoleInfo("Pre-requisite installer "+str(home)+"/install  "+str(name)+" not found")
            return False
    return True


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataValidator -> Install')
    verboseHandle.printConsoleWarning('')
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    try:
        if(validateRPM()):
            installSingle()
        else:
            logger.info("No valid rpm found")

    except Exception as e:
        handleException(e)
