#!/usr/bin/env python3
import os.path
from configparser import ConfigParser
from scripts.logManager import LogManager
from configobj import ConfigObj
import configparser

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

configProperties = {}


def setConfigProperties():
    #file1 = open('config/app.config', 'r')
    file1 = open('/dbagigashare/current/ODSX/app.config', 'r')
    Lines = file1.readlines()
    for line in Lines:
        if (line.startswith("#")) or len(line) < 2:
            continue
        line = line.replace("\n", "")
        configProperties.update({line.split("=")[0]: line.split("=")[1]})


def readValuefromAppConfig(key, verbose=False):
    verboseHandle.setVerboseFlag(verbose)
    logger.debug("reading " + key + " from ")
    setConfigProperties()
    return configProperties.get(key)

def writeToFile(key,value,verbose=False):
    verboseHandle.setVerboseFlag(verbose)
    #file="config/app.config"
    file = "/dbagigashare/current/ODSX/app.config"
    logger.debug("writing to file "+file+" key="+key+" value="+value)
    file1 = open(file, 'a')
    file1.write('\n')
    file1.write(key+"="+value)
    file1.close()
    x = open(file)
    s = x.read().replace(" = ","=")
    x.close()
    x=open(file,"w")
    x.write(s)
    x.close

def set_value_in_property_file(key, value):
    #file='config/app.config'
    file= '/dbagigashare/current/ODSX/app.config'
    config = ConfigObj(file)
    if(len(value)==0):
        value=''
    config[key] = value        #Update Key
    config.write()             #Write Content
    x = open(file)
    s = x.read().replace(' = ','=')
    x.close()
    x=open(file,"w")
    x.write(s)
    x.close

def set_value_in_property_file_generic(key, value,file,section):
    cfg = get_config()
    cfg.read(str(file))
    cfgfile = open(str(file), 'w')
    cfg.set(section, key,value)
    cfg.write(cfgfile)
    cfgfile.close()

def get_config():  # used to maintain alignment camlecase for existing key
    config = configparser.ConfigParser()
    config.optionxform=str
    try:
        config.read(os.path.expanduser('~/.myrc'))
        return config
    except Exception as e:
        logger.error("While reading expanduser")
    return config

def read_value_in_property_file_generic_section(key,file,section):
    config_object = ConfigParser()
    config_object.read(file)
    #Get the password
    userinfo = config_object[section]
    #print("Password is {}".format(userinfo["password"]))
    return userinfo[key]

def readValueByConfigObj(key,file='config/app.config'):
    file='/dbagigashare/current/ODSX/app.config'
    config = ConfigObj(file)
    return  config.get(key)