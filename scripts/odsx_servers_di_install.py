#!/usr/bin/env python3

import os
import signal
import subprocess

from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import set_value_in_property_file, readValuefromAppConfig, getYamlFilePathInsideFolder
from utils.ods_cleanup import signal_handler
from utils.ods_cluster_config import config_add_dataIntegration_node, config_get_dataIntegration_nodes
from utils.ods_scp import scp_upload
from utils.ods_ssh import connectExecuteSSH

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
    logger.info("getDIServerHostList()")
    nodeList = config_get_dataIntegration_nodes()
    nodes = ""
    for node in nodeList:
        if (len(nodeList) == 1):
            nodes = os.getenv(node.ip)
        else:
            nodes = nodes + ',' + os.getenv(node.ip)
    if nodes[0]==',':
        nodes=nodes[1:]
    return nodes

def installCluster():
    logger.info("installCluster()")
    global user
    global kafkaBrokerHost1
    global kafkaBrokerHost2
    global kafkaBrokerHost3
    global zkWitnessHost
    #    global cr8InstallFlag
    global telegrafInstallFlag
    telegrafInstallFlag="y"
    global baseFolderLocation
    global dataFolderKafka
    global dataFolderZK
    global logsFolderKafka
    global logsFolderZK
    global wantJava

    kafkaBrokerHost1 = str(os.getenv("di1"))
    logger.info("kafkaBrokerHost1 : " + str(kafkaBrokerHost1))
    kafkaBrokerHost3 = str(os.getenv("di3"))
    logger.info("kafkaBrokerHost3 : " + str(kafkaBrokerHost3))
    zkWitnessHost = str(os.getenv("di4"))
    logger.info("zkWitnessHost :" + str(zkWitnessHost))
    kafkaBrokerHost2 = str(os.getenv("di2"))
    logger.info("kafkaBrokerHost2 : " + str(kafkaBrokerHost2))
    type_installer_dictionary_obj = obj_type_dictionary()
    type_installer_dictionary_obj.add('kafka Broker 1a',"[kafka,zk,telegraf]")
    type_installer_dictionary_obj.add('kafka Broker 1b',"[kafka,telegraf]")
    type_installer_dictionary_obj.add('kafka Broker 2',"[kafka,zk,telegraf]")
    type_installer_dictionary_obj.add('Zookeeper Witness',"[zk,telegraf]")
    nodeListSize = len(str((getDIServerHostList())).split(','))
    logger.info("nodeListSize : "+str(nodeListSize))
    srNo=0
    nodeList = config_get_dataIntegration_nodes()
    nodes = ""
    host_type_dictionary_obj = obj_type_dictionary()
    for node in nodeList:
        srNo=srNo+1
        if nodeListSize ==1 or nodeListSize==3:
            installer = "[kafka,zk,telegraf]"
            verboseHandle.printConsoleInfo(str(srNo)+". "+str(node.type)+" : "+installer)
        else:
            installer = str(type_installer_dictionary_obj.get(node.type))
            verboseHandle.printConsoleInfo(str(srNo)+". "+str(node.type)+"   "+installer+"  : "+os.getenv(node.ip))
        host_type_dictionary_obj.add(os.getenv(node.ip),str(node.type))

        clusterHosts.append(os.getenv(node.ip))

    user = "root"
    logger.info(" user: " + str(user))
    baseFolderLocation = str(readValuefromAppConfig("app.di.base.kafka.zk"))
    srNo=srNo+1
    print(Fore.GREEN +str(srNo)+ ". Installation base folder for Kafka and Zookeeper : "+baseFolderLocation+"" + Fore.RESET)
    logger.info(" base folder: " + str(baseFolderLocation))
    dataFolderKafka = str(readValuefromAppConfig("app.di.base.kafka.data"))
    srNo=srNo+1
    print(Fore.GREEN + str(srNo)+". Data folder for Kafka : "+dataFolderKafka+"" + Fore.RESET)
    logger.info(" dataFolderKafka: " + str(dataFolderKafka))
    dataFolderZK = str(readValuefromAppConfig("app.di.base.zk.data"))
    srNo=srNo+1
    print(Fore.GREEN + str(srNo)+". Data folder for Zookeeper : "+dataFolderZK+"" + Fore.RESET)
    logger.info(" dataFolderZK: " + str(dataFolderZK))
    logsFolderKafka = str(readValuefromAppConfig("app.di.base.kafka.logs"))
    srNo=srNo+1
    print(Fore.GREEN + str(srNo)+". Base logs folder for kafka : "+logsFolderKafka+"" + Fore.RESET)
    logger.info(" logsFolderKafka: " + str(logsFolderKafka))
    logsFolderZK = str(readValuefromAppConfig("app.di.base.zk.logs"))
    srNo=srNo+1
    print(Fore.GREEN + str(srNo)+". Base logs folder for Zookeeper : "+logsFolderZK+"" + Fore.RESET)
    logger.info(" logsFolderZK: " + str(logsFolderZK))
    wantJava = str(getYamlFilePathInsideFolder(".kafka.jolokiaJar"))
    srNo=srNo+1
    print(Fore.GREEN + str(srNo)+". Jolokia jar file path source : "+wantJava+"" + Fore.RESET)
    logger.info(" wantJava: " + str(wantJava))
    wantJava = str(readValuefromAppConfig("app.di.base.java.want"))
    srNo=srNo+1
    print(Fore.GREEN + str(srNo)+". Want to install Java : "+wantJava+"" + Fore.RESET)
    logger.info(" wantJava: " + str(wantJava))
    srNo=srNo+1
    sourcePath= sourceInstallerDirectory+"/kafka/"
    packageName = [f for f in os.listdir(sourcePath) if f.endswith('.tgz')]
    verboseHandle.printConsoleInfo(str(srNo)+". kafka installer : "+str(packageName))
    srNo=srNo+1
    sourcePath= sourceInstallerDirectory+"/zk/"
    packageName = [f for f in os.listdir(sourcePath) if f.endswith('.gz')]
    verboseHandle.printConsoleInfo(str(srNo)+". Zookeeper installer : "+str(packageName))
    srNo=srNo+1
    sourcePath= sourceInstallerDirectory+"/telegraf/"
    packageName = [f for f in os.listdir(sourcePath) if f.endswith('.rpm')]
    verboseHandle.printConsoleInfo(str(srNo)+". Telegraf installer : "+str(packageName))
    srNo=srNo+1
    sourcePath= sourceInstallerDirectory+"/data-integration/di-manager/"
    packageName = [f for f in os.listdir(sourcePath) if f.endswith('.gz')]
    verboseHandle.printConsoleInfo(str(srNo)+". DI-Manager (DIM) installer : "+str(packageName))
    srNo=srNo+1
    sourcePath= sourceInstallerDirectory+"/data-integration/di-mdm/"
    packageName = [f for f in os.listdir(sourcePath) if f.endswith('.gz')]
    verboseHandle.printConsoleInfo(str(srNo)+". DI-Metadata Manager (MDM) installer : "+str(packageName))
    srNo=srNo+1
    sourcePath= sourceInstallerDirectory+"/data-integration/di-flink/"
    packageName = [f for f in os.listdir(sourcePath) if f.endswith('.tgz')]
    verboseHandle.printConsoleInfo(str(srNo)+". DI-Flink installer : "+str(packageName))

    logger.info("clusterHosts : " + str(clusterHosts))
    logger.info("host_type_dictionary_obj : " + str(host_type_dictionary_obj))
    confirmInstall = str(input(
        Fore.YELLOW + "Are you sure want to install DI servers on " + str(clusterHosts) + " (y/n) [y]: " + Fore.RESET))
    if (len(str(confirmInstall)) == 0):
        confirmInstall = 'y'
    if (confirmInstall == 'y'):
        counter = 1
        for host in clusterHosts:
            logger.info("proceeding for host : " + str(host))
            if (counter == 1):
                buildTarFileToLocalMachine(host)
            buildUploadInstallTarToServer(host)
            executeCommandForInstall(host, host_type_dictionary_obj.get(host), counter,nodeListSize)
            counter = counter + 1

def buildTarFileToLocalMachine(host):
    logger.info("buildTarFileToLocalMachine :" + str(host))
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))#str(readValuefromAppConfig("app.setup.sourceInstaller"))
    userCMD = os.getlogin()
    if userCMD == 'ec2-user':
        cmd = 'sudo cp install/zookeeper/odsxzookeeper.service install/kafka/odsxkafka.service '+sourceInstallerDirectory+"/zk/"
        cmd2= 'sudo cp install/kafka/odsxkafka.service '+sourceInstallerDirectory+"/kafka/"
    else:
        cmd = 'cp install/zookeeper/odsxzookeeper.service install/kafka/odsxkafka.service '+sourceInstallerDirectory+"/zk/"
        cmd2= 'cp install/kafka/odsxkafka.service '+sourceInstallerDirectory+"/kafka/"
    with Spinner():
        status = os.system(cmd)
        status = os.system(cmd2)
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))#str(readValuefromAppConfig("app.setup.sourceInstaller"))
    cmd = 'tar -cvf install/install.tar install'#+sourceInstallerDirectory  # Creating .tar file on Pivot machine
    with Spinner():
        status = os.system(cmd)
        logger.info("Creating tar file status : " + str(status))


def buildUploadInstallTarToServer(host):
    logger.info("buildUploadInstallTarToServer(): start host :" + str(host))
    try:
        with Spinner():
            logger.info("hostip ::" + str(host) + " user :" + str(user))
            scp_upload(host, user, 'install/install.tar', '')
    except Exception as e:
        handleException(e)


def executeCommandForInstall(host, type, count,nodeListSize):
    logger.info("executeCommandForInstall(): start host : " + str(host) + " type : " + str(type))

    try:
        additionalParam = ""
        additionalParam = telegrafInstallFlag + ' '
        if (len(clusterHosts) == 4):
            commandToExecute = "scripts/servers_di_install.sh"
            additionalParam = additionalParam + kafkaBrokerHost1 + ' ' + kafkaBrokerHost2 + ' ' + kafkaBrokerHost3 + ' ' + zkWitnessHost + ' ' + str(count) + ' ' + str(baseFolderLocation)+ ' ' + str(dataFolderKafka)+ ' ' + str(dataFolderZK)+ ' ' + str(logsFolderKafka)+ ' ' + str(logsFolderZK)+' '+str(wantJava)+' '+sourceInstallerDirectory+' '+host
        if(len(clusterHosts)==3):
            commandToExecute = "scripts/servers_di_install_all.sh"
            additionalParam = additionalParam +' '+str(nodeListSize)+' '+ kafkaBrokerHost1 + ' ' + kafkaBrokerHost2 + ' ' + kafkaBrokerHost3 + ' ' + str(count) + ' ' + str(baseFolderLocation)+ ' ' + str(dataFolderKafka)+ ' ' + str(dataFolderZK)+ ' ' + str(logsFolderKafka)+ ' ' + str(logsFolderZK)+' '+str(wantJava)+' '+sourceInstallerDirectory+' '+host
        if(len(clusterHosts)==1):
            commandToExecute = "scripts/servers_di_install_all.sh"
            additionalParam = additionalParam +' '+str(nodeListSize)+' '+ kafkaBrokerHost1 + ' ' + str(count) + ' ' + str(baseFolderLocation)+ ' ' + str(dataFolderKafka)+ ' ' + str(dataFolderZK)+ ' ' + str(logsFolderKafka)+ ' ' + str(logsFolderZK)+' '+str(wantJava)+' '+sourceInstallerDirectory+' '+host
        logger.info("Additional Param:" + additionalParam + " cmdToExec:" + commandToExecute + " Host:" + str(
            host) + " User:" + str(user))
        print(additionalParam)
        with Spinner():
            outputShFile = connectExecuteSSH(host, user, commandToExecute, additionalParam)
            logger.info("outputShFile kafka : " + str(outputShFile))
            print("Checking for Type ::::" + str(type))
            verboseHandle.printConsoleInfo("Node has been added :" + str(host))
    except Exception as e:
        handleException(e)

def executeLocalCommandAndGetOutput(commandToExecute):
    logger.info("executeLocalCommandAndGetOutput() cmd :" + str(commandToExecute))
    cmd = commandToExecute
    cmdArray = cmd.split(" ")
    process = subprocess.Popen(cmdArray, stdout=subprocess.PIPE)
    out, error = process.communicate()
    out = out.decode()
    return str(out).replace('\n', '')


def validateRPM():
    logger.info("validateRPM()")
    installerArray = []
    cmd = "pwd"
    home = executeLocalCommandAndGetOutput(cmd)
    logger.info("home dir : " + str(home))
    cmd = 'find '+sourceInstallerDirectory+'/jdk/ -name *.rpm -printf "%f\n"'  # Checking .rpm file on Pivot machine
    javaRpm = executeLocalCommandAndGetOutput(cmd)
    logger.info("javaRpm found :" + str(javaRpm))
    cmd = 'find '+sourceInstallerDirectory+'/kafka/ -name *.tgz -printf "%f\n"'  # Checking .tgz file on Pivot machine
    kafkaZip = executeLocalCommandAndGetOutput(cmd)
    logger.info("kafkaZip found :" + str(kafkaZip))
    cmd = 'find '+sourceInstallerDirectory+'/zk/ -name *.tar.gz -printf "%f\n"'  # Checking .tar.gz file on Pivot machine
    zkZip = executeLocalCommandAndGetOutput(cmd)
    logger.info("ZookeeperZip found :" + str(zkZip))
    cmd = 'find '+sourceInstallerDirectory+'/kafka/ -name *.jar -printf "%f\n"'  # Checking .tar.gz file on Pivot machine
    jolokiaJar = executeLocalCommandAndGetOutput(cmd)
    cmd = 'find '+sourceInstallerDirectory+'/telegraf/ -name *.rpm -printf "%f\n"'  # Checking .rpm file on Pivot machine
    telegrafRpm = executeLocalCommandAndGetOutput(cmd)
    logger.info("telegrafRpm found :" + str(telegrafRpm))

    di_installer_dict = obj_type_dictionary()
    di_installer_dict.add('Java', javaRpm)
    di_installer_dict.add('KafkaZip', kafkaZip)
    di_installer_dict.add('zkZip', zkZip)
    di_installer_dict.add('jolokiaJar', jolokiaJar)
    #di_installer_dict.add('CR8-LocalSetupZip', localSetupZip)
    di_installer_dict.add('Telegraf', telegrafRpm)

    for name, installer in di_installer_dict.items():
        if (len(str(installer)) == 0):
            verboseHandle.printConsoleInfo(
                "Pre-requisite installer "+sourceInstallerDirectory+"/.. " + str(name) + " not found")
            return False
    return True


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> DI -> Install')
    sourceInstallerDirectory=""
    signal.signal(signal.SIGINT, signal_handler)
    try:
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
        if (validateRPM()):
            installCluster()
        else:
            logger.info("No valid rpm found")

    except Exception as e:
        handleException(e)
