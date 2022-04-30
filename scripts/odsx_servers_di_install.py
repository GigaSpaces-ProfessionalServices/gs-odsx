#!/usr/bin/env python3

import os
import subprocess

from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import set_value_in_property_file
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
    nodeList = config_get_dataIntegration_nodes()
    nodes = ""
    for node in nodeList:
        # if(str(node.role).casefold() == 'server'):
        if (len(nodes) == 0):
            nodes = os.getenv(node.ip)
        else:
            nodes = nodes + ',' + os.getenv(node.ip)
    return nodes


def getDIServerTypeInstall():
    logger.info("getDIServerTypeInstall()")
    serverType = str(input(Fore.YELLOW + "[1] Single\n[2] Cluster\n[99] Exit : " + Fore.RESET))
    while (len(serverType) == 0):
        serverType = str(input(Fore.YELLOW + "[1] Single\n[2] Cluster\n[99] Exit : " + Fore.RESET))
    return serverType


def installSingle():
    logger.info("installSingle():")
    try:
        global user
        #        global cr8InstallFlag
        global telegrafInstallFlag

        host = str(input(Fore.YELLOW + "Enter host to install DI: " + Fore.RESET))
        while (len(str(host)) == 0):
            host = str(input(Fore.YELLOW + "Enter host to install DI: " + Fore.RESET))
        logger.info("Enter host to install di : " + str(host))
        user = str(input(Fore.YELLOW + "Enter user to connect DI servers [root]:" + Fore.RESET))
        if (len(str(user)) == 0):
            user = "root"
        logger.info(" user: " + str(user))

        telegrafInstallFlag = input("Do you want to install telegraf? yes(y)/no(n) [n]: ")
        logger.info("Selected answer telegraf:" + str(telegrafInstallFlag))
        if (telegrafInstallFlag.lower() == "y"):
            telegrafInstallFlag = "y"
        else:
            telegrafInstallFlag = "n"

        print(telegrafInstallFlag)
        #        cr8InstallFlag = input("Do you want to install cr8? yes(y)/no(n) [n]: ")
        #        logger.info("Selected answer cr8:" + str(cr8InstallFlag))
        #        if (cr8InstallFlag.lower() == "y"):
        #            cr8InstallFlag = True
        #        else:
        #            cr8InstallFlag = False

        confirmInstall = str(input(Fore.YELLOW + "Are you sure want to install DI servers (y/n) [y]: " + Fore.RESET))
        if (len(str(confirmInstall)) == 0):
            confirmInstall = 'y'
        if (confirmInstall == 'y'):
            buildTarFileToLocalMachine(host)
            buildUploadInstallTarToServer(host)
            executeCommandForInstall(host, 'SingleNode', 0)

    except Exception as e:
        handleException(e)


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

    kafkaBrokerHost1 = str(os.getenv("di1"))#str(input(Fore.YELLOW + "Enter kafka broker 1a host  :" + Fore.RESET))
    #while (len(kafkaBrokerHost1) == 0):
    #    kafkaBrokerHost1 = str(input(Fore.YELLOW + "Enter kafka broker 1a host  :" + Fore.RESET))
    logger.info("kafkaBrokerHost1 : " + str(kafkaBrokerHost1))
    kafkaBrokerHost3 = str(os.getenv("di3"))#str(input(Fore.YELLOW + "Enter kafka broker 2 host :" + Fore.RESET))
    #while (len(kafkaBrokerHost3) == 0):
    #    kafkaBrokerHost3 = str(input(Fore.YELLOW + "Enter kafka broker 2 host :" + Fore.RESET))
    logger.info("kafkaBrokerHost3 : " + str(kafkaBrokerHost3))
    zkWitnessHost = str(os.getenv("di4"))#str(input(Fore.YELLOW + "Enter Zookeeper WitnessHost :" + Fore.RESET))
    #while (len(zkWitnessHost) == 0):
    #    zkWitnessHost = str(input(Fore.YELLOW + "Enter Zookeeper WitnessHost :" + Fore.RESET))
    logger.info("zkWitnessHost :" + str(zkWitnessHost))
    kafkaBrokerHost2 = str(os.getenv("di2"))#str(input(Fore.YELLOW + "Enter kafka broker 1b host :" + Fore.RESET))
    #while (len(kafkaBrokerHost2) == 0):
    #    kafkaBrokerHost2 = str(input(Fore.YELLOW + "Enter kafka broker 1b host :" + Fore.RESET))
    logger.info("kafkaBrokerHost2 : " + str(kafkaBrokerHost2))
    verboseHandle.printConsoleWarning("1. kafka broker 1a host :"+kafkaBrokerHost1+"\n2. kafka broker 1b host :"+kafkaBrokerHost2+"\n3. kafka broker 2 host :"+kafkaBrokerHost3+"\n4. Zookeeper WitnessHost :"+zkWitnessHost)
    #user = str(input(Fore.YELLOW + "Enter user to connect DI servers [root]:" + Fore.RESET))
    #if (len(str(user)) == 0):
    user = "root"
    logger.info(" user: " + str(user))
    baseFolderLocation = str(input(Fore.YELLOW + "Enter installation base folder for Kafka and Zookeeper [/opt/Kafka/]:" + Fore.RESET))
    if (len(str(baseFolderLocation)) == 0):
        baseFolderLocation = "/opt/Kafka/"
    dataFolderKafka = str(input(Fore.YELLOW + "Enter data folder for Kafka [/data/kafka-data/]:" + Fore.RESET))
    if (len(str(dataFolderKafka)) == 0):
        dataFolderKafka = "/data/kafka-data/"
    logger.info(" dataFolderKafka: " + str(dataFolderKafka))
    dataFolderZK = str(input(Fore.YELLOW + "Enter data folder for Zookeeper [/data/zookeeper/]:" + Fore.RESET))
    if (len(str(dataFolderZK)) == 0):
        dataFolderZK = "/data/zookeeper/"
    logger.info(" dataFolderZK: " + str(dataFolderZK))
    logsFolderKafka = str(input(Fore.YELLOW + "Enter base logs folder for kafka [/data/kafka-logs/]:" + Fore.RESET))
    if (len(str(logsFolderKafka)) == 0):
        logsFolderKafka = "/data/kafka-logs/"
    logger.info(" logsFolderKafka: " + str(logsFolderKafka))
    logsFolderZK = str(input(Fore.YELLOW + "Enter base logs folder for kafka [/data/zookeeper-logs/]:" + Fore.RESET))
    if (len(str(logsFolderZK)) == 0):
        logsFolderZK = "/data/zookeeper-logs/"
    logger.info(" logsFolderZK: " + str(logsFolderZK))

    #  telegrafInstallFlag = input("Do you want to install telegraf? yes(y)/no(n) [n]: ")
    #  logger.info("Selected answer telegraf:" + str(telegrafInstallFlag))
    #  if (telegrafInstallFlag.lower() == "y"):
    #      telegrafInstallFlag = "y"
    #  else:
    #     telegrafInstallFlag = "n"

    #  print(telegrafInstallFlag)
    #    cr8InstallFlag = input("Do you want to install cr8? yes(y)/no(n) [n]: ")
    #    logger.info("Selected answer cr8:" + str(cr8InstallFlag))
    #    if (cr8InstallFlag.lower() == "y"):
    #        cr8InstallFlag = True
    #    else:
    #        cr8InstallFlag = False

    clusterHosts.append(kafkaBrokerHost1)
    clusterHosts.append(kafkaBrokerHost2)
    clusterHosts.append(kafkaBrokerHost3)
    clusterHosts.append(zkWitnessHost)

    host_type_dictionary_obj = obj_type_dictionary()
    host_type_dictionary_obj.add(kafkaBrokerHost1, 'kafka Broker 1a')
    host_type_dictionary_obj.add(kafkaBrokerHost2, 'kafka Broker 1b')
    host_type_dictionary_obj.add(kafkaBrokerHost3, 'kafka Broker 2')
    host_type_dictionary_obj.add(zkWitnessHost, 'Zookeeper Witness')
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
            executeCommandForInstall(host, host_type_dictionary_obj.get(host), counter)
            counter = counter + 1


def buildTarFileToLocalMachine(host):
    logger.info("buildTarFileToLocalMachine :" + str(host))
    cmd = 'tar -cvf install/install.tar install'  # Creating .tar file on Pivot machine
    with Spinner():
        status = os.system(cmd)
        logger.info("Creating tar file status : " + str(status))


def buildUploadInstallTarToServer(host):
    logger.info("buildUploadInstallTarToServer(): start host :" + str(host))
    try:
        with Spinner():
            logger.info("hostip ::" + str(host) + " user :" + str(user))
            scp_upload(host, user, 'install/install.tar', '/home/dbsh')
    except Exception as e:
        handleException(e)


def executeCommandForInstall(host, type, count):
    logger.info("executeCommandForInstall(): start host : " + str(host) + " type : " + str(type))

    try:
        # cmd = "java -version"
        # outputVersion = executeRemoteCommandAndGetOutputPython36(host,user,cmd)
        # print("output java version :"+str(outputVersion))
        commandToExecute = "scripts/servers_di_install.sh"
        additionalParam = ""
        additionalParam = telegrafInstallFlag + ' '
        if (len(clusterHosts) == 4):
            additionalParam = additionalParam + kafkaBrokerHost1 + ' ' + kafkaBrokerHost2 + ' ' + kafkaBrokerHost3 + ' ' + zkWitnessHost + ' ' + str(count) + ' ' + str(baseFolderLocation)+ ' ' + str(dataFolderKafka)+ ' ' + str(dataFolderZK)+ ' ' + str(logsFolderKafka)+ ' ' + str(logsFolderZK)

        logger.info("Additional Param:" + additionalParam + " cmdToExec:" + commandToExecute + " Host:" + str(
            host) + " User:" + str(user))
        print(additionalParam)
        with Spinner():
            outputShFile = connectExecuteSSH(host, user, commandToExecute, additionalParam)
            logger.info("outputShFile kafka : " + str(outputShFile))
            print("Checking for Type ::::" + str(type))

            #if (cr8InstallFlag == "y" and (type== 'Master' or type == 'Standby' or type == 'SingleNode')):
            #   verboseHandle.printConsoleInfo("Starting CR8 installation for "+str(type))
            #   logger.info("Installing cr8 for "+str(type))
            #    commandToExecute="scripts/servers_di_install_cr8.sh"
            #    outputShFile= connectExecuteSSH(host, user,commandToExecute,'')
            #    logger.info("outputShFile CR8 :"+str(outputShFile))
            #    logger.info("Done installation of cr8 for "+str(type))

            #config_add_dataIntegration_node(host, host, "dataIntegration", type)
            #set_value_in_property_file('app.di.hosts', host)
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
    cmd = 'find ' + str(home) + '/install/java/ -name *.rpm -printf "%f\n"'  # Checking .rpm file on Pivot machine
    javaRpm = executeLocalCommandAndGetOutput(cmd)
    logger.info("javaRpm found :" + str(javaRpm))
    cmd = 'find ' + str(home) + '/install/kafka/ -name *.tgz -printf "%f\n"'  # Checking .tgz file on Pivot machine
    kafkaZip = executeLocalCommandAndGetOutput(cmd)
    logger.info("kafkaZip found :" + str(kafkaZip))
    cmd = 'find ' + str(home) + '/install/zookeeper/ -name *.tar.gz -printf "%f\n"'  # Checking .tar.gz file on Pivot machine
    zkZip = executeLocalCommandAndGetOutput(cmd)
    logger.info("ZookeeperZip found :" + str(zkZip))
    #cmd = 'find ' + str(home) + '/install/cr8/ -name *.rpm -printf "%f\n"'  # Checking .tar file on Pivot machine
    #cr8Rpm = executeLocalCommandAndGetOutput(cmd)
    #logger.info("cr8Rpm found :" + str(cr8Rpm))
    #cmd = 'find ' + str(home) + '/install/cr8/ -name *.gz -printf "%f\n"'  # Checking .tar file on Pivot machine
    #localSetupZip = executeLocalCommandAndGetOutput(cmd)
    #logger.info("localSetupZip found :" + str(localSetupZip))
    cmd = 'find ' + str(home) + '/install/telegraf/ -name *.rpm -printf "%f\n"'  # Checking .rpm file on Pivot machine
    telegrafRpm = executeLocalCommandAndGetOutput(cmd)
    logger.info("telegrafRpm found :" + str(telegrafRpm))

    di_installer_dict = obj_type_dictionary()
    di_installer_dict.add('Java', javaRpm)
    di_installer_dict.add('KafkaZip', kafkaZip)
    di_installer_dict.add('zkZip', zkZip)
    #di_installer_dict.add('CR8Rpm', cr8Rpm)
    #di_installer_dict.add('CR8-LocalSetupZip', localSetupZip)
    di_installer_dict.add('Telegraf', telegrafRpm)

    for name, installer in di_installer_dict.items():
        if (len(str(installer)) == 0):
            verboseHandle.printConsoleInfo(
                "Pre-requisite installer " + str(home) + "/install  " + str(name) + " not found")
            return False
    return True


def addNodeToCluster(nodes):
    logger.info("addNodeToCluster()")
    nodeList = config_get_dataIntegration_nodes()
    global masterHost
    global standByHost
    global witnessHost

    for node in nodeList:
        if (str(node.type) == 'Master'):
            masterHost = str(node.ip)
        if (str(node.type) == 'Standby'):
            standByHost = str(node.ip)
        if (str(node.type) == 'Witness'):
            witnessHost = str(node.ip)
    if (len(str(masterHost)) == 0):
        masterHost = str(input(Fore.YELLOW + "Enter Kafka broker 1a  :" + Fore.RESET))
        while (len(masterHost) == 0):
            masterHost = str(input(Fore.YELLOW + "Enter Kafka broker 1a  :" + Fore.RESET))
    logger.info("Kafka broker 1a : " + str(masterHost))
    if (len(str(standByHost)) == 0):
        standByHost = str(input(Fore.YELLOW + "Enter Kafka broker 1b :" + Fore.RESET))
        while (len(standByHost) == 0):
            standByHost = str(input(Fore.YELLOW + "Enter Kafka broker 1b :" + Fore.RESET))
    logger.info("Kafka broker 1b : " + str(standByHost))
    if (len(str(witnessHost)) == 0):
        witnessHost = str(input(Fore.YELLOW + "Enter Kafka broker 2 :" + Fore.RESET))
        while (len(witnessHost) == 0):
            witnessHost = str(input(Fore.YELLOW + "Enter Kafka broker 2 :" + Fore.RESET))
        logger.info("Kafka broker 2 :" + str(witnessHost))
    user = str(input(Fore.YELLOW + "Enter user to connect DI servers [root]:" + Fore.RESET))


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> DI -> Install')
    try:
        if (validateRPM()):
            diServerType = getDIServerTypeInstall()
            logger.info("diServerInstallType : " + str(diServerType))
            if (diServerType != '99'):
                if (diServerType == '1'):
                    print("single Host")
                    installSingle()
                if (diServerType == '2'):
                    print("cluster Host")
                    nodes = getDIServerHostList()
                    # nodesCount = nodes.split(',')
                    # logger.info("node Count :"+str(nodesCount))
                    # if(len(nodesCount)<3):
                    #    addNodeToCluster(nodes)
                    # else:
                    #    installCluster()
                    installCluster()
        else:
            logger.info("No valid rpm found")

    except Exception as e:
        handleException(e)
