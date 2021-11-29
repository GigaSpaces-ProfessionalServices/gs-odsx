#!/usr/bin/env python3
import os.path

from scripts.logManager import LogManager

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

configProperties = {}


def createPropertiesMapFromFile(fileName):
    file1 = open(fileName, 'r')
    Lines = file1.readlines()
    for line in Lines:
        if (line.startswith("#")) or len(line) < 2:
            continue
        line = line.replace("\n", "")
        configProperties.update({line.split("=")[0]: line.split("=")[1]})
    return configProperties


def readValuefromPropertiesFileByKey(fileName, key, verbose=False):
    verboseHandle.setVerboseFlag(verbose)
    logger.debug("reading " + key + " from ")
    createPropertiesMapFromFile(fileName)
    return configProperties.get(key)
