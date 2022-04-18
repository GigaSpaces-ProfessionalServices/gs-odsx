#!/usr/bin/env python3
import os
from colorama import Fore
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig,set_value_in_property_file
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '[92m'  # GREEN
    WARNING = '[93m'  # YELLOW
    FAIL = '[91m'  # RED
    RESET = '[0m'  # RESET COLOR

class host_dictionary_obj(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

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

def getSpaceServerHostList():
    nodeList = config_get_space_hosts()
    nodes=""
    for node in nodeList:
        #if(str(node.role).casefold() == 'server'):
        if(len(nodes)==0):
            nodes = node.ip
        else:
            nodes = nodes+','+node.ip
    return nodes

def updateSpaceServersGSC():
    logger.info("updateSpaceServersGSC()")
    try:
        spaceNodes = config_get_space_hosts()
        if(len(str(spaceNodes))>0):
            logger.info("spaceNodes: main"+str(spaceNodes))
            spaceHosts = getSpaceServerHostList()
            verboseHandle.printConsoleInfo("Available space hosts to update GSCs size : "+str(spaceHosts))

            gscFromConfig = str(readValuefromAppConfig("app.space.gsc.count"))
            gscToBeUpdated = str(input(Fore.YELLOW+"Enter GSC container create count per host to be updated from ["+gscFromConfig+"] : "))
            while(len(str(gscToBeUpdated))==0):
                gscToBeUpdated = str(input(Fore.YELLOW+"Enter GSC container create count per host to be updated from ["+gscFromConfig+"] : "))
            set_value_in_property_file("app.space.gsc.count",str(gscToBeUpdated))

            sizeFromConfig = str(readValuefromAppConfig("app.space.gsc.memory"))
            sizeToBeupdated = str(input(Fore.YELLOW+"Enter GSC container size per host to be updated from ["+sizeFromConfig+"] : "))
            while(len(str(sizeToBeupdated))==0):
                sizeToBeupdated = str(input(Fore.YELLOW+"Enter GSC container size per host to be updated from ["+sizeFromConfig+"] : "))
            set_value_in_property_file("app.space.gsc.memory",sizeToBeupdated)

            confirm = str(input(Fore.YELLOW+"Are you sure want to update container count="+str(gscToBeUpdated)+" and memory="+str(sizeToBeupdated)+" on [ "+str(spaceHosts)+" ] ? (y/n) [y]: "+Fore.RESET))
            if(confirm=='y' or len(confirm)==0):
                cmd = 'sed -i -e \'s|--count='+str(gscFromConfig)+'|--count='+str(gscToBeUpdated)+'|g\' /usr/local/bin/start_gsc.sh'
                cmd2= 'sed -i -e \'s|--memory='+str(sizeFromConfig)+'|--memory='+str(sizeToBeupdated)+'|g\' /usr/local/bin/start_gsc.sh'
                user= 'root'
                for node in spaceNodes:
                    with Spinner():
                        output = executeRemoteCommandAndGetOutputPython36(node.ip,user,cmd)
                        output2 = executeRemoteCommandAndGetOutputPython36(node.ip,user,cmd2)
            verboseHandle.printConsoleInfo("For take updates in action please re-start space servers.")
        else:
            logger.info("No Manager configuration found please check.")
            verboseHandle.printConsoleInfo("No Manager configuration found please check.")
    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Utilities -> Update Container")
    try:
        updateSpaceServersGSC()
    except Exception as e:
        handleException(e)
