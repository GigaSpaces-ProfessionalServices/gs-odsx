#!/usr/bin/env python3

import csv
import datetime
import io
import json
import os
import requests
import subprocess

from colorama import Fore

from scripts.logManager import LogManager
from scripts.odsx_servers_di_list import listDIServers
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_dataIntegration_nodes, config_remove_dataIntegration_byNameIP, \
    config_get_dataIntegrationiidr_nodes
from utils.ods_ssh import connectExecuteSSH
from utils.odsx_keypress import userInputWrapper

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

def getDIServerHostList():
    nodeList = config_get_dataIntegration_nodes()
    nodes=""
    for node in nodeList:
        #if(str(node.role).casefold() == 'server'):
        if(len(nodes)==0):
            nodes = os.getenv(node.ip)
        else:
            nodes = nodes+','+os.getenv(node.ip)
    return nodes

def getDIServerHost():
    nodeList = config_get_dataIntegration_nodes()
    for node in nodeList:
        return os.getenv(node.ip)
    return ""


def exportAllPipelinesBeforeRemove(diHost, export_path):
    """Export all pipelines to YAML files before removal."""
    logger.info("exportAllPipelinesBeforeRemove()")
    try:
        os.makedirs(export_path, exist_ok=True)
        rootpath = "/dbagiga/utils/dihctl/"
        login_cmd = f"{rootpath}dihctl -e dev login --noauth http://{diHost}:7080"
        verboseHandle.printConsoleInfo("dihctl login: " + login_cmd)
        login_result = subprocess.run(login_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if login_result.returncode != 0:
            verboseHandle.printConsoleError("dihctl login failed: " + login_result.stderr)
            return
        result = subprocess.run(
            [f'{rootpath}dihctl', '-e', 'dev', 'show', 'pipelines', '--format', 'csv'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )
        reader = csv.DictReader(io.StringIO(result.stdout))
        pipelines = list(reader)
        if not pipelines:
            verboseHandle.printConsoleInfo("No pipelines found to export.")
            return
        for pipeline in pipelines:
            name = pipeline.get("name", "")
            if not name:
                continue
            export_file = os.path.join(export_path, f"{name}.yaml")
            export_cmd = f"{rootpath}dihctl -e dev export pipelines {name} -o {export_file}"
            verboseHandle.printConsoleInfo("Exporting pipeline: " + export_cmd)
            export_result = subprocess.run(export_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if export_result.returncode != 0:
                verboseHandle.printConsoleError("Export failed for " + name + ": " + export_result.stderr)
            else:
                verboseHandle.printConsoleInfo("Pipeline exported: " + export_file)
        logger.info("exportAllPipelinesBeforeRemove() completed")
    except Exception as e:
        handleException(e)


def exportDatasourcesBeforeRemove(diHost, export_path):
    """Export all datasource configs to JSON before removal."""
    logger.info("exportDatasourcesBeforeRemove()")
    try:
        os.makedirs(export_path, exist_ok=True)
        url = f"http://{diHost}:6080/api/v1/datasource/"
        verboseHandle.printConsoleInfo("Fetching datasources from: " + url)
        response = requests.get(url, headers={"Content-Type": "application/json"})
        if response.status_code != 200:
            verboseHandle.printConsoleError("Failed to list datasources: " + str(response.status_code) + " " + response.text)
            return
        datasources = response.json()
        export_file = os.path.join(export_path, "datasources.json")
        with open(export_file, 'w') as f:
            json.dump(datasources, f, indent=2)
        verboseHandle.printConsoleInfo("Datasources exported to: " + export_file)
        logger.info("exportDatasourcesBeforeRemove() completed: " + export_file)
    except Exception as e:
        handleException(e)


def deleteAllPipelines(diHost):
    """Delete all pipelines (with subscriptions) before removal."""
    logger.info("deleteAllPipelines()")
    try:
        rootpath = "/dbagiga/utils/dihctl/"
        login_cmd = f"{rootpath}dihctl -e dev login --noauth http://{diHost}:7080"
        login_result = subprocess.run(login_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if login_result.returncode != 0:
            verboseHandle.printConsoleError("dihctl login failed: " + login_result.stderr)
            return
        result = subprocess.run(
            [f'{rootpath}dihctl', '-e', 'dev', 'show', 'pipelines', '--format', 'csv'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )
        reader = csv.DictReader(io.StringIO(result.stdout))
        pipelines = list(reader)
        if not pipelines:
            verboseHandle.printConsoleInfo("No pipelines found to delete.")
            return
        for pipeline in pipelines:
            name = pipeline.get("name", "")
            if not name:
                continue
            delete_cmd = f"{rootpath}dihctl -e dev delete pipelines {name} --delete-subscription yes"
            verboseHandle.printConsoleInfo("Deleting pipeline: " + delete_cmd)
            delete_result = subprocess.run(delete_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if delete_result.returncode != 0:
                verboseHandle.printConsoleError("Delete failed for " + name + ": " + delete_result.stderr)
            else:
                verboseHandle.printConsoleInfo("Pipeline deleted: " + name)
        logger.info("deleteAllPipelines() completed")
    except Exception as e:
        handleException(e)


def deleteDatasources(diHost):
    """Delete all datasources before removal."""
    logger.info("deleteDatasources()")
    try:
        url = f"http://{diHost}:6080/api/v1/datasource/"
        response = requests.get(url, headers={"Content-Type": "application/json"})
        if response.status_code != 200:
            verboseHandle.printConsoleError("Failed to list datasources: " + str(response.status_code) + " " + response.text)
            return
        datasources = response.json()
        if not datasources:
            verboseHandle.printConsoleInfo("No datasources found to delete.")
            return
        for ds in datasources:
            sor_name = ds.get("sorName", "")
            if not sor_name:
                continue
            del_url = f"http://{diHost}:6080/api/v1/datasource/{sor_name}"
            verboseHandle.printConsoleInfo("Deleting datasource: " + sor_name)
            del_response = requests.delete(del_url)
            if del_response.status_code in (200, 204):
                verboseHandle.printConsoleInfo("Datasource deleted: " + sor_name)
            else:
                verboseHandle.printConsoleError("Delete failed for " + sor_name + ": " + str(del_response.status_code) + " " + del_response.text)
        logger.info("deleteDatasources() completed")
    except Exception as e:
        handleException(e)


def removeInputUserAndHost():
    logger.info("removeInputUserAndHost():")
    try:
        global user
        global host
        #user = str(userInputWrapper(Fore.YELLOW+"Enter user to connect to DI server [root]:"+Fore.RESET))
        #if(len(str(user))==0):
        user="root"
        logger.info(" user: "+str(user))

    except Exception as e:
        handleException(e)

def proceedForIndividualRemove(host_dict_obj, nodes):
    logger.info("proceedForIndividualRemove :")
    hostNumer = str(userInputWrapper(Fore.YELLOW+"Enter serial number to remove : "+Fore.RESET))
    while(len(str(hostNumer))==0):
        hostNumer = str(userInputWrapper(Fore.YELLOW+"Enter serial number to remove : "+Fore.RESET))
    host = host_dict_obj.get(hostNumer)
    confirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to remove "+str(host)+" ? (y/n) [y]"+Fore.RESET))
    if(confirm=='y' or len(str(confirm))==0 ):
        logger.info("Individual host : "+str(host))
        commandToExecute="scripts/servers_di_remove.sh"
        outputShFile= connectExecuteSSH(host, user,commandToExecute,'')
        print(outputShFile)
        config_remove_dataIntegration_byNameIP(host,host)
        hostAppConfig = str(readValuefromAppConfig("app.di.hosts")).replace('"','')
        logger.info("hostAppConfig :"+str(hostAppConfig))
        hostAppConfig = hostAppConfig.replace(host,'')
        logger.info("hostConfig after remove : "+str(hostAppConfig))
        #set_value_in_property_file('app.di.hosts',hostAppConfig)
        verboseHandle.printConsoleInfo("Node has been removed :"+str(host))


def executeCommandForUnInstall():
    logger.info("executeCommandForUnInstall(): start")
    try:
        host_dict_obj = listDIServers()
        logger.info("host_dict_obj :"+str(host_dict_obj))
        nodes = getDIServerHostList()
        nodesCount = nodes.split(',')
        logger.info("nodesCount :"+str(len(nodesCount)))
        wantToRemoveKafka = str(readValuefromAppConfig("app.di.base.kafka.wanttoremove"))
        wantToRemoveZk = str(readValuefromAppConfig("app.di.base.zk.wanttoremove"))
        wantToRemoveTelegraf = str(readValuefromAppConfig("app.di.base.telegraf.wanttoremove"))
        if(len(nodes)>0):
            removeType=''
            #if(len(nodesCount)>1):
                #removeType = str(userInputWrapper(Fore.YELLOW+"[1] Individual remove \n[Enter] To remove all \n[99] ESC : "))
            if(len(str(removeType))==0):
                verboseHandle.printConsoleInfo("Want to remove kafka : "+str(wantToRemoveKafka))
                verboseHandle.printConsoleInfo("Want to remove zookeeper : "+str(wantToRemoveZk))
                verboseHandle.printConsoleInfo("Want to remove telegraf : "+str(wantToRemoveTelegraf))
                confirmUninstall = str(userInputWrapper(Fore.YELLOW+"Are you sure want to remove DI servers ["+nodes+"] (y/n) [y]: "+Fore.RESET))
                if(len(str(confirmUninstall))==0):
                    confirmUninstall='y'
                logger.info("confirmUninstall :"+str(confirmUninstall))
                if(confirmUninstall=='y'):
                    # Export pipelines and datasources, then delete them before removing DI
                    diHost = getDIServerHost()
                    if diHost:
                        export_path = str(readValuefromAppConfig("app.dataengine.dihctl.yamlfolderpath"))
                        if not export_path.strip():
                            export_path = f"/tmp/di-export-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                        verboseHandle.printConsoleInfo("Exporting pipelines to: " + export_path)
                        exportAllPipelinesBeforeRemove(diHost, export_path)
                        exportDatasourcesBeforeRemove(diHost, export_path)
                        verboseHandle.printConsoleInfo("Deleting pipelines...")
                        deleteAllPipelines(diHost)
                        verboseHandle.printConsoleInfo("Deleting datasources...")
                        deleteDatasources(diHost)
                    else:
                        verboseHandle.printConsoleError("No DI server host found; skipping pipeline/datasource export+delete.")
                    commandToExecute="scripts/servers_di_remove.sh"
                    additionalParam= wantToRemoveKafka+" "+wantToRemoveZk+" "+wantToRemoveTelegraf
                    logger.debug("Additinal Param:"+additionalParam+" cmdToExec:"+commandToExecute+" Host:"+str(nodes)+" User:"+str(user))
                    with Spinner():
                        for host in nodes.split(','):
                            print(host)
                            outputShFile= connectExecuteSSH(host, user,commandToExecute,additionalParam)
                            print(outputShFile)
                            #config_remove_dataIntegration_byNameIP(host,host)
                            #set_value_in_property_file('app.di.hosts','')
                            verboseHandle.printConsoleInfo("Node has been removed :"+str(host))

                        nodeiidrList = config_get_dataIntegrationiidr_nodes()
                        for nodes in nodeiidrList:
                            iidrHost=os.getenv(nodes.ip)
                            outputShFile= connectExecuteSSH(iidrHost, user,commandToExecute,additionalParam)
                            verboseHandle.printConsoleInfo("DI Subscription Manager removal completed on IIDR host: "+str(iidrHost))
            if(removeType=='1'):
                proceedForIndividualRemove(host_dict_obj,nodes)
            if(removeType=='99'):
                return
        else:
            logger.info("No server details found.")
            verboseHandle.printConsoleInfo("No server details found.")
    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> DI -> Remove')
    try:
        removeInputUserAndHost()
        executeCommandForUnInstall()
    except Exception as e:
        handleException(e)
