# to remove space
import argparse
import os
import sys
from utils.odsx_print_tabular_data import printTabular
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_nb_list
from colorama import Fore
from scripts.spinner import Spinner
from utils.ods_ssh import executeRemoteCommandAndGetOutput,executeRemoteCommandAndGetOutputPython36

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


def listNB():
    logger.debug("listing NB servers")
    nbServers = config_get_nb_list()
    verboseHandle.printConsoleWarning("Servers -> Northbound -> List\n")
    #verboseHandle.printConsoleWarning("IP\t\t\tHost\t\t\tgsc\t\tResume Mode")
    headers = [Fore.YELLOW+"IP"+Fore.RESET,
               Fore.YELLOW+"Host"+Fore.RESET,
               Fore.YELLOW+"Role"+Fore.RESET,
               Fore.YELLOW+"Resume Mode"+Fore.RESET,
               Fore.YELLOW+"Status"+Fore.RESET]
    data=[]
    #print("==========\t\t=========\t\t==========\t===========")
    for stream in nbServers:
        cmd=''
        if(str(stream.role).__contains__('agent')):
            cmd = "systemctl status consul.service"
        if(str(stream.role).__contains__('applicative') or str(stream.role).__contains__('management')):
            cmd = 'systemctl status northbound.target'
        logger.info("Getting status.. :"+str(cmd))
        user = 'root'
        with Spinner():
            output = executeRemoteCommandAndGetOutputPython36(stream.ip, user, cmd)
        logger.info(cmd+" :"+str(output))
        if(output==0):
            dataArray=[Fore.GREEN+stream.ip+Fore.RESET,
                       Fore.GREEN+stream.name+Fore.RESET,
                       Fore.GREEN+stream.role+Fore.RESET,
                       Fore.GREEN+stream.resumeMode+Fore.RESET,
                       Fore.GREEN+"ON"+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+stream.ip+Fore.RESET,
                       Fore.GREEN+stream.name+Fore.RESET,
                       Fore.GREEN+stream.role+Fore.RESET,
                       Fore.GREEN+stream.resumeMode+Fore.RESET,
                       Fore.RED+"OFF"+Fore.RESET]
        data.append(dataArray)

    printTabular(None,headers,data)
if __name__ == '__main__':
    args = []
    menuDrivenFlag = 'm'  # To differentiate between CLI and Menudriven Argument handling help section
    args.append(sys.argv[0])
    myCheckArg()
    listNB()
