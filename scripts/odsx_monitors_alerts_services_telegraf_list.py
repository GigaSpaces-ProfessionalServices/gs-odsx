import os

from colorama import Fore

from scripts.logManager import LogManager
from scripts.spinner import Spinner
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_dataIntegration_nodes, config_get_nb_list
from utils.ods_cluster_config import config_get_manager_node, config_get_space_hosts
from utils.ods_ssh import executeRemoteCommandAndGetOutputPython36, executeRemoteCommandAndGetOutputValuePython36
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

class host_dictionary(dict):
    # __init__ function
    def __init__(self):
        self = dict()

    # Function to add key:value
    def add(self, key, value):
        self[key] = value

def getStatusOfTelegraf(node):
    user="root"
    cmd = "systemctl status telegraf"
    with Spinner():
        output = executeRemoteCommandAndGetOutputPython36(node, user, cmd)
        logger.info("output1 : "+str(output))
        if(output!=0):
            logger.info(" Service :"+str(cmd)+" not started."+str(node))
        return output

def isInstalledATelegraf(node):
    logger.info("isTelegrafInstalledNot"+node+" : ")
    isInstalled = "Yes"
    commandToExecute='ls /usr/lib/systemd/system/telegraf.service'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(node, 'root', commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    if len(str(outputShFile))==0:
        return "No"
    return isInstalled

def listAllTelegrafServers():
    logger.info("Manager server list :")
    headers = [Fore.YELLOW+"Sr No"+Fore.RESET,
               Fore.YELLOW+"Type of host"+Fore.RESET,
               Fore.YELLOW+"IP"+Fore.RESET,
               Fore.YELLOW+"Installed"+Fore.RESET,
               Fore.YELLOW+"Status"+Fore.RESET]
    data=[]
    managerNodes = config_get_manager_node()
    count = 0
    spaceDict = {}
    for node in managerNodes:
        count = count+1
        host = os.getenv(node.ip)
        spaceDict.update({count: host})
        status = getStatusOfTelegraf(host)
        install = isInstalledATelegraf(host)
        logger.info("install : "+str(install))
        dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                   Fore.GREEN+"Manager"+Fore.RESET,
                   Fore.GREEN+os.getenv(node.ip)+Fore.RESET,
                   Fore.GREEN+install+Fore.RESET if(install=='Yes') else Fore.RED+install+Fore.RESET,
                   Fore.GREEN+"ON"+Fore.RESET if(status==0) else Fore.RED+"OFF"+Fore.RESET]
        data.append(dataArray)
    logger.info("Space server list.")
    spaceServers = config_get_space_hosts()
    host_dict_obj = host_dictionary()
    for server in spaceServers:
        cmd = 'systemctl is-active gs.service'
        user='root'
        output = executeRemoteCommandAndGetOutputPython36(os.getenv(server.ip), user, cmd)
        logger.info("executeRemoteCommandAndGetOutputPython36 : output:"+str(output))
        host_dict_obj.add(os.getenv(server.ip),str(output))
    logger.info("host_dict_obj :"+str(host_dict_obj))

    for server in spaceServers:
        count = count+1
        host = os.getenv(server.ip)
        spaceDict.update({count: host})
        logger.info(host)
        status = getStatusOfTelegraf(host)
        logger.info("status"+str(status))
        install = isInstalledATelegraf(host)
        logger.info("install : "+str(install))
        dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                   Fore.GREEN+"Space"+Fore.RESET,
                   Fore.GREEN+os.getenv(server.ip)+Fore.RESET,
                   Fore.GREEN+install+Fore.RESET if(install=='Yes') else Fore.RED+install+Fore.RESET,
                   Fore.GREEN+"ON"+Fore.RESET if(status==0) else Fore.RED+"OFF"+Fore.RESET]
        data.append(dataArray)
    logger.info("NB servers list")
    nbServers = config_get_nb_list()
    for server in nbServers:
        host = os.getenv(server.ip)
        if(str(server.role).__contains__('applicative') or str(server.role).__contains__('management')):
            count = count+1
            spaceDict.update({count: host})
            status = getStatusOfTelegraf(host)
            install = isInstalledATelegraf(host)
            logger.info("install : "+str(install))
            dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                       Fore.GREEN+"Northbound "+server.role+Fore.RESET,
                   Fore.GREEN+os.getenv(server.ip)+Fore.RESET,
                   Fore.GREEN+install+Fore.RESET if(install=='Yes') else Fore.RED+install+Fore.RESET,
                   Fore.GREEN+"ON"+Fore.RESET if(status==0) else Fore.RED+"OFF"+Fore.RESET]

            data.append(dataArray)
#
    logger.info("pivot server list.")
    host = os.getenv("pivot1")
    status = getStatusOfTelegraf(host)
    count=count+1
    spaceDict.update({count: host})
    install = isInstalledATelegraf(host)
    logger.info("install : "+str(install))
    dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                   Fore.GREEN+"Pivot"+Fore.RESET,
                   Fore.GREEN+os.getenv("pivot1")+Fore.RESET,
                   Fore.GREEN+install+Fore.RESET if(install=='Yes') else Fore.RED+install+Fore.RESET,
                   Fore.GREEN+"ON"+Fore.RESET if(status==0) else Fore.RED+"OFF"+Fore.RESET]
    data.append(dataArray)
#
    env = str(readValuefromAppConfig("app.setup.env"))
    if env != "dr":
        logger.info("DI servers list")
        dIServers = config_get_dataIntegration_nodes()
        counter=1
        for node in dIServers:
            count=count+1
            host = os.getenv(node.ip)
            spaceDict.update({count: host})
            host_dict_obj.add(str(counter),str(node.ip))
            status = getStatusOfTelegraf(host)
            installStatus = isInstalledATelegraf(host)
            dataArray=[Fore.GREEN+str(count)+Fore.RESET,
                       Fore.GREEN+str(node.role)+" "+str(node.type)+Fore.RESET,
                       Fore.GREEN+os.getenv(node.name)+Fore.RESET,
                       Fore.GREEN+installStatus+Fore.RESET if(installStatus=='Yes') else Fore.RED+installStatus+Fore.RESET,
                       Fore.GREEN+"ON"+Fore.RESET if(status==0) else Fore.RED+"OFF"+Fore.RESET]
            data.append(dataArray)
            counter=counter+1
    printTabular(None,headers,data)
    return spaceDict

if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> Monitors ->  Alerts -> Service -> Telegraf -> List')
    try:
        listAllTelegrafServers()
    except Exception as e:
        handleException(e)
