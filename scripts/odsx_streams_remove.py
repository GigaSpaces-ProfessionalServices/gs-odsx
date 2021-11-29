#!/usr/bin/env python3
import os,sys

from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_cdc_streams, config_remove_cdc_stream, config_remove_cdc_streamById,getStreamIdAndName
from datetime import datetime

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

def exitAndDisplay(isMenuDriven):
    if(isMenuDriven=='m'):
        os.system('python3 scripts/odsx_streams_list.py'+' '+isMenuDriven)
    else:
        cliArgumentsStr=''
        for arg in cliArguments:
            cliArgumentsStr+=arg
            cliArgumentsStr+=' '
        os.system('python3 scripts/odsx_streams_list.py'+' '+cliArgumentsStr)

def display_stream_list(args,menuDrivenFlag):
    cliArguments=''
    streams = config_get_cdc_streams()
    verboseHandle.printConsoleWarning("MENU -> STREAMS -> Remove\n")
    streamDict = getStreamIdAndName()
    optionMainMenu = int(input("Enter your option: "))
    if(optionMainMenu != 99):
        cliArguments = args[1:]
        if len(streamDict) >= optionMainMenu:
            stream = streamDict.get(optionMainMenu)
            verboseHandle.printConsoleWarning("Are you sure want to remove stream ? [Yes][No][Cancel]")
            choice = str(input(""))
            if(choice.casefold()=='no'):
                if(isMenuDriven=='m'):
                    os.system('python3 scripts/odsx_streams_remove.py'+' '+isMenuDriven)
                else:
                    exitAndDisplay(isMenuDriven)
            elif(choice.casefold()=='yes'):
                    config_remove_cdc_streamById(stream.id)
                    verboseHandle.printConsoleWarning("Stream "+stream.id+" has been removed.")
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


if __name__ == '__main__':
    args = []
    menuDrivenFlag='m' # To differentiate between CLI and Menudriven Argument handling help section
    args.append(sys.argv[0])
    streamResumeStream=''
    optionMainMenu=''
    choice=''
    cliArguments=''
    isMenuDriven=''
    if(len(sys.argv)>=2):
        if(sys.argv[1]==menuDrivenFlag):
            isMenuDriven='m'
    display_stream_list(sys.argv,menuDrivenFlag)
