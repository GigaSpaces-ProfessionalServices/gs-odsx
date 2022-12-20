#!/usr/bin/env python3
import os, subprocess, sys, argparse, platform
from concurrent.futures import ThreadPoolExecutor

from scripts.logManager import LogManager
from utils.ods_ssh import executeRemoteShCommandAndGetOutput, connectExecuteSSH
from utils.ods_cluster_config import config_get_space_list_with_status, config_get_space_hosts_list, config_remove_space_nodeByIP
from colorama import Fore
from utils.ods_app_config import readValuefromAppConfig
from scripts.spinner import Spinner
from utils.odsx_keypress import userInputWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

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

def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    parser.add_argument('-f', nargs='?')
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

def execute_scriptBuilder(host):
    logger.info("execute_scriptBuilder(args)")
    commandToExecute="scripts/servers_space_remove.sh"
    additionalParam = removeJava+' '+removeUnzip
    logger.info("additionalParam : "+str(additionalParam))
    with Spinner():
        #outputShFile= executeRemoteShCommandAndGetOutput(host, 'root', additionalParam, commandToExecute)
        outputShFile = connectExecuteSSH(host, user,commandToExecute,additionalParam)
        print(outputShFile)
        logger.info("Output : scripts/servers_manager_remove.sh :"+str(outputShFile))
        #config_remove_space_nodeByIP(host)
        logger.debug(str(host)+" has been removed.")
        verboseHandle.printConsoleInfo(str(host)+" has been removed.")

def exitAndDisplay(isMenuDriven):
    logger.info("exitAndDisplay(isMenuDriven)")
    if(isMenuDriven=='m'):
        logger.info("exitAndDisplay(isMenuDriven) : MenuDriven")
        os.system('python3 scripts/odsx_servers_space_remove.py'+' '+isMenuDriven)
    else:
        cliArgumentsStr=''
        for arg in cliArguments:
            cliArgumentsStr+=arg
            cliArgumentsStr+=' '
        os.system('python3 scripts/odsx_servers_space_remove.py'+' '+cliArgumentsStr)

def removeSpaceServer(host,args,menuDrivenFlag,user):
    logger.info("BEFORE")
    logger.info("Removing host:"+str(host))
    args.append(menuDrivenFlag)
    args.append('--host')
    args.append(host)
    args.append('-u')
    args.append(user)
    args.append('--id')
    args.append(str(os.getenv(host)))
    argsString = str(args)
    logger.info(argsString)
    logger.debug('Arguments :'+argsString)
    argsString =argsString.replace('[','').replace("'","").replace("]",'').replace(',','').strip()
    #print(argsString)
    #os.system('python3 scripts/servers_manager_scriptbuilder.py '+argsString)
    execute_scriptBuilder(os.getenv(host))
    logger.info("AFTER")
    args.remove(menuDrivenFlag)
    args.remove("--host")
    args.remove(host)
    args.remove('-u')
    args.remove(user)
    args.remove('--id')
    args.remove(os.getenv(host))
    logger.info(args)
if __name__ == '__main__':
    logger.info("odsx_servers_manager_remove")
    verboseHandle.printConsoleWarning('Menu -> Servers -> Space -> Remove')
    # global args
    args = []
    menuDrivenFlag='m' # To differentiate between CLI and Menudriven Argument handling help section
    args.append(sys.argv[0])
    try:
        streamResumeStream=''
        optionMainMenu=''
        choice=''
        cliArguments=''
        isMenuDriven=''
        # changed : 25-Aug hence systemctl always with root no need to ask
        #user = str(userInputWrapper("Enter your user [root]: "))
        #if(len(str(user))==0):
        #    user="root"
        #logger.info("user :"+str(user))
        user='root'
        global removeJava
        global removeUnzip
        streamDict = config_get_space_list_with_status(user)
        serverStartType = str(userInputWrapper(Fore.YELLOW+"press [1] if you want to remove individual server. \nPress [Enter] to remove all. \nPress [99] for exit.: "+Fore.RESET))
        logger.info("serverStartType:"+str(serverStartType))
        if(serverStartType=='1'):
            optionMainMenu = int(userInputWrapper("Enter your host number to remove: "))
            logger.info("optionMainMenu:"+str(optionMainMenu))
            if(optionMainMenu != 99):
                if len(streamDict) >= optionMainMenu:
                    managerRemove = streamDict.get(optionMainMenu)
                    removeJava = str(userInputWrapper(Fore.YELLOW+"Do you want to remove Java ? (y/n) [n] :"))
                    if(len(str(removeJava))==0):
                        removeJava='n'
                    removeUnzip = str(userInputWrapper(Fore.YELLOW+"Do you want to remove Unzip ? (y/n) [n] :"))
                    if(len(str(removeUnzip))==0):
                        removeUnzip='n'
                    choice = str(userInputWrapper(Fore.YELLOW+"Are you sure want to remove server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    while(len(str(choice))==0):
                        choice = str(userInputWrapper(Fore.YELLOW+"Are you sure want to remove server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    logger.info("choice remvoe server:"+str(choice))
                    if(choice.casefold()=='no' or choice.casefold()=='n'):
                        if(isMenuDriven=='m'):
                            logger.info("isMenuDriven:")
                            os.system('python3 scripts/odsx_servers_space_remove.py'+' '+isMenuDriven)
                        else:
                            logger.info("Not menudriven")
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
                            args.append(os.getenv(managerRemove.ip))
                            #user = readValuefromAppConfig("app.server.user")
                            args.append('-u')
                            args.append(user)
                            args.append('--id')
                            args.append(os.getenv(managerRemove.ip))
                        args = str(args)
                        #print('args',args)
                        #logger.info('Menu driven flag :'+menuDrivenFlag)
                        logger.debug('Arguments :'+args)
                        logger.info("Arguments"+str(args))
                        args =args.replace('[','').replace("'","").replace("]",'').replace(',','').strip()
                        #print(args)
                        #os.system('python3 scripts/servers_manager_scriptbuilder.py '+args)
                        #os.system('python3 scripts/remote_script_exec.py '+args)
                        execute_scriptBuilder(os.getenv(managerRemove.ip))
                else:
                    verboseHandle.printConsoleError("please select valid option")
                    optionMainMenu=''
                    choice=''
                    exitAndDisplay(isMenuDriven)
            else :
                print("")
        elif(serverStartType =='99'):
            logger.info("99")
        else:
            removeJava = str(userInputWrapper(Fore.YELLOW+"Do you want to remove Java ? (y/n) [n] :"))
            if(len(str(removeJava))==0):
                removeJava='n'
            removeUnzip = str(userInputWrapper(Fore.YELLOW+"Do you want to remove Unzip ? (y/n) [n] :"))
            if(len(str(removeUnzip))==0):
                removeUnzip='n'
            confirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to remove all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            while(len(str(confirm))==0):
                confirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to remove all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            logger.info("confirm :"+str(confirm))
            if(confirm=='yes' or confirm=='y'):
                spaceHosts = config_get_space_hosts_list()
                spaceHostsLength = len(spaceHosts)+1
                with ThreadPoolExecutor(spaceHostsLength) as executor:
                    for host in spaceHosts:
                        executor.submit(removeSpaceServer,host,args,menuDrivenFlag,user)
            elif(confirm =='no' or confirm=='n'):
                if(isMenuDriven=='m'):
                    logger.info("menudriven")
                    os.system('python3 scripts/odsx_servers_space_remove.py'+' '+isMenuDriven)

    except Exception as e:
        logger.error("Error while removing space host:"+str(e))
        verboseHandle.printConsoleError("Invalid argument"+str(e))
        handleException(e)