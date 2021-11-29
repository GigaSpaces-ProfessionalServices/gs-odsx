#!/usr/bin/env python3
# s6.py
#!/usr/bin/python
import  os
from utils.ods_ssh import executeRemoteShCommandAndGetOutput
import platform
from colorama import Fore
from scripts.logManager import LogManager

#HOST='18.116.237.91'#
HOST='3.21.166.237'
user='ec2-user'
osuser='dbsh'
password='x'

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

def test_case_1():
    logger.info("Test-Case-1")
    if(isValidHost(HOST)):
        print(Fore.LIGHTYELLOW_EX+"Test-case-1: "+Fore.YELLOW+"Host is reachable or not : "+Fore.GREEN+"Pass"+Fore.RESET)
    else:
        print(Fore.LIGHTYELLOW_EX+"Test-case-1: "+Fore.YELLOW+"Host is reachable or not : "+Fore.RED+"Fail"+Fore.RESET)

def test_case_2():
    logger.info("Test-Case-2: Command is available to pause stream or not")
    osuser='dbsh'
    password=''
    additionalParam=osuser+' '+password
    cmdFile = "unit-test/test_odsx_streams_startonline.sh"
    logger.info("cmdFile:"+cmdFile)
    logger.info("params:"+additionalParam)
    output = executeRemoteShCommandAndGetOutput(HOST,user,additionalParam,cmdFile)
    if(str(output).__contains__('True')):
        print(Fore.LIGHTYELLOW_EX+"Test-case-2: "+Fore.YELLOW+" Command is available to start stream : "+Fore.GREEN+"Pass"+Fore.RESET)
        logger.info("Test-case-2: Command is available to start stream : Pass")
    elif(str(output).__contains__('False')):
        print(Fore.LIGHTYELLOW_EX+"Test-case-2: "+Fore.YELLOW+" Command is available to start stream : "+Fore.RED+"Fail"+Fore.RESET)
        logger.info('Test-case-2: Command is available to start stream: Fail')

def test_case_3():
    logger.info("Test-Case-3")
    streamConfigName='bll_db2_gs'
    additionalParam=osuser+' '+password+' '+streamConfigName
    cmdFile = "scripts/streams_startonline.sh"
    logger.info("params:"+additionalParam)
    output = executeRemoteShCommandAndGetOutput(HOST,user,additionalParam,cmdFile)
    if(str(output).casefold().__contains__('already running') or str(output).casefold().__contains__('started')):
        print(Fore.LIGHTYELLOW_EX+"Test-case-3:"+Fore.YELLOW+" start stream : "+Fore.GREEN+"Pass"+Fore.RESET)
        logger.info("Test-case-3: start stream : Pass")
    else:
        print(Fore.LIGHTYELLOW_EX+"Test-case-3:"+Fore.YELLOW+" start stream : "+Fore.RED+"Fail"+Fore.RESET)
        logger.info("Test-case-3: start stream : Fail")

def test_case_4():
    logger.info("Test-Case-4")
    streamConfigName='bll_db2_gs'
    additionalParam=osuser+' '+password+' '+streamConfigName
    cmdFile = "scripts/streams_status.sh"
    logger.info("params:"+additionalParam)
    output = executeRemoteShCommandAndGetOutput(HOST,user,additionalParam,cmdFile)
    if(str(output).casefold().__contains__('is running')):
        print(Fore.LIGHTYELLOW_EX+"Test-case-4:"+Fore.YELLOW+" stream running: "+Fore.GREEN+"Pass"+Fore.RESET)
        logger.info("Test-case-3: start stream : Pass")
    else:
        print(Fore.LIGHTYELLOW_EX+"Test-case-4:"+Fore.YELLOW+" stream running: "+Fore.RED+"Fail"+Fore.RESET)
        logger.info("Test-case-3: start stream : Fail")

def test_case_5():
    logger.info("Test-Case-5 - Stop stream")
    streamConfigName='bll_db2_gs'
    additionalParam='x'+' '+osuser+' '+password+' '+streamConfigName
    cmdFile = "scripts/streams_pauseonline.sh"
    logger.info("params:"+additionalParam)
    output = executeRemoteShCommandAndGetOutput(HOST,user,additionalParam,cmdFile)
    if(str(output).casefold().__contains__('been killed')):
        print(Fore.LIGHTYELLOW_EX+"Test-case-5:"+Fore.YELLOW+" stop stream: "+Fore.GREEN+"Pass"+Fore.RESET)
        logger.info("Test-case-5: stop stream : Pass")
    else:
        print(Fore.LIGHTYELLOW_EX+"Test-case-4:"+Fore.YELLOW+" stop stream : "+Fore.RED+"Fail"+Fore.RESET)
        logger.info("Test-case-5: stop stream : Fail")


def isValidHost(host):
    current_os = platform.system().lower()
    if current_os == "windows":
        parameter = "-n"
    else:
        parameter = "-c"
    exit_code = os.system(f"ping {parameter} 1 -w2 {HOST} > /dev/null 2>&1")
    if(exit_code==0):
        return True
    else:
        return False

if __name__ == '__main__':

    test_case_1()
    test_case_2()
    test_case_3()
    test_case_4()
    test_case_5()