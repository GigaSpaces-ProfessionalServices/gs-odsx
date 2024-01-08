#!/usr/bin/env python3
# s6.py
# !/usr/bin/python
import argparse
import os
import shutil
import sys

from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
from utils.odsx_keypress import userInputWithEscWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR


def screen_clear():
    # for mac and linux(here, os.name is 'posix')
    if os.name == 'posix':
        _ = os.system('clear')
    else:
        # for windows platfrom
        _ = os.system('cls')


def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    parser.add_argument('--host',
                        help='host ip',
                        required='False',
                        default='localhost')
    parser.add_argument('-u', '--user',
                        help='user name',
                        default='root')
    parser.add_argument('-dryrun', '--dryrun',
                        help='Dry run flag',
                        default='false', action='store_true')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])


def execute_scriptBuilder(args):
    logger.info("execute_scriptBuilder(args) : " + str(args))
    args = str(args)
    logger.debug('Arguments :' + args)
    args = args.replace('[', '').replace("'", "").replace("]", '').replace(',', '').strip()
    # print(args)
    os.system('python3 scripts/servers_manager_scriptbuilder.py ' + args)
    logger.info("python3 scripts/servers_manager_scriptbuilder.py executed.")


def exitAndDisplay(isMenuDriven):
    logger.info("exitAndDisplay(isMenuDriven)")
    if (isMenuDriven == 'm'):
        os.system('python3 scripts/odsx_security_manager_stop.py' + ' ' + isMenuDriven)
        logger.info("python3 scripts/odsx_security_manager_stop.py executed")


def createFolderIfNotExists(folderPath):
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)


watchFolderPath = str(readValuefromAppConfig("odsx.utilities.scripts.folder"))
createFolderIfNotExists(watchFolderPath)

verboseHandle = LogManager(os.path.basename(__file__))
verboseHandle.printConsoleInfo(watchFolderPath)
logger = verboseHandle.logger


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


def listAllScripts(listScriptsPath):
    try:
        if os.path.exists(listScriptsPath):
            files = [file for file in os.listdir(listScriptsPath) if
                     os.path.isfile(os.path.join(listScriptsPath, file))]
        else:
            files = []
        return files
    except Exception as e:
        handleException(e)


def listAllFolders(listFoldersPath):
    try:
        if os.path.exists(listFoldersPath):
            subfolders = [f.name for f in os.scandir(listFoldersPath) if f.is_dir()]
        else:
            subfolders = []
        return subfolders
    except Exception as e:
        handleException(e)


def listAllFoldersAndFiles(listFolderAndFilesPath):
    try:
        if os.path.exists(listFolderAndFilesPath):
            files = [_folderAndFilesPath for _folderAndFilesPath in os.listdir(listFolderAndFilesPath)]
        else:
            files = []
        return files
    except Exception as e:
        handleException(e)


def _createWatchFolderString(_FolderPath):
    try:
        _watchFolderPathlist = listAllFoldersAndFiles(_FolderPath)
        _watchFolderPathString = ""
        for eachFile in range(len(_watchFolderPathlist)):
            if os.path.isfile(_FolderPath + "/" + _watchFolderPathlist[eachFile]) == True:
                _watchFolderPathString = _watchFolderPathString + "[" + str(eachFile) + "] Run " + _watchFolderPathlist[
                    eachFile] + " \n"
            if os.path.isdir(_FolderPath + "/" + _watchFolderPathlist[eachFile]) == True:
                _watchFolderPathString = _watchFolderPathString + "[" + str(eachFile) + "] Open Folder " + \
                                         _watchFolderPathlist[eachFile] + " \n"
        return _watchFolderPathString
    except Exception as e:
        handleException(e)

def _runScripts(selectedScript):
    try:
        if ".py" in str(selectedScript):
            cmd = "python3 " + str(selectedScript)
            verboseHandle.printConsoleInfo(cmd)
            verboseHandle.printConsoleInfo(str(os.system(cmd)))
        elif ".sh" in str(selectedScript):
            cmd = "sh " + str(selectedScript)
            verboseHandle.printConsoleInfo(cmd)
            verboseHandle.printConsoleInfo(str(os.system(cmd)))
        elif "." not in str(selectedScript):
            verboseHandle.printConsoleInfo(str(os.system(selectedScript)))
        else:
            verboseHandle.printConsoleInfo("Add run command for script = " + str(selectedScript))
    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    try:
        logger.info("odsx_menu_utilities_Scripts")
        logger.debug("odsx_menu_utilities_Scripts")
        shutil.copy(os.getcwd() + "/scripts/Recoverymonitor.py",watchFolderPath + "/RecoveryMonitor.py")
        shutil.copy(os.getcwd() + "/scripts/Gcexplicit.py", watchFolderPath + "/GcExplicit.py")
        shutil.copy(os.getcwd() + "/scripts/Checkmanagersync.py",watchFolderPath + "/CheckManagerSync.py")

        verboseHandle.printConsoleWarning("MENU -> UTILITIES -> Scripts")
        args = []
        menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
        args.append(sys.argv[0])

        watchFolderPathString = _createWatchFolderString(watchFolderPath)
        hostConfiguration = str(userInputWithEscWrapper(
            Fore.YELLOW + watchFolderPathString + "Press [Enter] to stop current Configuration. \nPress [99] for exit.: " + Fore.RESET))

        watchFolderPathlist = listAllFoldersAndFiles(watchFolderPath)
        if len(sys.argv) > 1 and sys.argv[1] != menuDrivenFlag:
            arguments = myCheckArg(sys.argv[1:])
            logger.info("argumenets " + str(arguments))
        elif ((type(int(hostConfiguration)) == int) and ((len(watchFolderPathlist) - 1) >= int(hostConfiguration))):
            selectedFolderOrFileFromMenu = watchFolderPath + "/" + str(watchFolderPathlist[int(hostConfiguration)])
            if (os.path.exists(selectedFolderOrFileFromMenu)):
                if (os.path.isfile(selectedFolderOrFileFromMenu)):
                    _runScripts(selectedFolderOrFileFromMenu)
                elif (os.path.isdir(selectedFolderOrFileFromMenu)):
                    selectedWatchFolder = selectedFolderOrFileFromMenu
                    while ((os.path.isdir(selectedWatchFolder)) == True):
                        _watchFolderPathlist = listAllFoldersAndFiles(selectedWatchFolder)
                        watchFolderPathStringNew = _createWatchFolderString(selectedWatchFolder)
                        screen_clear()
                        hostConfiguration = str(userInputWithEscWrapper(Fore.YELLOW + watchFolderPathStringNew + "Press [Enter] to stop current Configuration. \nPress [99] for exit.: " + Fore.RESET))
                        selectedWatchFolder = selectedWatchFolder + "/" + str(_watchFolderPathlist[int(hostConfiguration)])
                        _runScripts(selectedWatchFolder)
            else:
                verboseHandle.printConsoleInfo("Check Path = " + str(selectedFolderOrFileFromMenu))
        elif (hostConfiguration == '99'):
            logger.info("99 - Exist stop")
        else:
            verboseHandle.printConsoleInfo("hostConfiguration = " + str(hostConfiguration))
    except Exception as e:
        logger.error("Invalid argument " + str(e))
        verboseHandle.printConsoleError("Invalid argument")
