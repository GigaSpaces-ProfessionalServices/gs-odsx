#!/usr/bin/env python3
import os, socket, sys, argparse
from scripts.logManager import LogManager
from colorama import Fore
from utils.ods_cluster_config import config_add_manager_node, config_add_space_node,config_cdc_list,getCDCIPAndName,config_add_cdc_stream, config_add_cdc_node
import requests,json
from utils.ods_ssh import executeRemoteCommandAndGetOutput
from datetime import datetime

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR

def discoveryManager():
    logger.info("discoveryManager()")
    hostsConfig=''
    managerType = int(input("Enter manager configuration type: "+Fore.YELLOW+"\n[1] Single \n[2] Cluster : "+Fore.RESET))
    logger.info("Manager Configuration Type : "+str(managerType))
    if(managerType==1):
        hostsConfig = str(input("Enter manager host: "))
        if(len(hostsConfig)<=0):
            verboseHandle.printConsoleError("Invalid host. Host configuration is required please specify valid host ip.")
            #break
    elif(managerType==2):
        host1 = str(input("Enter manager host1: "))
        host2 = str(input("Enter manager host2: "))
        host3 = str(input("Enter manager host3: "))
        if(len(host1)<=0 or len(host2)<=0 or len(host3)<=0):
            verboseHandle.printConsoleError("Invalid host. Host configuration is required please specify valid host ip.")
            #break
        hostsConfig=host1+','+host2+','+host3
        #logger.info("Congigured hosts : ",str(hostsConfig))
    else:
    #    logger.info("Invalid input host.")
        verboseHandle.printConsoleError("Invalid input host option configuration is required please specify valid host ip.")
        #break
    #logger.info("Congigured hosts : ",hostsConfig)
    hostsConfigArrray=[]
    hostsConfigArrray = hostsConfig.split(',')
    for host in hostsConfigArrray:
        serverHost=''
        try:
            serverHost = socket.gethostbyaddr(host).__getitem__(0)
        except Exception as e:
            serverHost=host
        config_add_manager_node(host,serverHost,"admin","true")
        verboseHandle.printConsoleInfo("Host "+host+" added successfully.")
    os.system('python3 scripts/odsx_servers_manager_list.py ')

def discoverySpace(host):
    logger.info("discoverySpace()")
    #logger.info("Servers - space host :"+str(host))
    response = requests.get('http://'+host+':8090/v2/hosts', headers={'Content-Type': 'application/json'} )
    #logger.info("Response status :"+response.status_code)
    #logger.info("Response content :"+response.content)
    responseStrArray = str(response.content).replace("b'","").replace("'","")
    jsonObjectArray = json.loads(responseStrArray)
    containers=[]
    for jsonObject in jsonObjectArray:
        containers = jsonObject['containers']
    serverHost=''
    try:
        serverHost = socket.gethostbyaddr(host).__getitem__(0)
    except Exception as e:
        serverHost=host
    config_add_space_node(host, serverHost, str(len(containers)), "true")
    verboseHandle.printConsoleInfo("Space host "+host+" added successfully.")
    os.system('python3 scripts/odsx_servers_space_list.py ')

def discoverStreams():
    logger.info("discover stream")
    cdclist =  config_cdc_list()
    streamIP=''
    streamConfigurationName=''
    streamState=''
    streamName=''
    streamHost=''
    output=''
    user = str(input("Enter user [ec2-user]: "))
    if(len(user)==0):
        user='ec2-user'
    if(len(cdclist)>1):
        streamDict = getCDCIPAndName()
        optionMainMenu = int(input("Enter your option: "))
        if(optionMainMenu != 99):
            if len(streamDict) >= optionMainMenu:
                stream = streamDict.get(optionMainMenu) #to get IP
                streamIP=stream.ip
    else:
        for cdc in cdclist:
            streamIP=cdc.ip
    #curl --request GET --header "Content-Type: application/json" http://10.0.0.220:2050/CR8/CM/configurations/getStatus
    #cmd = "curl -s  http://10.0.0.220:2050/CR8/CM/configurations/getStatus"
    cmd = "curl -s  http://"+streamIP+":2050/CR8/CM/configurations/getStatus"
    logger.info("cmd:"+str(cmd))
    output = executeRemoteCommandAndGetOutput(streamIP,user,cmd)
    logger.info("stream REST output:"+str(output))
    #print(output)
    '''
    streamDescription = str(input("Enter stream description [demo stream]: "))
    streamServerPathConfig = str(input("Enter stream file path [/home/dbsh/cr8/latest_cr8/etc/CR8Config.json]: "))
    if(len(streamDescription)==0):
        streamDescription='demo stream'
    if(len(streamServerPathConfig)==0):
        streamServerPathConfig='/home/dbsh/cr8/latest_cr8/etc/CR8Config.json'
    '''
    #output='''
    #[{"configurationName":"bll_db2_gs","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1623223816562,"state":"STOPPED","stateTimeStamp":1623223816562,"isSynchronized":false,"isSynchronizedTimeStamp":0,"modulesStatusList":[]},{"configurationName":"bll_db2_gs_551","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1618142930713,"state":"STOPPED","stateTimeStamp":1623139487125,"isSynchronized":false,"isSynchronizedTimeStamp":0,"modulesStatusList":[]},{"configurationName":"bll_db2_gs_614","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1618143123797,"state":"STOPPED","stateTimeStamp":1623139487152,"isSynchronized":false,"isSynchronizedTimeStamp":0,"modulesStatusList":[]},{"configurationName":"bll_db2_gs_928","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1618143182247,"state":"STOPPED","stateTimeStamp":1623139487175,"isSynchronized":false,"isSynchronizedTimeStamp":0,"modulesStatusList":[]},{"configurationName":"bll_db2_gs_ext_math","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1623761984931,"state":"STOPPED","stateTimeStamp":1623825039806,"isSynchronized":true,"isSynchronizedTimeStamp":1623825039816,"modulesStatusList":[]},{"configurationName":"bll_db2_gs_gimal","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1623762528312,"state":"STOPPED","stateTimeStamp":1623762579651,"isSynchronized":true,"isSynchronizedTimeStamp":1623762579662,"modulesStatusList":[]},{"configurationName":"bll_db2_gs_hbmain","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1624790782707,"state":"STOPPED","stateTimeStamp":1624790782707,"isSynchronized":true,"isSynchronizedTimeStamp":1623825899176,"modulesStatusList":[]},{"configurationName":"bll_db2_gs_heshbonlak","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1623762607510,"state":"STOPPED","stateTimeStamp":1623762607510,"isSynchronized":false,"isSynchronizedTimeStamp":0,"modulesStatusList":[]},{"configurationName":"bll_db2_gs_indxlak","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1623668681414,"state":"STOPPED","stateTimeStamp":1623668681414,"isSynchronized":false,"isSynchronizedTimeStamp":0,"modulesStatusList":[]},{"configurationName":"bll_db2_gs_joni_party","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1624520575268,"state":"STOPPED","stateTimeStamp":1624520575268,"isSynchronized":true,"isSynchronizedTimeStamp":1624461358404,"modulesStatusList":[]},{"configurationName":"bll_db2_gs_joni_prty","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1625580381601,"state":"STOPPED","stateTimeStamp":1625580381601,"isSynchronized":true,"isSynchronizedTimeStamp":1624969850755,"modulesStatusList":[]},{"configurationName":"bll_db2_gs_joni_prty_ddl_parser","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1624803603585,"state":"STOPPED","stateTimeStamp":1624803780572,"isSynchronized":true,"isSynchronizedTimeStamp":1624803780584,"modulesStatusList":[]},{"configurationName":"bll_db2_gs_joni_prty_satge","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1625580450171,"state":"STOPPED","stateTimeStamp":1625580450171,"isSynchronized":false,"isSynchronizedTimeStamp":0,"modulesStatusList":[]},{"configurationName":"bll_db2_gs_mati_isky","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1623668291842,"state":"STOPPED","stateTimeStamp":1623668291842,"isSynchronized":true,"isSynchronizedTimeStamp":1623224440915,"modulesStatusList":[]},{"configurationName":"bll_db2_gs_not_tn_mati","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1624442798550,"state":"STOPPED","stateTimeStamp":1624442798550,"isSynchronized":false,"isSynchronizedTimeStamp":0,"modulesStatusList":[]},{"configurationName":"bll_db2_gs_segment","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1624866059136,"state":"STOPPED","stateTimeStamp":1624866059136,"isSynchronized":true,"isSynchronizedTimeStamp":1623825598996,"modulesStatusList":[]},{"configurationName":"bll_db2_gs_tn_math","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1623761775255,"state":"STOPPED","stateTimeStamp":1623824837366,"isSynchronized":true,"isSynchronizedTimeStamp":1623824837379,"modulesStatusList":[]},{"configurationName":"bll_db2_gs_tn_mati","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1622633917187,"state":"STOPPED","stateTimeStamp":1623139487381,"isSynchronized":false,"isSynchronizedTimeStamp":0,"modulesStatusList":[]},{"configurationName":"bll_db2_gs_tn_mati_new","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1626176676649,"state":"STOPPED","stateTimeStamp":1626176676649,"isSynchronized":true,"isSynchronizedTimeStamp":1623826215369,"modulesStatusList":[]},{"configurationName":"tst_db2_gs_ext_math","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1624527706273,"state":"STOPPED","stateTimeStamp":1624527706273,"isSynchronized":false,"isSynchronizedTimeStamp":0,"modulesStatusList":[]},{"configurationName":"tst_db2_gs_gimal","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1624768248512,"state":"STOPPED","stateTimeStamp":1624768248512,"isSynchronized":true,"isSynchronizedTimeStamp":1624440837911,"modulesStatusList":[]},{"configurationName":"tst_db2_gs_hbmain","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1624768432146,"state":"STOPPED","stateTimeStamp":1624768432146,"isSynchronized":true,"isSynchronizedTimeStamp":1623590085389,"modulesStatusList":[]},{"configurationName":"tst_db2_gs_joni_party","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":false,"isValidTimeStamp":1624438200116,"state":"STOPPED","stateTimeStamp":1624438200116,"isSynchronized":false,"isSynchronizedTimeStamp":0,"modulesStatusList":[]},{"configurationName":"tst_db2_gs_mati_isky","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1624768149946,"state":"STOPPED","stateTimeStamp":1624768149946,"isSynchronized":true,"isSynchronizedTimeStamp":1623751353476,"modulesStatusList":[]},{"configurationName":"tst_db2_gs_tn_math","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1624768559281,"state":"STOPPED","stateTimeStamp":1624768559281,"isSynchronized":false,"isSynchronizedTimeStamp":0,"modulesStatusList":[]},{"configurationName":"tst_db2_gs_tn_mati_new","sourceDbType":"DB2ZOS","targetDBType":"GIGASPACES","isValid":true,"isValidTimeStamp":1624524934927,"state":"STOPPED","stateTimeStamp":1624802443704,"isSynchronized":true,"isSynchronizedTimeStamp":1624802443714,"modulesStatusList":[]}]
    #'''
    data = json.loads(output)
    for i in data :
        streamName=i["configurationName"]
        streamState = i["state"]
        streamDescription=streamName
        if('STOPPED'.casefold()==str(streamState).casefold()):
            streamState='Stopped'
        if('RUNNING'.casefold()==str(streamState).casefold()):
            streamState='Running'
        if('STARTED'.casefold()==str(streamState).casefold()):
            streamState='Running'
        streamServerPathConfig='/home/dbsh/cr8/latest_cr8/etc/'+streamName+'.json'
        now = datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")

        try:
            streamHost = socket.gethostbyaddr(streamIP).__getitem__(0)
        except Exception as e:
            logger.info("Exception while discover stream "+str(e))
            streamHost=streamIP
        logger.info("data adding "+str(streamName)+" "+str(streamDescription)+" "+str(dt_string)+" "+str(streamHost)+" "+str(streamServerPathConfig)+" "+str(streamState))
        config_add_cdc_stream(streamName,streamDescription,dt_string,streamHost,streamIP,streamServerPathConfig,streamState)
    verboseHandle.printConsoleInfo("Stream has been added.")
    logger.info("Stream added.")
def discoverCDC():
    hostIP = str(input("Enter cdc host or IP: "))
    logger.info("cdc hostip:"+str(hostIP))
    host=''
    try:
        host = socket.gethostbyaddr(hostIP).__getitem__(0)
    except Exception as e:
        host=hostIP
    if(len(host)>0):
        config_add_cdc_node(hostIP, host, "admin", "true")
    else:
        logger.info("Invalid host")
        verboseHandle.printConsoleError("Invalid host.")

if __name__ == '__main__':
    #discoveryManager()
    #host='13.59.135.138'
    #discoverySpace(host)
    discoverStreams()


