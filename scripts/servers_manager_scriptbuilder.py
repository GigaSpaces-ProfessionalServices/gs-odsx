#!/usr/bin/env python3
# s6.py
#!/usr/bin/python
import os, subprocess, sys, argparse
from os import  path
from utils.ods_cluster_config import config_get_cluster_airgap, config_add_manager_node, config_add_space_node,config_remove_manager_nodeById,config_get_space_listWithoutDisplay,config_remove_space_nodeByIP, \
    config_add_cdc_stream, config_update_stream_statusByCreationDate,getStreamIdByStreamCreationDateTime, config_get_manager_listWithoutDisplay, config_update_stream_statusById,config_get_manager_list,config_remove_manager_nodeByIP, \
    config_remove_space_nodeById,config_add_cdc_node,config_update_space_gsc_byHost,config_get_streamName_statusById,config_update_stream_statusByHost,config_get_cdc_streams,getStreamIdAndNameWithoutDisplay, getStreamIdAndName
from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_ssh import executeRemoteShCommandAndGetOutput
import socket
from utils.ods_ssh import executeRemoteCommandAndGetOutput
from utils.ods_app_config import readValuefromAppConfig, writeToFile, set_value_in_property_file
from datetime import datetime
from colorama import Fore

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

def check_argM(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('--host',
                        help='host ip',
                        required='True',
                        default='localhost')
    parser.add_argument('-u', '--user',
                        help='user name',
                        nargs="?",
                        default='root',
                        required=False)
    parser.add_argument('--id',
                        help='id',
                        default='')
    parser.add_argument('m', nargs='?')
    #verboseHandle.checkAndEnableVerbose(parser,sys.argv[1:])
    return parser.parse_args(args)
def check_arg(args=None):
    parser = argparse.ArgumentParser(description='Script to learn basic argparse')
    parser.add_argument('--host',
                        help='host ip',
                        required='True',
                        default='localhost')
    parser.add_argument('-u', '--user',
                        help='user name',
                        nargs="?",
                        default='root',
                        required=False)
    parser.add_argument('-dryrun', '--dryrun',
                        help='Dry run flag',
                        default='false', action='store_true')
    parser.add_argument('--id',
                        help='id',
                        default='')
    parser.add_argument('m', nargs='?')
    verboseHandle.checkAndEnableVerbose(parser,sys.argv[1:])
    return parser.parse_args(args)

def remote_run(arguments,cmdFile):
    host = arguments.host
    user = arguments.user
    logger.debug("Arguments"+str(arguments))
    optionID=str(arguments.id).strip()
    cmd_list = []
    cmdFile = cmdFile.replace('odsx_','').replace('.py','.sh')
    logger.info("Find respected shell script:"+cmdFile)
    if(path.exists(cmdFile)):
        #Pre command execution business validations and status validation
        cmd_list.append(cmdFile)
        #print('cmdList.:',cmdFile)
        pemFileName = readValuefromAppConfig("cluster.pemFile")
        exe = {'py':'python', 'sh':'bash', 'pl':'perl'}
        isConnectUsingPem = readValuefromAppConfig("cluster.usingPemFile")
        if(isConnectUsingPem=='True'):
            ssh = ''.join(['ssh',' -i ', pemFileName ,' ', user, '@',  host, ' '])
        else:
            ssh = ''.join(['ssh',' ', host, ' '])
        for cmd in cmd_list:
            type = exe[cmd.split('.')[1]]
            #if AirGap True then the installagtion will proceed from user/install/ ... java/unzip/wget/gs
            additionalParam=''
            java_version=''
            gsType=''
            gsVersion=''
            gsc=''
            streamName=''
            streamDescription = ''
            streamServerPathConfig=''
            if(cmdFile.__contains__('servers_manager_install') ) or (cmdFile.__contains__('servers_space_install')):
                logger.info("cmdfile : "+str(cmdFile)+" AirGap: "+str(config_get_cluster_airgap()))
                if(config_get_cluster_airgap()=='false'):
                    verboseHandle.printConsoleWarning('Please provide a value for the following, or click ENTER to accept the [default value]')
                    java_version=str(input("Enter java version want to install. "+Fore.YELLOW+"\n[1] Java 8 \n[Enter] Java 11: "+Fore.RESET))
                    if(len(java_version)==0):
                        java_version='11'
                    elif(java_version=='1'):
                        java_version='8'
                    gsType=str(input("Enter Gigaspace type you want to install. "+Fore.YELLOW+"\n[1] insightedge \n[Enter] xap : "+Fore.RESET))
                    if(len(gsType)==0):
                        gsType='xap'
                    elif(gsType=='1'):
                        gsType='insightedge'
                    gsVersion=str(input("Enter Gigaspace version you want to install [15.8.0]: "))
                    if(len(gsVersion)==0):
                        gsVersion='15.8.0'
                    logger.debug("JavaVersion:"+str(java_version))
                    logger.debug("GSType:"+str(gsType))
                    logger.debug("gsVersion:"+str(gsVersion))
            if(cmdFile.__contains__('servers_manager_install') ):
                logger.debug("Server - manager - install")
                hostConfiguration=''
                hostManager=optionID
                logger.debug("optionID:"+str(optionID))
                additionalParam = str(input("Enter target directory to install GS [/home/ec2-user/gs]: "))
                if(len(additionalParam)==0):
                    additionalParam='/home/ec2-user/gs'+' '+hostManager+' '+java_version+' '+gsType+' '+gsVersion
                else:
                    additionalParam=additionalParam+' '+hostManager+' '+java_version+' '+gsType+' '+gsVersion
                logger.debug('additional param :'+additionalParam)
                #print("PARAM:",additionalParam)
            elif(cmdFile.__contains__('servers_space_install')):
                hostsConfig = readValuefromAppConfig("app.manager.hosts")
                logger.debug("hostConfig :"+str(hostsConfig))
                verboseHandle.printConsoleWarning('Configured manger ['+hostsConfig+']')
                additionalParam = str(input("Enter target directory to install GS [/home/ec2-user/gs]: "))
                if(len(additionalParam)==0):
                    additionalParam='/home/ec2-user/gs'+' '+hostsConfig+' '+java_version+' '+gsType+' '+gsVersion
                else:
                    additionalParam=additionalParam+' '+hostsConfig+' '+java_version+' '+gsType+' '+gsVersion
                logger.debug('additional param :'+additionalParam)
            #if(cmdFile.__contains__('servers_space_start') or cmdFile.__contains__('servers_manager_start')):
            if(cmdFile.__contains__('servers_space_start')):
                '''
                verboseHandle.printConsoleWarning('Please provide a value for the following, or click ENTER to accept the [default value]')
                gsc = str(input("Enter number of GSC to start [2]: "))
                if(len(gsc)==0):
                    gsc='2'
                additionalParam=gsc
                '''
                logger.debug("Starting for host:"+host)
                #print('GSC:'+gsc+' Addnparam'+additionalParam)
            if(cmdFile.__contains__('streams_startonline') or cmdFile.__contains__('streams_resumeonline') or cmdFile.__contains__('streams_stoponline')):
                verboseHandle.printConsoleWarning('Please provide a value for the following, or click ENTER to accept the [default value]')
                osuser = str(input("Enter OS user [dbsh]: "))
                if(len(osuser)==0):
                    osuser='dbsh'
                password = str(input("Enter password: "))
                if(len(password)==0):
                    password='x' # dummy param added if blank password to provide stream name as 3rd param
                if(cmdFile.__contains__('streams_startonline')):
                    streamName = config_get_streamName_statusById(optionID)
                    streamDescription = streamName
                    streamServerPathConfig='/home/dbsh/cr8/latest_cr8/etc/'+streamName+'.json'
                    '''
                    streamName = str(input("Enter stream name [demo]: "))
                    streamDescription = str(input("Enter stream description [demo stream]: "))
                    streamServerPathConfig = str(input("Enter stream file path [/home/dbsh/cr8/latest_cr8/etc/CR8Config.json]: "))
                    if(len(streamDescription)==0):
                        streamDescription='demo stream'
                    if(len(streamServerPathConfig)==0):
                        streamServerPathConfig='/home/dbsh/cr8/latest_cr8/etc/CR8Config.json'
                    if(len(streamName)==0):
                        streamName='demo'
                    '''
                    additionalParam=osuser+' '+password+' '+streamName+' '+streamServerPathConfig
                if(cmdFile.__contains__('streams_resumeonline') or cmdFile.__contains__('streams_stoponline')):
                    streamName = config_get_streamName_statusById(optionID)
                    print("StreamName:",streamName)
                    additionalParam=osuser+' '+password+' '+streamName
            if(config_get_cluster_airgap()):
                #print(ssh + type +' -s '+config_get_cluster_airgap()+' < ' + cmd)
                cmd = ssh + type +' -s '+config_get_cluster_airgap()+' '+ additionalParam+' '+' < ' + cmd #+ '>> mylog.txt 2>&1'
                print(cmd)
                logger.info("cmd-AirGap-True :"+str(cmd))
            else:
                #print(ssh + type + ' < ' + cmd)
                cmd = ssh + type + ' < ' + cmd #+ '>> mylog.txt 2>&1'
                print(cmd)
                logger.info("cmd :"+str(cmd))
            outputMainScript=''
            streamDictStream=''
            streamResumeStream=''
            streamStatus=''

            with Spinner():
                if(cmdFile.__contains__('streams_startonline')):
                    cmd = ssh + type + ' -s '+additionalParam+' < scripts/streams_validator.sh'
                    print(cmd)
                    logger.info("cmd to validate stream:"+cmd)
                    os.system(cmd)
                    outputMainScript = executeRemoteShCommandAndGetOutput(host,user,additionalParam,cmdFile)
                    logger.info("SH output start stream:"+str(outputMainScript))
                    if(len(outputMainScript)>0):
                        status=0
                    streamStatus = getStreamStatus(outputMainScript, '')
                    print(streamStatus)
                    if(streamStatus=='Running'):
                        verboseHandle.printConsoleWarning('Stream is already in running mode.')
                        os.system('python3 scripts/odsx_streams_list.py')
                else:
                    status = os.system(cmd)
            # POST command execution Business process / status update /  display details
            if(cmdFile.__contains__('servers_manager_install') and status ==0):
                logger.info("Adding manager to config file:"+host)
                serverHost=''
                try:
                    serverHost = socket.gethostbyaddr(host).__getitem__(0)
                except Exception as e:
                    serverHost=host
                managerList = config_add_manager_node(host,serverHost,"admin","true")
                logger.info("Manager "+host+" added to config file")
                if(len(managerList)==1):
                    #verboseHandle.printConsoleInfo("Starting scheduler.")
                    logger.info("starting scheduler.")
                    cmd = "scripts/scheduler.sh start"
                    os.system(cmd)
            if(cmdFile.__contains__('servers_space_install') and status ==0):
                logger.debug("Adding host to config :"+str(host))
                serverHost=''
                try:
                    serverHost = socket.gethostbyaddr(host).__getitem__(0)
                except Exception as e:
                    serverHost=host
                config_add_space_node(host, serverHost, "N/A")
                logger.debug("Host "+str(host)+" Added to config. ")
                #or (cmdFile.__contains__('streams_resumeonline') and status==0 and streamStatus=='Started')
            if(cmdFile.__contains__('servers_manager_remove') and status ==0):
                logger.debug("server_manager_remove status==0")
                '''
                #Flow diverted takes manager remove list from appconfig instead cluster config 
                streamDict = config_get_manager_listWithoutDisplay()
                managerRemove = streamDict.get(int(optionID))
                config_remove_manager_nodeById(managerRemove.name,managerRemove.ip)
                verboseHandle.printConsoleInfo(managerRemove.name+" has been removed.")
                '''
                config_remove_manager_nodeByIP(optionID)
                logger.debug(str(optionID)+" has been removed.")
            #if(cmdFile.__contains__('servers_space_start') and status ==0):
                #logger.debug("Space started host:"+host+" with GSC:"+gsc)
                #config_update_space_gsc_byHost(host,gsc)
                #logger.debug("Space host:"+host+" updated with GSC:"+gsc+" in config.")
            if(cmdFile.__contains__('servers_space_remove') and status ==0):
                '''
                streamDict = config_get_space_listWithoutDisplay()
                spaceRemove = streamDict.get(int(optionID))
                config_remove_space_nodeById(spaceRemove.name,spaceRemove.ip)
                '''
                config_remove_space_nodeByIP(optionID)
                verboseHandle.printConsoleInfo(optionID+" has been removed.")
            if(cmdFile.__contains__('streams_startonline') and status ==0 and streamStatus=='Started'):
                now = datetime.now()
                dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
                #verboseHandle.printConsoleWarning('Please provide a value for the following, or click ENTER to accept the [default value]')
                #updatedStream = config_add_cdc_stream(streamName,streamDescription,dt_string,host,host,streamServerPathConfig,'Stopped')
                output = executeRemoteShCommandAndGetOutput(host,user,additionalParam,'scripts/streams_status.sh')
                print(output)
                status = getStreamStatus(output, status)
                print(status)
                config_update_stream_statusById(optionID,status)
                #config_update_stream_statusByCreationDate(dt_string,'Running')
                streamId = getStreamIdByStreamCreationDateTime(dt_string)
                verboseHandle.printConsoleInfo("Stream "+str(streamId)+" is in "+str(status)+' mode.')
                os.system('python3 scripts/odsx_streams_list.py')
            if(cmdFile.__contains__('streams_stoponline') and status ==0):
                config_update_stream_statusById(optionID,'Stopped')
                os.system('python3 scripts/odsx_streams_list.py')
            if(cmdFile.__contains__('streams_resumeonline') and status ==0):
                config_update_stream_statusById(optionID,'Running')
                os.system('python3 scripts/odsx_streams_list.py')
            if(cmdFile.__contains__('servers_cdc_install')  and status ==0):
                serverHost=''
                try:
                    serverHost = socket.gethostbyaddr(host).__getitem__(0)
                except Exception as e:
                    serverHost=host
                config_add_cdc_node(host, serverHost, "admin")

    else:
        verboseHandle.printConsoleError("Shell script "+cmdFile+" does not exist.")
        logger.error("Shell script "+cmdFile+" does not exist.")


def getStreamStatus(output, status):
    #print(str(output).__contains__('already'))
    status = ''
    if (str(output).casefold().__contains__('is NOT running')):
        status = 'Stopped'
    elif (str(output).casefold().__contains__('is running')):
        status = 'Running'
    elif (str(output).casefold().__contains__('been started pid')):
        status = 'Started'
    elif (str(output).casefold().__contains__('already running')):
        status = 'Running'
    return status


if __name__ == '__main__':
    #print('Len : ',len(sys.argv))
    #print('Flagfile : ',sys.argv[1])
    #print('FlagM : ',sys.argv[2])
    menuDrivenFlag='m' # To differentiate between CLI and Menudriven Argument handling help section
    optionID=""
    if(sys.argv[2] == menuDrivenFlag):
        args = check_argM(sys.argv[3:]) # it contain file_name + menudriven flag
    else:
        args = check_arg(sys.argv[2:]) # contains filename only (CLI)
    #print('1',sys.argv[0])
    #print(args)
    remote_run(args,sys.argv[1])
