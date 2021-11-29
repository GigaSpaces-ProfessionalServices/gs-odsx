#!/usr/bin/env python3
# s6.py
#!/usr/bin/python
import  os
from socket import *
import socket
import requests
import platform
import time
#from scripts.odsx_servers_manager_install import manager_install

HOST='18.223.117.24'
PORT = '8099'

def test_case_1():
    current_os = platform.system().lower()
    if current_os == "windows":
        parameter = "-n"
    else:
        parameter = "-c"
    exit_code = os.system(f"ping {parameter} 1 -w2 {HOST} > /dev/null 2>&1")
    if(exit_code == 0):
        print("Test-case-1: Pass")
    else:
        print("Test-case-1: Pass")
def test_case_2():
    status = port_check(HOST,PORT)
    if(status =='false'):
        print("Test-case-2: Pass")
    else:
        print("Test-case-2: Fail")

def test_case_3():
    try:
        response = requests.get(('http://'+HOST+':8090/v2/hosts'), headers={'Accept': 'application/json'})
        if(response.status_code != 200):
            print('Test-case-3: Pass')
        else:
            print('Test-case-3: Fail')
    except Exception as e:
        print('Test-case-3: Pass')
    #pass
def port_check(HOST,PORT):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((HOST, int(PORT)))
        s.shutdown(1)
        return "true"
    except :
        return "false"


if __name__ == '__main__':
    test_case_1()
    test_case_2()
    test_case_3()