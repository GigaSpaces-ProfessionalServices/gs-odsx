import os
import csv
import io
import json
import requests
import subprocess
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_dataIntegration_nodes
from utils.odsx_keypress import userInputWrapper
from utils.ods_app_config import readValuefromAppConfig
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


def getDIServerHost():
    nodeList = config_get_dataIntegration_nodes()
    for node in nodeList:
        return os.getenv(node.ip)
    return ""


def exportPipeline(diManagerHost):
    try:
        nodeiidrList = config_get_dataIntegration_nodes()
        for nodes in nodeiidrList:
            iidrHost = os.getenv(nodes.ip)

        verboseHandle.printConsoleInfo("ip -> " + str(iidrHost))
        
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
                Fore.GREEN + str(idx)                      + Fore.RESET,
                Fore.GREEN + pipeline.get("name", "")      + Fore.RESET,
                Fore.GREEN + pipeline.get("sorName", "")   + Fore.RESET,
                Fore.GREEN + pipeline.get("spaceName", "") + Fore.RESET,
                Fore.GREEN + pipeline.get("status", "")    + Fore.RESET,
            ])


        printTabular(None, headers, dataTable)

        if not dataTable:
            verboseHandle.printConsoleWarning("No pipeline available.")
            return

        selection = userInputWrapper(f"Select pipeline number to export (1-{len(pipelines)}): ").strip()
        if not selection.isdigit() or not (1 <= int(selection) <= len(pipelines)):
            verboseHandle.printConsoleError("Invalid selection.")
            return
        selected_pipeline = pipelines[int(selection) - 1].get("name", "")
        verboseHandle.printConsoleInfo(f"Selected pipeline: {selected_pipeline}")
        logger.info(f"Selected pipeline: {selected_pipeline}")

        export_path = str(readValuefromAppConfig("app.dataengine.dihctl.pipelinefolderpath"))
        if not export_path.strip():
            verboseHandle.printConsoleError("Export path cannot be empty.")
            return
        if not os.path.exists(export_path):
            verboseHandle.printConsoleError(f"Export path not found: {export_path}")
            return

        export_file = os.path.join(export_path, f"{selected_pipeline}.yaml")
        export_cmd = f"{rootpath}dihctl -e dev export pipelines {selected_pipeline} -o {export_file}"
        verboseHandle.printConsoleInfo(f"Running: {export_cmd}")
        logger.info(f"Running: {export_cmd}")
        export_result = subprocess.run(export_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if export_result.returncode != 0:
            verboseHandle.printConsoleError(f"Export failed: {export_result.stderr}")
            return
        verboseHandle.printConsoleInfo(f"Export successful: {export_file}")
        logger.info(f"Export successful: {export_result.stdout}")

    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle CDC Export Pipeline')
    logger.info('Menu -> DataEngine -> Oracle CDC Export Pipeline')
    diManagerHost = getDIServerHost()
    if diManagerHost:
        exportPipeline(diManagerHost)
    else:
        verboseHandle.printConsoleError("No DI Manager host found.")
