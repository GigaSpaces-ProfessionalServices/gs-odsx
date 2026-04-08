import os
import subprocess
import yaml
from scripts.logManager import LogManager
import subprocess, csv, io
from colorama import Fore, init
from utils.odsx_print_tabular_data import printTabularGrid, printTabular
from utils.ods_cluster_config import config_get_dataIntegration_nodes, config_get_manager_node, \
    config_get_dataIntegrationiidr_nodes

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


def handleException(e):
    verboseHandle.printConsoleInfo("handleException()")

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


def getDIHost(filePath='config/cluster.config'):
    with open(filePath, 'r') as f:
        content = yaml.safe_load(f)
    return content['servers']['dataIntegration']['host1']



def showPipelines():
    try:
        nodeiidrList = config_get_dataIntegration_nodes()
        for nodes in nodeiidrList:
            iidrHost=os.getenv(nodes.ip)

        verboseHandle.printConsoleInfo("ip -> "  + str(iidrHost))
        
        rootpath = "/dbagiga/utils/dihctl/"
        login_cmd = f"{rootpath}dihctl -e dev login --noauth http://{iidrHost}:7080"
        verboseHandle.printConsoleInfo(f"Running: {login_cmd}")
        logger.info(f"Running: {login_cmd}")
        login_result = subprocess.run(login_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if login_result.returncode != 0:
            verboseHandle.printConsoleError(f"Login failed: {login_result.stderr}")
            return

        result = subprocess.run(
            [f'{rootpath}dihctl', '-e', 'dev', 'show', 'pipelines', '--format', 'csv'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )
        reader = csv.DictReader(io.StringIO(result.stdout))
        pipelines = list(reader)

        headers = [
            Fore.YELLOW + "Sr No."        + Fore.RESET,
            Fore.YELLOW + "Pipeline Name" + Fore.RESET,
            Fore.YELLOW + "SOR Name"      + Fore.RESET,
            Fore.YELLOW + "Space Name"    + Fore.RESET,
            Fore.YELLOW + "Status"        + Fore.RESET,
            ]

        dataTable = []
        for idx, pipeline in enumerate(pipelines, start=1):
            dataTable.append([
                Fore.GREEN + str(idx)                        + Fore.RESET,
                Fore.GREEN + pipeline.get("name", "")        + Fore.RESET,
                Fore.GREEN + pipeline.get("sorName", "")     + Fore.RESET,
                Fore.GREEN + pipeline.get("spaceName", "")   + Fore.RESET,
                Fore.GREEN + pipeline.get("status", "")      + Fore.RESET,
                ])

        printTabular(None, headers, dataTable)

    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle CDC Show Pipeline')
    logger.info('Menu -> DataEngine -> Oracle CDC Show Pipeline')
    showPipelines()
