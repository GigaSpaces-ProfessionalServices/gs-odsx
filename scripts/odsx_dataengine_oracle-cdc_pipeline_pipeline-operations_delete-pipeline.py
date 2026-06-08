import os
import csv
import io
import time
import requests
import subprocess

from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_dataIntegration_nodes
from utils.odsx_keypress import userInputWrapper
from utils.odsx_print_tabular_data import printTabular
from utils.ods_ssh import executeRemoteCommandAndGetOutputValuePython36

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


def isMDMInstalled(host, nodeType):
    if str(nodeType) == 'Zookeeper Witness':
        return Fore.GREEN + "NA" + Fore.RESET
    logger.info("isMDMInstalled" + str(host))
    commandToExecute = 'ls /etc/systemd/system/di-mdm.service'
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
    outputShFile = str(outputShFile).replace('\n', '')
    if len(str(outputShFile)) == 0:
        return Fore.RED + "NO" + Fore.RESET
    return Fore.GREEN + "Yes" + Fore.RESET


def getDIServerHost():
    nodeList = config_get_dataIntegration_nodes()
    for node in nodeList:
        return os.getenv(node.ip)
    return ""


def deletePipeline(diManagerHost):
    iidrHost = ""
    dIServers = config_get_dataIntegration_nodes("config/cluster.config")
    for node in dIServers:
        actualIp = os.getenv(node.ip)
        mdmStatus = isMDMInstalled(actualIp, str(node.type))
        if "Yes" in mdmStatus:
            iidrHost = actualIp
            break

    if not iidrHost:
        verboseHandle.printConsoleError("No DI node with MDM installed found.")
        return

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

    selection = userInputWrapper(f"Select pipeline(s) to delete (e.g. 1 or 1-3 or 1,4,5 or all): ").strip()
    selected_indices = set()
    if selection.lower() == "all":
        selected_indices = set(range(1, len(pipelines) + 1))
    else:
        for part in selection.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-", 1)
                selected_indices.update(range(int(start.strip()), int(end.strip()) + 1))
            elif part.isdigit():
                selected_indices.add(int(part))
    selected_indices = sorted(i for i in selected_indices if 1 <= i <= len(pipelines))
    if not selected_indices:
        verboseHandle.printConsoleError("Invalid selection.")
        return

    selected_pipelines = [pipelines[i - 1].get("name", "") for i in selected_indices]
    verboseHandle.printConsoleInfo(f"Selected pipelines: {selected_pipelines}")
    logger.info(f"Selected pipelines: {selected_pipelines}")

    pl_list_response = requests.get(f"http://{iidrHost}:6080/api/v1/pipeline/", headers={"accept": "*/*"})
    pl_list = pl_list_response.json()

    for selected_pipeline in selected_pipelines:
        pipeline_status = next((pl.get("status", "").strip().upper() for pl in pl_list if pl.get("name") == selected_pipeline), "")
        if pipeline_status == "ERROR":
            verboseHandle.printConsoleError(f"Pipeline Is in ERROR state Cannot perform {selected_pipeline} Delete pipeline operation")
            logger.error(f"Pipeline '{selected_pipeline}' is in ERROR state.")
            return

    confirm = userInputWrapper(
        Fore.YELLOW + f"This will stop and permanently delete {selected_pipelines} pipeline(s). Continue? (yes/no): " + Fore.RESET
    ).strip().lower()
    if confirm not in ("yes", "y"):
        verboseHandle.printConsoleWarning("Operation cancelled by user.")
        return

    for selected_pipeline in selected_pipelines:
        verboseHandle.printConsoleInfo(f"--- Processing pipeline: {selected_pipeline} ---")
        logger.info(f"--- Processing pipeline: {selected_pipeline} ---")

        # Stop pipeline
        pipeline_id = next((pl["pipelineId"] for pl in pl_list if pl.get("name") == selected_pipeline), None)
        if not pipeline_id:
            verboseHandle.printConsoleError(f"Pipeline ID not found for: {selected_pipeline}")
            continue
        if pipeline_status == "INACTIVE":
            verboseHandle.printConsoleInfo(f"Pipeline '{selected_pipeline}' is already INACTIVE. Skipping stop.")
            logger.info(f"Pipeline '{selected_pipeline}' is already INACTIVE. Skipping stop.")
        else:
            verboseHandle.printConsoleInfo(f"Stopping pipeline: {selected_pipeline} [{pipeline_id}]")
            logger.info(f"Stopping pipeline: {selected_pipeline} [{pipeline_id}]")
            stop_response = requests.post(
                f"http://{iidrHost}:6080/api/v1/pipeline/{pipeline_id}/stop",
                headers={"accept": "*/*", "Content-Type": "application/json"}
            )
            stop_status = stop_response.json().get("status", "unknown")
            verboseHandle.printConsoleInfo(f"Stop pipeline response status: {stop_status}")
            logger.info(f"Stop pipeline response status: {stop_status}")

        # Delete pipeline
        delete_cmd = f"{rootpath}dihctl -e dev delete pipelines {selected_pipeline}"
        verboseHandle.printConsoleInfo(f"Running: {delete_cmd}")
        logger.info(f"Running: {delete_cmd}")
        delete_result = subprocess.run(delete_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if delete_result.returncode != 0:
            verboseHandle.printConsoleError(f"Delete pipeline failed for '{selected_pipeline}': {delete_result.stderr}")
            continue
        verboseHandle.printConsoleInfo(f"Pipeline deleted successfully: {selected_pipeline}")
        logger.info(f"Pipeline deleted successfully: {delete_result.stdout}")



if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle CDC Delete Pipeline')
    logger.info('Menu -> DataEngine -> Oracle CDC Delete Pipeline')
    diManagerHost = getDIServerHost()
    if diManagerHost:
        deletePipeline(diManagerHost)
    else:
        verboseHandle.printConsoleError("No DI Manager host found.")
