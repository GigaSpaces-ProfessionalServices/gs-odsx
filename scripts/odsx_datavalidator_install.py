#!/usr/bin/env python3

import os,subprocess
import platform
from os import path
from colorama import Fore
from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_ssh import connectExecuteSSH,executeRemoteCommandAndGetOutputPython36
from utils.ods_scp import scp_upload
from utils.ods_cluster_config import config_add_dataValidation_node, config_get_dataIntegration_nodes
from utils.ods_app_config import set_value_in_property_file

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

def installSingle():
    logger.info("installSingle():")
    try:
        global user
        host = str(input(Fore.YELLOW+"Enter host to install Data Validation Service: "+Fore.RESET))
        while(len(str(host))==0):
            host = str(input(Fore.YELLOW+"Enter host to install Data Validation Service: "+Fore.RESET))

        user = str(input(Fore.YELLOW+"Enter user to connect Data Validation Service servers [root]:"+Fore.RESET))
        if(len(str(user))==0):
            user="root"
        logger.info(" user: "+str(user))
        #open and add properties as per user inputs
        dbPath= str(input(Fore.YELLOW+"Enter db path[datavalidator.db]: "+Fore.RESET))
        if(len(str(dbPath))==0):
            dbPath='datavalidator.db'
        logFilepath= str(input(Fore.YELLOW+"Enter  log file path[datavalidator.log] : "+Fore.RESET))
        if(len(str(logFilepath))==0):
            logFilepath='datavalidator.log'
        
        with open('install/data-validation/application.properties', 'w') as f:
         f.write('server.port=7890')
         f.write('\n')
         f.write('logging.file.name='+logFilepath)
         f.write('\n')
         f.write('pathToDataBase='+dbPath)
        
    
        confirmInstall = str(input(Fore.YELLOW+"Are you sure want to install Data Validation Service server (y/n) [y]: "+Fore.RESET))
        if(len(str(confirmInstall))==0):
            confirmInstall='y'
        if(confirmInstall=='y'):
            buildTarFileToLocalMachine(host)
            buildUploadInstallTarToServer(host)
            executeCommandForInstall(host,'SingleNode',0)

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
            scp_upload(host, user, 'install/install.tar', '/home/gsods')
    except Exception as e:
        handleException(e)

def executeCommandForInstall(host,type,count):
    logger.info("executeCommandForInstall(): start host : "+str(host) +" type : "+str(type))

    try:
        #cmd = "java -version"
        #outputVersion = executeRemoteCommandAndGetOutputPython36(host,user,cmd)
        #print("output java version :"+str(outputVersion))
        commandToExecute="scripts/servers_datavalidation_install.sh"
        additionalParam=""
        logger.info("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user))
        with Spinner():
            outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
            logger.info("outputShFile : "+str(outputShFile))

            config_add_dataValidation_node(host, host, "dataValidation", "true", type)
            set_value_in_property_file('app.dv.hosts',host)
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
    cmd = 'find '+str(home)+'/install/java/ -name *.rpm -printf "%f\n"' # Creating .tar file on Pivot machine
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
    try:
        if(validateRPM()):
            installSingle()
        else:
            logger.info("No valid rpm found")

    except Exception as e:
        handleException(e)