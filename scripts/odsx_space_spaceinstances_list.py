#!/usr/bin/env python3
import os, requests,json
import signal

from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_space_hosts, config_get_manager_node
from scripts.odsx_tieredstorage_undeploy import getManagerHost
from utils.odsx_print_tabular_data import printTabular
from utils.ods_cleanup import signal_handler


verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

class bcolors:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    RESET = '\033[0m'  # RESET COLOR


class host_dictionary_obj(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

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

def listDeployed(managerHost,spaceName):
    optionForFilter = str(input(
        Fore.YELLOW + "press [1] if you want to Filter by Mode. \n[Enter] For all  \nPress [99] for exit.: " + Fore.RESET))
        # Fore.YELLOW + "press [1] if you want to Filter by Mode.\npress [2] if you want to Filter by Host.\n[Enter] For all  \nPress [99] for exit.: " + Fore.RESET))
    if optionForFilter != '99':
        if optionForFilter == '1':
            logger.info("Filter by mode")
            try:
                logger.info("managerHost :" + str(managerHost))
                response = requests.get(
                    "http://" + str(managerHost) + ":8090/v2/spaces/" + str(spaceName) + "/instances")
                logger.info("response status of host :" + str(managerHost) + " status :" + str(
                    response.status_code) + " Content: " + str(response.content))
                jsonArray = json.loads(response.text)

                verboseHandle.printConsoleWarning("Resources on cluster:")
                headers = [Fore.YELLOW + "Sr No." + Fore.RESET,
                           Fore.YELLOW + "Mode" + Fore.RESET]
                dataModeTable = []
                c = 0
                modeDict = {}
                modeArray = set()
                for item in jsonArray:
                    if str(item) not in modeArray:
                        modeArray.add(item["mode"])
                for data in modeArray:
                    c = c + 1
                    modeDict.update({c: data})
                    dataArray = [Fore.GREEN + str(c) + Fore.RESET,
                                 Fore.GREEN + data + Fore.RESET]
                    dataModeTable.append(dataArray)
                printTabular(None, headers, dataModeTable)

                modeMenu = str(input("Enter your mode srno.: "))

                if len(modeDict) >= int(modeMenu):
                    modeName= modeDict.get(int(modeMenu))
                    modeJsonArray = [x for x in jsonArray if x['mode'] == str(modeName)]

                logger.info("Enter your srno to remove container:" + str(modeMenu))

                headers = [Fore.YELLOW + "Sr No." + Fore.RESET,
                           Fore.YELLOW + "Instances" + Fore.RESET,
                           Fore.YELLOW + "Mode" + Fore.RESET,
                           Fore.YELLOW + "HostId" + Fore.RESET,
                           Fore.YELLOW + "Container Ids" + Fore.RESET
                           # Fore.YELLOW+"Suspend Type "+Fore.RESET
                           ]
                gs_space_dictionary_obj = host_dictionary_obj()
                logger.info("gs_space_dictionary_obj : " + str(gs_space_dictionary_obj))
                counter = 0
                dataTable = []
                spaceDict = {}
                for data in modeJsonArray:
                    counter = counter + 1
                    dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                                 Fore.GREEN + data["id"] + Fore.RESET,
                                 Fore.GREEN + data["mode"] + Fore.RESET,
                                 Fore.GREEN + str(data["hostId"]) + Fore.RESET,
                                 Fore.GREEN + str(data["containerId"]) + Fore.RESET
                                 ]
                    spaceDict.update({counter: data})
                    dataTable.append(dataArray)
                printTabular(None, headers, dataTable)
            except Exception as e:
                handleException(e)
            return spaceDict

        elif len(optionForFilter) == 0:
            try:
                logger.info("managerHost :" + str(managerHost))
                response = requests.get(
                    "http://" + str(managerHost) + ":8090/v2/spaces/" + str(spaceName) + "/instances")
                logger.info("response status of host :" + str(managerHost) + " status :" + str(
                    response.status_code) + " Content: " + str(response.content))
                jsonArray = json.loads(response.text)
                verboseHandle.printConsoleWarning("Resources on cluster:")
                headers = [Fore.YELLOW + "Sr No." + Fore.RESET,
                           Fore.YELLOW + "Instances" + Fore.RESET,
                           Fore.YELLOW + "Mode" + Fore.RESET,
                           Fore.YELLOW + "HostId" + Fore.RESET,
                           Fore.YELLOW + "Container Ids" + Fore.RESET
                           # Fore.YELLOW+"Suspend Type "+Fore.RESET
                           ]
                gs_space_dictionary_obj = host_dictionary_obj()
                logger.info("gs_space_dictionary_obj : " + str(gs_space_dictionary_obj))
                counter = 0
                dataTable = []
                spaceDict = {}
                for data in jsonArray:
                    counter = counter + 1
                    dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
                                 Fore.GREEN + data["id"] + Fore.RESET,
                                 Fore.GREEN + data["mode"] + Fore.RESET,
                                 Fore.GREEN + str(data["hostId"]) + Fore.RESET,
                                 Fore.GREEN + str(data["containerId"]) + Fore.RESET
                                 ]
                    spaceDict.update({counter: data})
                    dataTable.append(dataArray)
                printTabular(None, headers, dataTable)
            except Exception as e:
                handleException(e)
            return spaceDict
        # elif optionForFilter == '2':
        #     logger.info("Filter by host")
        #     try:
        #         logger.info("managerHost :" + str(managerHost))
        #         response = requests.get(
        #             "http://" + str(managerHost) + ":8090/v2/spaces/" + str(spaceName) + "/instances")
        #         logger.info("response status of host :" + str(managerHost) + " status :" + str(
        #             response.status_code) + " Content: " + str(response.content))
        #         jsonArray = json.loads(response.text)
        #
        #         verboseHandle.printConsoleWarning("Resources on cluster:")
        #         headers = [Fore.YELLOW + "Sr No." + Fore.RESET,
        #                    Fore.YELLOW + "Host" + Fore.RESET]
        #         dataModeTable = []
        #         c = 0
        #         modeDict = {}
        #         spaceServers = config_get_space_hosts()
        #
        #         for data in spaceServers:
        #             host = os.getenv(data.ip)
        #             c = c + 1
        #             modeDict.update({c: data})
        #             dataArray = [Fore.GREEN + str(c) + Fore.RESET,
        #                          Fore.GREEN + host + Fore.RESET]
        #             dataModeTable.append(dataArray)
        #         printTabular(None, headers, dataModeTable)
        #
        #         modeMenu = str(input("Enter your host srno.: "))
        #
        #         if len(modeDict) >= int(modeMenu):
        #             modeName= modeDict.get(int(modeMenu))
        #             modeJsonArray = [x for x in jsonArray if x['hostId'] == str(modeName)]
        #
        #         logger.info("Enter your srno to remove container:" + str(modeMenu))
        #
        #         headers = [Fore.YELLOW + "Sr No." + Fore.RESET,
        #                    Fore.YELLOW + "Instances" + Fore.RESET,
        #                    Fore.YELLOW + "Mode" + Fore.RESET,
        #                    Fore.YELLOW + "Host" + Fore.RESET,
        #                    Fore.YELLOW + "Containers" + Fore.RESET
        #                    # Fore.YELLOW+"Suspend Type "+Fore.RESET
        #                    ]
        #         gs_space_dictionary_obj = host_dictionary_obj()
        #         logger.info("gs_space_dictionary_obj : " + str(gs_space_dictionary_obj))
        #         counter = 0
        #         dataTable = []
        #         spaceDict = {}
        #         for data in modeJsonArray:
        #             counter = counter + 1
        #             dataArray = [Fore.GREEN + str(counter) + Fore.RESET,
        #                          Fore.GREEN + data["id"] + Fore.RESET,
        #                          Fore.GREEN + data["mode"] + Fore.RESET,
        #                          Fore.GREEN + str(data["hostId"]) + Fore.RESET,
        #                          Fore.GREEN + str(data["containerId"]) + Fore.RESET
        #                          ]
        #             spaceDict.update({counter: data})
        #             dataTable.append(dataArray)
        #         printTabular(None, headers, dataTable)
        #     except Exception as e:
        #         handleException(e)
        #     return spaceDict


def listOfSpacename(managerHost):
    try:
        logger.info("managerHost :"+str(managerHost))
        response = requests.get("http://"+str(managerHost)+":8090/v2/spaces/")
        logger.info("response status of host :"+str(managerHost)+" status :"+str(response.status_code)+" Content: "+str(response.content))
        jsonArray = json.loads(response.text)
        verboseHandle.printConsoleWarning("Instance of space:")
        headers = [Fore.YELLOW+"Sr No."+Fore.RESET,
                   Fore.YELLOW+"Name"+Fore.RESET
                   ]
        gs_space_dictionary_obj = host_dictionary_obj()
        logger.info("gs_space_dictionary_obj : "+str(gs_space_dictionary_obj))
        counter=0
        dataTable=[]
        # spaceDict = {}
        for data in jsonArray:
            # spaceDict.update({counter: data})
            dataArray = [Fore.GREEN+str(counter+1)+Fore.RESET,
                         Fore.GREEN+data["name"]+Fore.RESET
                         ]
            gs_space_dictionary_obj.add(str(counter+1),str(data["name"]))
            counter=counter+1
            dataTable.append(dataArray)
        printTabular(None,headers,dataTable)
        return gs_space_dictionary_obj
    except Exception as e:
        handleException(e)
    # return spaceDict

def instancelistFromHosts(managerNodes):
    optionMainMenu = ''
    signal.signal(signal.SIGINT, signal_handler)
    managerNodes = config_get_manager_node()
    try:
        if(len(str(managerNodes))>0):
            exitMenu = True
            while exitMenu:
                logger.info("managerNodes: main"+str(managerNodes))
                managerHost = getManagerHost(managerNodes)
                logger.info("managerHost : "+str(managerHost))

                if(len(str(managerHost))>0):
                    logger.info("Manager Host :"+str(managerHost))
                    spacename = listOfSpacename(managerHost)

                    optionMainMenu = str(input(Fore.YELLOW+"press [1] Enter your space srno. for instance list. \nPress [99] for exit.: "+Fore.RESET))
                    logger.info("Enter your space srno. for instance list:" + str(optionMainMenu))

                    if(str(optionMainMenu) == '1'):
                             if len(spacename) >= int(optionMainMenu):
                                  host = spacename.get(optionMainMenu)
                                  listDeployed(managerHost,host)
                    elif(str(optionMainMenu) == '99'):
                            exitMenu = False

            else:
                logger.info("Please check manager server status.")
                verboseHandle.printConsoleInfo("Please check manager server status.")
        else:
            logger.info("No Manager configuration found please check.")
            verboseHandle.printConsoleInfo("No Manager configuration found please check.")
    except Exception as e:
        verboseHandle.printConsoleError("Error in odsx_space_spaceinstances_list.py : "+str(e))
        logger.error("Exception in odsx_space_spaceinstances_list.py"+str(e))
        handleException(e)

    # if len(spacename) >= int(optionMainMenu):
    #     host = spacename.get(optionMainMenu)
    #     listDeployed(managerHost,host)

if __name__ == '__main__':
    verboseHandle.printConsoleWarning("Menu -> Space -> Space -> Instances -> List")
    managerNodes = config_get_manager_node()
    instancelistFromHosts(managerNodes)