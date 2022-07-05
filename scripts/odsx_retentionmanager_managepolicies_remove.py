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


def editRetentionPolicy():
    
    logger.info("editRetentionPolicy()")
    
    listAllRetentionPolicies()
    
    verboseHandle.printConsoleWarning('');
    verboseHandle.printConsoleWarning('Remove Retention Period:')
    idInput = Fore.GREEN +"Enter an id of object type to update retention Policy: "+Fore.RESET
    id = str(input(idInput))
    
    while(len(str(id))==0):
        id = str(input(idInput))

    confirmInput = str(input(Fore.YELLOW+"Are you sure want to remove this retention Policy ? [Yes (y) / No (n)]: "+Fore.RESET))
    while(len(str(confirmInput))==0):
        confirmInput = str(input(Fore.YELLOW+"Are you sure want to remove this retention Policy ? [Yes (y) / No (n)]: "+Fore.RESET))

    if(str(confirmInput).casefold()=='n' or str(confirmInput).casefold()=='no'):
        logger.info("Exiting without removing policy")
        exit(0)
    
    object_type = ""
    contraintField = ""
    active = True
    validObjFound =False
    for record in retentionPolicyListJSON:
        if str(record['id']) == id:
            object_type = str(record['objectType'])
            contraintField = str(record['constraintField'])
            active = record['active']
            validObjFound = True
            break

    if(validObjFound==False):
        verboseHandle.printConsoleError("Id does not exists. Please enter valid id from list.")
        exit(0) 

    hostname = getLocalHostName()
    verboseHandle.printConsoleWarning('');
    data = {
        "id":id,
        "active":False,      
        "retentionPeriod": '',
        "objectType": object_type,
        "constraintField": contraintField
    }

    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.put("http://"+hostname+":3210/retention/policies"
                                , data=json.dumps(data)
                                , headers=headers)

    logger.info(str(response.status_code))
    jsonArray = json.loads(response.text)

    jsonResponse  = jsonArray["response"]
    #verboseHandle.printConsoleWarning("------------------------------------------------------------")
    if(str(jsonResponse).startswith("Success")):
        verboseHandle.printConsoleInfo("Retention Policy for '"+object_type+"' is removed successfully.")
    else:
        verboseHandle.printConsoleError("Retention Policy for '"+object_type+"' could not be removed.")
    #verboseHandle.printConsoleWarning("------------------------------------------------------------")
    logger.info("Exiting editRetentionPolicy()")



if __name__ == '__main__':
    logger.info("MENU -> Retention Manager -> Manage Retention Policy -> Edit")
    verboseHandle.printConsoleWarning("MENU -> Retention Manager -> Manage Retention Policy -> Edit")
    
    try:
        # with Spinner():
        editRetentionPolicy()
    except Exception as e:
        logger.error("Exception in Menu->Retention Manager" + str(e))
        verboseHandle.printConsoleError("Exception in Menu->Retention Manager" + str(e))
