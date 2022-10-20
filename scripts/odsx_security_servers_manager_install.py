#!/usr/bin/env python3
# s6.py
#!/usr/bin/python
import os, subprocess, sys, argparse, platform,socket,signal
from scripts.logManager import LogManager
from scripts.odsx_security_servers_space_install import configureMetricsXML
from utils.ods_app_config import readValuefromAppConfig, set_value_in_property_file, readValueByConfigObj, set_value_in_property_file_generic, read_value_in_property_file_generic_section, readValueFromYaml, \
    getYamlJarFilePath, getYamlFilePathInsideFolder
from colorama import Fore

from utils.ods_cleanup import signal_handler
from utils.ods_list import validateRPMS
from utils.ods_scp import scp_upload,scp_upload_multiple
from utils.ods_ssh import executeRemoteCommandAndGetOutput, executeRemoteShCommandAndGetOutput, \
    executeShCommandAndGetOutput, executeRemoteCommandAndGetOutputPython36, executeLocalCommandAndGetOutput, \
    connectExecuteSSH, executeRemoteCommandAndGetOutputValuePython36
from utils.ods_cluster_config import config_add_manager_node, config_get_cluster_airgap,config_get_dataIntegration_nodes
from scripts.spinner import Spinner
from utils.ods_cluster_config import config_get_manager_node

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR

class host_nic_dictionary(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

host_nic_dict_obj = host_nic_dictionary()

class obj_type_dictionary(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
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

def getDIServerHostList():
    nodeList = config_get_dataIntegration_nodes()
    nodes = ""
    count=0  # Only 3 Kafka host we will configure
    for node in nodeList:
        # if(str(node.role).casefold() == 'server'):
        if count <3:
            if (len(nodes) == 0):
                nodes = os.getenv(node.ip)
            else:
                nodes = nodes + ',' + os.getenv(node.ip)
        count=count+1
    return nodes

def getBootstrapAddress(hostConfig):
    logger.info("getBootstrapAddress()")
    bootstrapAddress=''
    for host in hostConfig.split(','):
        bootstrapAddress=bootstrapAddress+host+':9092,'
    bootstrapAddress=bootstrapAddress[:-1]
    logger.info("getBootstrapAddress : "+str(bootstrapAddress))
    return bootstrapAddress

def getManagerHostFromEnv():
    logger.info("getManagerHostFromEnv()")
    hosts = ''
    managerNodes = config_get_manager_node()
    for node in managerNodes:
        hosts+=str(os.getenv(str(node.ip)))+','
    hosts=hosts[:-1]
    return hosts

def getHostConfiguration():
    logger.info("getHostConfiguration()")
    try:
        hostsConfig=""
        hostConfigArray=[]
        hostConfiguration=""
        wantNicAddress=""
        #hostsConfig = readValuefromAppConfig("app.manager.hosts")
        hostsConfig = getManagerHostFromEnv()
        logger.info("hostsConfig : "+str(hostsConfig))
        hostConfigArray=hostsConfig.replace('"','').split(",")

        applicativeUserFile = readValuefromAppConfig("app.server.user")
        #applicativeUser = str(input(Fore.YELLOW+"Applicative user ["+applicativeUserFile+"]: "+Fore.RESET))
        #if(len(str(applicativeUser))==0):
        applicativeUser = str(applicativeUserFile)
        logger.info("Applicative user : "+str(applicativeUser))
        set_value_in_property_file_generic('User',applicativeUser,'install/gs/gsa.service','Service')
        set_value_in_property_file_generic('User',applicativeUser,'install/gs/gsa.service','Service')
        set_value_in_property_file_generic('Group',applicativeUser,'install/gs/gsc.service','Service')
        set_value_in_property_file_generic('Group',applicativeUser,'install/gs/gsc.service','Service')

        if(len(hostsConfig)==2):
            hostsConfig=hostsConfig.replace('"','')
            logger.info("hostsConfig==2 : "+str(hostsConfig))
        if(len(str(hostsConfig))>0):
            logger.info("hostsConfig>0 : "+str(hostsConfig))
            #verboseHandle.printConsoleWarning("Current cluster configuration : ["+hostsConfig+"] ")
            #hostConfiguration = str(input("press [1] if you want to modify cluster configuration. \nPress [Enter] to continue with current Configuration. : "+Fore.RESET))
            hostConfiguration = ''
            logger.info("hostConfiguration : "+str(hostConfiguration))
            wantNicAddress = str(readValuefromAppConfig("app.manager.gsNicAddress"))
            #print(Fore.YELLOW+"Configure GS_NIC_ADDRESS for host : "+str(wantNicAddress)+" "+Fore.RESET)
            #while(len(str(wantNicAddress))==0):
            #    wantNicAddress = 'n'
            logger.info("wantNicAddress  : "+str(wantNicAddress))
            if(hostConfiguration != '1'):
                logger.info("hostConfiguration !=1 : "+str(hostConfiguration))
                for host in hostConfigArray:
                    logger.info("host  : "+str(host))
                    if(wantNicAddress=="yes" or wantNicAddress=="y"):
                        logger.info("wantNicAddress  : "+str(wantNicAddress))
                        gsNICAddress = str(input(Fore.YELLOW+'Enter GS_NIC_ADDRESS for host '+host+" :"+Fore.RESET))
                        while(len(str(gsNICAddress))==0):
                            gsNICAddress = str(input(Fore.YELLOW+'Enter GS_NIC_ADDRESS for host '+host+" :"+Fore.RESET))
                        host_nic_dict_obj.add(host,gsNICAddress)
                        logger.info("host_nic_dict_obj  : "+str(host_nic_dict_obj))
                    if(wantNicAddress=="no" or wantNicAddress=="n"):
                        logger.info("wantNicAddress  : "+str(wantNicAddress))
                        gsNICAddress="x"
                        host_nic_dict_obj.add(host,gsNICAddress)
                        logger.info("host_nic_dict_obj  : "+str(host_nic_dict_obj))
        if(len(str(hostsConfig))==0) or (hostConfiguration=='1'):
            gsNicAddress=""
            gsNicAddress1=""
            gsNicAddress2=""
            gsNicAddress3 =""
            managerType = int(input("Enter manager installation type: "+Fore.YELLOW+"\n[1] Single \n[2] Cluster : "+Fore.RESET))
            logger.info("managerType  : "+str(managerType))
            if(managerType==1):
                logger.info("managerType  : "+str(managerType))
                hostsConfig = str(input(Fore.YELLOW+"Enter manager host: "+Fore.RESET))
                while(len(str(hostsConfig))==0):
                    hostsConfig = str(input(Fore.YELLOW+"Enter manager host: "+Fore.RESET))
                logger.info("hostsConfig  : "+str(hostsConfig))
                if(len(str(wantNicAddress))==0):
                    wantNicAddress = str(input(Fore.YELLOW+"Do you want to configure GS_NIC_ADDRESS for host ? [yes (y) / no (n)] [n]: "+Fore.RESET))
                if(len(str(wantNicAddress))==0):
                    wantNicAddress='n'
                logger.info("wantNicAddress  : "+str(wantNicAddress))
                if(wantNicAddress=="yes" or wantNicAddress=="y"):
                    logger.info("wantNicAddress  Y")
                    gsNicAddress = str(input(Fore.YELLOW+'Enter GS_NIC_ADDRESS for host '+hostsConfig+" :"+Fore.RESET))
                    logger.info("gsNicAddress  for host "+str(hostsConfig)+ ": "+str(gsNicAddress))
                if(wantNicAddress=="no" or wantNicAddress=="n"):
                    logger.info("wantNicAddress  N")
                    gsNicAddress="x"
                host_nic_dict_obj.add(hostsConfig,gsNicAddress)
                logger.info("host_nic_dict_obj  : "+str(host_nic_dict_obj))
                if(len(hostsConfig)<=0):
                    logger.info("Invalid host. Host configuration is required please specify valid host ip.:"+str(hostsConfig))
                    verboseHandle.printConsoleError("Invalid host. Host configuration is required please specify valid host ip.")
                    #break
            elif(managerType==2):
                logger.info("managerType==2  : "+str(managerType))
                host1 = str(input(Fore.YELLOW+"Enter manager host1: "+Fore.RESET))
                while(len(str(host1))==0):
                    host1 = str(input(Fore.YELLOW+"Enter manager host1: "+Fore.RESET))
                host2 = str(input(Fore.YELLOW+"Enter manager host2: "+Fore.RESET))
                while(len(str(host2))==0):
                    host2 = str(input(Fore.YELLOW+"Enter manager host2: "+Fore.RESET))
                host3 = str(input(Fore.YELLOW+"Enter manager host3: "+Fore.RESET))
                while(len(str(host3))==0):
                    host3 = str(input(Fore.YELLOW+"Enter manager host3: "+Fore.RESET))
                #wantNicAddress = str(input(Fore.YELLOW+"Do you want to configure GS_NIC_ADDRESS for host ? [yes (y) / no (n)]: "+Fore.RESET))
                logger.info("wantNicAddress  : "+str(wantNicAddress))
                if(wantNicAddress=="yes" or wantNicAddress=="y"):
                    logger.info("wantNicAddress  : "+str(wantNicAddress))
                    gsNicAddress1 = str(input(Fore.YELLOW+'Enter GS_NIC_ADDRESS for host '+host1+" :"+Fore.RESET))
                    while(len(str(gsNicAddress1))==0):
                        gsNicAddress1 = str(input(Fore.YELLOW+'Enter GS_NIC_ADDRESS for host '+host1+" :"+Fore.RESET))
                    gsNicAddress2 = str(input(Fore.YELLOW+'Enter GS_NIC_ADDRESS for host '+host2+" :"+Fore.RESET))
                    while(len(str(gsNicAddress2))==0):
                        gsNicAddress2 = str(input(Fore.YELLOW+'Enter GS_NIC_ADDRESS for host '+host2+" :"+Fore.RESET))
                    gsNicAddress3 = str(input(Fore.YELLOW+'Enter GS_NIC_ADDRESS for host '+host3+" :"+Fore.RESET))
                    while(len(str(gsNicAddress3))==0):
                        gsNicAddress3 = str(input(Fore.YELLOW+'Enter GS_NIC_ADDRESS for host '+host3+" :"+Fore.RESET))
                host_nic_dict_obj.add(host1,gsNicAddress1)
                host_nic_dict_obj.add(host2,gsNicAddress2)
                host_nic_dict_obj.add(host3,gsNicAddress3)
                logger.info("host_nic_dict_obj  : "+str(host_nic_dict_obj))
                if(len(host1)<=0 or len(host2)<=0 or len(host3)<=0):
                    logger.info("Invalid host. Host configuration is required please specify valid host ip.")
                    verboseHandle.printConsoleError("Invalid host. Host configuration is required please specify valid host ip.")
                    #break
                hostsConfig=host1+','+host2+','+host3
                logger.info("hostsConfig : "+str(hostsConfig))
            else:
                logger.info("Invalid input host option configuration is required please specify valid host ip.")
                verboseHandle.printConsoleError("Invalid input host option configuration is required please specify valid host ip.")
            if(len(hostsConfig)>0):
                set_value_in_property_file('app.manager.hosts',hostsConfig)
        return hostsConfig
    except Exception as e:
        handleException(e)

def execute_ssh_server_manager_install(hostsConfig,user):
    logger.info("execute_ssh_server_manager_install()")
    try:
        hostManager=[]
        gsNicAddress=''
        additionalParam=''
        targetDir=''
        hostManager=hostsConfig.replace('"','').split(",")
        #print("optionID:"+str(hostsConfig)+" : "+user)
        logger.debug("optionID:"+str(hostsConfig))

        gsOptionExtFromConfig = str(readValueByConfigObj("app.manager.security.gsOptionExt")).replace('[','').replace(']','').replace("'","").replace(', ',',')
        #gsOptionExtFromConfig = '"{}"'.format(gsOptionExtFromConfig)

        additionalParam = str(readValuefromAppConfig("app.manager.targetFolderInstall"))
        #print(Fore.YELLOW+"Target directory to install GS ["+Fore.GREEN+additionalParam+Fore.YELLOW+"]: "+Fore.RESET)
        #if(len(additionalParam)==0):
        #    targetDir='/dbagiga'
        #else:
        targetDir=additionalParam
        if(gsOptionExtFromConfig.__contains__('<DI servers>')):
            kafkaConfirm = str(readValuefromAppConfig("app.manager.wantKafkaServer"))
            #print(Fore.YELLOW+"Do you want to configure kafka servers : "+kafkaConfirm+Fore.RESET)
            kafkaHost=''
            if(len(str(kafkaConfirm))==0):
                kafkaConfirm='y'
            if(kafkaConfirm=='y'):
                dIHosts = getDIServerHostList()
                logger.info("dIHosts :"+str(dIHosts))
                if(len(str(dIHosts))>0):
                    kafkaHosts = getBootstrapAddress(dIHosts)
                    logger.info("kafkaHosts :"+str(kafkaHost))
                    #verboseHandle.printConsoleWarning("DI servers will be confiured ["+str(kafkaHosts)+"] ")
                else:
                    verboseHandle.printConsoleInfo("No DI server configuration found.")
                #set_value_in_property_file("app.manager.kafka.host",kafkaHost)
                gsOptionExtFromConfig = gsOptionExtFromConfig.replace('<DI servers>:9092',kafkaHosts)

        gsOptionExt = gsOptionExtFromConfig
        #print(Fore.YELLOW+' GS_OPTIONS_EXT  ['+Fore.GREEN+''+str(gsOptionExtFromConfig)+Fore.YELLOW+']: '+Fore.RESET)
        #if(len(str(gsOptionExt))==0):
            #gsOptionExt='\"-Dcom.gs.work=/dbagigawork -Dcom.gigaspaces.matrics.config=/dbagiga/gs_config/metrics.xml\"'
        #gsOptionExt=gsOptionExtFromConfig
        #else:
        #    set_value_in_property_file('app.manager.gsOptionExt',gsOptionExt)
        gsOptionExt='"\\"{}\\""'.format(gsOptionExt)
        #print("gsoptionext:"+gsOptionExt)

        gsManagerOptionsFromConfig = str(readValueByConfigObj("app.manager.gsManagerOptions")).replace('[','').replace(']','')
        #gsManagerOptionsFromConfig = '"{}"'.format(gsManagerOptionsFromConfig)
        gsManagerOptions =gsManagerOptionsFromConfig
        #print(Fore.YELLOW+'GS_MANAGER_OPTIONS  ['+Fore.GREEN+''+gsManagerOptionsFromConfig+Fore.YELLOW+']: '+Fore.RESET)
        #if(len(str(gsManagerOptions))==0):
            #gsManagerOptions="-Dcom.gs.hsqldb.all-metrics-recording.enabled=false"
        gsManagerOptions=gsManagerOptionsFromConfig
        #else:
        #    set_value_in_property_file('app.manager.gsManagerOptions',gsManagerOptions)
        #gsManagerOptions='"{}"'.format(gsManagerOptions)
        gsManagerOptions='"\\"{}\\""'.format(gsManagerOptions)

        gsLogsConfigFileFromConfig = str(readValuefromAppConfig("app.manager.gsLogsConfigFile")).replace('[','').replace(']','')
        gsLogsConfigFileFromConfig = '"{}"'.format(gsLogsConfigFileFromConfig)
        #gsLogsConfigFile = str(input(Fore.YELLOW+'Enter GS_LOGS_CONFIG_FILE  ['+Fore.GREEN+''+gsLogsConfigFileFromConfig+Fore.YELLOW+']: '+Fore.RESET))
        #if(len(str(gsLogsConfigFile))==0):
            #gsLogsConfigFile="/dbagiga/gs_config/xap_logging.properties"
        gsLogsConfigFile=gsLogsConfigFileFromConfig
        #else:
        #    set_value_in_property_file('app.manager.gsLogsConfigFile',gsLogsConfigFile)
        #gsLogsConfigFile = '"{}"'.format(gsLogsConfigFile)
        gsLogsConfigFile = '"\\"{}\\""'.format(gsLogsConfigFile)

        licenseConfig = str(getYamlFilePathInsideFolder(".gs.config.license.gslicense"))
        #licenseConfig='"{}"'.format(licenseConfig)
        gsLicenseFile = str(readValuefromAppConfig("app.manager.license"))
        #str(input(Fore.YELLOW+'Enter GS_LICENSE ['+Fore.GREEN+''+licenseConfig+Fore.YELLOW+']: '+Fore.RESET))
        #if(len(str(gsLicenseFile))==0):
        gsLicenseFile = licenseConfig
        #else:
            #gsLicenseFile = str(gsLicenseFile).replace(";","\;")
        gsLicenseFile='"\\"{}\\""'.format(gsLicenseFile)

        applicativeUser = read_value_in_property_file_generic_section('User','install/gs/gsa.service','Service')
        #print("Applicative User: "+str(applicativeUser))

        nofileLimit = str(readValuefromAppConfig("app.user.nofile.limit"))
        nofileLimitFile = nofileLimit
        #print(Fore.YELLOW+'User level open file limit : ['+Fore.GREEN+''+nofileLimit+Fore.YELLOW+']: '+Fore.RESET)
        logger.info("hardNofileLimitFile : "+str(nofileLimitFile))
        #if(len(str(nofileLimitFile))==0):
        nofileLimitFile = nofileLimit
        #else:
        #    set_value_in_property_file('app.user.hard.nofile',hardNofileLimitFile)
        nofileLimitFile = '"{}"'.format(nofileLimitFile)

        wantToInstallJava = str(readValuefromAppConfig("app.manager.wantToInstallJava"))
        #print(Fore.YELLOW+"Install Java :"+wantToInstallJava)
        #if(len(str(wantToInstallJava))==0):
        #    wantToInstallJava='n'

        wantToInstallUnzip = str(readValuefromAppConfig("app.manager.wantToInstallUnzip"))
        #print(Fore.YELLOW+"Install unzip : "+wantToInstallUnzip)
        #if(len(str(wantToInstallUnzip))==0):
        #    wantToInstallUnzip='n'

        #sourceDirectoryForJar = str(readValuefromAppConfig("app.manager.source.directory.jarfiles"))
        #print(Fore.YELLOW+"Source directory to copy files "+sourceDirectoryForJar+Fore.RESET)
        #if(len(str(sourceDirectoryForJar))==0):


        cefLoggingJarInput = str(getYamlFilePathInsideFolder(".security.jars.cef.cefjar")).replace('[','').replace(']','')

        cefLoggingJarInputTarget = str(readValuefromAppConfig("app.manager.cefLogging.jar.target")).replace('[','').replace(']','')

        springLdapCoreJarInput = str(getYamlFilePathInsideFolder(".security.jars.springldapcore")).replace('[','').replace(']','')
        springLdapJarInput = str(getYamlFilePathInsideFolder(".security.jars.springldapjar")).replace('[','').replace(']','')
        vaultSupportJarInput = str(getYamlFilePathInsideFolder(".security.jars.vaultsupportjar")).replace('[','').replace(']','')
        javaPasswordJarInput = str(getYamlFilePathInsideFolder(".security.jars.javapassword")).replace('[','').replace(']','')

        springTargetJarInput = str(readValuefromAppConfig("app.manager.security.spring.jar.target")).replace('[','').replace(']','')
        sourceJar = springLdapCoreJarInput+' '+springLdapJarInput+' '+vaultSupportJarInput+' '+javaPasswordJarInput

        ldapSecurityConfigInput = str(getYamlFilePathInsideFolder(".security.config.ldapsourcefile"))
        ldapSecurityConfigTargetInput = str(readValuefromAppConfig("app.manager.security.config.ldap.target.file"))

        logTargetPath=str(readValuefromAppConfig("app.log.target.file"))
        logSourcePath=str(getYamlFilePathInsideFolder(".gs.config.log.xap_logging"))
    #To Display Summary ::
        verboseHandle.printConsoleWarning("------------------------------------------------------------")
        verboseHandle.printConsoleWarning("***Summary***")
        print(Fore.GREEN+"1. "+
              Fore.GREEN+"Current configuration = "+
              Fore.GREEN+hostsConfig+Fore.RESET)
        print(Fore.GREEN+"2. "+
              Fore.GREEN+"Target Directory = "+
              Fore.GREEN+targetDir.replace('"','')+Fore.RESET)
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
              Fore.GREEN+"Do you want to install Java ? : "+Fore.RESET,
              Fore.GREEN+wantToInstallJava+Fore.RESET)
        print(Fore.GREEN+"9. "+
              Fore.GREEN+"Do you want to install Unzip ? "+Fore.RESET,
              Fore.GREEN+wantToInstallUnzip+Fore.RESET)
        print(Fore.GREEN+"10. "+
              Fore.GREEN+"CEFLogger-1.0-SNAPSHOT.jar source : "+Fore.RESET,
              Fore.GREEN+str(cefLoggingJarInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"11. "+
              Fore.GREEN+"CEFLogger-1.0-SNAPSHOT.jar target : "+Fore.RESET,
              Fore.GREEN+str(cefLoggingJarInputTarget).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"11A. "+
              Fore.GREEN+"CEFLogger-1.0-SNAPSHOT.jar target2 : "+Fore.RESET,
              Fore.GREEN+str(readValuefromAppConfig("app.manager.security.spring.jar.target"))+Fore.RESET)
        print(Fore.GREEN+"12. "+
              Fore.GREEN+"spring-ldap-core-2.3.3.RELEASE.jar source : "+Fore.RESET,
              Fore.GREEN+str(springLdapCoreJarInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"13. "+
              Fore.GREEN+"spring-security-ldap-5.1.7.RELEASE.jar source : "+Fore.RESET,
              Fore.GREEN+str(springLdapJarInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"14. "+
              Fore.GREEN+"VaultSupport-1.0-SNAPSHOT.jar source : "+Fore.RESET,
              Fore.GREEN+str(vaultSupportJarInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"15. "+
              Fore.GREEN+"JavaPasswordSDK.jar source : "+Fore.RESET,
              Fore.GREEN+str(javaPasswordJarInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"16. "+
              Fore.GREEN+"Spring jar target : "+Fore.RESET,
              Fore.GREEN+str(springTargetJarInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"17. "+
              Fore.GREEN+"ldap-security-config.xml source : "+Fore.RESET,
              Fore.GREEN+str(ldapSecurityConfigInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"18. "+
              Fore.GREEN+"ldap-security-config.xml target : "+Fore.RESET,
              Fore.GREEN+str(ldapSecurityConfigTargetInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"19. "+
              Fore.GREEN+"Log source file path : "+Fore.RESET,
              Fore.GREEN+str(logSourcePath).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"20. "+
          Fore.GREEN+"Log target file path : "+Fore.RESET,
          Fore.GREEN+str(logTargetPath).replace('"','')+Fore.RESET)
        verboseHandle.printConsoleWarning("------------------------------------------------------------")
        summaryConfirm = str(input(Fore.YELLOW+"Do you want to continue installation for above configuration ? [yes (y) / no (n)]: "+Fore.RESET))
        while(len(str(summaryConfirm))==0):
            summaryConfirm = str(input(Fore.YELLOW+"Do you want to continue installation for above configuration ? [yes (y) / no (n)]: "+Fore.RESET))

        if(summaryConfirm == 'y' or summaryConfirm =='yes'):

            #if(len(additionalParam)==0):
            #    additionalParam= 'true'+' '+targetDir+' '+hostsConfig+' '+gsOptionExt+' '+gsManagerOptions+' '+gsLogsConfigFile+' '+gsLicenseFile+' '+applicativeUser+' '+nofileLimitFile+' '+wantToInstallJava+' '+wantToInstallUnzip
            #else:
            sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
            additionalParam='true'+' '+additionalParam+' '+hostsConfig+' '+gsOptionExt+' '+gsManagerOptions+' '+gsLogsConfigFile+' '+gsLicenseFile+' '+applicativeUser+' '+nofileLimitFile+' '+wantToInstallJava+' '+wantToInstallUnzip+' '+sourceInstallerDirectory
            #print('additional param :'+additionalParam)
            logger.info('additional param :'+additionalParam)
            output=""
            logger.info("Building .tar file : tar -cvf install/install.tar install")
            cmd = 'tar -cvf install/install.tar install'
            with Spinner():
                status = os.system(cmd)
                logger.info("Creating tar file status : "+str(status))

            for host in hostManager:
                gsNicAddress = host_nic_dict_obj[host]
                logger.info("NIC address:"+gsNicAddress+" for host "+host)
                if(len(str(gsNicAddress))==0):
                    gsNicAddress='x'     # put dummy param to maintain position of arguments
                additionalParam=additionalParam+' '+gsNicAddress+' '+logSourcePath+' '+logTargetPath
                with Spinner():
                    scp_upload(host, user, 'install/install.tar', '')
                    ##scp_upload(host, user, 'install/gs.service', '')
                verboseHandle.printConsoleInfo(output)
                cmd = 'tar -xvf install.tar'
                verboseHandle.printConsoleInfo("Extracting..")
                with Spinner():
                    output = executeRemoteCommandAndGetOutput(host, user, cmd)
                logger.info("Extracting .tar file :"+str(output))
                verboseHandle.printConsoleInfo(str(output))

                commandToExecute="scripts/security_manager_install.sh"
                #print(additionalParam)
                logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user))
                logger.info("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user))
                with Spinner():
                    outputShFile= executeRemoteShCommandAndGetOutput(host, user, additionalParam, commandToExecute)

                    executeRemoteCommandAndGetOutputValuePython36(host, user,"cp "+cefLoggingJarInput+" "+cefLoggingJarInputTarget)
                    executeRemoteCommandAndGetOutputValuePython36(host, user,"cp "+cefLoggingJarInput+" "+readValuefromAppConfig("app.manager.security.spring.jar.target"))
                    #print("cp "+sourceJar+" "+readValuefromAppConfig("app.manager.security.spring.jar.target"))
                    executeRemoteCommandAndGetOutputValuePython36(host, user,"cp "+sourceJar+" "+springTargetJarInput)
                    executeRemoteCommandAndGetOutputValuePython36(host, user,"cp "+ldapSecurityConfigInput+" "+ldapSecurityConfigTargetInput)
                    #print("cp /dbagiga/gigaspaces-smart-ods/lib/optional/security/* "+readValuefromAppConfig("app.manager.security.spring.jar.target"))
                    executeRemoteCommandAndGetOutputValuePython36(host, user,"cp /dbagiga/gigaspaces-smart-ods/lib/optional/security/* "+springTargetJarInput)
                    #print("chown "+applicativeUser+":"+applicativeUser+" "+readValuefromAppConfig("app.manager.security.spring.jar.target")+"* "+readValuefromAppConfig("app.manager.security.config.target")+"*")
                    executeRemoteCommandAndGetOutputValuePython36(host, user,"chown "+applicativeUser+":"+applicativeUser+" "+readValuefromAppConfig("app.manager.security.spring.jar.target")+"* "+readValuefromAppConfig("app.manager.security.config.target")+"*")
                    configureMetricsXML(host)
                serverHost=''
                try:
                    serverHost = socket.gethostbyaddr(host).__getitem__(0)
                except Exception as e:
                    serverHost=host
                #managerList = config_add_manager_node(host,host,"admin")
                logger.info("Installation of manager server "+str(host)+" has been done!")
                verboseHandle.printConsoleInfo("Installation of manager server "+host+" has been done!")
        elif(summaryConfirm == 'n' or summaryConfirm =='no'):
            logger.info("menudriven")
            return

    except Exception as e:
        handleException(e)

if __name__ == '__main__':
    logger.info("odsx_security_manager -> install")
    verboseHandle.printConsoleWarning('Menu -> Servers ->  Manager -> Install')
    args = []
    menuDrivenFlag='m' # To differentiate between CLI and Menudriven Argument handling help section
    #print('Len : ',len(sys.argv))
    #print('Flag : ',sys.argv[0])

    args.append(sys.argv[0])
    signal.signal(signal.SIGINT, signal_handler)
    try:
        isValidRPMs = validateRPMS()
        if(isValidRPMs):

            args.append(menuDrivenFlag)
            #host = str(input("Enter your host: "))
            #args.append('--host')
            #args.append(host)
            #user = readValuefromAppConfig("app.server.user")
            #user = str(input("Enter your user [root]: "))
            user='root'
            if(len(str(user))==0):
                user="root"
            args.append('-u')
            args.append(user)
            hostsConfig = getManagerHostFromEnv()
            args.append('--id')
            hostsConfig=getHostConfiguration()
            args = str(args)
            args =args.replace('[','').replace("'","").replace("]",'').replace(',','').strip()
            args =args+' '+str(hostsConfig)
            logger.debug('Arguments :'+args)
            if(config_get_cluster_airgap):
                execute_ssh_server_manager_install(hostsConfig,user)
            #os.system('python3 scripts/servers_manager_scriptbuilder.py '+args)
            ## Execution script flow diverted to this file hence major changes required and others scripts will going to distrub
        else:
            pass
    except Exception as e:
        handleException(e)
        logger.error("Invalid argument. "+str(e))
        #verboseHandle.printConsoleError("Invalid argument.")
