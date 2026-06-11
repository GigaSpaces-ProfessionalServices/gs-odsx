#!/usr/bin/env python3

import os
import csv
import io
import subprocess
import requests
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_dataIntegration_nodes
from utils.ods_app_config import readValuefromAppConfig
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


def compareIndexPipelineMenu():
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
        login_result = subprocess.run(login_cmd, shell=True, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, universal_newlines=True)
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
            verboseHandle.printConsoleWarning("No pipelines available.")
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
                Fore.GREEN + str(idx)                               + Fore.RESET,
                Fore.GREEN + pipeline.get("name", "").strip()       + Fore.RESET,
                Fore.GREEN + pipeline.get("sorName", "").strip()    + Fore.RESET,
                Fore.GREEN + pipeline.get("spaceName", "").strip()  + Fore.RESET,
                Fore.GREEN + pipeline.get("status", "").strip()     + Fore.RESET,
            ])
        printTabular(None, headers, dataTable)

        selection = userInputWrapper(f"Select pipeline number to compare index (1-{len(pipelines)}): ").strip()
        if not selection.isdigit() or not (1 <= int(selection) <= len(pipelines)):
            verboseHandle.printConsoleError("Invalid selection.")
            return

        selected = pipelines[int(selection) - 1]
        selected_name = selected.get("name", "").strip()
        selected_status = selected.get("status", "").strip().upper()
        verboseHandle.printConsoleInfo(f"Selected pipeline: {selected_name}")
        logger.info(f"Selected pipeline: {selected_name}")

        if selected_status == "ERROR":
            verboseHandle.printConsoleError("Pipeline is in ERROR state. Cannot perform compare index operation.")
            logger.error(f"Pipeline '{selected_name}' is in ERROR state.")
            return

        # Resolve pipeline ID
        pl_response = requests.get(
            f"http://{iidrHost}:6080/api/v1/pipeline/",
            headers={"accept": "*/*"},
            proxies={"http": None, "https": None}
        )
        pl_list = pl_response.json()
        pipeline_id = next((pl["pipelineId"] for pl in pl_list if pl.get("name") == selected_name), None)
        if not pipeline_id:
            verboseHandle.printConsoleError(f"Pipeline ID not found for: {selected_name}")
            return

        username = str(readValuefromAppConfig("app.cdc.datasource.username") or "").strip()
        password = str(readValuefromAppConfig("app.cdc.datasource.password") or "").strip()

        api_url = f"http://{iidrHost}:6080/api/v2/pipeline/{pipeline_id}/compare-indexes"
        payload = {
            "sourceUsername": username,
            "sourcePassword": password,
        }
        verboseHandle.printConsoleInfo(f"Calling compare-indexes API for pipeline: {selected_name}")
        logger.info(f"compareIndexPipeline POST {api_url} pipeline={selected_name}")

        resp = requests.post(
            api_url,
            json=payload,
            headers={"accept": "*/*", "Content-Type": "application/json"},
            proxies={"http": None, "https": None},
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()

        comparison_results = data.get("comparisonResults", [])

        if not comparison_results:
            verboseHandle.printConsoleWarning("No comparison results returned.")
            return

        result_headers = [
            Fore.YELLOW + "Sr No."             + Fore.RESET,
            Fore.YELLOW + "Source Table"       + Fore.RESET,
            Fore.YELLOW + "Destination Table"  + Fore.RESET,
            Fore.YELLOW + "Table Match"        + Fore.RESET,
        ]
        result_data = []
        all_match = True
        for idx, entry in enumerate(comparison_results, start=1):
            meta         = entry.get("meta", {})
            source_table = str(meta.get("sourceTable", ""))
            dest_table   = str(meta.get("destinationTable", ""))
            table_match  = entry.get("tableMatch", False)
            if not table_match:
                all_match = False
            match_color = Fore.GREEN if table_match else Fore.RED
            result_data.append([
                Fore.GREEN  + str(idx)         + Fore.RESET,
                Fore.GREEN  + source_table     + Fore.RESET,
                Fore.GREEN  + dest_table       + Fore.RESET,
                match_color + str(table_match) + Fore.RESET,
            ])

        printTabular(None, result_headers, result_data)
        all_match_color = Fore.GREEN if all_match else Fore.RED
        verboseHandle.printConsoleInfo(
            f"All Tables Match: {all_match_color}{all_match}{Fore.RESET}")
        logger.info(f"compareIndexPipeline allTablesMatch={all_match} results={len(comparison_results)}")

    except requests.exceptions.HTTPError as he:
        verboseHandle.printConsoleError(f"API error: {he}")
        logger.error(f"compareIndexPipeline HTTP error: {he}")
    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle CDC -> Pipeline -> Pipeline Operations -> Compare Index Pipeline')
    logger.info('Menu -> DataEngine -> Oracle CDC -> Pipeline -> Pipeline Operations -> Compare Index Pipeline')
    compareIndexPipelineMenu()
