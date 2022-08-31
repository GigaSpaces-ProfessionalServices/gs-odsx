#!/usr/bin/env python3
from distutils.log import debug
from math import floor
import os
import subprocess
from colorama import Back, Fore, Style
import requests,json
from os import  path
from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
from requests.auth import HTTPBasicAuth
from utils.ods_cluster_config import config_get_manager_node
from utils.ods_ssh import executeRemoteCommandAndGetOutput
from utils.ods_validation import getSpaceServerStatus

defualt_port = '8090'

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

def handleException(e):
    logger.info("handleException()")
    trace = []
    tb = e.__traceback__
    while tb is not None:
        trace.append({
            "filename": tb.tb_frame.f_code.co_filename,
            "name": tb.tb_frame.f_code.co_name,
            "lineno": tb.tb_lineno
        })
        tb = tb.tb_next
    logger.error(str({
        'type': type(e).__name__,
        'message': str(e),
        'trace': trace
    }))
    verboseHandle.printConsoleError((str({
        'type': type(e).__name__,
        'message': str(e),
        'trace': trace
    })))


def _url(host="localhost", port="8090", spaceName="demo"):
    return 'http://' + host + ':' + port + '/v2/pus/'

def getManagerHost():
    managerNodes = config_get_manager_node()
    managerHost = ""
    try:
        logger.info("getManagerHost() : managerNodes :" + str(managerNodes))
        for node in managerNodes:
            status = getSpaceServerStatus(os.getenv(node.ip))
            if (status == "ON"):
                managerHost = os.getenv(node.ip)
        return managerHost
    except Exception as e:
        handleException(e)

    return managerHost
    
def getManagerInfo(isSecure=False,username=None,password=None):
    logger.info("getManagerInfo : start()")
    managerHost = getManagerHost()
    isSecure = False
    username = None
    password = None
    url='http://'+str(managerHost)+':'+defualt_port+'/v2/info'
    logger.info("url : "+str('http://'+str(managerHost)+':'+defualt_port+'/v2/info'))
    if(isSecure==True and username is not None and password is not None):
        response = requests.get(url,auth = HTTPBasicAuth(username, password),headers={'Accept': 'application/json'})
    else:
        response = requests.get(url, headers={'Accept': 'application/json'})
    output = response.content.decode("utf-8")
    logger.info("Json Response container:"+str(output))
    data = json.loads(response.text)
    #print()
    logger.debug("GS Manager Info Data -> "+str(data))
    logger.info("getManagerInfo : end()")
    return data