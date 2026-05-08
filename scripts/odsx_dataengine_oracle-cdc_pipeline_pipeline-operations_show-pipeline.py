import os
import csv
import io
import requests
import subprocess
import yaml

from colorama import Fore, init
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_dataIntegration_nodes
from utils.odsx_keypress import userInputWrapper
from utils.odsx_objectmanagement_utilities import getPivotHost
from utils.odsx_print_tabular_data import printTabularGrid, printTabular
from utils.ods_ssh import executeRemoteCommandAndGetOutputValuePython36


verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

def isMDMInstalled(host,nodeType):
    if(str(nodeType)=='Zookeeper Witness'):
        return Fore.GREEN+"NA"+Fore.RESET
    logger.info("isMDMInstalled"+str(host))
    isInstalled = "Yes"
    commandToExecute='ls /etc/systemd/system/di-mdm.service'
    logger.info("commandToExecute :"+str(commandToExecute))
    outputShFile = executeRemoteCommandAndGetOutputValuePython36(host, 'root', commandToExecute)
    outputShFile=str(outputShFile).replace('\n','')
    logger.info("outputShFile :"+str(outputShFile))
    if len(str(outputShFile))==0:
        return Fore.RED+"NO"+Fore.RESET
    return Fore.GREEN+"Yes"+Fore.RESET

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


def showPipelines():
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

        selection = userInputWrapper(f"Select pipeline number to view tables (1-{len(pipelines)}): ").strip()
        if not selection.isdigit() or not (1 <= int(selection) <= len(pipelines)):
            verboseHandle.printConsoleError("Invalid selection.")
            return

        selected_pipeline = pipelines[int(selection) - 1]
        selected_name = selected_pipeline.get("name", "")
        verboseHandle.printConsoleInfo(f"Selected pipeline: {selected_name}")
        logger.info(f"Selected pipeline: {selected_name}")

        # Fetch pipeline ID
        pl_list_response = requests.get(f"http://{iidrHost}:6080/api/v1/pipeline/", headers={"accept": "*/*"})
        pl_list = pl_list_response.json()
        pipeline_id = next((pl["pipelineId"] for pl in pl_list if pl.get("name") == selected_name), None)
        if not pipeline_id:
            verboseHandle.printConsoleError(f"Pipeline ID not found for: {selected_name}")
            return
        verboseHandle.printConsoleInfo(f"Pipeline ID: {pipeline_id}")
        logger.info(f"Pipeline ID: {pipeline_id}")

        # Fetch tables for selected pipeline
        tables_response = requests.get(
            f"http://{iidrHost}:6080/api/v1/pipeline/{pipeline_id}/tablepipeline",
            headers={"accept": "*/*"}
        )
        tables_response.raise_for_status()
        tables = tables_response.json()

        if not tables:
            verboseHandle.printConsoleWarning(f"No tables found for pipeline '{selected_name}'.")
            return

        verboseHandle.printConsoleInfo(f"Tables for pipeline '{selected_name}':")
        tbl_headers = [
            Fore.YELLOW + "Sr No."            + Fore.RESET,
            Fore.YELLOW + "Space Type Name"   + Fore.RESET,
            Fore.YELLOW + "Source Schema"     + Fore.RESET,
            Fore.YELLOW + "Source Table"      + Fore.RESET,
            Fore.YELLOW + "Exclude Fields"    + Fore.RESET,
            Fore.YELLOW + "Status"            + Fore.RESET,
            ]
        tbl_data = []
        for idx, tbl in enumerate(tables, start=1):
            exclude_fields = tbl.get("excludeFields") or []
            tbl_data.append([
                Fore.GREEN + str(idx)                                                        + Fore.RESET,
                Fore.GREEN + str(tbl.get("spaceTypeName", ""))                               + Fore.RESET,
                Fore.GREEN + str(tbl.get("sourceSchema", ""))                                + Fore.RESET,
                Fore.GREEN + str(tbl.get("sourceTable", tbl.get("sourceTables", "")))        + Fore.RESET,
                Fore.GREEN + (", ".join(exclude_fields) if exclude_fields else "-")          + Fore.RESET,
                Fore.GREEN + str(tbl.get("status", ""))                                      + Fore.RESET,
                ])
        printTabular(None, tbl_headers, tbl_data)

        # Select a table to view object type columns
        tbl_selection = userInputWrapper(f"Select table number to view object type (1-{len(tables)}): ").strip()
        if not tbl_selection.isdigit() or not (1 <= int(tbl_selection) <= len(tables)):
            verboseHandle.printConsoleError("Invalid selection.")
            return

        selected_table = tables[int(tbl_selection) - 1]
        space_type_name = str(selected_table.get("spaceTypeName", "")).strip()
        verboseHandle.printConsoleInfo(f"Selected space type: {space_type_name}")
        logger.info(f"Selected space type: {space_type_name}")

        # Fetch object type columns from object management API
        objectMgmtHost = getPivotHost()
        verboseHandle.printConsoleInfo(f"Fetching object type details from {objectMgmtHost}:7001")
        logger.info(f"Fetching object type details from {objectMgmtHost}:7001")

        try:
            list_response = requests.get(
                f"http://{objectMgmtHost}:7001/list",
                headers={"Accept": "application/json"}
            )
            list_response.raise_for_status()
            object_list = list_response.json()
        except requests.exceptions.ConnectionError:
            verboseHandle.printConsoleError(f"Cannot connect to object management API at {objectMgmtHost}:7001")
            return
        except requests.exceptions.HTTPError as e:
            verboseHandle.printConsoleError(f"HTTP error from object management API: {e}")
            return

        columns = None
        for space in object_list:
            for obj in space.get("objects", []):
                if str(obj.get("tablename", "")).strip() == space_type_name:
                    columns = obj.get("columns", [])
                    break
            if columns is not None:
                break

        if columns is None:
            verboseHandle.printConsoleWarning(f"Space type '{space_type_name}' not found in object management registration.")
            return

        if not columns:
            verboseHandle.printConsoleWarning(f"No columns found for space type '{space_type_name}'.")
            return

        verboseHandle.printConsoleInfo(f"Object type columns for '{space_type_name}':")
        col_headers = [
            Fore.YELLOW + "Sr No."        + Fore.RESET,
            Fore.YELLOW + "Column Name"   + Fore.RESET,
            Fore.YELLOW + "Data Type"     + Fore.RESET,
            Fore.YELLOW + "Space ID"      + Fore.RESET,
            Fore.YELLOW + "Space Routing" + Fore.RESET,
            Fore.YELLOW + "Space Index"   + Fore.RESET,
            Fore.YELLOW + "Tier Criteria" + Fore.RESET,
            ]
        col_data = []
        for idx, col in enumerate(columns, start=1):
            col_data.append([
                Fore.GREEN + str(idx)                             + Fore.RESET,
                Fore.GREEN + str(col.get("columnname", ""))       + Fore.RESET,
                Fore.GREEN + str(col.get("columntype", ""))       + Fore.RESET,
                Fore.GREEN + str(col.get("spaceId", ""))          + Fore.RESET,
                Fore.GREEN + str(col.get("spaceRouting", ""))     + Fore.RESET,
                Fore.GREEN + str(col.get("spaceIndex", ""))       + Fore.RESET,
                Fore.GREEN + str(col.get("tierCriteria", ""))     + Fore.RESET,
                ])
        printTabular(None, col_headers, col_data)

    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle CDC Show Pipeline')
    logger.info('Menu -> DataEngine -> Oracle CDC Show Pipeline')
    showPipelines()
