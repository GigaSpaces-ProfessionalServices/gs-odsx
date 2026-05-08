#!/usr/bin/env python3

import os
import json
import requests
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_dataIntegration_nodes, config_get_dataIntegrationiidr_nodes
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


def createDatasource():
    """Create datasource(s) via di-manager API after DI install.
    Loads exported datasources.json if available; each field falls back to app.config defaults
    when the exported value is missing or blank. username and password always use app.config
    values regardless of what is in the exported file."""
    logger.info("createDatasource()")
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

        defaultUsername = str(readValuefromAppConfig("app.cdc.datasource.username"))
        defaultPassword = str(readValuefromAppConfig("app.cdc.datasource.password"))
        defaultIidrHost = ""
        for node in config_get_dataIntegrationiidr_nodes():
            defaultIidrHost = os.getenv(node.ip)
            break

        defaults = {
            "sorName":        "ORACLE",
            "dbProvider":     "ORACLE",
            "url":            f"iidr://{defaultIidrHost}:11001",
            "username":       defaultUsername,
            "password":       defaultPassword,
            "additionalInfo": "",
            "offlineMode":    False
        }

        # File selection from datasource folder
        exported_list = []
        export_path = str(readValuefromAppConfig("app.dataengine.dihctl.datasourcefolderpath"))
        if not export_path.strip():
            verboseHandle.printConsoleError("File path cannot be empty.")
            return
        if not os.path.exists(export_path):
            verboseHandle.printConsoleError(f"Path not found: {export_path}")
            return

        files = [f for f in os.listdir(export_path) if os.path.isfile(os.path.join(export_path, f))]
        if not files:
            verboseHandle.printConsoleError(f"No files found in: {export_path}")
            return

        file_headers = [
            Fore.YELLOW + "Sr No."    + Fore.RESET,
            Fore.YELLOW + "File Name" + Fore.RESET,
        ]
        fileTable = []
        for idx, fname in enumerate(files, start=1):
            fileTable.append([
                Fore.GREEN + str(idx) + Fore.RESET,
                Fore.GREEN + fname    + Fore.RESET,
            ])
        printTabular(None, file_headers, fileTable)

        file_selection = userInputWrapper(f"Select file number (1-{len(files)}): ").strip()
        if not file_selection.isdigit() or not (1 <= int(file_selection) <= len(files)):
            verboseHandle.printConsoleError("Invalid selection.")
            return
        selected_file = files[int(file_selection) - 1]
        verboseHandle.printConsoleInfo(f"Selected file: {selected_file}")
        logger.info(f"Selected file: {selected_file}")

        export_file = os.path.join(export_path, selected_file)
        if os.path.isfile(export_file):
            with open(export_file, 'r') as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                exported_list = [loaded]
            elif isinstance(loaded, list):
                exported_list = loaded
            else:
                exported_list = []
            if exported_list:
                verboseHandle.printConsoleInfo("Loaded datasource file: " + export_file)

        # username and password always come from app.config regardless of exported file
        credential_fields = {"username", "password"}

        # Build the list to create: exported entries with per-field fallback, or just the default
        if exported_list:
            datasources_to_create = []
            for ds in exported_list:
                entry = {}
                for field, default_val in defaults.items():
                    if field in credential_fields:
                        entry[field] = default_val
                    else:
                        exported_val = ds.get(field)
                        if exported_val is not None and str(exported_val).strip() != "":
                            entry[field] = exported_val
                        else:
                            entry[field] = default_val
                            verboseHandle.printConsoleInfo(
                                "Field '" + field + "' missing/blank in export for datasource '" +
                                str(ds.get("sorName", "?")) + "'; using default: " + str(default_val))
                datasources_to_create.append(entry)
        else:
            verboseHandle.printConsoleInfo("No exported datasource file found; using default ORACLE config.")
            datasources_to_create = [defaults]

        api_url = f"http://{iidrHost}:6080/api/v1/datasource/save-connection"
        for body in datasources_to_create:
            verboseHandle.printConsoleInfo("Creating datasource " + body["sorName"] + ", url=" + body["url"])
            logger.info("createDatasource POST " + api_url)
            response = requests.post(api_url, json=body, headers={"Content-Type": "application/json"},
                                     proxies={"http": None, "https": None})
            if response.status_code in (200, 201):
                verboseHandle.printConsoleInfo("Datasource " + body["sorName"] + " created successfully.")
            else:
                verboseHandle.printConsoleError(
                    "Datasource creation failed for " + body["sorName"] + ": " +
                    str(response.status_code) + " " + response.text)
            logger.info("createDatasource response: " + str(response.status_code) + " " + str(response.text))
    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle CDC Import Datasource')
    logger.info('Menu -> DataEngine -> Oracle CDC Import Datasource')
    createDatasource()
