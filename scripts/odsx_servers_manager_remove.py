#!/usr/bin/env python3
# s6.py
#!/usr/bin/python
import os, subprocess, sys, argparse, platform
from scripts.logManager import LogManager
from utils.ods_ssh import executeRemoteShCommandAndGetOutput
from utils.ods_app_config import readValuefromAppConfig
from colorama import Fore
from utils.ods_cluster_config import config_get_manager_listWithStatus

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
    args =args.replace('[','').replace("'","").replace("]",'').replace(',','').strip()
    logger.info(args)
    os.system('python3 scripts/servers_manager_scriptbuilder.py '+args)
    logger.info("python3 scripts/servers_manager_scriptbuilder.py completed")

def exitAndDisplay(isMenuDriven):
    logger.info("exitAndDisplay(isMenuDriven)")
    if(isMenuDriven=='m'):
        logger.info("python3 scripts/odsx_servers_manager_remove.py executed")
        os.system('python3 scripts/odsx_servers_manager_remove.py'+' '+isMenuDriven)

if __name__ == '__main__':
    logger.info("servers - manager - Remove ")
    verboseHandle.printConsoleWarning('Servers -> Manager -> Remove')
    args = []
    menuDrivenFlag='m' # To differentiate between CLI and Menudriven Argument handling help section
    args.append(sys.argv[0])

    managerDict = config_get_manager_listWithStatus()

    hostsConfig=''
    hostsConfig = readValuefromAppConfig("app.manager.hosts")
    logger.info("hostConfig:"+str(hostsConfig))
    hostsConfig=hostsConfig.replace('"','')
    if(len(str(hostsConfig))>0):
        verboseHandle.printConsoleWarning("Current cluster configuration : ["+hostsConfig+"] ")
    hostConfiguration = str(input(Fore.YELLOW+"press [1] if you want to remove individual server. \nPress [Enter] to remove current Configuration. \nPress [99] for exit.: "+Fore.RESET))
    logger.info("hostConfiguration"+str(hostConfiguration))

    try:
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
                #output = subprocess.check_output("ssh -i ps-share.pem ec2-user@18.188.147.174 bash -s  < utils/java_check.sh | grep f89e7000 | awk '{print $1}'", shell=True)
                try:
                    exit_code = executeRemoteShCommandAndGetOutput(arguments.host, arguments.user, '', 'utils/java_check.sh')
                    if(str(exit_code).__contains__('javac')):
                        verboseHandle.printConsoleInfo("Java Installed.")
                except Exception as e:
                    verboseHandle.printConsoleInfo("Java not found.")
                try:
                    exit_code = executeRemoteShCommandAndGetOutput(arguments.host, arguments.user, '', 'utils/gs_check.sh')
                    logger.info("exit_code"+str(exit_code))
                    if(len(str(exit_code)) > 6):
                        verboseHandle.printConsoleInfo("Gigaspace Installed.")
                    else:
                        verboseHandle.printConsoleInfo("Gigaspace not found.")
                except Exception as e:
                    verboseHandle.printConsoleInfo("Gigaspace not found.")
                quit()

            for arg in sys.argv[1:]:
                args.append(arg)
            logger.info('args : :'+str(args))
            args = str(args)
            logger.debug('Arguments :'+args)
            execute_scriptBuilder(args)
        elif(sys.argv[1]==menuDrivenFlag):
            logger.info("Menudriven..")
            args.append(menuDrivenFlag)
            if(hostConfiguration=='1'):
                optionMenu = str(input("Enter your host number to remove : "))
                while(len(optionMenu)==0):
                    optionMenu = str(input("Enter your host number to remove : "))
                confirm = str(input(Fore.YELLOW+"Are you sure want to remove server ? [yes (y)] / [no (n)]"+Fore.RESET))
                while(len(str(confirm))==0):
                    confirm = str(input(Fore.YELLOW+"Are you sure want to remove server ? [yes (y)] / [no (n)]"+Fore.RESET))
                logger.info("confirm :"+str(confirm))
                if(confirm=='yes' or confirm=='y'):
                    managerStart = managerDict.get(int(optionMenu))
                    args.append('--host')
                    args.append(str(managerStart.ip))
                    #userConfig = readValuefromAppConfig("app.server.user")
                    user = str(input("Enter your user [root]: "))
                    if(len(str(user))==0):
                        user="root"
                    logger.info("app.server.user: "+str(user))
                    #if(len(str(user))==0):
                    #    user="ec2-user"
                    args.append('-u')
                    args.append(user)
                    args.append('--id')
                    args.append(str(managerStart.ip))
                    execute_scriptBuilder(args)
                elif(confirm =='no' or confirm=='n'):
                    if(menuDrivenFlag=='m'):
                        logger.info("menudriven")
                        os.system('python3 scripts/odsx_servers_manager_remove.py'+' '+menuDrivenFlag)
            elif(hostConfiguration=='99'):
                logger.info("99 - Exist stop")
            else:
                confirm = str(input(Fore.YELLOW+"Are you sure want to remove all server ? [yes (y)] / [no (n)]"+Fore.RESET))
                while(len(str(confirm))==0):
                    confirm = str(input(Fore.YELLOW+"Are you sure want to remove all server ? [yes (y)] / [no (n)]"+Fore.RESET))
                logger.info("confirm :"+str(confirm))
                if(confirm=='yes' or confirm=='y'):
                    logger.info("Removing Cluster")
                    #userConfig = readValuefromAppConfig("app.server.user")
                    user = str(input("Enter your user [root]: "))
                    if(len(str(user))==0):
                        user='root'
                    logger.info("app.server.user: "+str(user))
                    #if(len(str(user))==0):
                    #    user="ec2-user"
                    hostsConfigArray = hostsConfig.split(",")
                    for host in hostsConfigArray:
                        logger.info("Removing host :"+str(host))
                        verboseHandle.printConsoleInfo("Removing Host :"+str(host))
                        args.append('--host')
                        args.append(host)
                        args.append('-u')
                        args.append(user)
                        args.append('--id')
                        args.append(host)
                        execute_scriptBuilder(args)
                        args.remove("--host")
                        args.remove(host)
                        args.remove('-u')
                        args.remove(user)
                elif(confirm =='no' or confirm=='n'):
                    if(menuDrivenFlag=='m'):
                        logger.info("menudriven")
                        os.system('python3 scripts/odsx_servers_manager_remove.py'+' '+menuDrivenFlag)
    except Exception as e:
        logger.error("Invalid argument "+str(e))
        verboseHandle.printConsoleError("Invalid argumentss")
