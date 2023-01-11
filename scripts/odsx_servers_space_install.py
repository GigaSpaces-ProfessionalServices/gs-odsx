#!/usr/bin/env python3
# s6.py
#!/usr/bin/python
import os, subprocess, sys, argparse, platform,socket
from concurrent.futures import ThreadPoolExecutor

from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig, set_value_in_property_file, readValueByConfigObj, \
    set_value_in_property_file_generic, read_value_in_property_file_generic_section, readValueFromYaml, \
    getYamlJarFilePath, getYamlFilePathInsideFolder, getYamlFilePathInsideConfigFolder
from colorama import Fore

from utils.ods_list import getManagerHostFromEnv, configureMetricsXML
from utils.ods_scp import scp_upload
from utils.ods_ssh import executeRemoteCommandAndGetOutput, executeRemoteShCommandAndGetOutput, connectExecuteSSH, \
    executeRemoteCommandAndGetOutputValuePython36
from utils.ods_cluster_config import config_add_space_node, config_get_cluster_airgap, config_get_space_hosts,isInstalledAndGetVersion
from scripts.odsx_servers_manager_install import validateRPMS,getPlainOutput
from scripts.spinner import Spinner
from utils.ods_scp import scp_upload,scp_upload_specific_extension
from utils.odsx_keypress import userInputWrapper

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

def getSpaceHostFromEnv():
    logger.info("getSpaceHostFromEnv()")
    hosts = ''
    spaceNodes = config_get_space_hosts()
    for node in spaceNodes:
        hosts+=str(os.getenv(str(node.ip)))+','
    hosts=hosts[:-1]
    return hosts

def getHostConfiguration():
    logger.info("getHostConfiguration()")
    try:
        hostsConfig=''
        #hostsConfig = readValuefromAppConfig("app.manager.hosts")
        hostsConfig =getManagerHostFromEnv()
        logger.info("Manager hostConfig : "+str(hostsConfig))
        applicativeUserFile = readValuefromAppConfig("app.server.user")
        #applicativeUser = str(userInputWrapper(Fore.YELLOW+"Applicative user ["+applicativeUserFile+"]: "+Fore.RESET))
        #if(len(str(applicativeUser))==0):
        applicativeUser = str(applicativeUserFile)
        logger.info("Applicative user : "+str(applicativeUser))
        set_value_in_property_file_generic('User',applicativeUser,'install/gs/gsa.service','Service')
        set_value_in_property_file_generic('User',applicativeUser,'install/gs/gsa.service','Service')
        set_value_in_property_file_generic('Group',applicativeUser,'install/gs/gsc.service','Service')
        set_value_in_property_file_generic('Group',applicativeUser,'install/gs/gsc.service','Service')

        if(len(hostsConfig)==2):
            hostsConfig=hostsConfig.replace('"','')
        #if(len(str(hostsConfig))>0):
        #    verboseHandle.printConsoleWarning("Current cluster configuration : ["+hostsConfig+"] ")
        #else:
        #    verboseHandle.printConsoleError("No manager configuration found:")
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
        #print("optionID:"+str(hostsConfig)+" : "+user)
        logger.debug("optionID:"+str(hostsConfig))
        targetDirectory=''
        gsOptionExtFromConfig = str(readValueByConfigObj("app.space.gsOptionExt")).replace('[','').replace(']','').replace("'","").replace(', ',',')
        #gsOptionExtFromConfig = '"{}"'.format(gsOptionExtFromConfig)
        additionalParam = str(readValuefromAppConfig("app.space.targetDirectory"))
        #print(Fore.YELLOW+"Target directory to install GS ["+Fore.GREEN+additionalParam+Fore.YELLOW+"]: "+Fore.RESET)
        targetDirectory=str(additionalParam)
        #if(len(additionalParam)==0):
        targetDirectory=additionalParam
        logger.info("targetDirecory :"+str(targetDirectory))
        gsOptionExt = ""
        #print(Fore.YELLOW+'GS_OPTIONS_EXT : '+Fore.GREEN+str(gsOptionExtFromConfig)+Fore.YELLOW+' '+Fore.RESET)
        #if(len(str(gsOptionExt))==0):
        #gsOptionExt='\"-Dcom.gs.work=/dbagigawork -Dcom.gigaspaces.matrics.config=/dbagiga/gs_config/metrics.xml\"'
        gsOptionExt=gsOptionExtFromConfig
        #else:
        #    set_value_in_property_file('app.space.gsOptionExt',gsOptionExt)
        gsOptionExt='"\\"{}\\""'.format(gsOptionExt)
        #print("gsoptionext:"+gsOptionExt)

        gsManagerOptionsFromConfig = str(readValueByConfigObj("app.manager.gsManagerOptions")).replace('[','').replace(']','')
        #gsManagerOptionsFromConfig = '"{}"'.format(gsManagerOptionsFromConfig)
        gsManagerOptions = ""
        #print(Fore.YELLOW+'Enter GS_MANAGER_OPTIONS  ['+Fore.GREEN+str(gsManagerOptionsFromConfig)+Fore.YELLOW+']: '+Fore.RESET)
        #if(len(str(gsManagerOptions))==0):
        #gsManagerOptions="-Dcom.gs.hsqldb.all-metrics-recording.enabled=false"
        gsManagerOptions=gsManagerOptionsFromConfig
        #else:
        #    set_value_in_property_file('app.manager.gsManagerOptions',gsManagerOptions)
        #gsManagerOptions='"{}"'.format(gsManagerOptions)
        gsManagerOptions='"\\"{}\\""'.format(gsManagerOptions)

        gsLogsConfigFileFromConfig = str(getYamlFilePathInsideFolder(".gs.config.log.xap_logging")).replace('[','').replace(']','')
        #gsLogsConfigFileFromConfig = '"{}"'.format(gsLogsConfigFileFromConfig)
        gsLogsConfigFile = ""
        #print(Fore.YELLOW+'Enter GS_LOGS_CONFIG_FILE  ['+Fore.GREEN+gsLogsConfigFileFromConfig+Fore.YELLOW+']: '+Fore.RESET)
        #if(len(str(gsLogsConfigFile))==0):
        #gsLogsConfigFile="/dbagiga/gs_config/xap_logging.properties"
        # gsLogsConfigFile=str(readValuefromAppConfig("app.log.target.file"))
        #else:
        #    set_value_in_property_file('app.manager.gsLogsConfigFile',gsLogsConfigFile)
        #gsLogsConfigFile = '"{}"'.format(gsLogsConfigFile)
        gsLogsConfigFile = str(readValuefromAppConfig("app.manager.gsLogsConfigFile"))

        licenseConfig = str(getYamlFilePathInsideFolder(".gs.config.license.gslicense"))
        #licenseConfig='"{}"'.format(licenseConfig)
        #gsLicenseFile = str(userInputWrapper(Fore.YELLOW+'GS_LICENSE ['+Fore.GREEN+licenseConfig+Fore.YELLOW+']: '+Fore.RESET))
        #if(len(str(gsLicenseFile))==0):
        gsLicenseFile = licenseConfig
        #else:
        #    gsLicenseFile = str(gsLicenseFile).replace(";","\;")
        gsLicenseFile='"\\"{}\\""'.format(gsLicenseFile)

        applicativeUser = read_value_in_property_file_generic_section('User','install/gs/gsa.service','Service')
        #print("Applicative User: "+str(applicativeUser))

        nofileLimit = str(readValuefromAppConfig("app.user.nofile.limit"))
        nofileLimitFile = ""
        #print(Fore.YELLOW+'User level open file limit : ['+Fore.GREEN+nofileLimit+Fore.YELLOW+']: '+Fore.RESET)
        logger.info("hardNofileLimitFile : "+str(nofileLimitFile))
        #if(len(str(nofileLimitFile))==0):
        nofileLimitFile = nofileLimit
        #else:
        #    set_value_in_property_file('app.user.hard.nofile',hardNofileLimitFile)
        nofileLimitFile = '"{}"'.format(nofileLimitFile)

        wantToInstallJava = str(readValuefromAppConfig("app.space.wantInstallJava"))
        #print(Fore.YELLOW+"Install Java : "+wantToInstallJava+Fore.RESET)
        #if(len(str(wantToInstallJava))==0):
        #    wantToInstallJava='n'

        wantToInstallUnzip = str(readValuefromAppConfig("app.space.wantInstallUnzip"))
        #print(Fore.YELLOW+"Install unzip : "+wantToInstallUnzip+Fore.RESET)
        #if(len(str(wantToInstallUnzip))==0):
        #    wantToInstallUnzip='n'
        global gscCount
        global memoryGSC
        global zoneGSC

        gscCountConfig = str(readValuefromAppConfig("app.space.gsc.count"))
        gscCount = ""
        #print(Fore.YELLOW+"Number of GSC to create : "+str(gscCountConfig)+Fore.RESET)
        #if(len(str(gscCount))==0):
        gscCount = gscCountConfig
        #set_value_in_property_file("app.space.gsc.count",str(gscCount))

        memoryGSCConfig = str(readValuefromAppConfig("app.space.gsc.memory"))
        memoryGSC = ""
        #print(Fore.YELLOW+"Memory required to create GSC : "+str(memoryGSCConfig)+Fore.RESET)
        #if(len(str(memoryGSC))==0):
        memoryGSC = memoryGSCConfig
        #set_value_in_property_file("app.space.gsc.memory",memoryGSC)

        zoneGSC = str(readValuefromAppConfig("app.space.gsc.zone"))
        #print(Fore.YELLOW+"Zone to create GSC : "+zoneGSC+Fore.RESET)
        #if(len(str(zoneGSC))==0):
        #    zoneGSC = 'bll'

        sourceDirectoryForJar = str(readValuefromAppConfig("app.space.jar.sourceFolder"))
        #print(Fore.YELLOW+"Source directory to copy jars from : "+sourceDirectoryForJar+Fore.RESET)
        #if(len(str(sourceDirectoryForJar))==0):
        #    sourceDirectoryForJar='/dbagiga'
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
        logger.info("sourceInstallerDirectory :"+str(sourceInstallerDirectory))
        logTargetPath=str(readValuefromAppConfig("app.log.target.file"))
        logSourcePath=str(getYamlFilePathInsideFolder(".gs.config.log.xap_logging"))
        startSpaceGsc=str(readValuefromAppConfig("app.space.start.gsc.path"))
        if(len(additionalParam)==0):
            additionalParam= 'true'+' '+targetDirectory+' '+hostsConfig+' '+gsOptionExt+' '+gsManagerOptions+' '+gsLogsConfigFile+' '+gsLicenseFile+' '+applicativeUser+' '+nofileLimitFile+' '+wantToInstallJava+' '+wantToInstallUnzip+' '+gscCount+' '+memoryGSC+' '+zoneGSC+' '+sourceInstallerDirectory+' '+logSourcePath+' '+logTargetPath
        else:
            additionalParam='true'+' '+targetDirectory+' '+hostsConfig+' '+gsOptionExt+' '+gsManagerOptions+' '+gsLogsConfigFile+' '+gsLicenseFile+' '+applicativeUser+' '+nofileLimitFile+' '+wantToInstallJava+' '+wantToInstallUnzip+' '+gscCount+' '+memoryGSC+' '+zoneGSC+' '+sourceInstallerDirectory+' '+logSourcePath+' '+logTargetPath
        #print('additional param :'+additionalParam)
        logger.debug('additional param :'+additionalParam)

        #noOfHost = str(userInputWrapper(Fore.YELLOW+"Enter number of space hosts you want to create :"+Fore.RESET))
        #while (len(str(noOfHost))==0):
        #    noOfHost = str(userInputWrapper(Fore.YELLOW+"Enter number of space hosts you want to create : "+Fore.RESET))
        noOfHost=len(getSpaceHostFromEnv().split(','))
        logger.debug("No of space host :"+str(noOfHost))
        host_nic_dict_obj = host_nic_dictionary()
        spaceHostConfig=getSpaceHostFromEnv()
        for host in getSpaceHostFromEnv().split(','):
            '''
            host = str(userInputWrapper(Fore.YELLOW+"Enter space host"+str(x)+" :"+Fore.RESET))
            while(len(str(host))==0):
                host = str(userInputWrapper(Fore.YELLOW+"Enter space host"+str(x)+" :"+Fore.RESET))
            if(len(str(spaceHostConfig))>0):
                spaceHostConfig = spaceHostConfig+','+host
            else:
                spaceHostConfig = host
            '''
            host_nic_dict_obj.add(host,'')
        #set_value_in_property_file('app.space.hosts',spaceHostConfig)
        wantNicAddress = str(readValuefromAppConfig("app.space.gsNicAddress"))
        #str(userInputWrapper(Fore.YELLOW+"Do you want to configure GS_NIC_ADDRESS for host ? (y/n) [n] : "+Fore.RESET))
        if(len(str(wantNicAddress))==0):
            wantNicAddress='n'
        if(wantNicAddress=="yes" or wantNicAddress=="y"):
            for host in host_nic_dict_obj:
                nicAddr = str(userInputWrapper(Fore.YELLOW+"Enter GS_NIC_ADDRESS of space host"+str(host)+" :"+Fore.RESET))
                logger.debug("host enter:"+host+" nicAddr :"+nicAddr)
                host_nic_dict_obj.add(host,nicAddr)
        logger.debug("hostNicAddr :"+str(host_nic_dict_obj))

        cefLoggingJarInput = str(getYamlFilePathInsideFolder(".security.jars.cef.cefjar")).replace('[','').replace(']','')
        cefLoggingJarInputTarget = str(readValuefromAppConfig("app.manager.cefLogging.jar.target")).replace('[','').replace(']','')
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
              Fore.GREEN+"MsSQL Feeder files source : "+Fore.RESET,
              Fore.GREEN+str(msSqlFeederFileSource).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"20. "+
              Fore.GREEN+"MsSQL Feeder files target : "+Fore.RESET,
              Fore.GREEN+str(msSqlFeederFileTarget).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"21. "+
              Fore.GREEN+"Space server installation : "+Fore.RESET,
              Fore.GREEN+str(spaceHostConfig).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"22. "+
              Fore.GREEN+"Log source file path : "+Fore.RESET,
              Fore.GREEN+str(logSourcePath).replace('"','')+Fore.RESET)
        print(Fore.GREEN+"23. "+
              Fore.GREEN+"Log target file path : "+Fore.RESET,
              Fore.GREEN+str(logTargetPath).replace('"','')+Fore.RESET)


        verboseHandle.printConsoleWarning("------------------------------------------------------------")
        summaryConfirm = str(userInputWrapper(Fore.YELLOW+"Do you want to continue installation for above configuration ? [yes (y) / no (n)]: "+Fore.RESET))
        while(len(str(summaryConfirm))==0):
            summaryConfirm = str(userInputWrapper(Fore.YELLOW+"Do you want to continue installation for above configuration ? [yes (y) / no (n)]: "+Fore.RESET))

        if(summaryConfirm == 'y' or summaryConfirm =='yes'):
            hostListLength = len(host_nic_dict_obj)+1
            with ThreadPoolExecutor(hostListLength) as executor:
                for host in host_nic_dict_obj:
                    executor.submit(installSpaceServer,host,additionalParam,host_nic_dict_obj,cefLoggingJarInput,cefLoggingJarInputTarget,db2jccJarInput,db2FeederJarTargetInput,db2jccJarLicenseInput,msSqlFeederFileTarget,startSpaceGsc)
        elif(summaryConfirm == 'n' or summaryConfirm =='no'):
            logger.info("menudriven")
            return
    except Exception as e:
        handleException(e)

def installSpaceServer(host,additionalParam,host_nic_dict_obj,cefLoggingJarInput,cefLoggingJarInputTarget,db2jccJarInput,db2FeederJarTargetInput,db2jccJarLicenseInput,msSqlFeederFileTarget,startSpaceGsc):
    installStatus='No'
    install = isInstalledAndGetVersion(host)
    logger.info("install : "+str(install))
    if(len(str(install))>8):
        installStatus='Yes'
    if installStatus == 'No':
        gsNicAddress = host_nic_dict_obj[host]
        additionalParam=additionalParam+' '+startSpaceGsc+' '+gsNicAddress
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))#str(readValuefromAppConfig("app.setup.sourceInstaller"))
        logger.info("additionalParam - Installation :")
        logger.info("Building .tar file : tar -cvf install/install.tar install")
        '''
        userCMD = os.getlogin()
        if userCMD == 'ec2-user':
            cmd = 'sudo cp install/gs/* '+sourceInstallerDirectory+"/gs/"
        else:
            cmd = 'cp install/gs/* '+sourceInstallerDirectory+"/gs/"
        with Spinner():
            status = os.system(cmd)
        '''
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
        commandToExecute="scripts/servers_space_install.sh"
        logger.info("additionalParam : "+str(additionalParam))
        logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user))
        with Spinner():
            outputShFile= executeRemoteShCommandAndGetOutput(host, user, additionalParam, commandToExecute)
            #outputShFile = connectExecuteSSH(host, user,commandToExecute,additionalParam)
            logger.debug("script output"+str(outputShFile))
            #print(outputShFile)
            #Upload CEF logging jar
            #scp_upload(host,user,cefLoggingJarInput,cefLoggingJarInputTarget)
            verboseHandle.printConsoleInfo(cefLoggingJarInput+" -> "+cefLoggingJarInputTarget)
            executeRemoteCommandAndGetOutputValuePython36(host, user,"cp "+cefLoggingJarInput+" "+cefLoggingJarInputTarget)
            #UPLOAD DB2FEEDER JAR
            #if(confirmDb2FeederJar=='y'):
            #print("source :"+db2jccJarInput)
            #scp_upload(host,user,db2jccJarInput,db2FeederJarTargetInput)
            verboseHandle.printConsoleInfo(db2jccJarInput+" -> "+db2FeederJarTargetInput)
            executeRemoteCommandAndGetOutputValuePython36(host, user,"cp "+db2jccJarInput+" "+db2FeederJarTargetInput)
            #print("source2 :"+db2jccJarLicenseInput)
            #scp_upload(host,user,db2jccJarLicenseInput,db2FeederJarTargetInput)
            verboseHandle.printConsoleInfo(db2jccJarLicenseInput+" -> "+db2FeederJarTargetInput)
            executeRemoteCommandAndGetOutputValuePython36(host, user,"cp "+db2jccJarLicenseInput+" "+db2FeederJarTargetInput)
            #scp_upload_specific_extension(host,user,msSqlFeederFileSource,msSqlFeederFileTarget,'keytab')
            verboseHandle.printConsoleInfo("*"+getYamlFilePathInsideConfigFolder("..keytab")+" -> "+msSqlFeederFileTarget)
            executeRemoteCommandAndGetOutputValuePython36(host, user,"cp "+getYamlFilePathInsideConfigFolder("..keytab").replace("keytab","*keytab")+" "+msSqlFeederFileTarget)
            #scp_upload_specific_extension(host,user,msSqlFeederFileSource,msSqlFeederFileTarget,'conf')
            verboseHandle.printConsoleInfo(getYamlFilePathInsideConfigFolder("..sqljdbc")+" ->"+msSqlFeederFileTarget)
            executeRemoteCommandAndGetOutputValuePython36(host, user,"cp "+getYamlFilePathInsideConfigFolder("..sqljdbc")+" "+msSqlFeederFileTarget)
            configureMetricsXML(host)
        serverHost=''
        try:
            serverHost = socket.gethostbyaddr(host).__getitem__(0)
        except Exception as e:
            serverHost=host
        #managerList = config_add_space_node(host, host, "N/A", "true")
        logger.info("Installation of space server "+str(host)+" has been done!")
        verboseHandle.printConsoleInfo("Installation of space server "+host+" has been done!")
    else:
        verboseHandle.printConsoleInfo("Found installation. skipping installation for host "+host)
        logger.info("Found installation. skipping installation for host "+host)

if __name__ == '__main__':
    logger.info("odsx_servers_space_install")
    verboseHandle.printConsoleWarning('Menu -> Servers -> Space -> Install')
    args = []
    menuDrivenFlag='m' # To differentiate between CLI and Menudriven Argument handling help section
    #print('Len : ',len(sys.argv))
    #print('Flag : ',sys.argv[0])
    args.append(sys.argv[0])
    try:
        isValidRPMs = validateRPMS()
        if(isValidRPMs):
            args.append(menuDrivenFlag)
            #host = str(userInputWrapper("Enter your host: "))
            #args.append('--host')
            #args.append(host)
            #user = readValuefromAppConfig("app.server.user")
            #user = str(userInputWrapper("Enter your user [root]: "))
            #if(len(str(user))==0):
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
        else:
            pass
    except Exception as e:
        handleException(e)


