#!/usr/bin/env python3
import glob
import os

from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_monitors_alerts_services_kapacitor_list import getStatusOfKapacitor
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig
from utils.odsx_keypress import userInputWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR

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

def addTick():
    logger.info("addTick()")
    global sourceTickFilePath
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    sourceTickFilePath = str(sourceInstallerDirectory+".kapacitor.alerts.").replace('.','/')
    status=getStatusOfKapacitor(host)
    if status=="ON":
        directory = os.getcwd()
        os.chdir(sourceTickFilePath)
        for file in glob.glob("*.tick"):
            os.chdir(directory)
            aliasName = str(file).replace(".tick","")
            #kapacitor delete tasks pipeline-status
            filePath=str(sourceTickFilePath+file)
            cmd = '"kapacitor define '+aliasName+' -tick '+filePath
            logger.info("Getting tick path.. kapacitor :"+str(cmd))
            user = 'root'
            with Spinner():
                isConnectUsingPem = readValuefromAppConfig("cluster.usingPemFile")
                pemFileName = readValuefromAppConfig("cluster.pemFile")
                ssh = ""
                additionalParam= aliasName+' '+filePath
                if isConnectUsingPem == 'True':
                    ssh = ''.join(
                        ['ssh', ' -i ', pemFileName, ' ', user, '@', str(host), ' '])
                else:
                    ssh = ''.join(['ssh', ' ', str(host), ' '])
                cmd = ssh + 'bash' + ' -s ' + additionalParam + ' < scripts/monitors_alerts_catalogue_add.sh'
                with Spinner():
                    os.system(cmd)
                    pass
    else:
        verboseHandle.printConsoleInfo("Kapacitor status is off. Please start kapacitor on host."+str(host))

'''
def listCatalogue():
    logger.info("listCatalogue()")
    global sourceDB2FeederShFilePath
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    sourceDB2FeederShFilePath = str(sourceInstallerDirectory+".kapacitor.alerts.").replace('.','/')

    directory = os.getcwd()
    os.chdir(sourceDB2FeederShFilePath)
    for file in glob.glob("*.tick"):
        print(file)
        os.chdir(directory)
'''


def displaySummary():
    logger.info("displaysummary()")
    verboseHandle.printConsoleInfo("-----------Summary-----------------")
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    sourceTickFilePath = str(sourceInstallerDirectory+".kapacitor.alerts.").replace('.','/')
    verboseHandle.printConsoleInfo("Source file for tick : "+sourceTickFilePath)
    verboseHandle.printConsoleInfo("-----------------------------------")

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Monitors -> Alerts -> Catalogue -> Add')
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    try:
        host = os.getenv("pivot1")
        displaySummary()
        choice = str(userInputWrapper(Fore.YELLOW+"Are you sure want to proceed ? (y/n) : "+Fore.RESET))
        if choice=='y':
            addTick()
        else:
            quit()
    except Exception as e:
        handleException(e)