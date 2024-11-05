import os
import time
import requests
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig, getYamlFilePathInsideFolder
from utils.ods_cluster_config import config_get_manager_node, config_get_dataIntegration_nodes, \
    config_get_dataIntegrationiidr_nodes
from utils.ods_ssh import executeRemoteCommandAndGetOutputValuePython36
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_keypress import userInputWrapper, userInputWithEscWrapper
from utils.odsx_objectmanagement_utilities import getPivotHost

from utils.odsx_print_tabular_data import printTabular
from datetime import datetime

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


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

class host_dictionary_obj(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

def printPipelineTables(managerHost):
    di_manager_url = "http://"+managerHost+":6080"  # replace with actual URL

    # Get pipeline IDs
    response = requests.get(f"{di_manager_url}/api/v1/pipeline/")
    pipeline_ids = [pipeline["pipelineId"] for pipeline in response.json()]

    # Get table names for each pipeline
    dataTable = []
    counter = 0
    global gs_space_dictionary_obj
    gs_space_dictionary_obj = host_dictionary_obj()
    verboseHandle.printConsoleWarning("CDC Space Types :")
    headers = [Fore.YELLOW + "Sr No." + Fore.RESET,
               Fore.YELLOW + "Type" + Fore.RESET,
               Fore.YELLOW + "Piperline Name" + Fore.RESET
               ]

    for pipeline_id in pipeline_ids:
        pipeline_response = requests.get(f"{di_manager_url}/api/v1/pipeline/{pipeline_id}")
        pipeline_name = pipeline_response.json()["name"]

        tables_response = requests.get(f"{di_manager_url}/api/v1/pipeline/{pipeline_id}/tablepipeline")
        table_names = [table["spaceTypeName"] for table in tables_response.json()]

        for table_name in table_names:
            dataArray = [Fore.GREEN + str(counter + 1) + Fore.RESET,
                         Fore.GREEN + str(table_name) + Fore.RESET,
                         Fore.GREEN + str(pipeline_name) + Fore.RESET
                         ]
            gs_space_dictionary_obj.add(str(counter + 1), str(table_name))
            counter = counter + 1
            dataTable.append(dataArray)
    printTabular(None, headers, dataTable)

def getManagerHost():
    managerNodes = config_get_manager_node()
    managerHost = ""
    try:
        logger.info("getManagerHost() : managerNodes :" + str(managerNodes))
        for node in managerNodes:
            status = getSpaceServerStatus(os.getenv(node.ip))
            if (status == "ON"):
                managerHost = os.getenv(node.ip)
        return managerHost
    except Exception as e:
        handleException(e)

def getDIServerHost():
    nodeList = config_get_dataIntegration_nodes()
    nodes = ""
    for node in nodeList:
        # if(str(node.role).casefold() == 'server'):
        if (len(nodes) == 0):
            return os.getenv(node.ip)
    return nodes

def getIIDRHost():
    nodeiidrList = config_get_dataIntegrationiidr_nodes()
    for nodes in nodeiidrList:
        iidrHost=os.getenv(nodes.ip)
        return iidrHost

def cdcTypeRedeplyment(spaceType,diManagerHost, iidrHost):
    diManagerHost = diManagerHost + ":6080"
    #iidrHost = iidrHost + ":6082"
    args = spaceType+" "+managerHost+" "+diManagerHost+" "+iidrHost+" "+asHost+" "+asHostPort+" "+asUser+" "+asPass+" "+spaceName+" "+iidr_kafka_gs_properties_path+" "+iidrSubscriptionMangerPort
    commandToExecute = "scripts/cdc_schema_change.sh "+args
    os.system(commandToExecute)

def killManagersWebUI():
    managerNodes = config_get_manager_node()
    #commandToExecute = "kill -9 `ps -ef | grep webui | grep -v grep | awk '{print $2}'`"
    commandToExecute = "ps -ef | grep 'services=WEBUI' | grep java | awk '{print $2}' | xargs kill"
    for node in managerNodes:
        managerHost=str(os.getenv(str(node.ip)))
        outputShFile = executeRemoteCommandAndGetOutputValuePython36(managerHost, 'root', commandToExecute)
        verboseHandle.printConsoleInfo("Restarted web-ui for host:"+str(os.getenv(str(node.ip))))

def restartSpacedeck():
    managerNodes = config_get_manager_node()
    #commandToExecute = "kill -9 `ps -ef | grep webui | grep -v grep | awk '{print $2}'`"
    commandToExecute = '[ "$(docker ps | grep spacedeck-spacedeck-1)" ] && docker stop spacedeck-spacedeck-1 && docker start spacedeck-spacedeck-1'
    for node in managerNodes:
        managerHost=str(os.getenv(str(node.ip)))
        outputShFile = executeRemoteCommandAndGetOutputValuePython36(managerHost, 'root', commandToExecute)
        #verboseHandle.printConsoleInfo("Restarted for host:"+str(os.getenv(str(node.ip))))

    diNodes = config_get_dataIntegration_nodes()
    for node in diNodes:
        diHost=str(os.getenv(str(node.ip)))
        outputShFile = executeRemoteCommandAndGetOutputValuePython36(diHost, 'root', commandToExecute)

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle CDC Schema change')
    logger.info('Menu -> DataEngine -> Oracle CDC Schema change')
    managerNodes = config_get_manager_node()
    global diManagerHost
    global managerHost
    global iidrHost
    global asUser
    global asHost
    global asHostPort
    global asPass
    global spaceName
    global iidr_kafka_gs_properties_path
    global iidrSubscriptionMangerPort

    logger.info("managerNodes: main" + str(managerNodes))
    if (len(str(managerNodes)) > 0):
        diManagerHost = getDIServerHost()
        managerHost = getManagerHost()
        iidrHost = getIIDRHost()
        asHost = str(readValuefromAppConfig("app.cdc.ashost"))
        asHostPort = str(readValuefromAppConfig("app.cdc.ashostport"))
        asUser = str(readValuefromAppConfig("app.iidr.username"))
        asPass = str(readValuefromAppConfig("app.iidr.password"))
        spaceName = str(readValuefromAppConfig("app.spacejar.space.name"))
        iidr_kafka_gs_properties_path = str(readValuefromAppConfig("app.iidr-kafka.user-exit.properties.file.read-path"))
        iidrSubscriptionMangerPort = str(readValuefromAppConfig("app.iidr.iidrSubscriptionMangerPort"))
        printPipelineTables(diManagerHost)
        optionMainMenu = str(userInputWrapper("Enter Type Sr Number : "))
        if(len(optionMainMenu)==0):
            verboseHandle.printConsoleError("Invalid Input")
            exit(0)
        spaceType = gs_space_dictionary_obj.get(optionMainMenu)
        logger.info('gs_space_dictionary_obj : '+str(gs_space_dictionary_obj))
        finalConfirm = str(userInputWrapper(Fore.YELLOW+"Are you sure want to proceed - type will be dropped and reloaded? (y/n) [n] :"+Fore.RESET))
        if(len(str(finalConfirm))==0):
            finalConfirm='n'
        if(finalConfirm=='y'):
            cdcTypeRedeplyment(spaceType,diManagerHost, iidrHost)
            killManagersWebUI()
            tableListfilePath = str(getYamlFilePathInsideFolder(".object.config.ddlparser.ddlBatchFileName")).replace("//", "/")
            ddlAndPropertiesBasePath = os.path.dirname(tableListfilePath) + "/"
            wantToAddIndex = str(userInputWithEscWrapper("Do you want to add index (y/n) [n] ?"))
            if wantToAddIndex == 'y':
                timestamp = time.time()
                filename_suffix = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d_%H-%M-%S')
                os.system("cp " +ddlAndPropertiesBasePath+"/batchIndexes.csv" + " " +ddlAndPropertiesBasePath+"/batchIndexes.csv" + ".backup." + filename_suffix)
                addedIndex = str(userInputWithEscWrapper("modified index (Ex. STUD.TA_PERSON  SHEM_MISHP_ENG  ORDERED :"))
                addedIndex = addedIndex.replace(" ","\t")
                with open(ddlAndPropertiesBasePath+"/batchIndexes.csv", 'a') as file:
                    file.write("\n"+addedIndex)
                #Run the indexes
            elif wantToAddIndex== "99":
                exit(0)
            objectMgmtHost = getPivotHost()
            response = requests.post('http://' + objectMgmtHost + ':7001/index/addinbatch',
                                     headers={'Accept': 'application/json'})
            logger.info("indexes response : "+str(response))
            verboseHandle.printConsoleInfo("Added indexes")
            verboseHandle.printConsoleWarning("Please redeploy services which are using this table")
        #restartSpacedeck()
        else:
            exit(0)

