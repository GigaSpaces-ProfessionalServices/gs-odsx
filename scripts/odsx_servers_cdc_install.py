#!/usr/bin/env python3
# s6.py
#!/usr/bin/python
import os, subprocess, sys, argparse
from scripts.logManager import LogManager

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
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])

if __name__ == '__main__':
    logger.info("odsx_servers_cdc_install")
    verboseHandle.printConsoleInfo('Servers - CDC - Install')

    args = []
    menuDrivenFlag='m' # To differentiate between CLI and Menudriven Argument handling help section
    #print('Len : ',len(sys.argv))
    #print('Flag : ',sys.argv[0])
    args.append(sys.argv[0])
    try:
        if len(sys.argv) > 1 and sys.argv[1] != menuDrivenFlag:
            myCheckArg()
            for arg in sys.argv[1:]:
                args.append(arg)
           # print('install :',args)
        elif(sys.argv[1]==menuDrivenFlag):
            args.append(menuDrivenFlag)
            host = str(input("Enter your host: "))
            args.append('--host')
            args.append(host)
            user = str(input("Enter your user: "))
            args.append('-u')
            args.append(user)
        args = str(args)
        #logger.info('Menu driven flag :'+menuDrivenFlag)
        logger.debug('Arguments :'+args)
        #print('args',args)
        args =args.replace('[','').replace("'","").replace("]",'').replace(',','').strip()
        #print(args)
        os.system('python3 scripts/servers_manager_scriptbuilder.py '+args)
        #os.system('python3 scripts/remote_script_exec.py '+args)
    except Exception as e:
        verboseHandle.printConsoleError("Invalid argument.")
