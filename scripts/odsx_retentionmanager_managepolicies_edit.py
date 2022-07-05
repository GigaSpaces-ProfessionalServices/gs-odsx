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
    verboseHandle.printConsoleWarning('Edit Retention Policy:')

    idInput = Fore.GREEN +"Enter an id of object type to update retention Policy: "+Fore.RESET
    retentionPolicyInput = Fore.GREEN +"Enter Retention Period [d/M/y]: "+Fore.RESET
    
    

    id = str(input(idInput))
    
    while(len(str(id))==0):
        id = str(input(idInput))

    object_type = ""
    contraintField = ""
    active = True
    validObjFound = False
    for record in retentionPolicyListJSON:
        if str(record['id']) == id:
            object_type = str(record['objectType'])
            if 'constraintField' in record:
                contraintField = str(record['constraintField'])
            active = record['active']
            validObjFound=True
            break
    
    if(validObjFound==False):
        verboseHandle.printConsoleError("Id does not exists. Please enter valid id from list.")
        exit(0) 

    retention_policy = str(input(retentionPolicyInput))
    while(len(str(retention_policy))==0):
        retention_policy = str(input(retentionPolicyInput))
    
    isPolicyValid = validateRetentionPolicy(retention_policy)
   
    while(isPolicyValid==False):
        verboseHandle.printConsoleError('Retention Policy must start with number and end with [d/M/y]')
        retention_policy = str(input(retentionPolicyInput))
        isPolicyValid = validateRetentionPolicy(retention_policy)
    
    contraintFieldInput = Fore.GREEN +"Enter Constraint Field ["+contraintField+"]: "+Fore.RESET 
    newContraintField = str(input(contraintFieldInput))
    if(len(str(newContraintField))>0):
        contraintField=newContraintField;

    displaySummary(object_type,retention_policy,contraintField)

    
    confirmInput = str(input(Fore.YELLOW+"Are you sure want to edit this retention Policy with above inputs? [Yes (y) / No (n)]: "+Fore.RESET))
    while(len(str(confirmInput))==0):
        confirmInput = str(input(Fore.YELLOW+"Are you sure want to edit this retention Policy with above inputs ? [Yes (y) / No (n)]: "+Fore.RESET))

    if(str(confirmInput).casefold()=='n' or str(confirmInput).casefold()=='no'):
        logger.info("Exiting without editing policy")
        exit(0)

    hostname = getLocalHostName()
    verboseHandle.printConsoleWarning('');
    data = {
        "id":id,
        "active":active,      
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
        verboseHandle.printConsoleInfo("Retention Policy for '"+object_type+"' is updated successfully.")
    else:
        verboseHandle.printConsoleError("Retention Policy for '"+object_type+"' could not be updated.")
    #verboseHandle.printConsoleWarning("------------------------------------------------------------")
    logger.info("Exiting editRetentionPolicy()")


def displaySummary(object_type,retention_period,contraintField):
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleWarning("***Summary***")
    print(Fore.GREEN+"1. "+
            Fore.GREEN+"Object Type = "+
            Fore.GREEN+object_type+Fore.RESET)
    print(Fore.GREEN+"2. "+
            Fore.GREEN+"Retention Period = "+
            Fore.GREEN+retention_period+Fore.RESET)
    print(Fore.GREEN+"3. "+
            Fore.GREEN+"Constraint Field = "+
            Fore.GREEN+contraintField+Fore.RESET)
    verboseHandle.printConsoleWarning("------------------------------------------------------------")

if __name__ == '__main__':
    logger.info("MENU -> Retention Manager -> Manage Retention Policy -> Edit")
    verboseHandle.printConsoleWarning("MENU -> Retention Manager -> Manage Retention Policy -> Edit")
    
    try:
        # with Spinner():
        editRetentionPolicy()
    except Exception as e:
        logger.error("Exception in Menu->Retention Manager" + str(e))
        verboseHandle.printConsoleError("Exception in Menu->Retention Manager" + str(e))
