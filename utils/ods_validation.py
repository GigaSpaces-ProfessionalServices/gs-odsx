#!/usr/bin/env python3
import platform
import os
import socket, platform

def isValidHost(host):
    current_os = platform.system().lower()
    if current_os == "windows":
        parameter = "-n"
    else:
        parameter = "-c"
    exit_code = os.system(f"ping {parameter} 1 -w2 {host} > /dev/null 2>&1")
    if(exit_code==0):
        return True
    else:
    #    return False   # Commented because in some machine ping command is not working
        return True

def validateClusterCsvHost(hostips):
    for hostip in hostips.replace(" ", "").split(","):
        current_os = platform.system().lower()
        if current_os == "windows":
            parameter = "-n"
        else:
            parameter = "-c"
        exit_code = os.system(f"ping {parameter} 1 -w2 {hostip} > /dev/null 2>&1")
        if exit_code != 0:
            return False
    return True


PORT = '8099'
def port_check(HOST,PORT):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.connect((HOST, int(PORT)))
        s.shutdown(1)
        return True
    except :
        return False

def getSpaceServerStatus(host):
    if(isValidHost(host)):
        status = port_check(host,PORT)
        if(status):
            return "ON"
        else:
            return "OFF"
    else:
        return "OFF"


def port_check_config(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.connect((host, int(port)))
        s.shutdown(1)
        return True
    except :
        return False


def getTelnetStatus(host,port):
    if(isValidHost(host)):
        status = port_check_config(host,port)
        if(status):
            return "ON"
        else:
            return "OFF"
    else:
        return "OFF"