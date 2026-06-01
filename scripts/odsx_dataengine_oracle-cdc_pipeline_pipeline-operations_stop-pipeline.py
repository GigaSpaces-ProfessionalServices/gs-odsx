import os
import csv
import io
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


def stopPipeline(diManagerHost):
    try:
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

        if not pipelines:
            verboseHandle.printConsoleWarning("No pipeline available.")
            return

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

        selection = userInputWrapper(f"Select pipeline(s) to stop (e.g. 1 or 1-3 or 1,4,5 or all): ").strip()
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

        # Fetch all pipeline IDs once
        pl_list_response = requests.get(f"http://{iidrHost}:6080/api/v1/pipeline/", headers={"accept": "*/*"})
        pl_list = pl_list_response.json()

        for idx in selected_indices:
            selected_pipeline = pipelines[idx - 1].get("name", "")
            selected_status   = pipelines[idx - 1].get("status", "").strip().upper()
            verboseHandle.printConsoleInfo(f"Selected pipeline: {selected_pipeline} (status: {selected_status})")
            logger.info(f"Selected pipeline: {selected_pipeline} (status: {selected_status})")

            if selected_status == "ERROR":
                verboseHandle.printConsoleError("Pipeline Is in ERROR state Cannot perform Stop pipeline operation")
                logger.error(f"Pipeline '{selected_pipeline}' is in ERROR state.")
                continue

            if selected_status != "RUNNING":
                verboseHandle.printConsoleWarning(f"Pipeline '{selected_pipeline}' is not running (status: {selected_status}). Skipping.")
                continue

            pipeline_id = next((pl["pipelineId"] for pl in pl_list if pl.get("name") == selected_pipeline), None)
            if not pipeline_id:
                verboseHandle.printConsoleError(f"Pipeline ID not found for: {selected_pipeline}")
                continue
            verboseHandle.printConsoleInfo(f"Pipeline ID: {pipeline_id}")
            logger.info(f"Pipeline ID: {pipeline_id}")

            verboseHandle.printConsoleInfo(f"Stopping pipeline: {selected_pipeline} [{pipeline_id}]")
            logger.info(f"Stopping pipeline: {selected_pipeline} [{pipeline_id}]")
            stop_response = requests.post(
                f"http://{iidrHost}:6080/api/v1/pipeline/{pipeline_id}/stop",
                headers={"accept": "*/*", "Content-Type": "application/json"}
            )
            stop_status = stop_response.json().get("status", "unknown")
            verboseHandle.printConsoleInfo(f"Stop pipeline '{selected_pipeline}' response status: {stop_status}")
            logger.info(f"Stop pipeline response status: {stop_status}")

    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle CDC Stop Pipeline')
    logger.info('Menu -> DataEngine -> Oracle CDC Stop Pipeline')
    diManagerHost = getDIServerHost()
    if diManagerHost:
        stopPipeline(diManagerHost)
    else:
        verboseHandle.printConsoleError("No DI Manager host found.")
