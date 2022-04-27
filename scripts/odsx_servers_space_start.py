#!/usr/bin/env python3
# s6.py
#!/usr/bin/python
import os, subprocess, sys, argparse, platform
from scripts.logManager import LogManager
from utils.ods_ssh import executeRemoteShCommandAndGetOutput
from utils.ods_cluster_config import config_get_space_list_with_status, config_get_space_hosts_list
from colorama import Fore
from utils.ods_app_config import readValuefromAppConfig

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
    logger.info("exitAndDisplay(isMenuDriven)")
    if(isMenuDriven=='m'):
        logger.info("exitAndDisplay(MenuDriven) ")
        os.system('python3 scripts/odsx_servers_space_start.py'+' '+isMenuDriven)
    else:
        cliArgumentsStr=''
        for arg in cliArguments:
            cliArgumentsStr+=arg
            cliArgumentsStr+=' '
        os.system('python3 scripts/odsx_servers_space_start.py'+' '+cliArgumentsStr)

if __name__ == '__main__':
    logger.info("servers - space - start ")
    verboseHandle.printConsoleWarning('Menu -> Servers -> Space -> Start')
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
        serverStartType = str(input(Fore.YELLOW+"press [1] if you want to start individual server. \nPress [Enter] to start all. \nPress [99] for exit.: "+Fore.RESET))
        logger.info("serverStartType:"+str(serverStartType))
        if(serverStartType=='1'):
            optionMainMenu = int(input("Enter your host number to start: "))
            logger.info("Enter your host number to start:"+str(optionMainMenu))
            if(optionMainMenu != 99):
                if len(streamDict) >= optionMainMenu:
                    spaceStart = streamDict.get(optionMainMenu)
                    choice = str(input(Fore.YELLOW+"Are you sure want to start server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    while(len(str(choice))==0):
                        choice = str(input(Fore.YELLOW+"Are you sure want to start server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    #print("coice start server:"+str(choice))
                    logger.info("choice :"+str(choice))
                    if(choice.casefold()=='no' or choice.casefold()=='n'):
                        if(isMenuDriven=='m'):
                            logger.info("menudriven")
                            os.system('python3 scripts/odsx_servers_space_start.py'+' '+isMenuDriven)
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
            confirm = str(input(Fore.YELLOW+"Are you sure want to start all servers ? [yes (y)] / [no (n)]"+Fore.RESET))
            while(len(str(confirm))==0):
                confirm = str(input(Fore.YELLOW+"Are you sure want to start all servers ? [yes (y)] / [no (n)]"+Fore.RESET))
            logger.info("confirm :"+str(confirm))
            if(confirm=='yes' or confirm=='y'):
                spaceHosts = config_get_space_hosts_list()
                for host in spaceHosts:
                    args.append(menuDrivenFlag)
                    args.append('--host')
                    args.append(os.getenv(host))
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
                    args.remove(os.getenv(host))
                    args.remove('-u')
                    args.remove(user)
                    logger.info(args)
            elif(confirm =='no' or confirm=='n'):
                if(isMenuDriven=='m'):
                    logger.info("menudriven")
                    os.system('python3 scripts/odsx_servers_space_start.py'+' '+isMenuDriven)

    except Exception as e:
        logger.error("Invalid argument space start :"+str(e))
        verboseHandle.printConsoleError("Invalid argument")
