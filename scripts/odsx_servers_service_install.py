#!/usr/bin/env python3
import os, subprocess, sys, argparse, platform,socket
from concurrent.futures import ThreadPoolExecutor

from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig, set_value_in_property_file, readValueByConfigObj, \
    set_value_in_property_file_generic, read_value_in_property_file_generic_section, readValueFromYaml, \
    getYamlJarFilePath, getYamlFilePathInsideFolder, getYamlFilePathInsideConfigFolder, getYamlFilePathInsideFolderList, \
    getYamlFileNamesInsideFolderList, getYamlFilePathInsideFolderList1
from colorama import Fore

from utils.ods_list import getManagerHostFromEnv, configureMetricsXML
from utils.ods_scp import scp_upload
from utils.ods_ssh import executeRemoteCommandAndGetOutput, executeRemoteShCommandAndGetOutput, connectExecuteSSH, \
    executeRemoteCommandAndGetOutputValuePython36
from utils.ods_cluster_config import config_add_service_node, config_get_cluster_airgap, config_get_service_hosts, isInstalledAndGetVersion, \
    config_get_service_list_with_status, getServiceHostFromEnv

from scripts.odsx_servers_manager_install import validateRPMS,getPlainOutput
from scripts.spinner import Spinner
from utils.ods_scp import scp_upload,scp_upload_specific_extension
from utils.odsx_keypress import userInputWrapper, userInputWithEscWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR

class host_nic_dictionary(dict):
    def __init__(self):
        self = dict()

    def add(self, key, value):
        self[key] = value

def myCheckArg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('m', nargs='?')
    parser.add_argument('--host',
                        help='host ip',
                        required='False',
                        default='localhost')
    parser.add_argument('-u', '--user',
                        help='user name',
                        default='root')
    parser.add_argument('-dryrun', '--dryrun',
                        help='Dry run flag',
                        default='false', action='store_true')
    return verboseHandle.checkAndEnableVerbose(parser, sys.argv[1:])

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

def getHostConfiguration():
    logger.info("getHostConfiguration()")
    try:
        hostsConfig=''
        hostsConfig =getManagerHostFromEnv()
        logger.info("Manager hostConfig : "+str(hostsConfig))
        applicativeUserFile = readValuefromAppConfig("app.server.user")
        applicativeUser = str(applicativeUserFile)
        logger.info("Applicative user : "+str(applicativeUser))
        set_value_in_property_file_generic('User',applicativeUser,'install/gs/gsa.service','Service')
        set_value_in_property_file_generic('User',applicativeUser,'install/gs/gsa.service','Service')
        set_value_in_property_file_generic('Group',applicativeUser,'install/gs/gsc.service','Service')
        set_value_in_property_file_generic('Group',applicativeUser,'install/gs/gsc.service','Service')

        if(len(hostsConfig)==2):
            hostsConfig=hostsConfig.replace('"','')
        return hostsConfig
    except Exception as e:
        handleException(e)


def execute_ssh_server_manager_install(hostsConfig,user):
    logger.info("execute_ssh_server_manager_install()")
    try:
        hostManager=[]
        gsNicAddress=''
        additionalParam=''
        hostManager=hostsConfig.replace('"','').split(",")
        logger.debug("optionID:"+str(hostsConfig))
        targetDirectory=''
        gsOptionExtFromConfig = str(readValueByConfigObj("app.space.gsOptionExt")).replace('[','').replace(']','').replace("'","").replace(', ',',')
        additionalParam = str(readValuefromAppConfig("app.space.targetDirectory"))
        targetDirectory=str(additionalParam)
        targetDirectory=additionalParam
        logger.info("targetDirecory :"+str(targetDirectory))
        gsOptionExt = ""
        gsOptionExt=gsOptionExtFromConfig
        gsOptionExt='"\\"{}\\""'.format(gsOptionExt)

        gsManagerOptionsFromConfig = str(readValueByConfigObj("app.manager.gsManagerOptions")).replace('[','').replace(']','')
        gsManagerOptions = ""
        gsManagerOptions=gsManagerOptionsFromConfig
        gsManagerOptions='"\\"{}\\""'.format(gsManagerOptions)

        gsLogsConfigFileFromConfig = str(getYamlFilePathInsideFolder(".gs.config.log.xap_logging")).replace('[','').replace(']','')
        gsLogsConfigFile = ""
        gsLogsConfigFile = str(readValuefromAppConfig("app.manager.gsLogsConfigFile"))

        licenseConfig = str(getYamlFilePathInsideFolder(".gs.config.license.gslicense"))
        gsLicenseFile = licenseConfig
        gsLicenseFile='"\\"{}\\""'.format(gsLicenseFile)

        applicativeUser = read_value_in_property_file_generic_section('User','install/gs/gsa.service','Service')

        nofileLimit = str(readValuefromAppConfig("app.user.nofile.limit"))
        nofileLimitFile = ""
        logger.info("hardNofileLimitFile : "+str(nofileLimitFile))
        nofileLimitFile = nofileLimit
        nofileLimitFile = '"{}"'.format(nofileLimitFile)

        wantToInstallJava = str(readValuefromAppConfig("app.space.wantInstallJava"))

        wantToInstallUnzip = str(readValuefromAppConfig("app.space.wantInstallUnzip"))
        global gscCount
        global memoryGSC
        global zoneGSC

        gscCountConfig = str(readValuefromAppConfig("app.space.gsc.count"))
        gscCount = ""
        gscCount = gscCountConfig

        memoryGSCConfig = str(readValuefromAppConfig("app.space.gsc.memory"))
        memoryGSC = ""
        memoryGSC = memoryGSCConfig

        zoneGSC = str(readValuefromAppConfig("app.space.gsc.zone"))

        sourceDirectoryForJar = str(readValuefromAppConfig("app.space.jar.sourceFolder"))
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
        logger.info("sourceInstallerDirectory :"+str(sourceInstallerDirectory))
        logTargetPath=str(readValuefromAppConfig("app.log.target.file"))
        logSourcePath=str(getYamlFilePathInsideFolder(".gs.config.log.xap_logging"))
        startSpaceGsc=str(readValuefromAppConfig("app.space.start.gsc.path"))
        if(len(additionalParam)==0):
            additionalParam= 'true'+' '+targetDirectory+' '+hostsConfig+' '+gsOptionExt+' '+gsManagerOptions+' '+gsLogsConfigFile+' '+gsLicenseFile+' '+applicativeUser+' '+nofileLimitFile+' '+wantToInstallJava+' '+wantToInstallUnzip+' '+gscCount+' '+memoryGSC+' '+zoneGSC+' '+sourceInstallerDirectory+' '+logSourcePath+' '+logTargetPath
        else:
            additionalParam='true'+' '+targetDirectory+' '+hostsConfig+' '+gsOptionExt+' '+gsManagerOptions+' '+gsLogsConfigFile+' '+gsLicenseFile+' '+applicativeUser+' '+nofileLimitFile+' '+wantToInstallJava+' '+wantToInstallUnzip+' '+gscCount+' '+memoryGSC+' '+zoneGSC+' '+sourceInstallerDirectory+' '+logSourcePath+' '+logTargetPath
        logger.debug('additional param :'+additionalParam)

        noOfHost=len(getServiceHostFromEnv().split(','))
        logger.debug("No of service host :"+str(noOfHost))
        host_nic_dict_obj = host_nic_dictionary()
        serviceHostConfig=getServiceHostFromEnv()
        for host in getServiceHostFromEnv().split(','):
            host_nic_dict_obj.add(host,'')
        wantNicAddress = str(readValuefromAppConfig("app.space.gsNicAddress"))
        if(len(str(wantNicAddress))==0):
            wantNicAddress='n'
        if(wantNicAddress=="yes" or wantNicAddress=="y"):
            for host in host_nic_dict_obj:
                nicAddr = str(userInputWrapper(Fore.YELLOW+"Enter GS_NIC_ADDRESS of service host"+str(host)+" :"+Fore.RESET))
                logger.debug("host enter:"+host+" nicAddr :"+nicAddr)
                host_nic_dict_obj.add(host,nicAddr)
        logger.debug("hostNicAddr :"+str(host_nic_dict_obj))

        cefLoggingJarInput = str(getYamlFilePathInsideFolder(".gs.jars.cef.cefjar")).replace('[','').replace(']','')
        cefLoggingJarInputTarget = str(readValuefromAppConfig("app.cefLogging.jar.target")).replace('[','').replace(']','')
        db2ccJarPath = ".db2.jars.db2ccjar"
        db2jccJarInput =str(readValueFromYaml(db2ccJarPath)).replace('[','').replace(']','')
        db2jccJarInput =getYamlJarFilePath(".db2.jars",db2jccJarInput)
        db2ccJarLicensePath=".db2.jars.db2ccLicense"
        db2jccJarLicenseInput = str(readValueFromYaml(db2ccJarLicensePath)).replace('[','').replace(']','')
        db2jccJarLicenseInput=getYamlJarFilePath(".db2.jars",db2jccJarLicenseInput)
        db2FeederJarTargetInput = str(readValuefromAppConfig("app.space.db2feeder.jar.target")).replace('[','').replace(']','')
        msSqlFeederFilePath="."
        msSqlFeederFileSource = str(os.getenv("ENV_CONFIG"))+str(msSqlFeederFilePath).replace('[','').replace(']','').replace('.','/')
        msSqlFeederFileTarget = str(readValuefromAppConfig("app.space.mssqlfeeder.files.target")).replace('[','').replace(']','')
        logTargetPath=str(readValuefromAppConfig("app.log.target.file"))
        logSourcePath=str(getYamlFilePathInsideFolder(".gs.config.log.xap_logging"))
        infraJarPath = ".gs.jars.infra.infrajar"
        infraJarInput = str(readValueFromYaml(infraJarPath)).replace('[','').replace(']','')
        infraJarInput = getYamlJarFilePath(".gs.jars.infra",infraJarInput)
        infraJarTargetInput = str(readValuefromAppConfig("app.space.infra.jar.target")).replace('[','').replace(']','')
        selinuxEnabled = str(readValuefromAppConfig("app.selinux.enabled"))


        serviceHostConfig = []
        serviceStart = ''
        user='root'
        logger.info("user :"+str(user))
        streamDict = config_get_service_list_with_status(user)
        serverStartType = str(userInputWithEscWrapper(Fore.YELLOW+"press [1] if you want to install individual server. \nPress [Enter] to install all. \nPress [99] for exit.: "+Fore.RESET))
        logger.info("serverStartType:"+str(serverStartType))
        isMenuDriven=''
        cliArguments=''
        if(serverStartType=='1'):
            optionMainMenu = str(userInputWithEscWrapper("Enter your host number to install: "))
            if (optionMainMenu.isdigit() == False):
                verboseHandle.printConsoleWarning("Invalid Input")
                return
            logger.info("Enter your host number to start:"+str(optionMainMenu))
            if(optionMainMenu != '99'):
                if len(streamDict) >= int(optionMainMenu):
                    serviceStart = streamDict.get(int(optionMainMenu))
                    for host in host_nic_dict_obj:
                        if ((os.getenv(serviceStart.ip)) == str(host)):
                            serviceHostConfig.append(str(host))
                            verboseHandle.printConsoleWarning(str(host))
                else:
                    verboseHandle.printConsoleWarning("Invalid Input")
                    return
            elif (optionMainMenu == '99'):
                logger.info("99 - Exist start")
                return
            else:
                verboseHandle.printConsoleWarning("Invalid Input")
                return
        elif(serverStartType =='99'):
            logger.info("99 - Exist start")
            return
        else:
            confirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to install all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            while(len(str(confirm))==0):
                confirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to install all servers ? [yes (y)] / [no (n)] : "+Fore.RESET))
            logger.info("confirm :"+str(confirm))
            if(confirm=='yes' or confirm=='y'):
                hostListLength=len(host_nic_dict_obj)+1
                with ThreadPoolExecutor(hostListLength) as executor:
                    for host in host_nic_dict_obj:
                        serviceHostConfig.append(str(host))
                        verboseHandle.printConsoleWarning(str(host))
            elif(confirm=='no' or confirm == 'n'):
                return
            else:
                verboseHandle.printConsoleWarning("Invalid Input")
                return




        #To Display Summary ::
        verboseHandle.printConsoleWarning("------------------------------------------------------------")
        verboseHandle.printConsoleWarning("***Summary***")
        print(Fore.GREEN+"1. "+
              Fore.GREEN+"Current manager configuration = "+
              Fore.GREEN+hostsConfig+Fore.RESET)
        print(Fore.GREEN+"2. "+
              Fore.GREEN+"Target Directory = "+
              Fore.GREEN+targetDirectory.replace('"','')+Fore.RESET)
        print(Fore.GREEN+"3. "+
              Fore.GREEN+"GS_OPTIONS_EXT = "+
              Fore.GREEN+gsOptionExt.replace('"','').replace( "\\",'')+Fore.RESET)
        print(Fore.GREEN+"4. "+
              Fore.GREEN+"GS_MANAGER_OPTIONS = "+
              Fore.GREEN+gsManagerOptions.replace('"','')+Fore.RESET)
        print(Fore.GREEN+"5. "+
              Fore.GREEN+"GS_LOGS_CONFIG_FILE = "+
              Fore.GREEN+gsLogsConfigFile.replace('"','')+Fore.RESET)
        print(Fore.GREEN+"6. "+
              Fore.GREEN+"GS_LICENSE = "+
              Fore.GREEN+gsLicenseFile.replace( "\\",'').replace('"','')+Fore.RESET)
        print(Fore.GREEN+"7. "+
              Fore.GREEN+"User level open file limit = "+Fore.RESET,
              Fore.GREEN+nofileLimitFile.replace('"','')+Fore.RESET)
        print(Fore.GREEN+"8. "+
              Fore.GREEN+"Service hosts = "+Fore.RESET,
              Fore.GREEN+",".join(map(str, serviceHostConfig))+Fore.RESET)
        print(Fore.GREEN+"9. "+
              Fore.GREEN+"Do you want to install Java ? "+Fore.RESET,
              Fore.GREEN+wantToInstallJava+Fore.RESET)
        print(Fore.GREEN+"10. "+
              Fore.GREEN+"Do you want to install Unzip ? "+Fore.RESET,
              Fore.GREEN+wantToInstallUnzip+Fore.RESET)
        print(Fore.GREEN+"11. "+
              Fore.GREEN+"CEFLogger-1.0-SNAPSHOT.jar source : "+Fore.RESET,
              Fore.GREEN+str(cefLoggingJarInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"12. "+
              Fore.GREEN+"CEFLogger-1.0-SNAPSHOT.jar target : "+Fore.RESET,
              Fore.GREEN+str(cefLoggingJarInputTarget).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"13. "+
              Fore.GREEN+"db2jcc-4.26.14.jar source : "+Fore.RESET,
              Fore.GREEN+str(db2jccJarInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"14. "+
              Fore.GREEN+"db2jcc_license_cu-4.16.53.jar source : "+Fore.RESET,
              Fore.GREEN+str(db2jccJarLicenseInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"15. "+
              Fore.GREEN+"DB2 Feeder jars target : "+Fore.RESET,
              Fore.GREEN+str(db2FeederJarTargetInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"16. "+
              Fore.GREEN+"MsSQL Feeder files source : "+Fore.RESET,
              Fore.GREEN+str(msSqlFeederFileSource).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"17. "+
              Fore.GREEN+"MsSQL Feeder files target : "+Fore.RESET,
              Fore.GREEN+str(msSqlFeederFileTarget).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"18. "+
              Fore.GREEN+"Log source file path : "+Fore.RESET,
              Fore.GREEN+str(logSourcePath).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"19. "+
              Fore.GREEN+"Log target file path : "+Fore.RESET,
              Fore.GREEN+str(logTargetPath).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"20. "+
              Fore.GREEN+"Is SELinux Enabled : "+Fore.RESET,
              Fore.GREEN+str(selinuxEnabled)+Fore.RESET)
        print(Fore.GREEN+"21. "+
              Fore.GREEN+"infra-1.1-SNAPSHOT-jar-with-dependencies.jar source : "+Fore.RESET,
              Fore.GREEN+str(infraJarInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"22. "+
              Fore.GREEN+"Infra jar target : "+Fore.RESET,
              Fore.GREEN+str(infraJarTargetInput).replace('"','')+Fore.RESET)

        verboseHandle.printConsoleWarning("------------------------------------------------------------")
        summaryConfirm = str(userInputWrapper(Fore.YELLOW+"Do you want to continue installation for above configuration ? [yes (y) / no (n)]: "+Fore.RESET))
        while(len(str(summaryConfirm))==0):
            summaryConfirm = str(userInputWrapper(Fore.YELLOW+"Do you want to continue installation for above configuration ? [yes (y) / no (n)]: "+Fore.RESET))

        if(summaryConfirm == 'y' or summaryConfirm =='yes'):
            hostListLength = len(host_nic_dict_obj)+1
            verboseHandle.printConsoleInfo(str(hostListLength))
            with ThreadPoolExecutor(hostListLength) as executor:
                for host in host_nic_dict_obj:
                    if (host in serviceHostConfig):
                        executor.submit(installServiceServer,host,additionalParam,host_nic_dict_obj,cefLoggingJarInput,cefLoggingJarInputTarget,db2jccJarInput,db2FeederJarTargetInput,db2jccJarLicenseInput,msSqlFeederFileTarget,startSpaceGsc,None,selinuxEnabled,infraJarInput,infraJarTargetInput)
        elif(summaryConfirm == 'n' or summaryConfirm =='no'):
            logger.info("menudriven")
            return
    except Exception as e:
        handleException(e)

def installServiceServer(host,additionalParam,host_nic_dict_obj,cefLoggingJarInput,cefLoggingJarInputTarget,db2jccJarInput,db2FeederJarTargetInput,db2jccJarLicenseInput,msSqlFeederFileTarget,startSpaceGsc,newZkJarTarget,selinuxEnabled,infraJarInput,infraJarTargetInput):
    installStatus='No'
    install = isInstalledAndGetVersion(host)
    logger.info("install : "+str(install))
    if(len(str(install))>8):
        installStatus='Yes'
    if installStatus == 'No':
        gsNicAddress = host_nic_dict_obj[host]
        additionalParam=additionalParam+' '+startSpaceGsc+' '+selinuxEnabled + ' '+ gsNicAddress
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
        logger.info("additionalParam - Installation :")
        logger.info("Building .tar file : tar -cvf install/install.tar install")
        cmd = 'tar -cvf install/install.tar install'
        with Spinner():
            status = os.system(cmd)
            logger.info("Creating tar file status : "+str(status))
        with Spinner():
            scp_upload(host, user, 'install/install.tar', '')
        cmd = 'tar -xvf install.tar'
        verboseHandle.printConsoleInfo("Extracting..")
        logger.debug("host : "+str(host)+" user:"+str(user)+" cmd "+str(cmd))
        output = executeRemoteCommandAndGetOutput(host, user, cmd)
        logger.debug("Execute RemoteCommand output:"+str(output))
        verboseHandle.printConsoleInfo(output)
        commandToExecute="scripts/servers_service_install.sh"
        logger.info("additionalParam : "+str(additionalParam))
        logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user))
        with Spinner():
            outputShFile= executeRemoteShCommandAndGetOutput(host, user, additionalParam, commandToExecute)
            logger.debug("script output"+str(outputShFile))
            verboseHandle.printConsoleInfo(cefLoggingJarInput+" -> "+cefLoggingJarInputTarget)
            executeRemoteCommandAndGetOutputValuePython36(host, user,"cp "+cefLoggingJarInput+" "+cefLoggingJarInputTarget)
            verboseHandle.printConsoleInfo(db2jccJarInput+" -> "+db2FeederJarTargetInput)
            executeRemoteCommandAndGetOutputValuePython36(host, user,"cp "+db2jccJarInput+" "+db2FeederJarTargetInput)
            verboseHandle.printConsoleInfo(db2jccJarLicenseInput+" -> "+db2FeederJarTargetInput)
            executeRemoteCommandAndGetOutputValuePython36(host, user,"cp "+db2jccJarLicenseInput+" "+db2FeederJarTargetInput)

            verboseHandle.printConsoleInfo(infraJarInput+" -> "+infraJarTargetInput)
            executeRemoteCommandAndGetOutputValuePython36(host, user,"cp "+infraJarInput+" "+infraJarTargetInput)

            configureMetricsXML(host)
        serverHost=''
        try:
            serverHost = socket.gethostbyaddr(host).__getitem__(0)
        except Exception as e:
            serverHost=host
        logger.info("Installation of service server "+str(host)+" has been done!")
        verboseHandle.printConsoleInfo("Installation of service server "+host+" has been done!")
    else:
        verboseHandle.printConsoleInfo("Found installation. skipping installation for host "+host)
        logger.info("Found installation. skipping installation for host "+host)

if __name__ == '__main__':
    logger.info("odsx_servers_service_install")
    verboseHandle.printConsoleWarning('Menu -> Servers -> Service -> Install')
    args = []
    menuDrivenFlag='m' # To differentiate between CLI and Menudriven Argument handling help section
    args.append(sys.argv[0])
    try:
        isValidRPMs = validateRPMS()
        if(isValidRPMs):
            args.append(menuDrivenFlag)
            user="root"
            args.append('-u')
            args.append(user)
            hostsConfig = readValuefromAppConfig("app.manager.hosts")
            args.append('--id')
            hostsConfig=getHostConfiguration()
            args = str(args)
            args =args.replace('[','').replace("'","").replace("]",'').replace(',','').strip()
            args =args+' '+str(hostsConfig)
            logger.debug('Arguments :'+args)
            if(config_get_cluster_airgap):
                execute_ssh_server_manager_install(hostsConfig,user)
        else:
            pass
    except Exception as e:
        handleException(e)
