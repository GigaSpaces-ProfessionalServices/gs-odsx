#!/usr/bin/env python3

import os
import json
import requests
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_dataIntegration_nodes
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


def exportDatasourcesBeforeRemove(diHost, export_path):
    """Export selected datasource config(s) to JSON."""
    logger.info("exportDatasourcesBeforeRemove()")
    try:
        os.makedirs(export_path, exist_ok=True)
        url = f"http://{diHost}:6080/api/v1/datasource/"
        verboseHandle.printConsoleInfo("Fetching datasources from: " + url)
        response = requests.get(url, headers={"Content-Type": "application/json"},
                                proxies={"http": None, "https": None})
        if response.status_code != 200:
            verboseHandle.printConsoleError("Failed to list datasources: " + str(response.status_code) + " " + response.text)
            return
        datasources = response.json()
        if not datasources:
            verboseHandle.printConsoleWarning("No datasources found.")
            return

        headers = [
            Fore.YELLOW + "Sr No."       + Fore.RESET,
            Fore.YELLOW + "SOR Name"     + Fore.RESET,
            Fore.YELLOW + "DB Provider"  + Fore.RESET,
            Fore.YELLOW + "URL"          + Fore.RESET,
        ]
        dataTable = []
        for idx, ds in enumerate(datasources, start=1):
            dataTable.append([
                Fore.GREEN + str(idx)                        + Fore.RESET,
                Fore.GREEN + str(ds.get("sorName", ""))      + Fore.RESET,
                Fore.GREEN + str(ds.get("dbProvider", ""))   + Fore.RESET,
                Fore.GREEN + str(ds.get("url", ""))          + Fore.RESET,
            ])
        printTabular(None, headers, dataTable)

        selection = userInputWrapper(
            Fore.YELLOW + f"Select datasource(s) to export (e.g. 1 or 1-{len(datasources)} or 1,2): " + Fore.RESET
        ).strip()

        selected_indices = set()
        for part in selection.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-", 1)
                selected_indices.update(range(int(start.strip()), int(end.strip()) + 1))
            else:
                selected_indices.add(int(part))
        selected_indices = sorted(i for i in selected_indices if 1 <= i <= len(datasources))
        if not selected_indices:
            verboseHandle.printConsoleError("Invalid selection.")
            return

        selected_datasources = [datasources[i - 1] for i in selected_indices]
        verboseHandle.printConsoleInfo(f"Selected datasource(s): {[ds.get('sorName', '') for ds in selected_datasources]}")
        logger.info(f"Selected datasource(s): {selected_datasources}")

        for ds in selected_datasources:
            sor_name = ds.get("sorName", "datasource").strip()
            export_file = os.path.join(export_path, f"{sor_name}.json")
            with open(export_file, 'w') as f:
                json.dump(ds, f, indent=2)
            verboseHandle.printConsoleInfo(f"Datasource '{sor_name}' exported to: {export_file}")
            logger.info(f"exportDatasourcesBeforeRemove() completed: {export_file}")
    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle CDC Export Datasource')
    logger.info('Menu -> DataEngine -> Oracle CDC Export Datasource')

    diHost = ""
    for node in config_get_dataIntegration_nodes():
        diHost = os.getenv(node.ip)
        break

    if not diHost:
        verboseHandle.printConsoleError("No DI host found.")
    else:
        export_path = str(readValuefromAppConfig("app.dataengine.dihctl.datasourcefolderpath"))
        if not export_path.strip():
            verboseHandle.printConsoleError("Export path cannot be empty (app.dataengine.dihctl.datasourcefolderpath).")
        else:
            exportDatasourcesBeforeRemove(diHost, export_path)
