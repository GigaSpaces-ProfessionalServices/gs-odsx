#!/usr/bin/env python3
import json
import os
import signal

import requests
from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_cleanup import signal_handler
from utils.odsx_keypress import userInputWrapper
from utils.odsx_print_tabular_data import printTabular

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

def listAllRetentionPolicies():
    
    logger.info("listAllRetentionPolicies()")
    #hostname = getLocalHostName()
    hostname = os.getenv("pivot1")
    global retentionPolicyListJSON;
    response = requests.get('http://' + hostname + ':3210/retention/policies')
    
    if response.status_code == 200:
        logger.info(str(response.status_code))
        jsonArray = json.loads(response.text)
        response = json.loads(jsonArray["response"])
        retentionPolicyListJSON = response;
        headers = [Fore.YELLOW + "Id" + Fore.RESET,
                   Fore.YELLOW + "Object Type" + Fore.RESET,
                   Fore.YELLOW + "Retention Period" + Fore.RESET,
                   Fore.YELLOW + "Contraint Field" + Fore.RESET,
                   Fore.YELLOW + "Active" + Fore.RESET
                   ]
        data = []
        if response:
            for record in response:
            
                retentionPeriod=''
                constraintField=''
                active=''
                if 'retentionPeriod' in record:
                    retentionPeriod = str(record["retentionPeriod"])
                if 'constraintField' in record:
                    constraintField = str(record["constraintField"])
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


def deactivatePolicy():
    
    logger.info("deactivatePolicy()")
    
    listAllRetentionPolicies()
    
    verboseHandle.printConsoleWarning('');
    verboseHandle.printConsoleWarning('Deactivate Retention Policy:')

    idInput = Fore.GREEN +"Enter an id of object type to update retention Policy: "+Fore.RESET
   
    id = str(userInputWrapper(idInput))
    
    while(len(str(id))==0):
        id = str(userInputWrapper(idInput))

    confirmInput = str(userInputWrapper(Fore.YELLOW+"Are you sure want to deactivate this retention Policy ?  [Yes (y) / No (n)]: "+Fore.RESET))
    while(len(str(confirmInput))==0):
        confirmInput = str(userInputWrapper(Fore.YELLOW+"Are you sure want to deactivate this retention Policy ?  [Yes (y) / No (n)]: "+Fore.RESET))

    if(str(confirmInput).casefold()=='n' or str(confirmInput).casefold()=='no'):
        logger.info("Exiting without deactivating policy")
        exit(0)


    object_type = ""
    contraintField = ""
    retention_policy=""
    validObjFound=False
    for record in retentionPolicyListJSON:
        if str(record['id']) == id:
            object_type = str(record['objectType'])
            if 'constraintField' in record:
                contraintField = str(record['constraintField'])
            if 'retentionPeriod' in record:
                retention_policy = str(record['retentionPeriod'])
            validObjFound=True
            break

    if(validObjFound==False):
        verboseHandle.printConsoleError("Id does not exists. Please enter valid id from list.")
        exit(0) 

    #hostname = getLocalHostName()
    hostname = os.getenv("pivot1")
    verboseHandle.printConsoleWarning('');
    data = {
        "id":id,
        "active":False,      
        "retentionPeriod": retention_policy,
        "objectType": object_type,
        "constraintField": contraintField
    }

    #print("data=>"+str(data))
    
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.put("http://"+hostname+":3210/retention/policies"
                                , data=json.dumps(data)
                                , headers=headers)

    logger.info(str(response.status_code))
    jsonArray = json.loads(response.text)

    jsonResponse  = jsonArray["response"]
    #verboseHandle.printConsoleWarning("------------------------------------------------------------")
    if(str(jsonResponse).startswith("Success")):
        verboseHandle.printConsoleInfo("Retention Policy for '"+object_type+"' is deactivated successfully.")
    else:
        verboseHandle.printConsoleError("Retention Policy for '"+object_type+"' could not be deactivated.")
    #verboseHandle.printConsoleWarning("------------------------------------------------------------")
    logger.info("Exiting deactivatePolicy()")


if __name__ == '__main__':
    verboseHandle.printConsoleWarning("MENU -> Object ->Retention Manager -> Manage Policy -> Deactivate")
    signal.signal(signal.SIGINT, signal_handler)
    deactivatePolicy()
