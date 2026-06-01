#!/usr/bin/env python3

import os
import requests
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_dataIntegration_nodes
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_ssh import executeRemoteCommandAndGetOutputValuePython36
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


def deleteDatasource(iidrHost):
    logger.info("deleteDatasource()")
    try:
        list_url = f"http://{iidrHost}:6080/api/v1/datasource/"
        verboseHandle.printConsoleInfo("Fetching datasources from: " + list_url)
        response = requests.get(list_url, headers={"Content-Type": "application/json"},
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
                Fore.GREEN + str(idx)                       + Fore.RESET,
                Fore.GREEN + str(ds.get("sorName", ""))     + Fore.RESET,
                Fore.GREEN + str(ds.get("dbProvider", ""))  + Fore.RESET,
                Fore.GREEN + str(ds.get("url", ""))         + Fore.RESET,
            ])
        printTabular(None, headers, dataTable)

        selection = userInputWrapper(
            Fore.YELLOW + f"Select datasource(s) to delete (e.g. 1 or 1-{len(datasources)} or 1,2): " + Fore.RESET
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
        selected_names = [ds.get("sorName", "") for ds in selected_datasources]
        verboseHandle.printConsoleInfo(f"Selected datasource(s): {selected_names}")
        logger.info(f"Selected datasource(s): {selected_datasources}")

        confirm = userInputWrapper(
            Fore.YELLOW + f"This will permanently delete {selected_names} datasource(s). Continue? (yes/no): " + Fore.RESET
        ).strip().lower()
        if confirm not in ("yes", "y"):
            verboseHandle.printConsoleInfo("Delete cancelled.")
            return

        for ds in selected_datasources:
            sor_name = ds.get("sorName", "").strip()
            if not sor_name:
                continue
            sub_port = str(readValuefromAppConfig("app.iidr.iidrSubscriptionMangerPort")).strip() or "6082"
            del_url = f"http://{iidrHost}:{sub_port}/api/v1/{sor_name}/subscriptions/GS_4700"
            verboseHandle.printConsoleInfo(f"Deleting datasource '{sor_name}': {del_url}")
            logger.info(f"DELETE {del_url}")
            del_response = requests.delete(del_url, headers={"accept": "*/*"},
                                           proxies={"http": None, "https": None})
            if del_response.status_code in (200, 201, 204):
                verboseHandle.printConsoleInfo(f"Datasource '{sor_name}' deleted successfully.")
            else:
                verboseHandle.printConsoleError(
                    f"Delete failed for '{sor_name}': " + str(del_response.status_code) + " " + del_response.text)
            logger.info(f"deleteDatasource response: {del_response.status_code} {del_response.text}")

    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle CDC Delete Datasource')
    logger.info('Menu -> DataEngine -> Oracle CDC Delete Datasource')

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
    else:
        deleteDatasource(iidrHost)
