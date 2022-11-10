#!/usr/bin/env python3
# s6.py
#!/usr/bin/python
import os, subprocess, sys, argparse, platform
from scripts.logManager import LogManager
from utils.ods_ssh import executeRemoteShCommandAndGetOutput
from utils.ods_app_config import readValuefromAppConfig
from colorama import Fore
from scripts.odsx_servers_manager_list import listFileFromDirectory
from utils.ods_cluster_config import config_get_manager_listWithStatus, config_get_manager_node
from scripts.odsx_servers_manager_install import getManagerHostFromEnv
from utils.odsx_keypress import userInputWithEscWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR

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
        os.system('python3 scripts/odsx_security_servers_manager_start.py'+' '+isMenuDriven)
    else:
        cliArgumentsStr=''
        for arg in cliArguments:
            cliArgumentsStr+=arg
            cliArgumentsStr+=' '
        os.system('python3 scripts/odsx_security_servers_manager_start.py'+' '+cliArgumentsStr)

if __name__ == '__main__':
    logger.info("security - manager - start ")
    verboseHandle.printConsoleWarning('Menu -> Servers -> Manager -> Start')
    args = []
    menuDrivenFlag='m' # To differentiate between CLI and Menudriven Argument handling help section
    args.append(sys.argv[0])
    cliArguments=''
    isMenuDriven=''
    user='root'
    try:
        managerDict = config_get_manager_listWithStatus()
        hostsConfig=''
        #hostsConfig = readValuefromAppConfig("app.manager.hosts")
        hostsConfig = getManagerHostFromEnv()
        logger.info("hostConfig:"+str(hostsConfig))
        hostsConfig=hostsConfig.replace('"','')
        if(len(str(hostsConfig))>0):
            verboseHandle.printConsoleWarning("Current cluster configuration : ["+hostsConfig+"] ")
        serverStartType = str(userInputWithEscWrapper(Fore.YELLOW+"press [1] if you want to start individual server. \nPress [Enter] to start current Configuration. \nPress [99] for exit.: "+Fore.RESET))
        if(serverStartType=='1'):
            optionMainMenu = int(input("Enter your host number to start: "))
            logger.info("Enter your host number to start:"+str(optionMainMenu))
            if(optionMainMenu != 99):
                if len(managerDict) >= optionMainMenu:
                    spaceStart = managerDict.get(optionMainMenu)
                    choice = str(input(Fore.YELLOW+"Are you sure want to start server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    while(len(str(choice))==0):
                        choice = str(input(Fore.YELLOW+"Are you sure want to start server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    #print("coice start server:"+str(choice))
                    logger.info("choice :"+str(choice))
                    if(choice.casefold()=='no' or choice.casefold()=='n'):
                        if(isMenuDriven=='m'):
                            logger.info("menudriven")
                            os.system('python3 scripts/odsx_security_servers_manager_start.py'+' '+isMenuDriven)
                        else:
                            exitAndDisplay(isMenuDriven)
                    elif(choice.casefold()=='yes' or choice.casefold()=='y'):
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
            confirm = str(input(Fore.YELLOW+"Are you sure want to start all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            while(len(str(confirm))==0):
                confirm = str(input(Fore.YELLOW+"Are you sure want to start all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            logger.info("confirm :"+str(confirm))
            if(confirm=='yes' or confirm=='y'):
                spaceHosts = config_get_manager_node()#config_get_space_hosts_list()
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
                    os.system('python3 scripts/servers_manager_scriptbuilder.py '+argsString)
                    args.remove(menuDrivenFlag)
                    args.remove("--host")
                    args.remove(os.getenv(host.ip))
                    args.remove('-u')
                    args.remove(user)
                    logger.info(args)
            elif(confirm =='no' or confirm=='n'):
                if(isMenuDriven=='m'):
                    logger.info("menudriven")
                    os.system('python3 scripts/odsx_security_servers_manager_start.py'+' '+menuDrivenFlag)
    except Exception as e:
        logger.error("Invalid arguement "+str(e))
        verboseHandle.printConsoleError("Invalid argument")
