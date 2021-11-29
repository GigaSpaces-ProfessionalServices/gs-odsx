#!/usr/bin/env python3
import os
import subprocess
from subprocess import Popen, PIPE
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_validation import isValidHost
from scripts.logManager import LogManager

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

def connectExecuteSSH(host, user, shellScript, params):
    if (isValidHost(host)):
        isConnectUsingPem = readValuefromAppConfig("cluster.usingPemFile")
        pemFileName = readValuefromAppConfig("cluster.pemFile")
        if (isConnectUsingPem=='True'):
            ssh = ''.join(['ssh', ' -i ', pemFileName, ' ', user, '@', host, ' '])
        else:
            ssh = ''.join(['ssh', ' ', host, ' '])
        if (len(params) > 0):
            cmd = ssh + 'bash' + ' -s ' + params + ' < ' + shellScript  # + '>> myl
        else:
            cmd = ssh + 'bash' + ' < ' + shellScript  # + '>> myl
        status = os.system(cmd)
    else:
        print("Invalid Host / IP."+str(host))


def executeRemoteCommandAndGetOutput(host, user, commandToExecute):
    logger.info("executeRemoteCommandAndGetOutput host:"+str(host)+" user:"+str(user)+" commmandToExecute:"+str(commandToExecute))
    pemFileName = readValuefromAppConfig("cluster.pemFile")
    logger.info("pemFileName : "+str(pemFileName))
    isConnectUsingPem = readValuefromAppConfig("cluster.usingPemFile")
    logger.info("isConnectUsingPem :"+str(isConnectUsingPem))
    if(isConnectUsingPem=='True'):
        cmd = "ssh -i " + pemFileName + " " + user + "@" + host + " " + commandToExecute
    else:
        cmd = "ssh" +" " + host + " " + commandToExecute
    logger.info("cmd :"+str(cmd))
    cmdArray = cmd.split(" ")
    logger.info("cmdArray:"+str(cmdArray))
    out = subprocess.check_output(cmdArray, universal_newlines=True)
    logger.info("out:"+str(out))
    return out

def executeRemoteCommandAndGetOutputPython36(host, user, commandToExecute):
    logger.info("executeRemoteCommandAndGetOutputPython36 : "+str(user)+" host:"+str(host)+" "+str(commandToExecute))
    pemFileName = readValuefromAppConfig("cluster.pemFile")
    logger.info("cluster.pemFile :"+str(pemFileName))
    isConnectUsingPem = readValuefromAppConfig("cluster.usingPemFile")
    logger.info("cluster.usingPemFile :"+str(isConnectUsingPem))
    if(isConnectUsingPem=='True'):
        cmd = "ssh -i " + pemFileName + " " + user + "@" + host + " " + commandToExecute
    else:
        cmd = "ssh" +" " + host + " " + commandToExecute
    logger.info("cmd :"+str(cmd))
    cmdArray = cmd.split(" ")
    logger.info("cmdArray:"+str(cmdArray))
    #out = subprocess.call(cmdArray)
    p = Popen(cmdArray,stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, err = p.communicate(b"input data that is passed to subprocess' stdin")
    rc = p.returncode
    logger.info("output : rc:"+str(rc))
    return rc


def executeRemoteShCommandAndGetOutput(host, user, additionalparam, commandToExecute):
    logger.info("executeRemoteShCommandAndGetOutput host:"+str(host)+" user:"+str(user)+" additinalparam:"+str(additionalparam)+" cmdtoexec:"+str(commandToExecute))
    pemFileName = readValuefromAppConfig("cluster.pemFile")
    logger.info("pemFileName : "+str(pemFileName))
    # ssh -i aharon_ami.pem ec2-user@34.245.126.19 < scripts/streams_status.sh
    isConnectUsingPem = readValuefromAppConfig("cluster.usingPemFile")
    logger.info("isConnectUsingPem :"+str(isConnectUsingPem))
    if(isConnectUsingPem=='True'):
        cmd = "ssh -i " + pemFileName + ' ' + user + "@" + host + ' ' + 'bash' + ' -s ' + additionalparam + " < " + commandToExecute
    else:
        cmd = "ssh " + host + ' ' + 'bash' + ' -s ' + additionalparam + " < " + commandToExecute
    logger.info("cmd:"+str(cmd))
    output = subprocess.check_output(cmd, shell=True)
    logger.info("output:"+str(output))
    return output


def executeLocalCommandAndGetOutput(commandToExecute):
    logger.info("executeLocalCommandAndGetOutput : "+str(commandToExecute))
    cmd = commandToExecute
    #print(cmd)
    cmdArray = cmd.split(" ")
    logger.info("cmdArray"+str(cmdArray))
    #out = subprocess.call(cmdArray, text=True)
    process = subprocess.Popen(cmdArray, stdout=subprocess.PIPE)
    out, error = process.communicate()
    logger.info("out :"+str(out))
    # out = out.replace("b'", "")
    return str(out)

def executeShCommandAndGetOutput(cmd,additionalParam):
    logger.info("executeShCommandAndGetOutput : "+str(cmd)+" param :"+str(additionalParam))
    cmd = cmd+' '+additionalParam
    logger.info("cmd:",cmd)
    output = subprocess.check_output(cmd)
    logger.info("output:"+str(output))
    return output
# if __name__ == '__main__':
# connectExecuteSSH('18.188.136.81','ec2-user','ssh_test.sh','')
# out = executeRemoteCommandAndGetOutput("3.140.195.199", "ec2-user",
#                                      "export CONSUL_HTTP_ADDR=3.140.195.199:8500; consul members")
