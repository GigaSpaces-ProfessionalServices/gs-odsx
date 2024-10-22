import os
import time
import requests
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_manager_node, config_get_dataIntegration_nodes, \
    config_get_dataIntegrationiidr_nodes
from utils.ods_validation import getSpaceServerStatus
from utils.odsx_keypress import userInputWrapper

from utils.odsx_print_tabular_data import printTabular

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
    iidrHost = iidrHost + ":6082"
    args = spaceType+" "+managerHost+" "+diManagerHost+" "+iidrHost+" "+asHost+" "+asHostPort+" "+asUser+" "+asPass+" "+spaceName
    commandToExecute = "scripts/cdc_schema_change.sh "+args
    os.system(commandToExecute)

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

        printPipelineTables(diManagerHost)
        optionMainMenu = str(userInputWrapper("Enter Type Sr Number : "))
        if(len(optionMainMenu)==0):
            verboseHandle.printConsoleError("Invalid Input")
            exit(0)
        spaceType = gs_space_dictionary_obj.get(optionMainMenu)
        logger.info('gs_space_dictionary_obj : '+str(gs_space_dictionary_obj))
        cdcTypeRedeplyment(spaceType,diManagerHost, iidrHost)

