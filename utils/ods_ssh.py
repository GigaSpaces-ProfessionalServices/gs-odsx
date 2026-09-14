#!/usr/bin/env python3
import getpass
import os
import subprocess
from subprocess import Popen, PIPE
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_validation import isValidHost
from scripts.logManager import LogManager

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

def get_ssh_user():
    user = readValuefromAppConfig("app.server.user")
    return user if user else getpass.getuser()

# Absolute path to the bash helper that defines read_property() (and
# validate_nonempty_paths). Resolved relative to this file so it works no
# matter what the caller's cwd is.
_LIB_APP_CONFIG = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "scripts", "lib_app_config.sh")
)

def build_remote_bash_cmd(host, user, shellScript, bash_args=""):
    """
    Build a `cat lib_app_config.sh script.sh | ssh user@host bash <bash_args>` command.

    Prepending lib_app_config.sh defines read_property() (and validate_nonempty_paths)
    on the remote — REQUIRED for any remote shell script that reads paths from
    app.config. Loud failure if the helper file is missing locally, since silent
    degradation here previously caused a `rm -rf /*` event in production.

    bash_args examples:
      ""             -> remote runs `bash` (script body via stdin, no positional args)
      "-s foo bar"   -> remote runs `bash -s foo bar` (positional args $1=foo $2=bar)
      "-l"           -> remote runs `bash -l` as a login shell
      "-l -s baz"    -> login shell with positional args
    """
    if not os.path.isfile(_LIB_APP_CONFIG):
        raise FileNotFoundError(
            "Required helper missing: {}. Cannot build remote SSH command "
            "without read_property() definition.".format(_LIB_APP_CONFIG)
        )
    isConnectUsingPem = readValuefromAppConfig("cluster.usingPemFile")
    pemFileName = readValuefromAppConfig("cluster.pemFile")
    pem = " -i " + pemFileName if isConnectUsingPem == "True" else ""
    bash_args = bash_args.strip()
    bash_part = ("bash " + bash_args) if bash_args else "bash"
    return "cat {helper} {script} | ssh{pem} {user}@{host} {bash_part}".format(
        helper=_LIB_APP_CONFIG,
        script=shellScript,
        pem=pem,
        user=user,
        host=host,
        bash_part=bash_part,
    )

def connectExecuteSSH(host, user, shellScript, params):
    if not isValidHost(host):
        print("Invalid Host / IP." + str(host))
        return
    bash_args = ("-s " + params) if (params and len(params) > 0) else ""
    cmd = build_remote_bash_cmd(host, user, shellScript, bash_args)
    logger.info("cmd:" + str(cmd))
    os.system(cmd)

def connectExecuteSSHWithLoginProxy(host, user, shellScript, params):
    if not isValidHost(host):
        print("Invalid Host / IP." + str(host))
        return
    bash_args = ("-l -s " + params) if (params and len(params) > 0) else "-l"
    cmd = build_remote_bash_cmd(host, user, shellScript, bash_args)
    logger.info("cmd:" + str(cmd))
    os.system(cmd)

def executeRemoteCommandAndGetOutput(host, user, commandToExecute):
    logger.info("executeRemoteCommandAndGetOutput host:"+str(host)+" user:"+str(user)+" commmandToExecute:"+str(commandToExecute))
    pemFileName = readValuefromAppConfig("cluster.pemFile")
    logger.info("pemFileName : "+str(pemFileName))
    isConnectUsingPem = readValuefromAppConfig("cluster.usingPemFile")
    logger.info("isConnectUsingPem :"+str(isConnectUsingPem))
    if(isConnectUsingPem=='True'):
        cmd = "ssh -i " + pemFileName + " " + user + "@" + host + " " + commandToExecute
    else:
        cmd = "ssh" +" " + user + "@" + host + " " + commandToExecute
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
        cmd = "ssh" +" " + user + "@" + host + " " + commandToExecute
    logger.info("cmd :"+str(cmd))
    cmdArray = cmd.split(" ")
    logger.info("cmdArray:"+str(cmdArray))
    #out = subprocess.call(cmdArray)
    p = Popen(cmdArray,stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output = p.communicate(b"input data that is passed to subprocess' stdin")
    rc = p.returncode
    logger.info("output : rc:"+str(rc))
    return rc

def executeRemoteCommandAndGetOutputValuePython36(host, user, commandToExecute):
    logger.info("executeRemoteCommandAndGetOutputPython36 : "+str(user)+" host:"+str(host)+" "+str(commandToExecute))
    pemFileName = readValuefromAppConfig("cluster.pemFile")
    logger.info("cluster.pemFile :"+str(pemFileName))
    isConnectUsingPem = readValuefromAppConfig("cluster.usingPemFile")
    logger.info("cluster.usingPemFile :"+str(isConnectUsingPem))
    if(isConnectUsingPem=='True'):
        cmd = "ssh -i " + pemFileName + " " + user + "@" + host + " " + commandToExecute
    else:
        cmd = "ssh" +" " + user + "@" + host + " " + commandToExecute
    logger.info("cmd :"+str(cmd))
    cmdArray = cmd.split(" ")
    logger.info("cmdArray:"+str(cmdArray))
    #out = subprocess.call(cmdArray)
    p = Popen(cmdArray,stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, err = p.communicate(b"input data that is passed to subprocess' stdin")
    rc = p.returncode
    logger.info("output : rc:"+str(rc))
    logger.info("output : output:"+str(output))
    logger.info("output : err:"+str(err))
    # print(output.decode("utf-8"))
    return output.decode("utf-8")

def executeRemoteShCommandAndGetOutput(host, user, additionalparam, commandToExecute):
    logger.info("executeRemoteShCommandAndGetOutput host:"+str(host)+" user:"+str(user)+" additinalparam:"+str(additionalparam)+" cmdtoexec:"+str(commandToExecute))
    bash_args = "-s " + additionalparam if additionalparam else "-s"
    cmd = build_remote_bash_cmd(host, user, commandToExecute, bash_args)
    logger.info("cmd:" + str(cmd))
    output = subprocess.check_output(cmd, shell=True)
    logger.info("output:" + str(output))
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
