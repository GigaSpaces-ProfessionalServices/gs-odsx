#!/usr/bin/env python3
import json
import os
import signal

import requests
from colorama import Fore

from scripts.logManager import LogManager
from utils.ods_cleanup import signal_handler
from utils.odsx_keypress import userInputWrapper
from utils.odsx_retentionmanager_utilities import validateObjectType, validateRetentionPolicy

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


def addRetentionPolicy():
    
    logger.info("addRetentionPolicy()")
    verboseHandle.printConsoleWarning('');
    verboseHandle.printConsoleWarning('Add new Retention Policy:')
    
    objTypeInput = Fore.GREEN +"Enter Object type: "+Fore.RESET
    retentionPolicyInput = Fore.GREEN +"Enter Retention period [d/M/y]: "+Fore.RESET
    constraintFieldInput = Fore.GREEN +"Enter Constraint Field: "+Fore.RESET

    object_type = str(userInputWrapper(objTypeInput))
    isObjTypeValid = validateObjectType(object_type)
    while(isObjTypeValid==False):
        verboseHandle.printConsoleError("Invalid Object Type")
        object_type = str(userInputWrapper(objTypeInput))
        isObjTypeValid = validateObjectType(object_type)

    retention_period = str(userInputWrapper(retentionPolicyInput))
    while(len(str(retention_period))==0):
        retention_period = str(userInputWrapper(retentionPolicyInput))
    
    isPolicyValid = validateRetentionPolicy(retention_period)
    
    while(isPolicyValid==False):
        verboseHandle.printConsoleError('Retention Policy must start with number and end with [d/M/y]')
        retention_period = str(userInputWrapper(retentionPolicyInput))
        isPolicyValid = validateRetentionPolicy(retention_period)

    contraintField = str(userInputWrapper(constraintFieldInput))
    while(len(str(contraintField))==0):
        contraintField = str(userInputWrapper(constraintFieldInput))
        
    displaySummary(object_type,retention_period,contraintField)

    summaryConfirm = str(userInputWrapper(Fore.YELLOW+"Do you want to continue registration with above inputs ? [Yes (y) / No (n)]: "+Fore.RESET))
    while(len(str(summaryConfirm))==0):
        summaryConfirm = str(userInputWrapper(Fore.YELLOW+"Do you want to continue registration with above inputs ? [Yes (y) / No (n)]: "+Fore.RESET))

    if(str(summaryConfirm).casefold()=='n' or str(summaryConfirm).casefold()=='no'):
        logger.info("Exiting without registering policy")
        exit(0)

    #hostname =getLocalHostName()
    hostname = os.getenv("pivot1")
    logger.info("hostip:->"+hostname)
    verboseHandle.printConsoleWarning('');
    
    data = {
        "active":True,      
        "retentionPeriod": retention_period,
        "objectType": object_type,
        "constraintField": contraintField
    }
    logger.info("Request Body : data -> "+str(data))
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post("http://"+hostname+":3210/retention/policies"
                                , data=json.dumps(data)
                                , headers=headers)

    logger.info(str(response.status_code))
    jsonArray = json.loads(response.text)

    jsonResponse  = jsonArray["response"]
    #verboseHandle.printConsoleWarning("------------------------------------------------------------")
    if(str(jsonResponse).startswith("Success")):
        verboseHandle.printConsoleInfo("Retention Policy for '"+object_type+"' is added successfully.")
    else:
        verboseHandle.printConsoleError("Retention Policy for '"+object_type+"' could not be added.")
    #verboseHandle.printConsoleWarning("------------------------------------------------------------")
    logger.info("Exiting addRetentionPolicy()")

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
    logger.info("MENU -> Retention Manager -> Manage Retention Policy -> Add")
    verboseHandle.printConsoleWarning("MENU -> Object ->Retention Manager -> Manage Policy -> Add")
    signal.signal(signal.SIGINT, signal_handler)
    try:
        # with Spinner():
        addRetentionPolicy()
    except Exception as e:
        logger.error("Exception in Menu->Retention Manager" + str(e))
        verboseHandle.printConsoleError("Exception in Menu->Retention Manager" + str(e))
