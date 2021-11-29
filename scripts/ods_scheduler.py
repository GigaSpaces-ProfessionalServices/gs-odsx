#!/usr/bin/env python3
import argparse
import os
import shutil
import sys
import time
from datetime import datetime

import schedule

from scripts.logManager import LogManager
from utils.ods_cluster_config import config_update_timestamp

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')

    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])


# To print log on console also will be useful in verbose mode
# logger.addHandler(logging.StreamHandler())
# logger.addHandler(my_handler)

# Read app config file
configProperties = {}


def setConfigProperties():
    logger.debug("setting and reading properties from app config")
    file1 = open('config/app.config', 'r')
    Lines = file1.readlines()
    for line in Lines:
        if (line.startswith("#")) or len(line) < 2:
            continue
        line = line.replace("\n", "")
        configProperties.update({line.split("=")[0]: line.split("=")[1]})


def readValuefromAppConfig(key):
    setConfigProperties()
    return configProperties.get(key)


# set back scheduler time from config

def backupJob():
    existingFileCount = 1
    backUpPath = readValuefromAppConfig("cluster.config.snapshot.backup.path")
    while os.path.exists(os.path.join(backUpPath, "cluster.config.%s" % existingFileCount)):
        existingFileCount += 1
    existingFileCount -= 1
    while os.path.exists(os.path.join(backUpPath, "cluster.config.%s" % existingFileCount)):
        if int(configProperties.get("cluster.config.snapshot.maxbackup")) <= existingFileCount:
            logger.info("removing backup/cluster.config.%s" % existingFileCount)
            os.remove(os.path.join(backUpPath, "cluster.config.%s" % existingFileCount))
        else:
            os.rename(os.path.join(backUpPath, "cluster.config.%s" % existingFileCount),
                      os.path.join(backUpPath, "cluster.config." + str(existingFileCount + 1)))
        existingFileCount -= 1

    existingFileCount = 1
    currentConfigPath = os.path.join("config", "cluster.config")
    config_update_timestamp(currentConfigPath,verboseHandle.verboseFlag)
    shutil.copy(currentConfigPath, os.path.join(backUpPath, "cluster.config." + str(existingFileCount)))
    logger.info("backup done " + format(datetime.now()))


def setBackupJob():
    logger.debug("reading properties from app config")
    backupTime = configProperties.get("cluster.config.snapshot.time")
    if backupTime is None:
        backupTime = "10 min"
    if "sec" in backupTime:
        backupTimeInSec = int(str(backupTime).split("sec")[0].strip())
        logger.info("in sec " + format(backupTimeInSec))
        schedule.every(backupTimeInSec).seconds.do(backupJob)
    elif "min" in backupTime:
        backupTimeInMin = int(str(backupTime).split("min")[0].strip())
        logger.info("in min " + format(backupTimeInMin))
        schedule.every(backupTimeInMin).minutes.do(backupJob)
    elif "hour" in backupTime:
        backupTimeInHour = int(str(backupTime).split("hour")[0].strip())
        logger.info("in hour " + format(backupTimeInHour))
        schedule.every(backupTimeInHour).hours.do(backupJob)
    logger.debug("snapshot back up job scheduled for every " + backupTime)


myCheckArg()

setConfigProperties()
logger.debug(configProperties)
setBackupJob()

while True:
    schedule.run_pending()
    time.sleep(1)
