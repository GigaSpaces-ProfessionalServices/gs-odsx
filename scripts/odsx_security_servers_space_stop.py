#!/usr/bin/env python3
# s6.py
#!/usr/bin/python
import os, subprocess, sys, argparse, platform
from concurrent.futures import ThreadPoolExecutor

from scripts.logManager import LogManager
from utils.ods_ssh import executeRemoteShCommandAndGetOutput
from utils.ods_cluster_config import config_get_space_list_with_status, config_get_space_hosts_list
from colorama import Fore
from utils.ods_app_config import readValuefromAppConfig
from utils.odsx_keypress import userInputWithEscWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR

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

def exitAndDisplay(isMenuDriven):
    if(isMenuDriven=='m'):
        os.system('python3 scripts/odsx_security_space_stop.py'+' '+isMenuDriven)
    else:
        cliArgumentsStr=''
        for arg in cliArguments:
            cliArgumentsStr+=arg
            cliArgumentsStr+=' '
        os.system('python3 scripts/odsx_security_space_stop.py'+' '+cliArgumentsStr)

def stopSecureSpaceServer(argsString):
    # args.append(menuDrivenFlag)
    # args.append('--host')
    # args.append(os.getenv(host))
    # args.append('-u')
    # args.append(user)
    # argsString = str(args)
    # logger.debug('Arguments :'+argsString)
    # argsString =argsString.replace('[','').replace("'","").replace("]",'').replace(',','').strip()
    # logger.info(argsString)
    os.system('python3 scripts/servers_manager_scriptbuilder.py '+argsString)
    # args.remove(menuDrivenFlag)
    # args.remove("--host")
    # args.remove(os.getenv(host))
    # args.remove('-u')
    # args.remove(user)

if __name__ == '__main__':
    logger.info("security - space - stop ")
    verboseHandle.printConsoleWarning('Menu -> Servers -> Space -> Stop')
    args = []
    menuDrivenFlag='m' # To differentiate between CLI and Menudriven Argument handling help section
    args.append(sys.argv[0])
    try:
        streamResumeStream=''
        optionMainMenu=''
        choice=''
        cliArguments=''
        isMenuDriven=''
        managerRemove=''
        # changed : 25-Aug hence systemctl always with root no need to ask
        #userConfig = readValuefromAppConfig("app.server.user")
        #logger.info("userConfig :"+str(userConfig))
        #user = str(input("Enter your user ["+userConfig+"]: "))
        #if(len(str(user))==0):
        #    user=userConfig
        user='root'
        logger.info("user :"+str(user))
        streamDict = config_get_space_list_with_status(user)
        serverStartType = str(userInputWithEscWrapper(Fore.YELLOW+"press [1] if you want to stop individual server. \nPress [Enter] to stop all. \nPress [99] for exit.: "+Fore.RESET))
        if(serverStartType=='1'):
            optionMainMenu = int(userInputWithEscWrapper("Enter your host number to stop: "))
            if(optionMainMenu != 99):
                if len(streamDict) >= optionMainMenu:
                    spaceStart = streamDict.get(optionMainMenu)
                    choice = str(input(Fore.YELLOW+"Are you sure want to stop server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    while(len(str(choice))==0):
                        choice = str(input(Fore.YELLOW+"Are you sure want to stop server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    logger.info("choice :"+str(choice))
                    if(choice.casefold()=='no' or choice.casefold()=='n'):
                        if(isMenuDriven=='m'):
                            os.system('python3 scripts/odsx_security_space_stop.py'+' '+isMenuDriven)
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
            logger.info("99 - Exist stop")
        else:
            confirm = str(input(Fore.YELLOW+"Are you sure want to stop all servers ? [yes (y)] / [no (n)]"+Fore.RESET))
            while(len(str(confirm))==0):
                confirm = str(input(Fore.YELLOW+"Are you sure want to stop all servers ? [yes (y)] / [no (n)]"+Fore.RESET))
            logger.info("confirm :"+str(confirm))
            if(confirm=='yes' or confirm=='y'):
                spaceHosts = config_get_space_hosts_list()
                spaceLength = len(spaceHosts)+1
                with ThreadPoolExecutor(spaceLength) as executor:
                    for host in spaceHosts:
                        args.append(menuDrivenFlag)
                        args.append('--host')
                        args.append(os.getenv(host))
                        args.append('-u')
                        args.append(user)
                        argsString = str(args)
                        logger.debug('Arguments :'+argsString)
                        argsString =argsString.replace('[','').replace("'","").replace("]",'').replace(',','').strip()
                        logger.info(argsString)
                        executor.submit(stopSecureSpaceServer,argsString)
                        args.remove(menuDrivenFlag)
                        args.remove("--host")
                        args.remove(os.getenv(host))
                        args.remove('-u')
                        args.remove(user)
                        # executor.submit(stopSecureSpaceServer,host,args,menuDrivenFlag,user)

                    logger.info(args)
            elif(confirm =='no' or confirm=='n'):
                if(isMenuDriven=='m'):
                    logger.info("menudriven")
                    os.system('python3 scripts/odsx_security_space_stop.py'+' '+isMenuDriven)
    except Exception as e:
        logger.error("Invalid argument space stop :"+str(e))
        verboseHandle.printConsoleError("Invalid argument")
