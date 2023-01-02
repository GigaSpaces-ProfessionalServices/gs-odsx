#!/usr/bin/env python3
# s6.py
#!/usr/bin/python
import os, subprocess, sys, argparse, platform
from concurrent.futures import ThreadPoolExecutor

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_ssh import executeRemoteShCommandAndGetOutput
from utils.ods_app_config import readValuefromAppConfig
from colorama import Fore
from scripts.odsx_servers_manager_list import listFileFromDirectory
from utils.ods_cluster_config import config_get_manager_listWithStatus, config_get_manager_node
from scripts.odsx_servers_manager_install import getManagerHostFromEnv
from utils.odsx_keypress import userInputWithEscWrapper, userInputWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

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

def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    parser.add_argument('--host',
                        help='host ip',
                        required='True',
                        default='localhost')
    parser.add_argument('-u', '--user',
                        help='user name',
                        default='root')
    parser.add_argument('-dryrun', '--dryrun',
                        help='Dry run flag',
                        default='false', action='store_true')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])

def execute_scriptBuilder(args):
    logger.info("execute_scriptBuilder(args)")
    args = str(args)
    logger.debug('Arguments :'+args)
    logger.info('Arguments :'+args)
    args =args.replace('[','').replace("'","").replace("]",'').replace(',','').strip()
    #print(args)
    os.system('python3 scripts/servers_manager_scriptbuilder.py '+args)
    logger.debug('python3 scripts/servers_manager_scriptbuilder.py completed :')

def exitAndDisplay(isMenuDriven):
    logger.info("exitAndDisplay(isMenuDriven)")
    if(isMenuDriven=='m'):
        logger.info("exitAndDisplay(MenuDriven) ")
        os.system('python3 scripts/odsx_servers_manager_start.py'+' '+isMenuDriven)
    else:
        cliArgumentsStr=''
        for arg in cliArguments:
            cliArgumentsStr+=arg
            cliArgumentsStr+=' '
        os.system('python3 scripts/odsx_servers_manager_start.py'+' '+cliArgumentsStr)

def startManagerServer(argsString):
    os.system('python3 scripts/servers_manager_scriptbuilder.py '+argsString)

if __name__ == '__main__':
    logger.info("servers - manager - start ")
    verboseHandle.printConsoleWarning('Menu -> Servers -> Manager -> Start')
    args = []
    menuDrivenFlag='m' # To differentiate between CLI and Menudriven Argument handling help section
    args.append(sys.argv[0])
    try:
        managerDict = config_get_manager_listWithStatus()
        hostsConfig=''
        streamResumeStream=''
        optionMainMenu=''
        choice=''
        cliArguments=''
        isMenuDriven=''
        managerRemove=''
        user='root'
        #hostsConfig = readValuefromAppConfig("app.manager.hosts")
        hostsConfig = getManagerHostFromEnv()
        logger.info("hostConfig:"+str(hostsConfig))
        hostsConfig=hostsConfig.replace('"','')
        if(len(str(hostsConfig))>0):
            verboseHandle.printConsoleWarning("Current cluster configuration : ["+hostsConfig+"] ")
        serverStartType = str(userInputWithEscWrapper(Fore.YELLOW+"press [1] if you want to start individual server. \nPress [Enter] to start current Configuration. \nPress [99] for exit.: "+Fore.RESET))
        if(serverStartType=='1'):
            optionMainMenu = int(userInputWrapper("Enter your host number to start: "))
            logger.info("Enter your host number to start:"+str(optionMainMenu))
            if(optionMainMenu != 99):
                if len(managerDict) >= optionMainMenu:
                    spaceStart = managerDict.get(optionMainMenu)
                    choice = str(userInputWrapper(Fore.YELLOW+"Are you sure want to start server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    while(len(str(choice))==0):
                        choice = str(userInputWrapper(Fore.YELLOW+"Are you sure want to start server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    #print("coice start server:"+str(choice))
                    logger.info("choice :"+str(choice))
                    if(choice.casefold()=='no' or choice.casefold()=='n'):
                        if(isMenuDriven=='m'):
                            logger.info("menudriven")
                            os.system('python3 scripts/odsx_servers_manager_start.py'+' '+isMenuDriven)
                        else:
                            exitAndDisplay(isMenuDriven)
                    elif(choice.casefold()=='yes' or choice.casefold()=='y'):
                        if len(sys.argv) > 1 and sys.argv[1] != menuDrivenFlag:
                            arguments = myCheckArg(sys.argv[1:])
                            if(arguments.dryrun==True):
                                current_os = platform.system().lower()
                                logger.debug("Current OS:"+str(current_os))
                                if current_os == "windows":
                                    parameter = "-n"
                                else:
                                    parameter = "-c"
                                exit_code = os.system(f"ping {parameter} 1 -w2 {arguments.host} > /dev/null 2>&1")
                                if(exit_code == 0):
                                    verboseHandle.printConsoleInfo("Connected to server with dryrun mode.!"+arguments.host)
                                    logger.debug("Connected to server with dryrun mode.!"+arguments.host)
                                else:
                                    verboseHandle.printConsoleInfo("Unable to connect to server."+arguments.host)
                                    logger.debug("Unable to connect to server."+arguments.host)
                                try:
                                    exit_code = executeRemoteShCommandAndGetOutput(arguments.host, arguments.user, '', 'utils/java_check.sh')
                                    if(str(exit_code).__contains__('javac')):
                                        verboseHandle.printConsoleInfo("Java Installed.")
                                    else:
                                        verboseHandle.printConsoleInfo("Java not found.")
                                except Exception as e:
                                    verboseHandle.printConsoleInfo("Java not found.")
                                try:
                                    exit_code = executeRemoteShCommandAndGetOutput(arguments.host, arguments.user, '', 'utils/gs_check.sh')
                                    if(len(str(exit_code)) > 6):
                                        verboseHandle.printConsoleInfo("Gigaspace Installed.")
                                    else:
                                        verboseHandle.printConsoleInfo("Gigaspace not found.")
                                except Exception as e:
                                    verboseHandle.printConsoleInfo("Gigaspace not found.")
                                quit()

                            for arg in sys.argv[1:]:
                                args.append(arg)
                            #print('install :',args)
                            args = str(args)
                            logger.debug('Arguments :'+args)
                        elif(sys.argv[1]==menuDrivenFlag):
                            args.append(menuDrivenFlag)
                            args.append('--host')
                            args.append(os.getenv(spaceStart.ip))
                            args.append('-u')
                            args.append(user)
                        args = str(args)
                        #print('args',args)
                        #logger.info('Menu driven flag :'+menuDrivenFlag)
                        logger.debug('Arguments :'+args)
                        args =args.replace('[','').replace("'","").replace("]",'').replace(',','').strip()
                        #print(args)
                        os.system('python3 scripts/servers_manager_scriptbuilder.py '+args)
                        #os.system('python3 scripts/remote_script_exec.py '+args)
                else:
                    verboseHandle.printConsoleError("please select valid option")
                    optionMainMenu=''
                    choice=''
                    exitAndDisplay(isMenuDriven)
            else :
                print("")
        elif(serverStartType =='99'):
            logger.info("99 - Exist start")
        else:
            confirm=''
            confirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to start all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            while(len(str(confirm))==0):
                confirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to start all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            logger.info("confirm :"+str(confirm))
            if(confirm=='yes' or confirm=='y'):
                spaceHosts = config_get_manager_node()#config_get_space_hosts_list()
                hostManagerLength=len(spaceHosts)+1
                with Spinner():
                    with ThreadPoolExecutor(hostManagerLength) as executor:
                        for host in spaceHosts:
                            args.append(menuDrivenFlag)
                            args.append('--host')
                            args.append(os.getenv(host.ip))
                            args.append('-u')
                            args.append(user)
                            argsString = str(args)
                            logger.debug('Arguments :'+argsString)
                            logger.info(argsString)
                            argsString =argsString.replace('[','').replace("'","").replace("]",'').replace(',','').strip()
                            #print(argsString)
                            # os.system('python3 scripts/servers_manager_scriptbuilder.py '+argsString)
                            executor.submit(startManagerServer,argsString)
                            args.remove(menuDrivenFlag)
                            args.remove("--host")
                            args.remove(os.getenv(host.ip))
                            args.remove('-u')
                            args.remove(user)
                            logger.info(args)
            elif(confirm =='no' or confirm=='n'):
                if(isMenuDriven=='m'):
                    logger.info("menudriven")
                    os.system('python3 scripts/odsx_servers_space_start.py'+' '+isMenuDriven)
    except Exception as e:
        handleException(e)