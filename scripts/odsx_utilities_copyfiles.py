#!/usr/bin/env python3
import os
import platform

from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_manager_node, config_get_space_node, config_get_nb_list, config_get_dataIntegration_nodes
from utils.ods_scp import scp_upload

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


def getOptions():
    options = {}
    counter = 1
    options.update({counter: "All servers"})
    options.update({counter + 1: "Manager servers"})
    options.update({counter + 2: "Space servers"})
    options.update({counter + 3: "Northbound servers"})
    options.update({counter + 4: "DI servers"})
    options.update({counter + 5: "Specific servers"})
    options.update({99: "ESC"})
    return options


def validation(srcPath, destPath):
    if os.path.exists(srcPath) == False:
        verboseHandle.printConsoleError("path not exist : " + srcPath)
        logger.error("path not exist : " + srcPath)
        return False


def validateHost(hostips):
    for hostip in hostips.replace(" ", "").split(","):
        current_os = platform.system().lower()
        if current_os == "windows":
            parameter = "-n"
        else:
            parameter = "-c"
        exit_code = os.system(f"ping {parameter} 1 -w2 {hostip} > /dev/null 2>&1")
        if exit_code != 0:
            verboseHandle.printConsoleError("Host not reachable")
            logger.error("Host not reachable")
            return False
    return True


def proceedForSpecificNBServer(nodes,inputServer,ips):
    logger.info("proceedForSpecificNBServer() inputServer :"+str(inputServer))
    if inputServer == 1:
        for node in nodes:
            if (str(node.role).__contains__("applicative")):
                ips.append(os.getenv(node.ip))
    if inputServer == 2:
        for node in nodes:
            if (str(node.role).__contains__("agent")):
                ips.append(os.getenv(node.ip))
    if inputServer == 3:
        for node in nodes:
            if (str(node.role).__contains__("management")):
                ips.append(os.getenv(node.ip))
    return ips

def getServerIps(optionSelected):
    logger.info("getServerIps() : optionSelected :"+str(optionSelected))
    ips = []
    if optionSelected == 1 or optionSelected == 2:
        nodes = config_get_manager_node()
        for node in nodes:
            ips.append(os.getenv(node.ip))
    if optionSelected == 1 or optionSelected == 3:
        nodes = config_get_space_node()
        for node in nodes:
                ips.append(os.getenv(node.ip))
    if optionSelected == 1 or optionSelected == 4:
        inputServer = str(input("[1] For applicative \n[2] For agent \n[3] For management \n[Enter] For all : "))
        logger.info("inputServer :"+str(inputServer))
        nodes = config_get_nb_list()
        if inputServer == "":
            for node in nodes:
                ips.append(os.getenv(node.ip))
        else:
            ips = proceedForSpecificNBServer(nodes,int(inputServer),ips)
    if optionSelected == 1 or optionSelected == 5:
        nodes = config_get_dataIntegration_nodes()
        for node in nodes:
            ips.append(os.getenv(node.ip))
    if optionSelected == 6:
        enteredIp = input("Enter host to copy : ")
        if enteredIp == "":
            verboseHandle.printConsoleWarning("invalid host name")
            logger.error("invalid host name : " + enteredIp)
        for ip in enteredIp.split(","):
            if validateHost(ip) == False:
                exit(0)
            ips.append(ip)
    if optionSelected == 99:
        exit(0)
    return ips


def copyFile(hostips, srcPath, destPath, dryrun=False):
    username = ""
    if not dryrun:
        username = input("Enter username for host [gsods] : ")
        if username == "":
            username = "gsods"
    else:
        username = "gsods"
    for hostip in hostips:
        scp_upload(hostip, username, srcPath, destPath)
        verboseHandle.printConsoleInfo(hostip)
        logger.info("Done copying, hostip=" + hostip + ", username=" + username + ", srcPath=" + srcPath + ", destPath=" + destPath)

def showAndSelectOption():
    print("\n")
    for key, value in getOptions().items():
        print("[" + str(key) + "] " + value)
    optionSelected = input("Enter your option [1]: ")
    if optionSelected == "":
        optionSelected = 1
    elif int(optionSelected) == 99 :
        exit(0)
    elif int(optionSelected) > len(getOptions().items()):
        verboseHandle.printConsoleError("Invalid option selected")
        exit(0)
    #print(optionSelected)
    srcPath = input("Enter source file absolute path: ")
    destPath = input("Enter destination file absolute path: ")
    if srcPath == "" or destPath == "":
        verboseHandle.printConsoleError("Invalid path selected")
        logger.error("Invalid path selected")
        exit(0)
    if validation(srcPath, destPath) == False:
        exit(0)
    ips = getServerIps(int(optionSelected))
    print(ips)
    logger.info("ips to copy file: "+str(ips))
    copyFile(ips, srcPath, destPath)
    os.system('python3 scripts/odsx_utilities_copyfiles.py  m')

if __name__ == '__main__':
    logger.info("Copy files Utilities")
    verboseHandle.printConsoleWarning("Menu -> Utilities -> Copy Files")
    verboseHandle.printConsoleInfo("Copy files Utilities")
    logger.error("Copy files Utilities")
    showAndSelectOption()
