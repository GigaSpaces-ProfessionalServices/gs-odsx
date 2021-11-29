#!/usr/bin/env python3
# s6.py
#!/usr/bin/python
import os, subprocess, sys, argparse, platform
from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

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

if __name__ == '__main__':
    logger.info("odsx_servers_space_restore")
    verboseHandle.printConsoleWarning('Servers - Space - Restore')
    args = []
    menuDrivenFlag='m' # To differentiate between CLI and Menudriven Argument handling help section
    #print('Len : ',len(sys.argv))
    #print('Flag : ',sys.argv[0])
    args.append(sys.argv[0])
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
                    verboseHandle.printConsoleInfo("Connected to server with dryrun mode.!")
                    logger.debug("Connected to server with dryrun mode.!")
                else:
                    verboseHandle.printConsoleInfo("Unable to connect to server.")
                    logger.debug("Unable to connect to server.")

            for arg in sys.argv[1:]:
                args.append(arg)
            #print('install :',args)
            args = str(args)
            logger.debug('Arguments :'+args)
        elif(sys.argv[1]==menuDrivenFlag):
            args.append(menuDrivenFlag)
            host = str(input("Enter your host: "))
            args.append('--host')
            args.append(host)
            user = readValuefromAppConfig("app.server.user")
            user = str(input("Enter your user ["+user+"]: "))
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
    except Exception as e:
        verboseHandle.printConsoleError("Invalid argument")
