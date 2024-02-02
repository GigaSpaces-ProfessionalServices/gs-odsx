#!/usr/bin/env python3

import os
from collections import defaultdict

from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_monitors_alerts_services_telegraf_list import listAllTelegrafServers
from scripts.odsx_servers_northbound_management_remove import getNBFolderName
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_space_node, config_get_manager_node, config_get_space_hosts, \
    config_get_nb_list, config_get_dataIntegration_nodes
from utils.ods_scp import scp_upload
from utils.ods_ssh import connectExecuteSSH, connectExecuteSSHWithLoginProxy, executeRemoteCommandAndGetOutput, \
    executeRemoteShCommandAndGetOutput
from utils.odsx_keypress import userInputWithEscWrapper, userInputWrapper
from utils.odsx_read_properties_file import createPropertiesMapFromFile

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR

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

def getManagerHostFromEnv():
    logger.info("getManagerHostFromEnv()")
    hosts = ''
    managerNodes = config_get_manager_node()
    for node in managerNodes:
        hosts+=str(os.getenv(str(node.ip)))+','
    hosts=hosts[:-1]
    return hosts

def proceedForPreInstallation(param,hostip):
    logger.info("proceedForPreInstallation : "+param)
    nb_user='root'
    remotePath='/dbagiga'
    sourceInstallerDirectory = str(os.getenv("ENV_CONFIG"))
    sourceInstallerDirectoryTar = str(os.getenv("ODSXARTIFACTS"))
    cmd = 'tar -cvf install/install.tar install' # Creating .tar file on Pivot machine
    with Spinner():
        status = os.system(cmd)
        logger.info("Creating tar file status : "+str(status))

    cmd = 'mkdir -p '+remotePath+'; chmod 777 /dbagiga'
    logger.info("cmd :"+str(cmd))
    with Spinner():
        output = executeRemoteCommandAndGetOutput(hostip, nb_user, cmd)
        logger.info("Created directory "+str(remotePath))
    logger.info("hostip : "+str(hostip))

    with Spinner():
        logger.info("hostip ::"+str(hostip)+" user :"+str(nb_user)+" remotePath: "+str(remotePath))
        scp_upload(hostip, nb_user, 'install/install.tar', '')

    if param.casefold()=='agent':
        remotePath='/dbagiga'
        commandToExecute="scripts/servers_northbound_agent_preinstall.sh"
    logger.info("commandToExecute :"+commandToExecute)
    nbConfig = sourceInstallerDirectory+"/nb/applicative/nb.conf.template"
    nbConfig = createPropertiesMapFromFile(nbConfig)
    sslCert = str(nbConfig.get("SSL_CERTIFICATE"))
    sslKey = str(nbConfig.get("SSL_PRIVATE_KEY"))
    sslCaCert = str(nbConfig.get("SSL_CA_CERTIFICATE"))
    additionalParam=remotePath+' '+sourceInstallerDirectory + ' '+sourceInstallerDirectoryTar + ' ' +sslCert +' '+sslKey+ ' '+sslCaCert

    logger.debug("Additional Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(hostip)+" User:"+str(nb_user))

    with Spinner():
        outputShFile= executeRemoteShCommandAndGetOutput(hostip, nb_user, additionalParam, commandToExecute)
        logger.info("Output"+str(outputShFile))


def proceedForNBInstallation(host):
    logger.info("proceedForNBInstallation()")
    remotePath='/dbagiga/'+getNBFolderName()
    nb_user='root'
    proceedForPreInstallation('AGENT',host)
    with Spinner():
        logger.info("connectExecuteSSHWithLoginProxy Agent: hostip "+str(host)+" user:"+str(nb_user)+" remotePath:"+str(remotePath))
        connectExecuteSSHWithLoginProxy(host, nb_user, "scripts/servers_northbound_install.sh", remotePath + " -t")
    logger.info("Completed installation for all agent server")
    verboseHandle.printConsoleInfo("Completed installation for all agent server")

def executeCommandForInstall(host, hostType):
    logger.info("executeCommandForInstall(): start")
    try:
        commandToExecute="scripts/monitors_alerts_service_telegraf_install.sh"
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))#str(readValuefromAppConfig("app.setup.sourceInstaller"))
        additionalParam=sourceInstallerDirectory+' '+getManagerHostFromEnv() + ' '+hostType
        logger.info("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+host+" User:"+str(user)+" sourceInstaller:"+sourceInstallerDirectory)
        with Spinner():

                outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
                verboseHandle.printConsoleInfo("Telegraf  has been installed on host :"+host)
    except Exception as e:
        handleException(e)
    logger.info("executeCommandForInstall(): end")

def agentCommandForInstall(host,hostType):
    logger.info("executeCommandForInstall(): start")
    try:
        commandToExecute="scripts/monitors_alerts_service_telegraf_agent_install.sh"
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))#str(readValuefromAppConfig("app.setup.sourceInstaller"))
        additionalParam=sourceInstallerDirectory+ ' '+hostType
        logger.info("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user)+" sourceInstaller:"+sourceInstallerDirectory)
        with Spinner():
            outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
            verboseHandle.printConsoleInfo("Telegraf  has been installed on host :"+str(host))
    except Exception as e:
        handleException(e)
    logger.info("executeCommandForInstall(): end")

def executeCommandForAgentPathCopy(hostType):
    nodelist = getSpaceServerList()
    for node in nodelist.split(','):
        agentCommandForInstall(node,hostType)

def getSpaceServerList():
    nodeList = config_get_space_node()
    nodes = ""
    for node in nodeList:
        if (len(nodeList) == 1):
            nodes = os.getenv(node.ip)
        else:
            nodes = nodes + ',' + os.getenv(node.ip)
    if nodes[0]==',':
        nodes=nodes[1:]
    return nodes
def getHostAndTypeDict():
    managerNodes = config_get_manager_node()
    nodeDict = defaultdict(list)
    for node in managerNodes:
        host = os.getenv(node.ip)
        nodeDict[host].append("manager")
    spaceServers = config_get_space_hosts()

    for server in spaceServers:
        host = os.getenv(server.ip)
        nodeDict[host].append("space")

    nbServers = config_get_nb_list()
    for server in nbServers:
        host = os.getenv(server.ip)
        if(str(server.role).__contains__('applicative') or str(server.role).__contains__('management')):
            nodeDict[host].append("nb")
    host = os.getenv("pivot1")
    nodeDict[host].append("pivot")

    env = str(readValuefromAppConfig("app.setup.env"))
    if env != "dr":
        dIServers = config_get_dataIntegration_nodes()
        for node in dIServers:
            host = os.getenv(node.ip)
            nodeDict[host].append("di")
    return nodeDict

def getHostNoAndTypeDict():
    logger.info("Manager server list :")
    headers = [Fore.YELLOW+"Sr No"+Fore.RESET,
               Fore.YELLOW+"Type of host"+Fore.RESET,
               Fore.YELLOW+"IP"+Fore.RESET,
               Fore.YELLOW+"Installed"+Fore.RESET,
               Fore.YELLOW+"Status"+Fore.RESET]
    data=[]
    managerNodes = config_get_manager_node()
    count = 0
    spaceDict = {}
    for node in managerNodes:
        count = count+1
        host = os.getenv(node.ip)
        spaceDict.update({count: "manager"})
    spaceServers = config_get_space_hosts()
    for server in spaceServers:
        count = count+1
        host = os.getenv(server.ip)
        spaceDict.update({count: "space"})
    nbServers = config_get_nb_list()
    for server in nbServers:
        host = os.getenv(server.ip)
        if(str(server.role).__contains__('applicative') or str(server.role).__contains__('management')):
            count = count+1
            spaceDict.update({count: "nb"})
    count=count+1
    spaceDict.update({count: "pivot"})
    #
    env = str(readValuefromAppConfig("app.setup.env"))
    if env != "dr":
        logger.info("DI servers list")
        dIServers = config_get_dataIntegration_nodes()
        counter=1
        for node in dIServers:
            count=count+1
            spaceDict.update({count: "di"})
    return spaceDict

def exitAndDisplay(isMenuDriven):
    logger.info("exitAndDisplay(isMenuDriven)")
    if(isMenuDriven=='m'):
        logger.info("exitAndDisplay(MenuDriven) ")
        os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_install.py'+' '+isMenuDriven)
    else:
        cliArgumentsStr=''
        for arg in cliArguments:
            cliArgumentsStr+=arg
            cliArgumentsStr+=' '
        os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_install.py'+' '+cliArgumentsStr)

def summaryInstall(host,hostType):
    #To Display Summary ::
    telegrafSpaceScriptFiles =[]
    telegrafPivotScriptFiles =[]
    telegrafSpaceConfigFiles =[]
    telegrafPivotConfigFiles =[]
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
    rpmPath=sourceInstallerDirectory+"/telegraf"

    #for file in glob.glob(rpmPath+"/*.rpm"):
    #    rpmFile=file
    rpmFile = [f for f in os.listdir(str(rpmPath)+"/") if f.endswith('.rpm')]
    telegrafSourcePath = rpmPath+"/scripts/"+hostType+"/"
    telegrafTartgetPath = str(readValuefromAppConfig("app.alert.telegraf.custommetrics"))
    telegrafConfSourcePath = rpmPath+"/config/"+hostType+"/"
    telegrafConfTartgetPath = "/etc/telegraf/telegraf.conf"
    #print(hostAndType)
    for scriptSpace in os.listdir(rpmPath+"/scripts/space/"):
        telegrafSpaceScriptFiles.append(scriptSpace)

    for scriptPivot in os.listdir(rpmPath+"/scripts/pivot/"):
        telegrafPivotScriptFiles.append(scriptPivot)

    for configSpace in os.listdir(rpmPath+"/config/space/"):
        telegrafSpaceConfigFiles.append(configSpace)

    for configPivot in os.listdir(rpmPath+"/config/pivot/"):
        telegrafPivotConfigFiles.append(configPivot)

    verboseHandle.printConsoleWarning("------------------------------------------------------------")
    verboseHandle.printConsoleWarning("***Summary***")
    count=1
    print(Fore.GREEN+str(count)+". "+
          Fore.GREEN+"Telegraf Version = "+
          Fore.GREEN+str(rpmFile)+Fore.RESET)
    count=count+1
    if os.path.exists(telegrafSourcePath):
        print(Fore.GREEN+str(count)+". "+
              Fore.GREEN+"Script source path = "+
              Fore.GREEN+str(telegrafSourcePath)+Fore.RESET)
        count=count+1
        print(Fore.GREEN+str(count)+". "+
              Fore.GREEN+"Script target path = "+
              Fore.GREEN+str(telegrafTartgetPath)+Fore.RESET)
        count=count+1
    if hostType == "pivot":
        print(Fore.GREEN+str(count)+". "+
              Fore.GREEN+"Scripts pivot files = "+
              Fore.GREEN+str(telegrafPivotScriptFiles)+Fore.RESET)
        count=count+1
        print(Fore.GREEN+str(count)+". "+
              Fore.GREEN+"Configuration pivot files = "+
              Fore.GREEN+str(telegrafPivotConfigFiles)+Fore.RESET)
        count=count+1
    if hostType == "space":
        print(Fore.GREEN+str(count)+". "+
              Fore.GREEN+"Scripts space files = "+
              Fore.GREEN+str(telegrafSpaceScriptFiles)+Fore.RESET)
        count=count+1
        print(Fore.GREEN+str(count)+". "+
              Fore.GREEN+"Configuration space files = "+
              Fore.GREEN+str(telegrafSpaceConfigFiles)+Fore.RESET)
        count=count+1
    if os.path.exists(telegrafConfSourcePath):
        print(Fore.GREEN+str(count)+". "+
              Fore.GREEN+"Configuration source path = "+
              Fore.GREEN+str(telegrafConfSourcePath)+Fore.RESET)
        count=count+1
        print(Fore.GREEN+str(count)+". "+
              Fore.GREEN+"Configuration target path = "+Fore.RESET,
              Fore.GREEN+telegrafConfTartgetPath+Fore.RESET)
    if(host != 0):
        count=count+1
        print(Fore.GREEN+str(count)+". "+
              Fore.GREEN+"Host = "+
              Fore.GREEN+str(host)+Fore.RESET)
    verboseHandle.printConsoleWarning("------------------------------------------------------------")

if __name__ == '__main__':
    logger.info("Menu -> Monitors -> Alerts -> Service -> Telegraf -> Install ")
    verboseHandle.printConsoleWarning('Menu -> Monitors -> Alerts -> Service -> Telegraf -> Install')
    global hostAndType
    try:
        streamResumeStream=''
        optionMainMenu=''
        choice=''
        cliArguments=''
        isMenuDriven=''
        managerRemove=''
        user='root'
        logger.info("user :"+str(user))
        streamDict = listAllTelegrafServers()
        serverInstallType = str(userInputWithEscWrapper(Fore.YELLOW+"press [1] if you want to install individual server. \nPress [Enter] to install all. \nPress [99] for exit.: "+Fore.RESET))
        logger.info("serverInstallType:"+str(serverInstallType))
        #hostAndType = getHostAndTypeDict()
        hostAndType = getHostNoAndTypeDict()
        if(serverInstallType=='1'):
            optionMainMenu = int(userInputWrapper("Enter your host number to install: "))
            logger.info("Enter your host number to install:"+str(optionMainMenu))
            if(optionMainMenu != 99):
                if len(streamDict) >= optionMainMenu:
                    host = streamDict.get(optionMainMenu)
                    summaryInstall(host,hostAndType.get(optionMainMenu))
                    choice = str(userInputWrapper(Fore.YELLOW+"Are you sure want to install server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    while(len(str(choice))==0):
                        choice = str(userInputWrapper(Fore.YELLOW+"Are you sure want to install server ? [yes (y)] / [no (n)] / [cancel (c)] :"+Fore.RESET))
                    logger.info("choice :"+str(choice))
                    if(choice.casefold()=='no' or choice.casefold()=='n'):
                        if(isMenuDriven=='m'):
                            logger.info("menudriven")
                            os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_install.py'+' '+isMenuDriven)
                        else:
                            exitAndDisplay(isMenuDriven)
                    elif(choice.casefold()=='yes' or choice.casefold()=='y'):
                        proceedForNBInstallation(host)
                        if(os.getenv("pivot1")==host):
                           executeCommandForInstall(host,hostAndType.get(optionMainMenu))
                           executeCommandForAgentPathCopy(hostAndType.get(optionMainMenu))
                        else:
                            executeCommandForInstall(host,hostAndType.get(optionMainMenu))

        elif(serverInstallType =='99'):
            logger.info("99 - Exist install")
        else:
            confirm=''
            confirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to install all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            while(len(str(confirm))==0):
                confirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to install all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            logger.info("confirm :"+str(confirm))
            if(confirm=='yes' or confirm=='y'):
                count=1
                for host in streamDict:
                    proceedForNBInstallation(host)
                    if(os.getenv("pivot1")==streamDict.get(host)):
                      executeCommandForInstall(streamDict.get(host, hostAndType.get(count)))
                      executeCommandForAgentPathCopy(hostAndType.get(count))
                    else:
                      executeCommandForInstall(streamDict.get(host, hostAndType.get(count)))
                    count = count + 1

            elif(confirm =='no' or confirm=='n'):
                if(isMenuDriven=='m'):
                    logger.info("menudriven")
                    os.system('python3 scripts/odsx_monitors_alerts_service_telegraf_install.py'+' '+isMenuDriven)
    except Exception as e:
        handleException(e)