
import argparse
import os
import sys
from utils.odsx_print_tabular_data import printTabular
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_dataIntegration_nodes
from colorama import Fore
from scripts.spinner import Spinner
from utils.ods_ssh import executeRemoteCommandAndGetOutput,executeRemoteCommandAndGetOutputPython36

verboseHandle = LogManager(os.path.basename(__file__))
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

def listDIServers():
    logger.info("listDIServers()")
    dIServers = config_get_dataIntegration_nodes()
    headers = [Fore.YELLOW+"Name"+Fore.RESET,
               Fore.YELLOW+"Type"+Fore.RESET,
               Fore.YELLOW+"Resume Mode"+Fore.RESET,
               Fore.YELLOW+"Role"+Fore.RESET,
               Fore.YELLOW+"Status"+Fore.RESET]
    data=[]
    for node in dIServers:
        cmd = "systemctl status odsxkafka.service"
        logger.info("Getting status.. :"+str(cmd))
        user = 'root'
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(node.ip, user, cmd)
            logger.info(str(output))
        if(output==0):
            dataArray=[Fore.GREEN+node.name+Fore.RESET,
                       Fore.GREEN+node.type+Fore.RESET,
                       Fore.GREEN+node.resumeMode+Fore.RESET,
                       Fore.GREEN+node.role+Fore.RESET,
                       Fore.GREEN+"ON"+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+node.name+Fore.RESET,
                       Fore.GREEN+node.type+Fore.RESET,
                       Fore.GREEN+node.resumeMode+Fore.RESET,
                       Fore.GREEN+node.role+Fore.RESET,
                       Fore.RED+"OFF"+Fore.RESET]
        data.append(dataArray)

    printTabular(None,headers,data)

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> DI -> List')
    try:
        args = []
        menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
        args.append(sys.argv[0])
        myCheckArg()
        listDIServers()
    except Exception as e:
        handleException(e)
