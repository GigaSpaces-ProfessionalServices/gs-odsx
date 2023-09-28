#!/usr/bin/env python3
import os.path, pathlib
from configparser import ConfigParser
from scripts.logManager import LogManager
from configobj import ConfigObj
import configparser,yaml

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

configProperties = {}


def setConfigProperties():
    #file1 = open('config/app.config', 'r')
    sourceInstallerDirectory = str(os.getenv("ENV_CONFIG"))
    logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)
    file1 = open(sourceInstallerDirectory+'/app.config', 'r')
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
    sourceInstallerDirectory = str(os.getenv("ENV_CONFIG"))
    logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)
    file = sourceInstallerDirectory+"/app.config"
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
    sourceInstallerDirectory = str(os.getenv("ENV_CONFIG"))
    logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)
    file= sourceInstallerDirectory+'/app.config'
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
    sourceInstallerDirectory = str(os.getenv("ENV_CONFIG"))
    logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)
    file=sourceInstallerDirectory+'/app.config'
    config = ConfigObj(file)
    return  config.get(key)

def readValueFromYaml(key):
    key = pathlib.Path(key).suffix[1:]
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)
    file=sourceInstallerDirectory+'/odsx/app.yaml'
    with open(file) as f:
        content = yaml.safe_load(f)
    for val in find(content, key):
        return val

def getYamlJarFilePath(yamlPath,appConfig):
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)
    return  sourceInstallerDirectory+yamlPath.replace('.','/')+'/'+appConfig

def getYamlFilePathInsideFolder(configPath):
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory +",configPath: "+configPath)
    fileName= readValueFromYaml(configPath)
    path = str(configPath)[:str(configPath).rindex('.')].replace('.','/')
    return sourceInstallerDirectory+path+'/'+fileName

def getYamlFileNamesInsideFolderList(configPath):
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)
    fileNames= readValueFromYaml(configPath)
    return fileNames

def getYamlFilePathInsideFolderList(configPath):
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)
    fileNames= readValueFromYaml(configPath)
    path = str(configPath)[:str(configPath).rindex('.')].replace('.','/')
    fileListWithPath=[]
    for fileName in fileNames:
        fileListWithPath.append(sourceInstallerDirectory+path+'/'+fileName)
    return fileListWithPath

def getYamlFilePathInsideConfigFolder(configPath):
    sourceInstallerDirectory = str(os.getenv("ENV_CONFIG"))
    logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)
    fileName= readValueFromYaml(configPath)
    path = str(configPath)[:str(configPath).rindex('.')].replace('.','/')
    return sourceInstallerDirectory+path+'/'+fileName

def find(d, tag):
    if tag in d:
        yield d[tag]
    for k, v in d.items():
        if isinstance(v, dict):
            for i in find(v, tag):
                yield i

def change_config(conf, key, value):
    if isinstance(conf, dict):
        for k, v in conf.items():
            if k == key:
                conf[k] = value
            elif isinstance(v, dict):
                change_config(v, key, value)

def set_value_yaml_config(key,value):
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    logger.info("sourceInstallerDirectory:"+sourceInstallerDirectory)
    with open(sourceInstallerDirectory+"/odsx/app.yaml", "r") as f:
        yaml_data = yaml.load(f, Loader=yaml.Loader)
    change_config(yaml_data, key, value)
    with open(sourceInstallerDirectory+"/odsx/app.yaml", "w") as f:
        yaml.dump(yaml_data, f)