#!/usr/bin/env python3
import os
import signal

from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig, getYamlFilePathInsideFolder
from utils.ods_cleanup import signal_handler
from utils.ods_cluster_config import config_get_manager_node, config_get_space_hosts
from utils.ods_scp import scp_upload
from utils.ods_ssh import executeRemoteShCommandAndGetOutput, connectExecuteSSH
from utils.odsx_keypress import userInputWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
serviceName = "object-management.service"
user = "root"
app_config_space_key = 'app.tieredstorage.pu.spacename'

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

def buildTarFileToLocalMachine():
    logger.info("buildTarFileToLocalMachine :")
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))#str(readValuefromAppConfig("app.setup.sourceInstaller"))
    userCMD = os.getlogin()
    if userCMD == 'ec2-user':
        cmd= 'sudo cp install/space-update-cache-policy.service '+sourceInstallerDirectory+"/"
    else:
        cmd= 'cp install/space-update-cache-policy.service '+sourceInstallerDirectory+"/"
    with Spinner():
        status = os.system(cmd)
    cmd = 'tar -cvf install/install.tar install'#+sourceInstallerDirectory  # Creating .tar file on Pivot machine
    with Spinner():
        status = os.system(cmd)
        logger.info("Creating tar file status : " + str(status))


def buildUploadInstallTarToServer(host):
    logger.info("buildUploadInstallTarToServer(): start host :" + str(host))
    try:
        with Spinner():
            logger.info("hostip ::" + str(host) + " user :" + str(user))
            scp_upload(host, user, 'install/install.tar', '')
    except Exception as e:
        handleException(e)

def getManagerHostFromEnv():
    logger.info("getManagerHostFromEnv()")
    hosts = ''
    managerNodes = config_get_manager_node()
    for node in managerNodes:
        hosts += str(os.getenv(str(node.ip))) + ','
    hosts = hosts[:-1]
    return hosts


def setupService():
    logger.info("setupService() : start")

    tieredCriteriaConfigFilePath = str(
        getYamlFilePathInsideFolder(".object.config.ddlparser.ddlCriteriaFileName")).replace('"', '')
    xapWorkLocation = readValuefromAppConfig("app.xap.workLocation")

    displaySummary(tieredCriteriaConfigFilePath, xapWorkLocation)

    confirmMsg = Fore.YELLOW + "Are you sure, you want to setup update cache policy service on each space servers ? (Yes/No) [Yes]:" + Fore.RESET
    choice = str(userInputWrapper(confirmMsg))
    if (len(choice) == 0):
        choice = 'y'

    while (
            choice.casefold() != 'yes' and choice.casefold() != 'no' and choice.casefold() != 'y' and choice.casefold() != 'n'):
        verboseHandle.printConsoleError("Invalid input")
        choice = str(userInputWrapper(confirmMsg))

    if (choice.casefold() == 'no' or choice.casefold() == 'n'):
        logger.info("Exiting without registering update cache policy service on each space servers")
        exit(0)

    args = serviceJar + " " + tieredCriteriaConfigFilePath + " " + xapWorkLocation
    commandToExecute = "scripts/space_server_cache_policy_service_setup.sh "
    logger.info("Command " + commandToExecute)
    try:
        with Spinner():
            spaceNodes = config_get_space_hosts()
            additionalParam = ""
            counter = 1
            for host in spaceNodes:
                if (counter == 1):
                    buildTarFileToLocalMachine()
                buildUploadInstallTarToServer(os.getenv(host.ip))

                outputShFile = connectExecuteSSH(os.getenv(host.ip), user, commandToExecute, args)
                counter = counter + 1
                logger.info("outputShFile : " + str(outputShFile))
                print("outputShFile : " + str(outputShFile))

        verboseHandle.printConsoleInfo("space server cache policy service setup successfully!")
    except Exception as e:
        logger.error("error registering space server cache policy service=>" + str(e))
        handleException(e)

    logger.info("setupService() : end")


def displaySummary(tieredCriteriaConfigFilePath, xapWorkLocation):
    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleWarning("***Summary***")
    global serviceJar
    serviceJar = str(getYamlFilePathInsideFolder(".gs.jars.spaceupdatecachepolicy.jar")).replace("//", "/")
    print(Fore.GREEN + "1. " +
          Fore.GREEN + "Tiered criteria file path = " +
          Fore.GREEN + tieredCriteriaConfigFilePath + Fore.RESET)
    print(Fore.GREEN + "2. " +
          Fore.GREEN + "XAP work location = " +
          Fore.GREEN + xapWorkLocation + Fore.RESET)
    print(Fore.GREEN + "3. " +
          Fore.GREEN + "space update cache policy jar= " +
          Fore.GREEN + str(serviceJar) + Fore.RESET)
    verboseHandle.printConsoleWarning("------------------------------------------------------------")


if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Servers -> Space -> Service -> Setup")
    signal.signal(signal.SIGINT, signal_handler)
    setupService()
