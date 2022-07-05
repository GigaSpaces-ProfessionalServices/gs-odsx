#!/usr/bin/env python3

import json
import os
import sys
import re
from colorama import Fore
import requests
from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_ssh import executeLocalCommandAndGetOutput
from utils.odsx_print_tabular_data import printTabular
from utils.odsx_retentionmanager_utilities import validateRetentionPolicy,getLocalHostName

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

    
def listAllRetentionPolicies():
    
    logger.info("listAllRetentionPolicies()")
    hostname = getLocalHostName()
    
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
                             Fore.GREEN + active + Fore.RESET
                             ]
                
                data.append(dataArray)

        printTabular(None, headers, data)
        verboseHandle.printConsoleWarning('');
        return len(response)

if __name__ == '__main__':
    logger.info("MENU -> Retention Manager -> Manage Retention Policy -> List")
    verboseHandle.printConsoleWarning("MENU -> Retention Manager -> Manage Retention Policy -> List")
    
    #try:
        # with Spinner():
    listAllRetentionPolicies()
    #except Exception as e:
    #    logger.error("Exception in Menu->Retention Manager" + str(e))
    #    verboseHandle.printConsoleError("Exception in Menu->Retention Manager" + str(e))
