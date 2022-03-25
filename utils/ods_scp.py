#!/usr/bin/env python3
# !/usr/bin/python
import os
from os import path
from utils.ods_app_config import readValuefromAppConfig
from scripts.logManager import LogManager

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


def scp_download(host, user, sourceFileWithPath, destPath):
    logger.debug(
        "Host: " + host + " User: " + user + " SourceFileWithPath:" + sourceFileWithPath + " DestPath:" + destPath)
    if (path.exists(destPath)):
        verboseHandle.printConsoleInfo("Downloading by scp...")
        pemFileName = readValuefromAppConfig("cluster.pemFile")
        isConnectUsingPem = readValuefromAppConfig("cluster.usingPemFile")
        if (isConnectUsingPem=='True'):
            ssh = ''.join(['scp', ' -i ', pemFileName, ' ', user, '@', host, ':'])
        else:
            ssh = ''.join(['scp', host, ':'])
        # scp -i ps-share.pem ubuntu@18.222.185.155:uninstall.sh /home/tapan/
        cmd = ssh + sourceFileWithPath + ' ' + destPath  # + type  ' < ' + cmd #+ '>> mylog.txt 2>&1'
        logger.debug("scp cmd : " + cmd)
        status = os.system(cmd)
        if (status == 0):
            verboseHandle.printConsoleInfo("File downloaded to " + destPath)
        else:
            verboseHandle.printConsoleError("Unable to download file.")
    else:
        verboseHandle.printConsoleError("Please check destination path exist or not :" + destPath)


def scp_upload(host, user, sourceFileWithPath, destPath):
    logger.debug(
        "Host: " + host + " User: " + user + " SourceFileWithPath:" + sourceFileWithPath + " DestPath:" + destPath)
    if (path.exists(sourceFileWithPath)):
        verboseHandle.printConsoleInfo("Uploading by scp...")
        pemFileName = readValuefromAppConfig("cluster.pemFile")
        isConnectUsingPem = readValuefromAppConfig("cluster.usingPemFile")
        if (isConnectUsingPem=='True'):
            ssh = ''.join(['scp', ' -i ', pemFileName, ' -r ', sourceFileWithPath, ' ', user, '@', host, ':'])
        else:
            ssh = ''.join(['scp',' -r ', sourceFileWithPath, ' ', host, ':'])
        # scp -i ps-share.pem /home/tapan/uninstall_1.sh ubuntu@18.222.185.155:
        cmd = ssh + destPath  # + type  ' < ' + cmd #+ '>> mylog.txt 2>&1'
        print(cmd)
        status = os.system(cmd)
        if (status == 0):
            verboseHandle.printConsoleInfo("File uploaded to " + destPath+' '+host)
            return True
        else:
            verboseHandle.printConsoleError("Unable to upload file.")
            return False
    else:
        verboseHandle.printConsoleError("Please check source path exist or not :" + sourceFileWithPath)
        return False

def scp_upload_multiple(host, user, sourceFileWithPath, destPath):
    print("sourceFileWithPath :"+sourceFileWithPath)
    logger.debug(
        "Host: " + host + " User: " + user + " SourceFileWithPath:" + sourceFileWithPath + " DestPath:" + destPath)

    for pathOfJar in str(sourceFileWithPath).split(" "):
        if (path.exists(pathOfJar)):
            verboseHandle.printConsoleInfo("File "+pathOfJar+" exist.")
        else:
            verboseHandle.printConsoleError("Please check source path exist or not :" + sourceFileWithPath)
            return False
    verboseHandle.printConsoleInfo("Uploading by scp...")
    pemFileName = readValuefromAppConfig("cluster.pemFile")
    isConnectUsingPem = readValuefromAppConfig("cluster.usingPemFile")
    if (isConnectUsingPem=='True'):
        ssh = ''.join(['scp', ' -i ', pemFileName, ' -r ', sourceFileWithPath, ' ', user, '@', host, ':'])
    else:
        ssh = ''.join(['scp',' -r ', sourceFileWithPath, ' ', host, ':'])
    # scp -i ps-share.pem /home/tapan/uninstall_1.sh ubuntu@18.222.185.155:
    cmd = ssh + destPath  # + type  ' < ' + cmd #+ '>> mylog.txt 2>&1'
    print(cmd)
    status = os.system(cmd)
    if (status == 0):
        verboseHandle.printConsoleInfo("File uploaded to " + destPath+' '+host)
        return True
    else:
        verboseHandle.printConsoleError("Unable to upload file.")
        return False

def scp_upload_specific_extension(host, user, sourceFileWithPath, destPath,extension):
    logger.debug(
        "Host: " + host + " User: " + user + " SourceFileWithPath:" + sourceFileWithPath+'/*'+extension + " DestPath:" + destPath)
    if (path.exists(sourceFileWithPath)):
        verboseHandle.printConsoleInfo("Uploading by scp...")
        pemFileName = readValuefromAppConfig("cluster.pemFile")
        isConnectUsingPem = readValuefromAppConfig("cluster.usingPemFile")
        if (isConnectUsingPem=='True'):
            ssh = ''.join(['scp', ' -i ', pemFileName, ' -r ', sourceFileWithPath+'/*.'+extension, ' ', user, '@', host, ':'])
        else:
            ssh = ''.join(['scp',' -r ', sourceFileWithPath+'/*.'+extension, ' ', host, ':'])
        # scp -i ps-share.pem /home/tapan/uninstall_1.sh ubuntu@18.222.185.155:
        cmd = ssh + destPath  # + type  ' < ' + cmd #+ '>> mylog.txt 2>&1'
        print(cmd)
        status = os.system(cmd)
        if (status == 0):
            verboseHandle.printConsoleInfo("File uploaded to " + destPath+' '+host)
            return True
        else:
            verboseHandle.printConsoleError("Unable to upload file.")
            return False
    else:
        verboseHandle.printConsoleError("Please check source path exist or not :" + sourceFileWithPath)
        return False