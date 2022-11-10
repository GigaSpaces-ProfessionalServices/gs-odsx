#!/usr/bin/env python3
import os, subprocess, sys, argparse
from scripts.logManager import LogManager
import platform
from utils.ods_cluster_config import getStreamIdAndName
from utils.ods_ssh import executeRemoteShCommandAndGetOutput
from utils.odsx_keypress import userInputWithEscWrapper

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

def exitAndDisplay(isMenuDriven):
    if(isMenuDriven=='m'):
        os.system('python3 scripts/odsx_streams_resumeonline.py'+' '+isMenuDriven)
    else:
        cliArgumentsStr=''
        for arg in cliArguments:
            cliArgumentsStr+=arg
            cliArgumentsStr+=' '
        os.system('python3 scripts/odsx_streams_resumeonline.py'+' '+cliArgumentsStr)

if __name__ == '__main__':
    logger.info("odsx_servers_streams_resumeonline")
    verboseHandle.printConsoleWarning('Servers -> Streams -> Resume online')
    args = []
    menuDrivenFlag='m' # To differentiate between CLI and Menudriven Argument handling help section
    #print('Len : ',len(sys.argv))
    #print('Flag : ',sys.argv[0])
    args.append(sys.argv[0])
    try:
        streamResumeStream=''
        optionMainMenu=''
        choice=''
        cliArguments=''
        isMenuDriven=''
        if(sys.argv[1]==menuDrivenFlag):
            isMenuDriven='m'
        streamDict = getStreamIdAndName()
        optionMainMenu = int(userInputWithEscWrapper("Enter your option: "))
        if(optionMainMenu != 99):
            cliArguments = sys.argv[1:]
            if len(streamDict) >= optionMainMenu:
                streamResumeStream = streamDict.get(optionMainMenu)
                verboseHandle.printConsoleWarning("Are you sure want to resume selected stream ? [Yes][No][Cancel]")
                choice = str(input(""))
                if(choice.casefold()=='no'):
                    if(isMenuDriven=='m'):
                        os.system('python3 scripts/odsx_streams_resumeonline.py'+' '+isMenuDriven)
                    else:
                        exitAndDisplay(isMenuDriven)
                elif(choice.casefold()=='yes'):
                    if len(sys.argv) > 1 and sys.argv[1] != menuDrivenFlag:
                        arguments = myCheckArg(sys.argv[1:])
                        if(streamResumeStream.serverip == arguments.host):
                            host =streamResumeStream.serverip
                            if(arguments.dryrun==True):
                                current_os = platform.system().lower()
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
                                cmdFile = "unit-test/test_odsx_streams_startonline.sh"
                                output = executeRemoteShCommandAndGetOutput(arguments.host,arguments.user,'',cmdFile)
                                if(str(output).__contains__('True')):
                                    verboseHandle.printConsoleInfo("CR8_ctl.sh found to execute startstream.")
                                elif(str(output).__contains__('False')):
                                    verboseHandle.printConsoleInfo('CR8_ctl.sh not found to execute startstream')
                                quit()
                            for arg in sys.argv[1:]:
                                args.append(arg)
                            #print('install :',args)

                        else:
                            verboseHandle.printConsoleError("Invalid host for selected stream")
                            sys.exit()
                    elif(sys.argv[1]==menuDrivenFlag):

                        verboseHandle.printConsoleWarning('Please provide a value for the following, or click ENTER to accept the [default value]')
                        user = str(input("Enter your user [ec2-user]:"))
                        if(len(user)==0):
                            user='ec2-user'
                        args.append(menuDrivenFlag)
                        args.append('--host')
                        args.append(streamResumeStream.serverip)
                        args.append('-u')
                        args.append(user)
                    args.append('--id')
                    args.append(streamResumeStream.id)
                    args = str(args)

                    #logger.info('Menu driven flag :'+menuDrivenFlag)
                    logger.debug('Arguments :'+args)
                    #print('args',args)
                    args =args.replace('[','').replace("'","").replace("]",'').replace(',','').strip()
                    #print(args)
                    os.system('python3 scripts/servers_manager_scriptbuilder.py '+args)
                    #os.system('python3 scripts/remote_script_exec.py '+args)
                elif(choice.casefold()=='cancel'):
                    optionMainMenu=''
                    streamResumeStream=''
                    streamDict=''
            else:
                verboseHandle.printConsoleError("please select valid option")
                optionMainMenu=''
                choice=''
                streamResumeStream=''
                exitAndDisplay(isMenuDriven)
        else:
            print("")
    except Exception as e:
        verboseHandle.printConsoleError("Invalid argument.")
