#!/usr/bin/env python3
from utils.ods_ssh import executeShCommandAndGetOutput
import subprocess,os

def startScheduler():
    cmd = "scripts/scheduler.sh start"
    status=''
    output = subprocess.check_output(cmd,shell=True)
    status = deriveSchedulerStatus(output)
    return status

def stopScheduler():
    cmd = "scripts/scheduler.sh stop"
    status=''
    output = subprocess.check_output(cmd,shell=True)
    status = deriveSchedulerStatus(output)
    return status

def getSchedulerStatus():
    cmd = "scripts/scheduler.sh status"
    status=''
    output = subprocess.check_output(cmd,shell=True)
    status = deriveSchedulerStatus(output)
    return status

def deriveSchedulerStatus(output):
    status=''
    if(str(output).casefold().__contains__('is running')):
        status='Running'
    if (str(output).casefold().__contains__('is not running')):
        status='Stopped'
    elif (str(output).casefold().__contains__('started')):
        status='Started'
    return status

if __name__ == '__main__':
    status = getSchedulerStatus()
    print(status)

