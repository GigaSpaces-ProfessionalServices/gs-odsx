#!/usr/bin/env python3
# s6.py
#!/usr/bin/python
import os, subprocess, sys, argparse, platform,socket
from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig, set_value_in_property_file, readValueByConfigObj, set_value_in_property_file_generic, read_value_in_property_file_generic_section
from colorama import Fore
from utils.ods_scp import scp_upload
from utils.ods_ssh import executeRemoteCommandAndGetOutput,executeRemoteShCommandAndGetOutput
from utils.ods_cluster_config import config_add_space_node, config_get_cluster_airgap
from scripts.spinner import Spinner

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

def getHostConfiguration():
    hostsConfig=''
    hostsConfig = readValuefromAppConfig("app.manager.hosts")

    applicativeUserFile = readValuefromAppConfig("app.server.user")
    applicativeUser = str(input(Fore.YELLOW+"Applicative user ["+applicativeUserFile+"]: "+Fore.RESET))
    if(len(str(applicativeUser))==0):
        applicativeUser = str(applicativeUserFile)
    logger.info("Applicative user : "+str(applicativeUser))
    set_value_in_property_file_generic('User',applicativeUser,'install/gs.service','Service')
    set_value_in_property_file_generic('Group',applicativeUser,'install/gs.service','Service')

    if(len(hostsConfig)==2):
        hostsConfig=hostsConfig.replace('"','')
    if(len(str(hostsConfig))>0):
        verboseHandle.printConsoleWarning("Current cluster configuration : ["+hostsConfig+"] ")
    else:
        verboseHandle.printConsoleError("No manager configuration found:")
    return hostsConfig

def execute_ssh_server_manager_install(hostsConfig,user):
    hostManager=[]
    gsNicAddress=''
    additionalParam=''
    hostManager=hostsConfig.replace('"','').split(",")
    #print("optionID:"+str(hostsConfig)+" : "+user)
    logger.debug("optionID:"+str(hostsConfig))

    gsOptionExtFromConfig = readValueByConfigObj("app.manager.gsOptionExt")
    #gsOptionExtFromConfig = '"{}"'.format(gsOptionExtFromConfig)
    additionalParam = str(input(Fore.YELLOW+"Enter target directory to install GS [/dbagiga]: "+Fore.RESET))
    gsOptionExt = str(input(Fore.YELLOW+'Enter GS_OPTIONS_EXT  ['+gsOptionExtFromConfig+']: '+Fore.RESET))
    if(len(str(gsOptionExt))==0):
        #gsOptionExt='\"-Dcom.gs.work=/dbagigawork -Dcom.gigaspaces.matrics.config=/dbagiga/gs_config/metrics.xml\"'
        gsOptionExt=gsOptionExtFromConfig
    else:
        set_value_in_property_file('app.manager.gsOptionExt',gsOptionExt)
    gsOptionExt='"\\"{}\\""'.format(gsOptionExt)
    #print("gsoptionext:"+gsOptionExt)

    gsManagerOptionsFromConfig = readValueByConfigObj("app.manager.gsManagerOptions")
    #gsManagerOptionsFromConfig = '"{}"'.format(gsManagerOptionsFromConfig)
    gsManagerOptions = str(input(Fore.YELLOW+'Enter GS_MANAGER_OPTIONS  ['+gsManagerOptionsFromConfig+']: '+Fore.RESET))
    if(len(str(gsManagerOptions))==0):
        #gsManagerOptions="-Dcom.gs.hsqldb.all-metrics-recording.enabled=false"
        gsManagerOptions=gsManagerOptionsFromConfig
    else:
        set_value_in_property_file('app.manager.gsManagerOptions',gsManagerOptions)
    gsManagerOptions='"{}"'.format(gsManagerOptions)

    gsLogsConfigFileFromConfig = readValueByConfigObj("app.manager.gsLogsConfigFile")
    #gsLogsConfigFileFromConfig = '"{}"'.format(gsLogsConfigFileFromConfig)
    gsLogsConfigFile = str(input(Fore.YELLOW+'Enter GS_LOGS_CONFIG_FILE  ['+gsLogsConfigFileFromConfig+']: '+Fore.RESET))
    if(len(str(gsLogsConfigFile))==0):
        #gsLogsConfigFile="/dbagiga/gs_config/xap_logging.properties"
        gsLogsConfigFile=gsLogsConfigFileFromConfig
    else:
        set_value_in_property_file('app.manager.gsLogsConfigFile',gsLogsConfigFile)
    gsLogsConfigFile = '"{}"'.format(gsLogsConfigFile)

    licenseConfig = readValueByConfigObj("app.manager.license")
    #licenseConfig='"{}"'.format(licenseConfig)
    gsLicenseFile = str(input(Fore.YELLOW+'Enter GS_LICENSE ['+licenseConfig+']: '+Fore.RESET))
    if(len(str(gsLicenseFile))==0):
        gsLicenseFile = licenseConfig
    #else:
    #    gsLicenseFile = str(gsLicenseFile).replace(";","\;")
    gsLicenseFile='"\\"{}\\""'.format(gsLicenseFile)

    applicativeUser = read_value_in_property_file_generic_section('User','install/gs.service','Service')
    #print("Applicative User: "+str(applicativeUser))

    nofileLimit = str(readValuefromAppConfig("app.user.nofile.limit"))
    nofileLimitFile = str(input(Fore.YELLOW+'Enter user level open file limit : ['+nofileLimit+']: '+Fore.RESET))
    logger.info("hardNofileLimitFile : "+str(nofileLimitFile))
    if(len(str(nofileLimitFile))==0):
        nofileLimitFile = nofileLimit
    #else:
    #    set_value_in_property_file('app.user.hard.nofile',hardNofileLimitFile)
    nofileLimitFile = '"{}"'.format(nofileLimitFile)

    if(len(additionalParam)==0):
        additionalParam= 'true'+' '+'/dbagiga'+' '+hostsConfig+' '+gsOptionExt+' '+gsManagerOptions+' '+gsLogsConfigFile+' '+gsLicenseFile+' '+applicativeUser+' '+nofileLimitFile
    else:
        additionalParam='true'+' '+additionalParam+' '+hostsConfig+' '+hostsConfig+' '+gsOptionExt+' '+gsManagerOptions+' '+gsLogsConfigFile+' '+gsLicenseFile+' '+applicativeUser+' '+nofileLimitFile
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
    wantNicAddress = str(input(Fore.YELLOW+"Do you want to configure GS_NIC_ADDRESS for host ? [yes (y) / no (n)]: "+Fore.RESET))
    if(wantNicAddress=="yes" or wantNicAddress=="y"):
        for host in host_nic_dict_obj:
            nicAddr = str(input(Fore.YELLOW+"Enter GS_NIC_ADDRESS of space host"+str(host)+" :"+Fore.RESET))
            logger.debug("host enter:"+host+" nicAddr :"+nicAddr)
            host_nic_dict_obj.add(host,nicAddr)
    logger.debug("hostNicAddr :"+str(host_nic_dict_obj))

    for host in host_nic_dict_obj:
        gsNicAddress = host_nic_dict_obj[host]
        #print(host+"  "+gsNicAddress)
        additionalParam=additionalParam+' '+gsNicAddress
        logger.info("Building .tar file : tar -cvf install/install.tar install")
        cmd = 'tar -cvf install/install.tar install'
        with Spinner():
            status = os.system(cmd)
            logger.info("Creating tar file status : "+str(status))
        with Spinner():
            scp_upload(host, user, 'install/install.tar', '')
            scp_upload(host, user, 'install/gs.service', '')

        cmd = 'tar -xvf install.tar'
        verboseHandle.printConsoleInfo("Extracting..")
        logger.debug("host : "+str(host)+" user:"+str(user)+" cmd "+str(cmd))
        output = executeRemoteCommandAndGetOutput(host, user, cmd)
        logger.debug("Execute RemoteCommand output:"+str(output))
        verboseHandle.printConsoleInfo(output)

        commandToExecute="scripts/servers_space_install.sh"
        #print(additionalParam)
        logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(host)+" User:"+str(user))
        with Spinner():
            outputShFile= executeRemoteShCommandAndGetOutput(host, user, additionalParam, commandToExecute)
            logger.debug("script output"+str(outputShFile))
            #print(outputShFile)
        serverHost=''
        try:
            serverHost = socket.gethostbyaddr(host).__getitem__(0)
        except Exception as e:
            serverHost=host
        managerList = config_add_space_node(host, host, "N/A", "true")
        logger.info("Installation of space server "+str(host)+" has been done!")
        verboseHandle.printConsoleInfo("Installation of space server "+host+" has been done!")

if __name__ == '__main__':
    logger.info("odsx_servers_space_install")
    verboseHandle.printConsoleWarning('Servers -> Space -> Install')
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
        logger.error("Invalid argument space install :"+str(e))
        verboseHandle.printConsoleError("Invalid argument."+str(e))

