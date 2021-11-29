#!/usr/bin/env python3
# !/usr/bin/python

from colorama import Fore
from utils.ods_validation import getTelnetStatus

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR

def getGrafanaServerDetails(grafanaServers):
    dataArray=[]
    for server in grafanaServers:
        status = getTelnetStatus(server.ip,3000)
        if(status=='ON'):
            dataArray=[Fore.GREEN+server.ip+Fore.RESET,
                       Fore.GREEN+server.name+Fore.RESET,
                       Fore.GREEN+server.role+Fore.RESET,
                       Fore.GREEN+server.resumeMode+Fore.RESET,
                       Fore.GREEN+status+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+server.ip+Fore.RESET,
                       Fore.GREEN+server.name+Fore.RESET,
                       Fore.GREEN+server.role+Fore.RESET,
                       Fore.GREEN+server.resumeMode+Fore.RESET,
                       Fore.RED+status+Fore.RESET]
    return dataArray

def getInfluxdbServerDetails(influxdbServers):
    dataArray=[]
    for server in influxdbServers:
        status = getTelnetStatus(server.ip,8086)
        if(status=='ON'):
            dataArray=[Fore.GREEN+server.ip+Fore.RESET,
                       Fore.GREEN+server.name+Fore.RESET,
                       Fore.GREEN+server.role+Fore.RESET,
                       Fore.GREEN+server.resumeMode+Fore.RESET,
                       Fore.GREEN+status+Fore.RESET]
        else:
            dataArray=[Fore.GREEN+server.ip+Fore.RESET,
                       Fore.GREEN+server.name+Fore.RESET,
                       Fore.GREEN+server.role+Fore.RESET,
                       Fore.GREEN+server.resumeMode+Fore.RESET,
                       Fore.RED+status+Fore.RESET]
    return dataArray
