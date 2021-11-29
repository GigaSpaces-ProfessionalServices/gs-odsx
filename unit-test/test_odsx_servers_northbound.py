#!/usr/bin/env python3

import os
import platform
from os import path
from utils.ods_app_config import set_value_in_property_file, readValuefromAppConfig
from colorama import Fore
from scripts.spinner import Spinner
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_add_nb_node, config_get_nb_list, config_remove_nb_streamByNameIP
from utils.ods_scp import scp_upload
from utils.ods_ssh import connectExecuteSSH, executeRemoteCommandAndGetOutput,executeRemoteCommandAndGetOutputPython36
from utils.odsx_read_properties_file import createPropertiesMapFromFile
from utils.ods_ssh import executeRemoteShCommandAndGetOutput
from scripts.odsx_servers_northbound_install import install_packages_to_nb_servers

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR

ip = "18.222.185.155"

def isValidHost(host):
    current_os = platform.system().lower()
    if current_os == "windows":
        parameter = "-n"
    else:
        parameter = "-c"
    exit_code = os.system(f"ping {parameter} 1 -w2 {ip} > /dev/null 2>&1")
    if(exit_code==0):
        return True
    else:
        return False

def update_app_config_file(linePatternToReplace, value, lines1):
    if lines1 == None:
        file_name = "csv/nb.conf.template"
        lines = open(file_name, 'r').readlines()
    else:
        lines = lines1
    lineNo = -1
    for line in lines:
        lineNo = lineNo + 1
        # if line.startswith("#") or line.startswith("\n"):
        #    continue
        # else:
        #    print(line)
        if line.startswith(linePatternToReplace):
            print(linePatternToReplace + '"' + value + '"')
            break
    lines[lineNo] = ""
    lines[lineNo] = linePatternToReplace + '"' + value + '"\n'

    out = open("config/nb.conf", 'w')
    out.writelines(lines)
    out.close()
    return lines

def upload_packages_to_nb_servers(hostip,nb_user,confirmServerInstall,confirmAgentInstall,confirmManagementInstall):
    remotePath = "/dbagiga"
    remotePath = remotePath + "/nb-infra"
    cmd = 'mkdir -p '+remotePath+'; chmod 777 /dbagiga'
    logger.info("cmd :"+str(cmd))
    with Spinner():
        output = executeRemoteCommandAndGetOutput(hostip, nb_user, cmd)
        logger.info("Created directory "+str(remotePath))
    logger.info("hostip : "+str(hostip))

    logger.info("Building .tar file : tar -cvf install/install.tar install")
    cmd = 'cp config/nb.conf install/nb/;tar -cvf install/install.tar install' # Creating .tar file on Pivot machine
    with Spinner():
        status = os.system(cmd)
        logger.info("Creating tar file status : "+str(status))
    with Spinner():
        logger.info("hostip ::"+str(hostip)+" user :"+str(nb_user)+" remotePath: "+str(remotePath))
        scp_upload(hostip, nb_user, 'install/install.tar', '')

    commandToExecute="scripts/servers_northbound_preinstall.sh"
    additionalParam='/dbagiga'
    print(additionalParam)
    logger.info("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(hostip)+" User:"+str(nb_user))
    with Spinner():
        outputShFile= executeRemoteShCommandAndGetOutput(hostip, nb_user, additionalParam, commandToExecute)
        logger.info("Output Agent"+str(outputShFile))

def test_case_1(ip):
    logger.info("Test-Case-1 : ip:"+ip)
    if(isValidHost(ip)):
        print(Fore.LIGHTYELLOW_EX+"Test-case-1:"+Fore.YELLOW+" Host / IP reachable or not :"+Fore.GREEN+"Pass "+Fore.RESET)
        logger.info("Test-Case-1: PASS Valid IP.")
    else:
        logger.info("Test-Case-1: FAIL : Invalid IP")
        print(Fore.LIGHTYELLOW_EX+"Test-case-1:"+Fore.YELLOW+" Host / IP reachable or not :"+Fore.RED+"Fail "+Fore.RESET)

def test_case_2(ip,nb_user,remotePath,nb_server,nb_agent,nb_management,nb_ops,confirmServerInstall,confirmAgentInstall,confirmManagementInstall):
    logger.info("Test-Case-2 : ip:"+ip+" User:"+nb_user)
    nb_server = nb_server.replace('"','').split(',')
    managerHostip=''
    if(confirmServerInstall=='y'):
        for hostip in nb_server:
            managerHostip=hostip
            upload_packages_to_nb_servers(hostip,nb_user,confirmServerInstall,confirmAgentInstall,confirmManagementInstall)
            remotePath = remotePath+"/nb-infra/"
            install_packages_to_nb_servers(nb_user, remotePath, confirmServerInstall, confirmAgentInstall, confirmManagementInstall)
    #if(server.role == 'agent'):
    #    cmd = "systemctl status consul.service"
    if(confirmServerInstall=='y'):
        cmd = 'systemctl status northbound.target'
        logger.info("Getting status.. :"+str(cmd))
        user = 'root'
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(managerHostip, user, cmd)
        logger.info(cmd+" :"+str(output))
        if(output ==0):
            print(Fore.LIGHTYELLOW_EX+"Test-case-2:"+Fore.YELLOW+" Installation NB-Server :"+Fore.GREEN+"Pass "+Fore.RESET)
            logger.info("Test-Case-2: PASS : Installation NB-Server successfull.")
            return 0
        else:
            print(Fore.LIGHTYELLOW_EX+"Test-case-2:"+Fore.YELLOW+" Installation NB-Server :"+Fore.RED+"Fail "+Fore.RESET)
            logger.info("Test-case-2: FAIL : Installation NB-Server")
            return 1

def test_case_3(ip,nb_user,remotePath,nb_server,nb_agent,nb_management,nb_ops,confirmServerInstall,confirmAgentInstall,confirmManagementInstall):
    logger.info("Test-Case-3 : ip:"+ip+" User:"+nb_user)
    nb_agent = nb_agent.replace('"','').split(',')
    print(nb_agent)
    agentHostip=''
    if(confirmAgentInstall=='y'):
        for hostip in nb_agent:
            agentHostip=hostip
            upload_packages_to_nb_servers(hostip,nb_user,confirmServerInstall,confirmAgentInstall,confirmManagementInstall)
            remotePath = remotePath+"/nb-infra/"
            connectExecuteSSH(hostip, nb_user, "scripts/servers_northbound_install.sh", remotePath + " --agent")
    #if(server.role == 'agent'):
    #    cmd = "systemctl status consul.service"
    if(confirmAgentInstall=='y'):
        cmd = 'systemctl status consul.service'
        logger.info("Getting status.. :"+str(cmd))
        user = 'root'
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(agentHostip, user, cmd)
        logger.info(cmd+" :"+str(output))
        if(output ==0):
            print(Fore.LIGHTYELLOW_EX+"Test-case-3:"+Fore.YELLOW+" Installation NB-Agent :"+Fore.GREEN+"Pass "+Fore.RESET)
            logger.info("Test-Case-3: PASS : Installation NB-Agent successfull.")
            return 0
        else:
            print(Fore.LIGHTYELLOW_EX+"Test-case-3:"+Fore.YELLOW+" Installation NB-Agent :"+Fore.RED+"Fail "+Fore.RESET)
            logger.info("Test-case-3: FAIL : Installation NB-Agent")
            return 1

def test_case_4(ip,user,remotePath,nb_server,nb_agent,nb_management,nb_ops,confirmServerInstall,confirmAgentInstall,confirmManagementInstall):
    if(confirmServerInstall=='y'):
        nb_server = nb_server.replace('"','').split(',')
        managerHostip=''
        finalStartStatus = ''
        for hostip in nb_server:
            cmd = 'systemctl start northbound.target'
            logger.info("Getting status.. :"+str(cmd))
            user = 'root'
            with Spinner():
                output = executeRemoteCommandAndGetOutputPython36(hostip, user, cmd)
                if(output!=0):
                    finalStartStatus='false'
        if(finalStartStatus!='false'):
            print(Fore.LIGHTYELLOW_EX+"Test-case-4:"+Fore.YELLOW+" Start NB-Server :"+Fore.GREEN+"Pass "+Fore.RESET)
            logger.info("Test-Case-4: PASS : Start NB-Server successfull.")
            return 0
        else:
            print(Fore.LIGHTYELLOW_EX+"Test-case-4:"+Fore.YELLOW+" Start NB-Server :"+Fore.RED+"Fail "+Fore.RESET)
            logger.info("Test-case-4: FAIL : Start NB-Server")
            return 1

def test_case_5(ip,user,remotePath,nb_server,nb_agent,nb_management,nb_ops,confirmServerInstall,confirmAgentInstall,confirmManagementInstall):
    if(confirmAgentInstall=='y'):
        nb_agent = nb_agent.replace('"','').split(',')
        managerHostip=''
        finalStartStatus = ''
        for hostip in nb_agent:
            cmd = 'systemctl start consul.service'
            logger.info("Getting status.. :"+str(cmd))
            user = 'root'
            with Spinner():
                output = executeRemoteCommandAndGetOutputPython36(hostip, user, cmd)
                if(output!=0):
                    finalStartStatus='false'
        if(finalStartStatus!='false'):
            print(Fore.LIGHTYELLOW_EX+"Test-case-4:"+Fore.YELLOW+" Start NB-Server :"+Fore.GREEN+"Pass "+Fore.RESET)
            logger.info("Test-Case-5: PASS : Start NB-Server successfull.")
            return 0
        else:
            print(Fore.LIGHTYELLOW_EX+"Test-case-4:"+Fore.YELLOW+" Start NB-Server :"+Fore.RED+"Fail "+Fore.RESET)
            logger.info("Test-case-5: FAIL : Start NB-Server")
            return 1

def test_case_6(ip,user,remotePath,nb_server,nb_agent,nb_management,nb_ops,confirmServerInstall,confirmAgentInstall,confirmManagementInstall):
    if(confirmAgentInstall=='y'):
        nb_agent = nb_agent.replace('"','').split(',')
        managerHostip=''
        finalStartStatus = ''
        for hostip in nb_agent:
            cmd = 'systemctl start consul.service'
            logger.info("Getting status.. :"+str(cmd))
            user = 'root'
            with Spinner():
                output = executeRemoteCommandAndGetOutputPython36(hostip, user, cmd)
                if(output!=0):
                    finalStartStatus='false'
        if(finalStartStatus!='false'):
            print(Fore.LIGHTYELLOW_EX+"Test-case-4:"+Fore.YELLOW+" Start NB-Server :"+Fore.GREEN+"Pass "+Fore.RESET)
            logger.info("Test-Case-5: PASS : Start NB-Server successfull.")
            return 0
        else:
            print(Fore.LIGHTYELLOW_EX+"Test-case-4:"+Fore.YELLOW+" Start NB-Server :"+Fore.RED+"Fail "+Fore.RESET)
            logger.info("Test-case-5: FAIL : Start NB-Server")
            return 1


def test_case_7(ip,user,remotePath,nb_server,nb_agent,nb_management,nb_ops,confirmServerInstall,confirmAgentInstall,confirmManagementInstall):
    if(confirmServerInstall=='y'):
        nb_server = nb_server.replace('"','').split(',')
        managerHostip=''
        finalStartStatus = ''
        for hostip in nb_server:
            connectExecuteSSH(hostip, "root", "scripts/servers_northbound_remove.sh", remotePath+"/nb-infra" + " --uninstall")
            config_remove_nb_streamByNameIP(hostip,hostip)

    if(confirmAgentInstall=='y'):
        nb_agent = nb_agent.replace('"','').split(',')
        managerHostip=''
        finalStartStatus = ''
        for hostip in nb_agent:
            connectExecuteSSH(hostip, "root", "scripts/servers_northbound_remove.sh", remotePath+"/nb-infra" + " --uninstall")
            config_remove_nb_streamByNameIP(hostip,hostip)

if __name__ == '__main__':
    ip = "54.155.204.21"
    user="root"
    nb_server = "10.0.0.110"
    consul_replica_number = '3'
    remotePath = "/dbagiga"

    nb_domain='example.gigaspaces.com'
    ssl_certificate = 'server.crt'
    ssl_private_key = 'server.key'
    ssl_ca_certificate = 'cacert.crt'
    nb_agent = "10.0.0.109"
    nb_management = "10.0.0.8"
    nb_ops = "10.0.0.146"
    gridui_servers = nb_ops
    opsmanager_servers = nb_ops
    nbConfig = createPropertiesMapFromFile("config/nb.conf")

    confirmServerInstall = "y"
    confirmAgentInstall = 'y'
    confirmManagementInstall = 'n'

    lines = update_app_config_file("consul_servers=".upper(), nb_server, None)
    lines = update_app_config_file("consul_replica_number=".upper(), consul_replica_number, lines)
    lines = update_app_config_file("nb_domain=".upper(), nb_domain, lines)
    lines = update_app_config_file("ssl_certificate=".upper(), ssl_certificate, lines)
    lines = update_app_config_file("ssl_private_key=".upper(), ssl_private_key, lines)
    lines = update_app_config_file("ssl_ca_certificate=".upper(), ssl_ca_certificate, lines)
    lines = update_app_config_file("gridui_servers=".upper(), gridui_servers, lines)
    update_app_config_file("opsmanager_servers=".upper(), opsmanager_servers, lines)

    test_case_1(ip)
    test_case_2(ip,user,remotePath,nb_server,nb_agent,nb_management,nb_ops,confirmServerInstall,confirmAgentInstall,confirmManagementInstall)
    test_case_3(ip,user,remotePath,nb_server,nb_agent,nb_management,nb_ops,confirmServerInstall,confirmAgentInstall,confirmManagementInstall)
    #test_case_4(ip,user,remotePath,nb_server,nb_agent,nb_management,nb_ops,confirmServerInstall,confirmAgentInstall,confirmManagementInstall)
    #test_case_5(ip,user,remotePath,nb_server,nb_agent,nb_management,nb_ops,confirmServerInstall,confirmAgentInstall,confirmManagementInstall)
    test_case_6(ip,user,remotePath,nb_server,nb_agent,nb_management,nb_ops,confirmServerInstall,confirmAgentInstall,confirmManagementInstall)
    test_case_7(ip,user,remotePath,nb_server,nb_agent,nb_management,nb_ops,confirmServerInstall,confirmAgentInstall,confirmManagementInstall)