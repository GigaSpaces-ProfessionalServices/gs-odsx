#!/usr/bin/env python3
import  os
import subprocess
import platform
from colorama import Fore
from utils.ods_ssh import executeRemoteShCommandAndGetOutput
from scripts.spinner import Spinner
from scripts.logManager import LogManager

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR

def test_case_1(ip):
    logger.info("Test-Case-1 : ip:"+ip)
    if(isValidHost(ip)):
        print(Fore.LIGHTYELLOW_EX+"Test-case-1:"+Fore.YELLOW+" Host / IP reachable or not :"+Fore.GREEN+"Pass "+Fore.RESET)
        logger.info("Test-Case-1: PASS Valid IP.")
    else:
        logger.info("Test-Case-1: FAIL : Invalid IP")
        print(Fore.LIGHTYELLOW_EX+"Test-case-1:"+Fore.YELLOW+" Host / IP reachable or not :"+Fore.RED+"Fail "+Fore.RESET)
def test_case_2(ip,user):
    logger.info("Test-Case-2 : ip:"+ip+" User:"+user)
    airGap='false' #1 Param  AirGap mode
    targetDir='/home/ec2-user/gs'   #2 param target dir
    gs_clusterhosts='172.31.32.69' #3 param if cluster then should be comma seperated
    openJdkVersion='11' #4 param  Java Version 8/11
    gsType='xap'  #5 param  xap / insightedge
    gsVersion='15.8.0' #6 param  gs version
    additionalParam=airGap+' '+targetDir+' '+gs_clusterhosts+' '+openJdkVersion+' '+gsType+' '+gsVersion
    logger.info("Params :"+additionalParam)
    with Spinner():
        if(isValidHost(ip)):
            logger.info("Test-Case-2: Valid IP")
            try:
                cmdFile='scripts/servers_manager_install.sh > /dev/null 2>&1'
                logger.info("cmdFile :"+cmdFile)
                output = executeRemoteShCommandAndGetOutput(ip,user,additionalParam,cmdFile)
                print(Fore.LIGHTYELLOW_EX+"Test-case-2:"+Fore.YELLOW+" manager installation :"+Fore.GREEN+" Pass "+Fore.RESET)
                logger.info("Test-Case-2: PASS : Manager installation ")
            except Exception as e:
                logger.info("Test-Case-2: FAIL : Manager installation ")
                print(Fore.LIGHTYELLOW_EX+"Test-case-2:"+Fore.YELLOW+" manager installation :"+Fore.RED+" Fail "+Fore.RESET)
        else:
            logger.info("Test-Case-2: FAIL : Manager installation. ")
            print(Fore.LIGHTYELLOW_EX+"Test-case-2:"+Fore.YELLOW+" manager installation :"+Fore.RED+" Fail "+Fore.RESET)
def test_case_3(ip,user):
    logger.info("Test-Case-3 : IP:"+ip+" User:"+user)
    airGap='false' #1 Param  AirGap mode
    noGSC='2'
    additionalParam=airGap+' '+noGSC
    with Spinner():
        if(isValidHost(ip)):
            try:
                cmdFile='scripts/servers_manager_start.sh > /dev/null 2>&1'
                output = executeRemoteShCommandAndGetOutput(ip,user,additionalParam,cmdFile)
                print(Fore.LIGHTYELLOW_EX+"Test-case-3:"+Fore.YELLOW+" manager start :"+Fore.GREEN+" Pass "+Fore.RESET)
                logger.info("Test-Case-3: PASS : Manager start. ")
            except Exception as e:
                print(Fore.LIGHTYELLOW_EX+"Test-case-3:"+Fore.YELLOW+" manager start :"+Fore.RED+" Fail "+Fore.RESET)
                logger.info("Test-Case-3: FAIL : Manager start. ")
        else:
            logger.info("Test-Case-3: FAIL : Manager start. ")
            print(Fore.LIGHTYELLOW_EX+"Test-case-3:"+Fore.YELLOW+" manager start :"+Fore.RED+" Fail "+Fore.RESET)

def test_case_4(ip,user):
    logger.info("Test-Case-4 : IP:"+ip+" User:"+user)
    airGap = 'false'
    additionalParam=airGap+' '

    with Spinner():
        if(isValidHost(ip)):
            try:
                cmdFile='scripts/servers_manager_stop.sh > /dev/null 2>&1'
                output = executeRemoteShCommandAndGetOutput(ip,user,additionalParam,cmdFile)
                print(Fore.LIGHTYELLOW_EX+"Test-case-4:"+Fore.YELLOW+" manager stop :"+Fore.GREEN+" Pass "+Fore.RESET)
                logger.info("Test-Case-4: PASS : Manager stop. ")
            except Exception as e:
                print(Fore.LIGHTYELLOW_EX+"Test-case-4:"+Fore.YELLOW+" manager stop :"+Fore.RED+" Fail "+Fore.RESET)
                logger.info("Test-Case-4: FAIL : Manager stop. ")
        else:
            print(Fore.LIGHTYELLOW_EX+"Test-case-4:"+Fore.YELLOW+" manager stop :"+Fore.RED+" Fail "+Fore.RESET)
            logger.info("Test-Case-4: FAIL : Manager stop. ")

def test_case_5(ip,user):
    logger.info("Test-Case-5 : IP:"+ip+" User:"+user)
    airGap = 'false'
    additionalParam=airGap+' '

    with Spinner():
        if(isValidHost(ip)):
            try:
                cmdFile='scripts/servers_manager_remove.sh' # > /dev/null 2>&1
                output = executeRemoteShCommandAndGetOutput(ip,user,additionalParam,cmdFile)
                print(Fore.LIGHTYELLOW_EX+"Test-case-5:"+Fore.YELLOW+" manager remove :"+Fore.GREEN+" Pass "+Fore.RESET)
                logger.info("Test-Case-5: PASS : Manager remove. ")
            except Exception as e:
                print(Fore.LIGHTYELLOW_EX+"Test-case-5:"+Fore.YELLOW+" manager remvoe :"+Fore.RED+" Fail "+Fore.RESET)
                logger.info("Test-Case-5: FAIL : Manager remove. ")
        else:
            print(Fore.LIGHTYELLOW_EX+"Test-case-5:"+Fore.YELLOW+" manager remove :"+Fore.RED+" Fail "+Fore.RESET)
            logger.info("Test-Case-5: FAIL : Manager remove. ")


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

if __name__ == '__main__':
    ip = "3.21.166.237"
    user="ec2-user"
    test_case_1(ip)
    test_case_2(ip,user)
    test_case_3(ip,user)
    test_case_4(ip,user)
    test_case_5(ip,user)
