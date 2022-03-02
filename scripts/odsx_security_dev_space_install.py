#!/usr/bin/env python3
# s6.py
#!/usr/bin/python
import os, subprocess, sys, argparse, platform,socket
from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig, set_value_in_property_file, readValueByConfigObj, set_value_in_property_file_generic, read_value_in_property_file_generic_section
from colorama import Fore
from utils.ods_scp import scp_upload
from utils.ods_ssh import executeRemoteCommandAndGetOutput,executeRemoteShCommandAndGetOutput,connectExecuteSSH
from utils.ods_cluster_config import config_add_space_node, config_get_cluster_airgap
from scripts.spinner import Spinner
from utils.ods_scp import scp_upload,scp_upload_multiple

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
        hostsConfig = readValuefromAppConfig("app.manager.hosts")

        applicativeUserFile = readValuefromAppConfig("app.server.user")
        applicativeUser = str(input(Fore.YELLOW+"Applicative user ["+applicativeUserFile+"]: "+Fore.RESET))
        if(len(str(applicativeUser))==0):
            applicativeUser = str(applicativeUserFile)
        logger.info("Applicative user : "+str(applicativeUser))
        set_value_in_property_file_generic('User',applicativeUser,'install/gs/gsa.service','Service')
        set_value_in_property_file_generic('User',applicativeUser,'install/gs/gsa.service','Service')
        set_value_in_property_file_generic('Group',applicativeUser,'install/gs/gsc.service','Service')
        set_value_in_property_file_generic('Group',applicativeUser,'install/gs/gsc.service','Service')

        if(len(hostsConfig)==2):
            hostsConfig=hostsConfig.replace('"','')
        if(len(str(hostsConfig))>0):
            verboseHandle.printConsoleWarning("Current cluster configuration : ["+hostsConfig+"] ")
        else:
            verboseHandle.printConsoleError("No manager configuration found:")
        return hostsConfig
    except Exception as e:
        handleException(e)


def getInputParamForSecurityCredantials():
    logger.info("getInputParamForSecurityCredantials()")
    global username
    global password
    username = str(readValuefromAppConfig("app.manager.dev.security.username")).replace('"','')
    password = str(readValuefromAppConfig("app.manager.dev.security.password")).replace('"','')

def execute_ssh_server_manager_install(hostsConfig,user):
    logger.info("execute_ssh_server_manager_install()")
    try:
        hostManager=[]
        gsNicAddress=''
        additionalParam=''
        hostManager=hostsConfig.replace('"','').split(",")
        #print("optionID:"+str(hostsConfig)+" : "+user)
        logger.debug("optionID:"+str(hostsConfig))
        targetDirectory=''
        gsOptionExtFromConfig = str(readValueByConfigObj("app.space.security.gsOptionExt")).replace('[','').replace(']','').replace("'","").replace(', ',',')
        #gsOptionExtFromConfig = '"{}"'.format(gsOptionExtFromConfig)
        additionalParam = str(input(Fore.YELLOW+"Enter target directory to install GS ["+Fore.GREEN+"/dbagiga"+Fore.YELLOW+"]: "+Fore.RESET))
        targetDirectory=str(additionalParam)
        if(len(additionalParam)==0):
            targetDirectory='/dbagiga'
        logger.info("targetDirecory :"+str(targetDirectory))
        gsOptionExt = str(input(Fore.YELLOW+'Enter GS_OPTIONS_EXT  ['+Fore.GREEN+str(gsOptionExtFromConfig)+Fore.YELLOW+']: '+Fore.RESET))
        if(len(str(gsOptionExt))==0):
            #gsOptionExt='\"-Dcom.gs.work=/dbagigawork -Dcom.gigaspaces.matrics.config=/dbagiga/gs_config/metrics.xml\"'
            gsOptionExt=gsOptionExtFromConfig
        else:
            set_value_in_property_file('app.space.gsOptionExt',gsOptionExt)
        gsOptionExt='"\\"{}\\""'.format(gsOptionExt)
        #print("gsoptionext:"+gsOptionExt)

        gsManagerOptionsFromConfig = str(readValueByConfigObj("app.manager.gsManagerOptions")).replace('[','').replace(']','')
        #gsManagerOptionsFromConfig = '"{}"'.format(gsManagerOptionsFromConfig)
        gsManagerOptions = str(input(Fore.YELLOW+'Enter GS_MANAGER_OPTIONS  ['+Fore.GREEN+str(gsManagerOptionsFromConfig)+Fore.YELLOW+']: '+Fore.RESET))
        if(len(str(gsManagerOptions))==0):
            #gsManagerOptions="-Dcom.gs.hsqldb.all-metrics-recording.enabled=false"
            gsManagerOptions=gsManagerOptionsFromConfig
        else:
            set_value_in_property_file('app.manager.gsManagerOptions',gsManagerOptions)
        #gsManagerOptions='"{}"'.format(gsManagerOptions)
        gsManagerOptions='"\\"{}\\""'.format(gsManagerOptions)

        gsLogsConfigFileFromConfig = str(readValueByConfigObj("app.manager.gsLogsConfigFile")).replace('[','').replace(']','')
        #gsLogsConfigFileFromConfig = '"{}"'.format(gsLogsConfigFileFromConfig)
        gsLogsConfigFile = str(input(Fore.YELLOW+'Enter GS_LOGS_CONFIG_FILE  ['+Fore.GREEN+gsLogsConfigFileFromConfig+Fore.YELLOW+']: '+Fore.RESET))
        if(len(str(gsLogsConfigFile))==0):
            #gsLogsConfigFile="/dbagiga/gs_config/xap_logging.properties"
            gsLogsConfigFile=gsLogsConfigFileFromConfig
        else:
            set_value_in_property_file('app.manager.gsLogsConfigFile',gsLogsConfigFile)
        #gsLogsConfigFile = '"{}"'.format(gsLogsConfigFile)
        gsLogsConfigFile = '"\\"{}\\""'.format(gsLogsConfigFile)

        licenseConfig = readValueByConfigObj("app.manager.license")
        #licenseConfig='"{}"'.format(licenseConfig)
        gsLicenseFile = str(input(Fore.YELLOW+'Enter GS_LICENSE ['+Fore.GREEN+licenseConfig+Fore.YELLOW+']: '+Fore.RESET))
        if(len(str(gsLicenseFile))==0):
            gsLicenseFile = licenseConfig
        #else:
        #    gsLicenseFile = str(gsLicenseFile).replace(";","\;")
        gsLicenseFile='"\\"{}\\""'.format(gsLicenseFile)

        applicativeUser = read_value_in_property_file_generic_section('User','install/gs/gsa.service','Service')
        #print("Applicative User: "+str(applicativeUser))

        nofileLimit = str(readValuefromAppConfig("app.user.nofile.limit"))
        nofileLimitFile = str(input(Fore.YELLOW+'Enter user level open file limit : ['+Fore.GREEN+nofileLimit+Fore.YELLOW+']: '+Fore.RESET))
        logger.info("hardNofileLimitFile : "+str(nofileLimitFile))
        if(len(str(nofileLimitFile))==0):
            nofileLimitFile = nofileLimit
        #else:
        #    set_value_in_property_file('app.user.hard.nofile',hardNofileLimitFile)
        nofileLimitFile = '"{}"'.format(nofileLimitFile)

        wantToInstallJava = str(input(Fore.YELLOW+"Do you want to install Java ? (y/n) [n] : "+Fore.RESET))
        if(len(str(wantToInstallJava))==0):
            wantToInstallJava='n'

        wantToInstallUnzip = str(input(Fore.YELLOW+"Do you want to install unzip ? (y/n) [n] : "+Fore.RESET))
        if(len(str(wantToInstallUnzip))==0):
            wantToInstallUnzip='n'
        global gscCount
        global memoryGSC
        global zoneGSC
        gscCount = str(input(Fore.YELLOW+"Enter number of GSC to create [20]: "+Fore.RESET))
        if(len(str(gscCount))==0):
            gscCount = '20'

        memoryGSC = str(input(Fore.YELLOW+"Enter memory required to create GSC [15g]: "+Fore.RESET))
        if(len(str(memoryGSC))==0):
            memoryGSC = '15g'

        zoneGSC = str(input(Fore.YELLOW+"Enter zone to create GSC [bll]: "+Fore.RESET))
        if(len(str(zoneGSC))==0):
            zoneGSC = 'bll'

        sourceDirectoryForJar = str(input(Fore.YELLOW+"Enter source directory to copy jars from [/dbagiga] : "+Fore.RESET))
        if(len(str(sourceDirectoryForJar))==0):
            sourceDirectoryForJar='/dbagiga'

        getInputParamForSecurityCredantials()

        if(len(additionalParam)==0):
            additionalParam= 'true'+' '+targetDirectory+' '+hostsConfig+' '+gsOptionExt+' '+gsManagerOptions+' '+gsLogsConfigFile+' '+gsLicenseFile+' '+applicativeUser+' '+nofileLimitFile+' '+wantToInstallJava+' '+wantToInstallUnzip+' '+gscCount+' '+memoryGSC+' '+zoneGSC+' '+username+' '+password
        else:
            additionalParam= 'true'+' '+targetDirectory+' '+hostsConfig+' '+hostsConfig+' '+gsOptionExt+' '+gsManagerOptions+' '+gsLogsConfigFile+' '+gsLicenseFile+' '+applicativeUser+' '+nofileLimitFile+' '+wantToInstallJava+' '+wantToInstallUnzip+' '+gscCount+' '+memoryGSC+' '+zoneGSC+' '+username+' '+password
        #print('additional param :'+additionalParam)
        logger.debug('additional param :'+additionalParam)

        noOfHost = str(input(Fore.YELLOW+"Enter number of space hosts you want to create :"+Fore.RESET))
        while (len(str(noOfHost))==0):
            noOfHost = str(input(Fore.YELLOW+"Enter number of space hosts you want to create : "+Fore.RESET))
        logger.debug("No of space host :"+str(noOfHost))
        host_nic_dict_obj = host_nic_dictionary()
        noOfHost=int(noOfHost)
        spaceHostConfig=""
        for x in range(1,noOfHost+1):
            host = str(input(Fore.YELLOW+"Enter space host"+str(x)+" :"+Fore.RESET))
            while(len(str(host))==0):
                host = str(input(Fore.YELLOW+"Enter space host"+str(x)+" :"+Fore.RESET))
            if(len(str(spaceHostConfig))>0):
                spaceHostConfig = spaceHostConfig+','+host
            else:
                spaceHostConfig = host
            host_nic_dict_obj.add(host,'')
        set_value_in_property_file('app.space.hosts',spaceHostConfig)
        #print("hostnic without"+str(host_nic_dict_obj))
        wantNicAddress = str(input(Fore.YELLOW+"Do you want to configure GS_NIC_ADDRESS for host ? (y/n) [n] : "+Fore.RESET))
        if(len(str(wantNicAddress))==0):
            wantNicAddress='n'
        if(wantNicAddress=="yes" or wantNicAddress=="y"):
            for host in host_nic_dict_obj:
                nicAddr = str(input(Fore.YELLOW+"Enter GS_NIC_ADDRESS of space host"+str(host)+" :"+Fore.RESET))
                logger.debug("host enter:"+host+" nicAddr :"+nicAddr)
                host_nic_dict_obj.add(host,nicAddr)
        logger.debug("hostNicAddr :"+str(host_nic_dict_obj))

        cefLoggingJarInput = str(readValuefromAppConfig("app.manager.cefLogging.jar")).replace('[','').replace(']','')
        cefLoggingJarInput=sourceDirectoryForJar+'/'+cefLoggingJarInput
        cefLoggingJarInputTarget = str(readValuefromAppConfig("app.manager.cefLogging.jar.target")).replace('[','').replace(']','')

        db2jccJarInput = str(readValuefromAppConfig("app.space.db2feeder.jar.db2jcc-4.26.14.jar")).replace('[','').replace(']','')
        db2jccJarInput = sourceDirectoryForJar+'/'+db2jccJarInput
        db2jccJarLicenseInput = str(readValuefromAppConfig("app.space.db2feeder.jar.db2jcc_license_cu-4.16.53.jar")).replace('[','').replace(']','')
        db2jccJarLicenseInput=sourceDirectoryForJar+'/'+db2jccJarLicenseInput
        db2FeederJarTargetInput = str(readValuefromAppConfig("app.space.db2feeder.jar.target")).replace('[','').replace(']','')

        springLdapCoreJarInput = str(readValuefromAppConfig("app.manager.security.spring.ldap.core.jar")).replace('[','').replace(']','')
        springLdapCoreJarInput=sourceDirectoryForJar+'/'+springLdapCoreJarInput
        springLdapJarInput = str(readValuefromAppConfig("app.manager.security.spring.ldap.jar")).replace('[','').replace(']','')
        springLdapJarInput=sourceDirectoryForJar+'/'+springLdapJarInput
        vaultSupportJarInput = str(readValuefromAppConfig("app.manager.security.spring.vaultSupport.jar")).replace('[','').replace(']','')
        vaultSupportJarInput=sourceDirectoryForJar+'/'+vaultSupportJarInput
        javaPasswordJarInput = str(readValuefromAppConfig("app.manager.security.spring.javaPassword.jar")).replace('[','').replace(']','')
        javaPasswordJarInput=sourceDirectoryForJar+'/'+javaPasswordJarInput
        springTargetJarInput = str(readValuefromAppConfig("app.manager.security.spring.jar.target")).replace('[','').replace(']','')

        sourceJar = springLdapCoreJarInput+' '+springLdapJarInput+' '+vaultSupportJarInput+' '+javaPasswordJarInput

        ldapSecurityConfigInput = str(readValuefromAppConfig("app.manager.security.config.ldap.source.file"))
        ldapSecurityConfigInput=sourceDirectoryForJar+'/'+ldapSecurityConfigInput
        ldapSecurityConfigTargetInput = str(readValuefromAppConfig("app.manager.security.config.ldap.target.file"))

        #To Display Summary ::
        verboseHandle.printConsoleWarning("------------------------------------------------------------")
        verboseHandle.printConsoleWarning("***Summary***")
        print(Fore.GREEN+"1. "+
              Fore.GREEN+"Current configuration = "+
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
              Fore.GREEN+"Space hosts = "+Fore.RESET,
              Fore.GREEN+spaceHostConfig.replace('"','')+Fore.RESET)
        print(Fore.GREEN+"9. "+
              Fore.GREEN+"Do you want to install Java ? "+Fore.RESET,
              Fore.GREEN+wantToInstallJava+Fore.RESET)
        print(Fore.GREEN+"10. "+
              Fore.GREEN+"Do you want to install Unzip ? "+Fore.RESET,
              Fore.GREEN+wantToInstallUnzip+Fore.RESET)
        print(Fore.GREEN+"11. "+
              Fore.GREEN+"Enter number of GSC to create : "+Fore.RESET,
              Fore.GREEN+gscCount+Fore.RESET)
        print(Fore.GREEN+"12. "+
              Fore.GREEN+"Enter memory required to create GSC : "+Fore.RESET,
              Fore.GREEN+memoryGSC+Fore.RESET)
        print(Fore.GREEN+"13. "+
              Fore.GREEN+"Enter zone to create GSC : "+Fore.RESET,
              Fore.GREEN+zoneGSC+Fore.RESET)
        print(Fore.GREEN+"14. "+
              Fore.GREEN+"CEFLogger-1.0-SNAPSHOT.jar source : "+Fore.RESET,
              Fore.GREEN+str(cefLoggingJarInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"15. "+
              Fore.GREEN+"CEFLogger-1.0-SNAPSHOT.jar target : "+Fore.RESET,
              Fore.GREEN+str(cefLoggingJarInputTarget).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"16. "+
              Fore.GREEN+"db2jcc-4.26.14.jar source : "+Fore.RESET,
              Fore.GREEN+str(db2jccJarInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"17. "+
              Fore.GREEN+"db2jcc_license_cu-4.16.53.jar source : "+Fore.RESET,
              Fore.GREEN+str(db2jccJarLicenseInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"18. "+
              Fore.GREEN+"DB2 Feeder jars target : "+Fore.RESET,
              Fore.GREEN+str(db2FeederJarTargetInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"19. "+
              Fore.GREEN+"spring-ldap-core-2.3.3.RELEASE.jar source : "+Fore.RESET,
              Fore.GREEN+str(springLdapCoreJarInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"20. "+
              Fore.GREEN+"spring-security-ldap-5.1.7.RELEASE.jar source : "+Fore.RESET,
              Fore.GREEN+str(springLdapJarInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"21. "+
              Fore.GREEN+"VaultSupport-1.0-SNAPSHOT.jar source : "+Fore.RESET,
              Fore.GREEN+str(vaultSupportJarInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"22. "+
              Fore.GREEN+"JavaPasswordSDK.jar source : "+Fore.RESET,
              Fore.GREEN+str(javaPasswordJarInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"23. "+
              Fore.GREEN+"Spring jar target : "+Fore.RESET,
              Fore.GREEN+str(springTargetJarInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"24. "+
              Fore.GREEN+"ldap-security-config.xml source : "+Fore.RESET,
              Fore.GREEN+str(ldapSecurityConfigInput).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"25. "+
              Fore.GREEN+"ldap-security-config.xml target : "+Fore.RESET,
              Fore.GREEN+str(ldapSecurityConfigTargetInput).replace('"','')+Fore.RESET)

        verboseHandle.printConsoleWarning("------------------------------------------------------------")
        summaryConfirm = str(input(Fore.YELLOW+"Do you want to continue installation for above configuration ? [yes (y) / no (n)]: "+Fore.RESET))
        while(len(str(summaryConfirm))==0):
            summaryConfirm = str(input(Fore.YELLOW+"Do you want to continue installation for above configuration ? [yes (y) / no (n)]: "+Fore.RESET))

        if(summaryConfirm == 'y' or summaryConfirm =='yes'):
            for host in host_nic_dict_obj:
                gsNicAddress = host_nic_dict_obj[host]
                #print(host+"  "+gsNicAddress)
                additionalParam=additionalParam+' '+gsNicAddress
                logger.info("additionalParam - Installation :")
                logger.info("Building .tar file : tar -cvf install/install.tar install")
                cmd = 'tar -cvf install/install.tar install'
                with Spinner():
                    status = os.system(cmd)
                    logger.info("Creating tar file status : "+str(status))
                with Spinner():
                    scp_upload(host, user, 'install/install.tar', '')
                    #scp_upload(host, user, 'install/gs.service', '')
                cmd = 'tar -xvf install.tar'
                verboseHandle.printConsoleInfo("Extracting..")
                logger.debug("host : "+str(host)+" user:"+str(user)+" cmd "+str(cmd))
                output = executeRemoteCommandAndGetOutput(host, user, cmd)
                logger.debug("Execute RemoteCommand output:"+str(output))
                verboseHandle.printConsoleInfo(output)

                commandToExecute="scripts/security_dev_space_install.sh"
                logger.info("additionalParam : "+str(additionalParam))
                logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user))
                with Spinner():
                    outputShFile= executeRemoteShCommandAndGetOutput(host, user, additionalParam, commandToExecute)
                    #outputShFile = connectExecuteSSH(host, user,commandToExecute,additionalParam)
                    logger.debug("script output"+str(outputShFile))
                    #print(outputShFile)
                    #Upload CEF logging jar
                    scp_upload(host,user,cefLoggingJarInput,cefLoggingJarInputTarget)
                    scp_upload(host,user,db2jccJarInput,db2FeederJarTargetInput)
                    scp_upload(host,user,db2jccJarLicenseInput,db2FeederJarTargetInput)
                    scp_upload_multiple(host,user,sourceJar,springTargetJarInput)
                    scp_upload(host,user,ldapSecurityConfigInput,ldapSecurityConfigTargetInput)
                serverHost=''
                try:
                    serverHost = socket.gethostbyaddr(host).__getitem__(0)
                except Exception as e:
                    serverHost=host
                managerList = config_add_space_node(host, host, "N/A", "true")
                logger.info("Installation of space server "+str(host)+" has been done!")
                verboseHandle.printConsoleInfo("Installation of space server "+host+" has been done!")
        elif(summaryConfirm == 'n' or summaryConfirm =='no'):
            logger.info("menudriven")
            return
    except Exception as e:
        handleException(e)

if __name__ == '__main__':
    logger.info("odsx_security_space-install")
    verboseHandle.printConsoleWarning('Menu -> Security -> Dev -> Space -> Install')
    args = []
    menuDrivenFlag='m' # To differentiate between CLI and Menudriven Argument handling help section
    #print('Len : ',len(sys.argv))
    #print('Flag : ',sys.argv[0])
    args.append(sys.argv[0])
    try:
        if len(sys.argv) > 1 and sys.argv[1] != menuDrivenFlag:
            arguments = myCheckArg(sys.argv[1:])
            if(arguments.dryrun==True):
                current_os = platform.system().lower()
                logger.debug("Current OS:"+str(current_os))
                if current_os == "windows":
                    parameter = "-n"
                else:
                    parameter = "-c"
                exit_code = os.system(f"ping {parameter} 1 -w2 {arguments.host} > /dev/null 2>&1")
                if(exit_code == 0):
                    verboseHandle.printConsoleInfo("Connected to server with dryrun mode.!"+arguments.host)
                    logger.debug("Connected to server with dryrun mode.!"+arguments.host)
                else:
                    verboseHandle.printConsoleInfo("Unable to connect to server."+arguments.host)
                    logger.debug("Unable to connect to server.:"+arguments.host)
                quit()
            for arg in sys.argv[1:]:
                args.append(arg)
        # print('install :',args)
        elif(sys.argv[1]==menuDrivenFlag):
            args.append(menuDrivenFlag)
            #host = str(input("Enter your host: "))
            #args.append('--host')
            #args.append(host)
            #user = readValuefromAppConfig("app.server.user")
            user = str(input("Enter your user [root]: "))
            if(len(str(user))==0):
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
        #os.system('python3 scripts/servers_manager_scriptbuilder.py '+args)
        ## Execution script flow diverted to this file hence major changes required and others scripts will going to distrub

    except Exception as e:
        handleException(e)


