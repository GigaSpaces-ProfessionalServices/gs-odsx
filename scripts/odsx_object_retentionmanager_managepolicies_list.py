#!/usr/bin/env python3

import json
import os
import signal

import requests
from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_cleanup import signal_handler
from utils.odsx_print_tabular_data import printTabular

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

    
def listAllRetentionPolicies():
    
    logger.info("listAllRetentionPolicies()")
    #hostname = getLocalHostName()
    hostname = os.getenv("pivot1")
    response = requests.get('http://' + hostname + ':3210/retention/policies')
    
    if response.status_code == 200:
        logger.info(str(response.status_code))
        jsonArray = json.loads(response.text)
        response = json.loads(jsonArray["response"])
        headers = [Fore.YELLOW + "Id" + Fore.RESET,
                   Fore.YELLOW + "Object Type" + Fore.RESET,
                   Fore.YELLOW + "Retention Period" + Fore.RESET,
                   Fore.YELLOW + "Constraint Field" + Fore.RESET,
                   Fore.YELLOW + "Active" + Fore.RESET
                   ]
        data = []
        if response:
            for record in response:
                retentionPeriod=''
                
                
                if 'retentionPeriod' in record:
                    retentionPeriod = str(record["retentionPeriod"])
                constraintField=''
                if 'constraintField' in record:
                    constraintField = str(record["constraintField"])
                active=''
                if 'active' in record:
                    active = str(record["active"])
                dataArray = [Fore.GREEN + str(record["id"]) + Fore.RESET,
                             Fore.GREEN + str(record["objectType"]) + Fore.RESET,
                             Fore.GREEN + retentionPeriod + Fore.RESET,
                             Fore.GREEN + constraintField+ Fore.RESET,
                             Fore.GREEN+"Yes"+Fore.RESET if(active=='True') else Fore.RED+"No"+Fore.RESET,
                             ]
                
                data.append(dataArray)

        printTabular(None, headers, data)
        verboseHandle.printConsoleWarning('');
        return len(response)

if __name__ == '__main__':
    logger.info("MENU -> Retention Manager -> Manage Retention Policy -> List")
    verboseHandle.printConsoleWarning("MENU -> Object -> Retention Manager -> Manage Policies -> List")
    signal.signal(signal.SIGINT, signal_handler)
    #try:
        # with Spinner():
    listAllRetentionPolicies()
    #except Exception as e:
    #    logger.error("Exception in Menu->Retention Manager" + str(e))
    #    verboseHandle.printConsoleError("Exception in Menu->Retention Manager" + str(e))
