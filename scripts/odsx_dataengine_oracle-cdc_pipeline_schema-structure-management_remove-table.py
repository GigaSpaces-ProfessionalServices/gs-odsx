import os
import yaml
import requests
import subprocess, csv, io

from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_dataIntegration_nodes
from utils.odsx_keypress import userInputWrapper
from utils.odsx_print_tabular_data import printTabular
from utils.ods_app_config import readValuefromAppConfig
from utils.odsx_objectmanagement_utilities import getPivotHost

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


def removeTable(diManagerHost):
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

    selection = userInputWrapper(f"Select pipeline number to remove table from (1-{len(pipelines)}): ").strip()
    if not selection.isdigit() or not (1 <= int(selection) <= len(pipelines)):
        verboseHandle.printConsoleError("Invalid selection.")
        return
    selected_pipeline = pipelines[int(selection) - 1].get("name", "")
    selected_status = pipelines[int(selection) - 1].get("status", "").strip().upper()
    verboseHandle.printConsoleInfo(f"Selected pipeline: {selected_pipeline}")
    logger.info(f"Selected pipeline: {selected_pipeline}")

    # Fetch pipeline ID from v2 API
    verboseHandle.printConsoleInfo(f"Fetching pipeline ID for: {selected_pipeline}")
    logger.info(f"Fetching pipeline ID for: {selected_pipeline}")
    try:
        pl_list_response = requests.get(f"http://{iidrHost}:6080/api/v2/pipeline/", headers={"accept": "*/*"})
        pl_list_response.raise_for_status()
        pl_raw = pl_list_response.json()
        if isinstance(pl_raw, list):
            pl_list = pl_raw
        elif isinstance(pl_raw, dict):
            pl_list = (
                pl_raw.get("data")
                or pl_raw.get("pipelines")
                or pl_raw.get("items")
                or []
            )
        else:
            pl_list = []
        pipeline_id = next(
            (pl.get("pipelineId") or pl.get("id") for pl in pl_list if isinstance(pl, dict) and pl.get("name") == selected_pipeline),
            None
        )
        if not pipeline_id:
            verboseHandle.printConsoleError(f"Pipeline ID not found for: {selected_pipeline}")
            return
        verboseHandle.printConsoleInfo(f"Pipeline ID: {pipeline_id}")
        logger.info(f"Pipeline ID: {pipeline_id}")
    except Exception as e:
        handleException(e)
        return

    # Fetch table pipelines from port 6081 and show as selection table
    verboseHandle.printConsoleInfo(f"Fetching table pipelines for pipeline ID: {pipeline_id}")
    logger.info(f"Fetching table pipelines for pipeline ID: {pipeline_id}")
    try:
        tp_api_response = requests.get(
            f"http://{iidrHost}:6081/api/v1/pipeline/{pipeline_id}/tablepipelines",
            headers={"accept": "*/*"}
        )
        tp_api_response.raise_for_status()
        api_table_pipelines = tp_api_response.json()
        logger.info(f"Table pipelines API response: {api_table_pipelines}")
    except Exception as e:
        handleException(e)
        return

    if not api_table_pipelines:
        verboseHandle.printConsoleWarning(f"No table pipelines found for pipeline '{selected_pipeline}'.")
        return

    if len(api_table_pipelines) <= 1:
        verboseHandle.printConsoleError("Pipeline has only one table. Cannot remove the last table.")
        return

    tp_headers = [
        Fore.YELLOW + "Sr No."            + Fore.RESET,
        Fore.YELLOW + "Space Type Name"   + Fore.RESET,
        Fore.YELLOW + "Table Pipeline ID" + Fore.RESET,
    ]
    tp_data = []
    for idx, tp in enumerate(api_table_pipelines, start=1):
        tp_id   = tp.get("tablePipelineId") or tp.get("id") or tp.get("pipelineId", "")
        tp_name = tp.get("spaceTypeName") or tp.get("name") or tp.get("sourceTable", "")
        tp_data.append([
            Fore.GREEN + str(idx)     + Fore.RESET,
            Fore.GREEN + str(tp_name) + Fore.RESET,
            Fore.GREEN + str(tp_id)   + Fore.RESET,
        ])
    printTabular(None, tp_headers, tp_data)

    tp_selection = userInputWrapper(f"Select table to remove (1-{len(api_table_pipelines)}): ").strip()
    if not tp_selection.isdigit() or not (1 <= int(tp_selection) <= len(api_table_pipelines)):
        verboseHandle.printConsoleError("Invalid selection.")
        return
    selected_tp_idx = int(tp_selection) - 1
    selected_tp     = api_table_pipelines[selected_tp_idx]
    selected_tp_id  = selected_tp.get("tablePipelineId") or selected_tp.get("id") or selected_tp.get("pipelineId", "")
    space_type_name = selected_tp.get("spaceTypeName") or selected_tp.get("name") or selected_tp.get("sourceTable", "")
    verboseHandle.printConsoleInfo(f"Selected table to remove: {space_type_name}")
    verboseHandle.printConsoleInfo(f"Selected table pipeline ID: {selected_tp_id}")
    logger.info(f"Selected table to remove: {space_type_name}, Table Pipeline ID: {selected_tp_id}")

    confirm = userInputWrapper(
        Fore.YELLOW + f"This will stop the pipeline, remove table '{space_type_name}', unregister its space type, and reimport the pipeline. Continue? (yes/no): " + Fore.RESET
    ).strip().lower()
    if confirm not in ("yes", "y"):
        verboseHandle.printConsoleWarning("Operation cancelled by user.")
        return

    objectMgmtHost = getPivotHost()
    # Stop pipeline
    verboseHandle.printConsoleInfo(f"Fetching pipeline ID for: {selected_pipeline}")
    logger.info(f"Fetching pipeline ID for: {selected_pipeline}")
    pl_list_response = requests.get(f"http://{iidrHost}:6080/api/v1/pipeline/", headers={"accept": "*/*"})
    pl_list = pl_list_response.json()
    pipeline_id = next((pl["pipelineId"] for pl in pl_list if pl.get("name") == selected_pipeline), None)
    if not pipeline_id:
        verboseHandle.printConsoleError(f"Pipeline ID not found for: {selected_pipeline}")
        return
    verboseHandle.printConsoleInfo(f"Stopping pipeline: {selected_pipeline} [{pipeline_id}]")
    logger.info(f"Stopping pipeline: {selected_pipeline} [{pipeline_id}]")
    stop_response = requests.post(
        f"http://{iidrHost}:6080/api/v1/pipeline/{pipeline_id}/stop",
        headers={"accept": "*/*", "Content-Type": "application/json"}
    )
    stop_status = stop_response.json().get("status", "unknown")
    verboseHandle.printConsoleInfo(f"Stop pipeline response status: {stop_status}")
    logger.info(f"Stop pipeline response status: {stop_status}")

    # Unregister space type for removed table
    verboseHandle.printConsoleInfo(f"Unregistering space type: {space_type_name}")
    logger.info(f"Unregistering space type: {space_type_name}")
    try:
        unreg_response = requests.post(
            f"http://{objectMgmtHost}:7001/unregistertype",
            data={"type": space_type_name},
            headers={"Accept": "application/json"}
        )
        if unreg_response.text.strip() == "success":
            verboseHandle.printConsoleInfo(f"Space type '{space_type_name}' unregistered successfully.")
            logger.info(f"Space type '{space_type_name}' unregistered successfully.")
        else:
            verboseHandle.printConsoleError(f"Failed to unregister space type '{space_type_name}': {unreg_response.text}")
            logger.error(f"Unregister space type response: {unreg_response.text}")
            return
    except requests.exceptions.ConnectionError:
        verboseHandle.printConsoleError(f"Cannot connect to object management API at {objectMgmtHost}:7001 for unregister.")
        return

    # Delete table pipeline
    verboseHandle.printConsoleInfo(f"Deleting table pipeline: {space_type_name} [{selected_tp_id}] from pipeline [{pipeline_id}]")
    logger.info(f"Deleting table pipeline: {space_type_name} [{selected_tp_id}] from pipeline [{pipeline_id}]")
    try:
        delete_tp_response = requests.delete(
            f"http://{iidrHost}:6080/api/v2/pipeline/{pipeline_id}/tablepipeline/{selected_tp_id}",
            headers={"accept": "*/*"}
        )
        delete_tp_response.raise_for_status()
        verboseHandle.printConsoleInfo(f"Table pipeline '{space_type_name}' deleted successfully.")
        logger.info(f"Delete table pipeline response: {delete_tp_response.status_code} {delete_tp_response.text}")
    except Exception as e:
        handleException(e)
        return

    # Start the pipeline
    verboseHandle.printConsoleInfo(f"Starting pipeline: {selected_pipeline} [{pipeline_id}]")
    logger.info(f"Starting pipeline: {selected_pipeline} [{pipeline_id}]")
    start_payload = {
        "reconciliationPolicy": "NONE",
        "kafkaRunParameters": {
            "CDC": {
                "kafkaOffsetStrategy": "COMMITTED",
                "kafkaOffset": -1
            }
        }
    }
    try:
        start_response = requests.post(
            f"http://{iidrHost}:6080/api/v1/pipeline/{pipeline_id}/start",
            headers={"accept": "*/*", "Content-Type": "application/json"},
            json=start_payload
        )
        if start_response.status_code in (200, 201, 202, 204):
            verboseHandle.printConsoleInfo(f"Pipeline '{selected_pipeline}' started successfully.")
            logger.info(f"Start pipeline response [{start_response.status_code}]: {start_response.text}")
        else:
            verboseHandle.printConsoleError(f"Failed to start pipeline '{selected_pipeline}'. Status: {start_response.status_code} Response: {start_response.text}")
            logger.error(f"Start pipeline failed [{start_response.status_code}]: {start_response.text}")
    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle CDC Remove Table')
    logger.info('Menu -> DataEngine -> Oracle CDC Remove Table')
    diManagerHost = getDIServerHost()
    if diManagerHost:
        removeTable(diManagerHost)
    else:
        verboseHandle.printConsoleError("No DI Manager host found.")
