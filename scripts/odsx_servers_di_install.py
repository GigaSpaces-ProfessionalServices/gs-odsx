#!/usr/bin/env python3

import json
import os
import signal
import subprocess
import time
import requests
import datetime
from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig, getYamlFilePathInsideFolder
from utils.ods_cleanup import signal_handler
from utils.ods_cluster_config import config_get_dataIntegration_nodes, config_get_manager_node, \
    config_get_dataIntegrationiidr_nodes
from utils.ods_manager import getManagerHost, getManagerInfo
from utils.ods_scp import scp_upload
from utils.ods_ssh import connectExecuteSSH, executeRemoteCommandAndGetOutput
from utils.odsx_keypress import userInputWrapper

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger
clusterHosts = []

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR


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


class obj_type_dictionary(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value


def getDIServerHostList():
    logger.info("getDIServerHostList()")
    nodeList = config_get_dataIntegration_nodes()
    nodes = ""
    for node in nodeList:
        if (len(nodeList) == 1):
            nodes = os.getenv(node.ip)
        else:
            nodes = nodes + ',' + os.getenv(node.ip)
    if nodes[0]==',':
        nodes=nodes[1:]
    return nodes

def installCluster():
    logger.info("installCluster()")
    global user
    global kafkaBrokerHost1
    global kafkaBrokerHost2
    global kafkaBrokerHost3
    global zkWitnessHost
    #    global cr8InstallFlag
    global telegrafInstallFlag
    telegrafInstallFlag="y"
    global baseFolderLocation
    global dataFolderKafka
    global dataFolderZK
    global logsFolderKafka
    global logsFolderZK
    global wantJava
    global flinkTaskManagerMemoryProcessSize
    global flinkJobManagerMemoryMetaspaceSize
    global dimMdmFlinkInstallon1bFlag
    global zkClientPort
    global zkDataDir
    global zkInitLimit
    global zkSyncLimit
    global zkTickTime

    global iidrHost
    global iidrUser
    global iidrPass
    global spaceLookupGroups
    global spaceLookupLocators

    kafkaBrokerHost1 = str(os.getenv("di1"))
    logger.info("kafkaBrokerHost1 : " + str(kafkaBrokerHost1))
    kafkaBrokerHost3 = str(os.getenv("di3"))
    logger.info("kafkaBrokerHost3 : " + str(kafkaBrokerHost3))
    zkWitnessHost = str(os.getenv("di4"))
    logger.info("zkWitnessHost :" + str(zkWitnessHost))
    kafkaBrokerHost2 = str(os.getenv("di2"))
    logger.info("kafkaBrokerHost2 : " + str(kafkaBrokerHost2))
    type_installer_dictionary_obj = obj_type_dictionary()
    type_installer_dictionary_obj.add('kafka Broker 1a',"[kafka,zk,telegraf]")
    type_installer_dictionary_obj.add('kafka Broker 1b',"[kafka,telegraf]")
    type_installer_dictionary_obj.add('kafka Broker 2',"[kafka,zk,telegraf]")
    type_installer_dictionary_obj.add('Zookeeper Witness',"[zk,telegraf]")
    nodeListSize = len(str((getDIServerHostList())).split(','))
    logger.info("nodeListSize : "+str(nodeListSize))
    srNo=0
    nodeList = config_get_dataIntegration_nodes()
    nodes = ""
    host_type_dictionary_obj = obj_type_dictionary()
    for node in nodeList:
        srNo=srNo+1
        if nodeListSize ==1 or nodeListSize==3:
            installer = "[kafka,zk,telegraf]"
            verboseHandle.printConsoleInfo(str(srNo)+". "+str(node.type)+" : "+installer)
        else:
            installer = str(type_installer_dictionary_obj.get(node.type))
            verboseHandle.printConsoleInfo(str(srNo)+". "+str(node.type)+"   "+installer+"  : "+os.getenv(node.ip))
        host_type_dictionary_obj.add(os.getenv(node.ip),str(node.type))

        clusterHosts.append(os.getenv(node.ip))

    user = "root"
    logger.info(" user: " + str(user))
    baseFolderLocation = str(readValuefromAppConfig("app.di.base.kafka.zk"))
    srNo=srNo+1
    print(Fore.GREEN +str(srNo)+ ". Installation base folder for Kafka and Zookeeper : "+baseFolderLocation+"" + Fore.RESET)
    logger.info(" base folder: " + str(baseFolderLocation))
    dataFolderKafka = str(readValuefromAppConfig("app.di.base.kafka.data"))
    srNo=srNo+1
    print(Fore.GREEN + str(srNo)+". Data folder for Kafka : "+dataFolderKafka+"" + Fore.RESET)
    logger.info(" dataFolderKafka: " + str(dataFolderKafka))
    dataFolderZK = str(readValuefromAppConfig("app.di.base.zk.data"))
    srNo=srNo+1
    print(Fore.GREEN + str(srNo)+". Data folder for Zookeeper : "+dataFolderZK+"" + Fore.RESET)
    logger.info(" dataFolderZK: " + str(dataFolderZK))
    logsFolderKafka = str(readValuefromAppConfig("app.di.base.kafka.logs"))
    srNo=srNo+1
    print(Fore.GREEN + str(srNo)+". Base logs folder for kafka : "+logsFolderKafka+"" + Fore.RESET)
    logger.info(" logsFolderKafka: " + str(logsFolderKafka))
    logsFolderZK = str(readValuefromAppConfig("app.di.base.zk.logs"))
    srNo=srNo+1
    print(Fore.GREEN + str(srNo)+". Base logs folder for Zookeeper : "+logsFolderZK+"" + Fore.RESET)
    logger.info(" logsFolderZK: " + str(logsFolderZK))
    wantJava = str(getYamlFilePathInsideFolder(".kafka.jolokiaJar"))
    srNo=srNo+1
    print(Fore.GREEN + str(srNo)+". Jolokia jar file path source : "+wantJava+"" + Fore.RESET)
    logger.info(" wantJava: " + str(wantJava))
    wantJava = str(readValuefromAppConfig("app.di.base.java.want"))
    srNo=srNo+1
    print(Fore.GREEN + str(srNo)+". Want to install Java : "+wantJava+"" + Fore.RESET)
    logger.info(" wantJava: " + str(wantJava))
    srNo=srNo+1
    sourcePath= sourceInstallerDirectory+"/kafka/"
    packageName = [f for f in os.listdir(sourcePath) if f.endswith('.tgz')]
    verboseHandle.printConsoleInfo(str(srNo)+". kafka installer : "+str(packageName))
    srNo=srNo+1
    sourcePath= sourceInstallerDirectory+"/zk/"
    packageName = [f for f in os.listdir(sourcePath) if f.endswith('.gz')]
    verboseHandle.printConsoleInfo(str(srNo)+". Zookeeper installer : "+str(packageName))
    srNo=srNo+1
    sourcePath= sourceInstallerDirectory+"/telegraf/"
    packageName = [f for f in os.listdir(sourcePath) if f.endswith('.rpm')]
    verboseHandle.printConsoleInfo(str(srNo)+". Telegraf installer : "+str(packageName))
    srNo=srNo+1
    sourcePath= sourceInstallerDirectory+"/data-integration/di-manager/"
    packageName = [f for f in os.listdir(sourcePath) if f.endswith('.gz')]
    verboseHandle.printConsoleInfo(str(srNo)+". DI-Manager (DIM) installer : "+str(packageName))
    srNo=srNo+1
    sourcePath= sourceInstallerDirectory+"/data-integration/di-mdm/"
    packageName = [f for f in os.listdir(sourcePath) if f.endswith('.gz')]
    verboseHandle.printConsoleInfo(str(srNo)+". DI-Metadata Manager (MDM) installer : "+str(packageName))
    srNo=srNo+1
    sourcePath= sourceInstallerDirectory+"/data-integration/di-flink/"
    packageName = [f for f in os.listdir(sourcePath) if f.endswith('.tgz')]
    verboseHandle.printConsoleInfo(str(srNo)+". DI-Flink installer >>: "+str(packageName))
    srNo=srNo+1
    flinkTaskManagerMemoryProcessSize = str(readValuefromAppConfig("app.di.flink.taskmanager.memory.process.size"))
    verboseHandle.printConsoleInfo(str(srNo)+". DI-Flink taskmanager.memory.process.size : "+str(flinkTaskManagerMemoryProcessSize))
    srNo=srNo+1
    flinkJobManagerMemoryMetaspaceSize = str(readValuefromAppConfig("app.di.flink.jobmanager.memory.jvm-metaspace.size"))
    verboseHandle.printConsoleInfo(str(srNo)+". DI-Flink jobmanager.memory.jvm-metaspace.size : "+str(flinkJobManagerMemoryMetaspaceSize))
    srNo=srNo+1
    dimMdmFlinkInstallon1bFlag = str(readValuefromAppConfig("app.di.flink.dim.mdm.install1b.confirm"))
    verboseHandle.printConsoleInfo(str(srNo)+". Install Flink/DIM/MDM on kafka broker 1b : "+ str(dimMdmFlinkInstallon1bFlag))
    srNo=srNo+1

    zkClientPort = str(readValuefromAppConfig("app.di.base.zk.clientPort"))
    zkDataDir = str(readValuefromAppConfig("app.di.base.zk.data"))
    zkInitLimit = str(readValuefromAppConfig("app.di.base.zk.initLimit"))
    zkSyncLimit = str(readValuefromAppConfig("app.di.base.zk.syncLimit"))
    zkTickTime = str(readValuefromAppConfig("app.di.base.zk.tickTime"))
    #iidrHost = str(readValuefromAppConfig("app.iidr.host"))
    iidrUser = str(readValuefromAppConfig("app.iidr.username"))
    iidrPass = str(readValuefromAppConfig("app.iidr.password"))
    iidrKafkaUser = str(readValuefromAppConfig("app.iidrkafka.username"))
    iidrKafkaPass = str(readValuefromAppConfig("app.iidrkafka.password"))
    iidrKafkaReadpath = str(readValuefromAppConfig("app.iidr-kafka.user-exit.properties.file.read-path"))
    iidrKafkaWritepath = str(readValuefromAppConfig("app.iidr-kafka.user-exit.properties.file.write-path"))

    verboseHandle.printConsoleInfo(str(srNo)+". zoo.cfg : clientPort="+ str(zkClientPort)+", dataDir="+str(zkDataDir)+", initLimit="+str(zkInitLimit)+", syncLimit="+str(zkSyncLimit)+", tickTime="+str(zkTickTime))

    logger.info("clusterHosts : " + str(clusterHosts))
    logger.info("host_type_dictionary_obj : " + str(host_type_dictionary_obj))
    managerHost = getManagerHost()
    managerInfo = getManagerInfo()
    spaceLookupGroups = str(managerInfo['lookupGroups'])
    spaceLookupLocators = str(managerHost) + ":4174"
    # Fallback: if getManagerHost() returned empty, derive host from cluster config
    if not managerHost:
        managerNodes = config_get_manager_node()
        for node in managerNodes:
            fallbackManagerHost = str(os.getenv(str(node.ip)))
            if fallbackManagerHost:
                spaceLookupLocators = fallbackManagerHost + ":4174"
                verboseHandle.printConsoleWarning("getManagerHost() returned empty; using config manager host: " + fallbackManagerHost)
                break
    verboseHandle.printConsoleInfo("spaceLookupGroups=" + spaceLookupGroups + "  spaceLookupLocators=" + spaceLookupLocators)
    nodeiidrList = config_get_dataIntegrationiidr_nodes()
    for nodes in nodeiidrList:
        iidrHost=os.getenv(nodes.ip)

    confirmInstall = str(userInputWrapper(
        Fore.YELLOW + "Are you sure want to install DI servers on " + str(clusterHosts) + " (y/n) [y]: " + Fore.RESET))
    if (len(str(confirmInstall)) == 0):
        confirmInstall = 'y'
    if (confirmInstall == 'y'):
        counter = 1
        diserver1=""
        di_all_servers=""
        managerHost1=""

        if len(clusterHosts) == 3:
            # Phase 1: Install ZK+Kafka on all 3 nodes; skip DI services on node1 (flag='n')
            dimMdmFlinkInstallon1bFlag = 'n'
            for host in clusterHosts:
                logger.info("Phase 1 - proceeding for host : " + str(host))
                if (counter == 1):
                    buildTarFileToLocalMachine(host)
                    diserver1=host
                if di_all_servers:
                    di_all_servers += ","
                di_all_servers += host + ":9092"
                buildUploadInstallTarToServer(host)
                executeCommandForInstall(host, host_type_dictionary_obj.get(host), counter, nodeListSize)
                counter = counter + 1

            # Wait for ZooKeeper quorum on node1 before installing DI services
            logger.info("Waiting for ZooKeeper quorum to form on " + kafkaBrokerHost1 + "...")
            print("Waiting for ZooKeeper quorum to form (up to 5 minutes)...")
            quorumFormed = False
            for attempt in range(30):
                try:
                    zkStatOutput = executeRemoteCommandAndGetOutput(kafkaBrokerHost1, user,
                                                                    "source /root/setenv.sh 2>/dev/null; $ZOOKEEPERPATH/bin/zkServer.sh status 2>/dev/null")
                    if 'leader' in zkStatOutput or 'follower' in zkStatOutput:
                        quorumFormed = True
                        logger.info("ZooKeeper quorum formed after " + str((attempt + 1) * 10) + "s")
                        print("ZooKeeper quorum formed.")
                        break
                except Exception:
                    pass
                logger.info("ZK quorum not ready yet (" + str(attempt + 1) + "/30), retrying in 10s...")
                time.sleep(10)
            if not quorumFormed:
                logger.warning("ZooKeeper quorum did not form within 5 minutes; proceeding anyway")
                print("WARNING: ZooKeeper quorum may not be ready. Proceeding with Phase 2...")

            # Phase 2: Install DI services on node1 only (flag='y')
            dimMdmFlinkInstallon1bFlag = 'y'
            logger.info("Phase 2 - installing DI services on node1: " + str(diserver1))
            print("Phase 2: Installing DI services on node1...")
            executeCommandForInstall(diserver1, host_type_dictionary_obj.get(diserver1), 1, nodeListSize)
        else:
            for host in clusterHosts:
                logger.info("proceeding for host : " + str(host))
                if (counter == 1):
                    buildTarFileToLocalMachine(host)
                    diserver1=host
                if di_all_servers:
                    di_all_servers += ","
                di_all_servers += host + ":9092"
                buildUploadInstallTarToServer(host)
                executeCommandForInstall(host, host_type_dictionary_obj.get(host), counter, nodeListSize)
                counter = counter + 1

        managerNodes = config_get_manager_node()
        for node in managerNodes:
            managerHost1=str(os.getenv(str(node.ip)))
            break
        managerInfo = getManagerInfo()
        lookupGroup = str(managerInfo['lookupGroups'])

        nodeiidrList = config_get_dataIntegrationiidr_nodes()
        for nodes in nodeiidrList:
            commandToExecute = "scripts/servers_di_install_all_subscription.sh"
            iidrHost=os.getenv(nodes.ip)
            additionalParam = iidrHost + ' '+ iidrUser + ' '+ iidrPass + ' ' + iidrKafkaUser + ' ' + iidrKafkaPass + ' '+ kafkaBrokerHost1 + ' '+sourceInstallerDirectory +' ' + iidrKafkaReadpath + ' '+iidrKafkaWritepath
            outputShFile = connectExecuteSSH(iidrHost, user, commandToExecute, additionalParam)
            logger.info("outputShFile iidr subscription : " + str(outputShFile))

            #Post DI install setup
            diProcessorJar = executeRemoteCommandAndGetOutput(iidrHost, user,
                                                              "ls /home/gsods/di-processor/latest-di-processor/lib/job-*.jar 2>/dev/null | head -n 1").strip()
            print("diProcessorJar from iidrHost: " + str(diProcessorJar))
            additionalParam = diserver1 +" "+ iidrHost + ' '+ managerHost1 + ' '+ lookupGroup + ' '+ di_all_servers + ' '+ diProcessorJar
            commandToExecute = "scripts/servers_di_post_install.sh "+additionalParam
            os.system(commandToExecute)

        # Create Oracle datasource and import pipelines after DI install
        createDatasource()
        importAllPipelines()

        # Restart subscription manager on di1 to pick up final config
        logger.info("Restarting di-subscription-manager-iidr on " + kafkaBrokerHost1)
        verboseHandle.printConsoleInfo("Restarting di-subscription-manager-iidr on " + kafkaBrokerHost1)
        executeRemoteCommandAndGetOutput(kafkaBrokerHost1, user,
                                         "sudo systemctl restart di-subscription-manager-iidr.service")

        # All brokers are KRaft-formatted and running (each has its own meta.properties);
        # the shared cluster-id handoff file is no longer needed, so clean it up.
        try:
            os.remove(os.path.join(sourceInstallerDirectory, "kafka-cluster-id"))
        except OSError:
            pass

        verboseHandle.printConsoleInfo("Completed DI installation")

def createDatasource():
    """Create datasource(s) via di-manager API after DI install.
    Loads exported datasources.json if available; each field falls back to app.config defaults
    when the exported value is missing or blank. username and password always use app.config
    values regardless of what is in the exported file."""
    logger.info("createDatasource()")
    try:
        # Always compute defaults so they can fill in any missing/blank exported fields
        defaultUsername = str(readValuefromAppConfig("app.cdc.datasource.username"))
        defaultPassword = str(readValuefromAppConfig("app.cdc.datasource.password"))
        defaultIidrHost = ""
        for node in config_get_dataIntegrationiidr_nodes():
            defaultIidrHost = os.getenv(node.ip)
            break
        defaults = {
            "sorName":        "ORACLE",
            "dbProvider":     "ORACLE",
            "url":            f"iidr://{defaultIidrHost}:11001",
            "username":       defaultUsername,
            "password":       defaultPassword,
            "additionalInfo": "",
            "offlineMode":    False
        }

        # Try to load datasources from the export file
        exported_list = []
        export_path = str(readValuefromAppConfig("app.dataengine.dihctl.datasourcefolderpath"))
        if export_path.strip():
            export_file = os.path.join(export_path, "datasources.json")
            if os.path.isfile(export_file):
                with open(export_file, 'r') as f:
                    exported_list = json.load(f) or []
                if exported_list:
                    verboseHandle.printConsoleInfo("Found exported datasource file: " + export_file)

        # username and password always come from app.config regardless of exported file
        credential_fields = {"username", "password"}

        # Build the list to create: exported entries with per-field fallback, or just the default
        if exported_list:
            datasources_to_create = []
            for ds in exported_list:
                entry = {}
                for field, default_val in defaults.items():
                    if field in credential_fields:
                        entry[field] = default_val
                    else:
                        exported_val = ds.get(field)
                        # Use exported value only when it is set and non-empty string
                        if exported_val is not None and str(exported_val).strip() != "":
                            entry[field] = exported_val
                        else:
                            entry[field] = default_val
                            verboseHandle.printConsoleInfo(
                                "Field '" + field + "' missing/blank in export for datasource '" +
                                str(ds.get("sorName", "?")) + "'; using default: " + str(default_val))
                datasources_to_create.append(entry)
        else:
            verboseHandle.printConsoleInfo("No exported datasource file found; using default ORACLE config.")
            datasources_to_create = [defaults]

        api_url = f"http://{kafkaBrokerHost1}:6080/api/v1/datasource/save-connection"
        for body in datasources_to_create:
            verboseHandle.printConsoleInfo("Creating datasource " + body["sorName"] + ", url=" + body["url"])
            logger.info("createDatasource POST " + api_url)
            response = requests.post(api_url, json=body, headers={"Content-Type": "application/json"},
                                     proxies={"http": None, "https": None})
            if response.status_code in (200, 201):
                verboseHandle.printConsoleInfo("Datasource " + body["sorName"] + " created successfully.")
            else:
                verboseHandle.printConsoleError("Datasource creation failed for " + body["sorName"] + ": " + str(response.status_code) + " " + response.text)
            logger.info("createDatasource response: " + str(response.status_code) + " " + str(response.text))
    except Exception as e:
        handleException(e)


def importAllPipelines():
    """Import all pipeline YAML files from the configured import folder via dihctl."""
    logger.info("importAllPipelines()")
    try:
        import_path = str(readValuefromAppConfig("app.dataengine.dihctl.pipelinefolderpath"))
        if not import_path.strip() or import_path.strip().lower() == "none":
            verboseHandle.printConsoleInfo("Pipeline import path (app.dataengine.dihctl.pipelinefolderpath) is not configured; skipping pipeline import.")
            return
        if not os.path.exists(import_path):
            verboseHandle.printConsoleError("Pipeline import path not found: " + import_path)
            return
        files = [f for f in os.listdir(import_path) if os.path.isfile(os.path.join(import_path, f)) and f.endswith('.yaml')]
        if not files:
            verboseHandle.printConsoleInfo("No pipeline YAML files found in: " + import_path)
            return
        rootpath = "/dbagiga/utils/dihctl/"
        login_cmd = f"{rootpath}dihctl -e dev login --noauth http://{kafkaBrokerHost1}:7080"
        verboseHandle.printConsoleInfo("dihctl login: " + login_cmd)
        login_result = subprocess.run(login_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if login_result.returncode != 0:
            verboseHandle.printConsoleError("dihctl login failed: " + login_result.stderr)
            return
        for fname in files:
            fpath = os.path.join(import_path, fname)
            import_cmd = f"{rootpath}dihctl -e dev apply -f {fpath}"
            verboseHandle.printConsoleInfo("Importing pipeline: " + import_cmd)
            result = subprocess.run(import_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if result.returncode != 0:
                verboseHandle.printConsoleError("Pipeline import failed for " + fname + ": " + result.stderr)
            else:
                verboseHandle.printConsoleInfo("Pipeline imported: " + fname + "\n" + result.stdout)
        logger.info("importAllPipelines() completed")
    except Exception as e:
        handleException(e)


def _downloadDIArtifacts(pkg):
    logger.info("_downloadDIArtifacts()")
    for artifact in pkg.artifacts:
        if artifact.id == "xap" or artifact.action != "download":
            continue
        dest_subpath = _ARTIFACT_DEST.get(artifact.id)
        if not dest_subpath:
            logger.warning("No destination mapping for artifact '" + artifact.id + "', skipping download")
            continue
        dest_dir = os.path.join(sourceInstallerDirectory, dest_subpath)
        verboseHandle.printConsoleInfo("Downloading " + artifact.id + " to " + dest_dir + " ...")
        with Spinner():
            process_artifact_by_id(pkg, artifact.id, dest_dir)
        verboseHandle.printConsoleInfo("Downloaded " + artifact.id)


def buildTarFileToLocalMachine(host):
    logger.info("buildTarFileToLocalMachine :" + str(host))
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))#str(readValuefromAppConfig("app.setup.sourceInstaller"))
    userCMD = os.getlogin()
    if userCMD == 'ec2-user':
        cmd = 'sudo cp install/zookeeper/odsxzookeeper.service install/kafka/odsxkafka.service '+sourceInstallerDirectory+"/zk/"
        cmd2= 'sudo cp install/kafka/odsxkafka.service '+sourceInstallerDirectory+"/kafka/"
    else:
        cmd = 'cp install/zookeeper/odsxzookeeper.service install/kafka/odsxkafka.service '+sourceInstallerDirectory+"/zk/"
        cmd2= 'cp install/kafka/odsxkafka.service '+sourceInstallerDirectory+"/kafka/"
    with Spinner():
        status = os.system(cmd)
        status = os.system(cmd2)
    sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))#str(readValuefromAppConfig("app.setup.sourceInstaller"))
    cmd = 'tar -cvf install/install.tar install'#+sourceInstallerDirectory  # Creating .tar file on Pivot machine
    with Spinner():
        status = os.system(cmd)
        logger.info("Creating tar file status : " + str(status))
        print("Creating tar file status : " + str(status))


def buildUploadInstallTarToServer(host):
    logger.info("buildUploadInstallTarToServer(): start host :" + str(host))
    try:
        with Spinner():
            logger.info("hostip ::" + str(host) + " user :" + str(user))
            scp_upload(host, user, 'install/install.tar', '')
    except Exception as e:
        handleException(e)


def executeCommandForInstall(host, type, count,nodeListSize):
    logger.info("executeCommandForInstall(): start host : " + str(host) + " type : " + str(type))

    try:
        additionalParam = ""
        additionalParam = telegrafInstallFlag + ' '
        #if (len(clusterHosts) == 4):
        #    commandToExecute = "scripts/servers_di_install.sh"
        #    additionalParam = additionalParam + kafkaBrokerHost1 + ' ' + kafkaBrokerHost2 + ' ' + kafkaBrokerHost3 + ' ' + zkWitnessHost + ' ' + str(count) + ' ' + str(baseFolderLocation)+ ' ' + str(dataFolderKafka)+ ' ' + str(dataFolderZK)+ ' ' + str(logsFolderKafka)+ ' ' + str(logsFolderZK)+' '+str(wantJava)+' '+sourceInstallerDirectory+' '+ host + ' ' + flinkJobManagerMemoryMetaspaceSize + ' ' + flinkTaskManagerMemoryProcessSize + ' ' + dimMdmFlinkInstallon1bFlag
        if(len(clusterHosts)==3):
            commandToExecute = "scripts/servers_di_install_all.sh"
            additionalParam = additionalParam +' '+str(nodeListSize)+' '+ kafkaBrokerHost1 + ' ' + kafkaBrokerHost2 + ' ' + kafkaBrokerHost3 + ' ' + str(count) + ' ' + str(baseFolderLocation)+ ' ' + str(dataFolderKafka)+ ' ' + str(dataFolderZK)+ ' ' + str(logsFolderKafka)+ ' ' + str(logsFolderZK)+' '+str(wantJava)+' '+sourceInstallerDirectory+' '+host + ' ' + flinkJobManagerMemoryMetaspaceSize + ' ' + flinkTaskManagerMemoryProcessSize + ' ' + dimMdmFlinkInstallon1bFlag + ' ' +zkClientPort+ ' ' + zkInitLimit+ ' ' +zkSyncLimit+ ' ' +zkTickTime + ' '+ iidrHost + ' '+ iidrUser + ' '+ iidrPass + ' ' + spaceLookupGroups + ' ' + spaceLookupLocators
        if(len(clusterHosts)==1):
            commandToExecute = "scripts/servers_di_install_all.sh"
            additionalParam = additionalParam +' '+str(nodeListSize)+' '+ kafkaBrokerHost1 + ' ' + str(count) + ' ' + str(baseFolderLocation)+ ' ' + str(dataFolderKafka)+ ' ' + str(dataFolderZK)+ ' ' + str(logsFolderKafka)+ ' ' + str(logsFolderZK)+' '+str(wantJava)+' '+sourceInstallerDirectory+' '+host + ' ' + flinkJobManagerMemoryMetaspaceSize + ' ' + flinkTaskManagerMemoryProcessSize + ' ' +zkClientPort+ ' ' +zkInitLimit+ ' ' +zkSyncLimit+ ' ' +zkTickTime + ' ' + iidrHost+ ' '+ iidrUser + ' '+ iidrPass + ' ' + spaceLookupGroups + ' ' + spaceLookupLocators
        logger.info("Additional Param:" + additionalParam + " cmdToExec:" + commandToExecute + " Host:" + str(
            host) + " User:" + str(user))
        print(additionalParam)
        with Spinner():
            verboseHandle.printConsoleInfo("S==========="+str(host))
            verboseHandle.printConsoleInfo(commandToExecute)
            verboseHandle.printConsoleInfo(additionalParam)
            verboseHandle.printConsoleInfo("E==========="+str(host))

            outputShFile = connectExecuteSSH(host, user, commandToExecute, additionalParam)
            logger.info("outputShFile kafka : " + str(outputShFile))
            print("Checking for Type ::::" + str(type))
            verboseHandle.printConsoleInfo("Node has been added :" + str(host))
    except Exception as e:
        handleException(e)

def executeLocalCommandAndGetOutput(commandToExecute):
    logger.info("executeLocalCommandAndGetOutput() cmd :" + str(commandToExecute))
    cmd = commandToExecute
    cmdArray = cmd.split(" ")
    process = subprocess.Popen(cmdArray, stdout=subprocess.PIPE)
    out, error = process.communicate()
    out = out.decode()
    return str(out).replace('\n', '')


def validateRPM():
    logger.info("validateRPM()")
    installerArray = []
    cmd = "pwd"
    home = executeLocalCommandAndGetOutput(cmd)
    logger.info("home dir : " + str(home))
    cmd = 'find '+sourceInstallerDirectory+'/jdk/ -name *.rpm -printf "%f\n"'  # Checking .rpm file on Pivot machine
    javaRpm = executeLocalCommandAndGetOutput(cmd)
    logger.info("javaRpm found :" + str(javaRpm))
    cmd = 'find '+sourceInstallerDirectory+'/kafka/ -name *.tgz -printf "%f\n"'  # Checking .tgz file on Pivot machine
    kafkaZip = executeLocalCommandAndGetOutput(cmd)
    logger.info("kafkaZip found :" + str(kafkaZip))
    cmd = 'find '+sourceInstallerDirectory+'/zk/ -name *.tar.gz -printf "%f\n"'  # Checking .tar.gz file on Pivot machine
    zkZip = executeLocalCommandAndGetOutput(cmd)
    logger.info("ZookeeperZip found :" + str(zkZip))
    cmd = 'find '+sourceInstallerDirectory+'/kafka/ -name *.jar -printf "%f\n"'  # Checking .tar.gz file on Pivot machine
    jolokiaJar = executeLocalCommandAndGetOutput(cmd)
    cmd = 'find '+sourceInstallerDirectory+'/telegraf/ -name *.rpm -printf "%f\n"'  # Checking .rpm file on Pivot machine
    telegrafRpm = executeLocalCommandAndGetOutput(cmd)
    logger.info("telegrafRpm found :" + str(telegrafRpm))

    di_installer_dict = obj_type_dictionary()
    di_installer_dict.add('Java', javaRpm)
    di_installer_dict.add('KafkaZip', kafkaZip)
    di_installer_dict.add('zkZip', zkZip)
    di_installer_dict.add('jolokiaJar', jolokiaJar)
    #di_installer_dict.add('CR8-LocalSetupZip', localSetupZip)
    di_installer_dict.add('Telegraf', telegrafRpm)

    for name, installer in di_installer_dict.items():
        if (len(str(installer)) == 0):
            verboseHandle.printConsoleInfo(
                "Pre-requisite installer "+sourceInstallerDirectory+"/.. " + str(name) + " not found")
            return False
    return True


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Servers -> DI -> Install')
    sourceInstallerDirectory=""
    signal.signal(signal.SIGINT, signal_handler)
    try:
        sourceInstallerDirectory = str(os.getenv("ODSXARTIFACTS"))
        if (validateRPM()):
            installCluster()
        else:
            logger.info("No valid rpm found")

    except Exception as e:
        handleException(e)
