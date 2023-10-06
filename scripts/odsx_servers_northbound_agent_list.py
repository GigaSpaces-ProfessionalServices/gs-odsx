# to remove space
import argparse
import os
import sys

from scripts.odsx_servers_northbound_management_remove import getNBFolderName
from utils.ods_app_config import readValuefromAppConfig
from utils.odsx_print_tabular_data import printTabular
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_nb_list
from colorama import Fore
from scripts.spinner import Spinner
from utils.ods_ssh import executeRemoteCommandAndGetOutput,executeRemoteCommandAndGetOutputPython36, executeRemoteCommandAndGetOutputValuePython36

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
    parser.add_argument('-dryrun', '--dryrun',
                        help='Dry run flag',
                        default='false', action='store_true')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])

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

def getVersion(ip):
    logger.info("getVersion () "+str(ip))
    output=''
    dbaGigaPath=str(readValuefromAppConfig("app.giga.path"))
    cmdToExecute = "cd "+dbaGigaPath+getNBFolderName()+"/;./install_nb_infra.sh -v;"
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(ip, 'root', cmdToExecute)
    logger.info(cmdToExecute+" :"+str(output))
    if(output==0):
        logger.info("cmdToExecute : "+str(cmdToExecute))
        with Spinner():
            output = executeRemoteCommandAndGetOutput(ip,"root",cmdToExecute)
        output=str(output).replace('\n','')
        logger.info("output : "+str(output))
    else:
        output="None"
    return str(output)

def isInstalledAndGetVersion(host):
    logger.info("isInstalledAndGetVersion")
    commandToExecute='ls /etc/systemd/system/northbound.target'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    return str(outputShFile)

def listNB():
    logger.debug("listing NB servers")
    nbServers = config_get_nb_list()
    verboseHandle.printConsoleWarning("Menu -> Servers -> Northbound -> Agent -> List\n")
    #verboseHandle.printConsoleWarning("IP\t\t\tHost\t\t\tgsc\t\tResume Mode")
    headers = [Fore.YELLOW+"IP"+Fore.RESET,
               Fore.YELLOW+"Host"+Fore.RESET,
               Fore.YELLOW+"Role"+Fore.RESET,
               Fore.YELLOW+"Installed"+Fore.RESET,
               Fore.YELLOW+"Status"+Fore.RESET,
               Fore.YELLOW+"Version"+Fore.RESET]

    data=[]
    #print("==========\t\t=========\t\t==========\t===========")
    for stream in nbServers:
        host = str(os.getenv(stream.ip))
        cmd=''
        if(str(stream.role).__contains__('agent')):
            cmd = "systemctl status consul.service"
            logger.info("Getting status.. :"+str(cmd))
            user = 'root'
            with Spinner():
                output = executeRemoteCommandAndGetOutputPython36(host, user, cmd)
            logger.info(cmd+" :"+str(output))
            version = getVersion(host)
            installStatus='No'
            install = isInstalledAndGetVersion(str(host))
            logger.info("install : "+str(install))
            if(len(str(install))>0):
                installStatus='Yes'
            dataArray=[Fore.GREEN+host+Fore.RESET,
                       Fore.GREEN+host+Fore.RESET,
                       Fore.GREEN+stream.role+Fore.RESET,
                       Fore.GREEN+installStatus+Fore.RESET if(installStatus=='Yes') else Fore.RED+installStatus+Fore.RESET,
                       Fore.GREEN+"ON"+Fore.RESET if(output==0) else Fore.RED+"OFF"+Fore.RESET,
                       Fore.GREEN+version+Fore.RESET]
            data.append(dataArray)

    printTabular(None,headers,data)
if __name__ == '__main__':
    args = []
    menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
    args.append(sys.argv[0])
    myCheckArg()
    try:
        listNB()
    except Exception as e:
        handleException(e)
