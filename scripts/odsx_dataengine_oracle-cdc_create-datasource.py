#!/usr/bin/env python3

import os
import json
import requests
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_dataIntegration_nodes, config_get_dataIntegrationiidr_nodes
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


def createDatasource():
    """Create datasource(s) via di-manager API.
    Loads exported datasources.json if available; each field falls back to app.config defaults
    when the exported value is missing or blank. username and password always use app.config
    values regardless of what is in the exported file."""
    logger.info("createDatasource()")
    try:
        diHost = ""
        for node in config_get_dataIntegration_nodes():
            diHost = os.getenv(node.ip)
            break

        defaultUsername = str(readValuefromAppConfig("app.dataengine.oracle-feeder.oracle.username"))
        defaultPassword = str(readValuefromAppConfig("app.dataengine.oracle-feeder.oracle.password"))
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

        exported_list = []
        export_path = str(readValuefromAppConfig("app.dataengine.dihctl.datasourcefolderpath"))
        if export_path.strip() and os.path.isdir(export_path):
            json_files = [f for f in os.listdir(export_path)
                          if os.path.isfile(os.path.join(export_path, f)) and f.endswith('.json')]
            if json_files:
                headers = [
                    Fore.YELLOW + "Sr No."    + Fore.RESET,
                    Fore.YELLOW + "File Name" + Fore.RESET,
                ]
                dataTable = []
                for idx, fname in enumerate(json_files, start=1):
                    dataTable.append([
                        Fore.GREEN + str(idx)  + Fore.RESET,
                        Fore.GREEN + fname     + Fore.RESET,
                    ])
                printTabular(None, headers, dataTable)

                selection = userInputWrapper(
                    Fore.YELLOW + f"Select datasource file number (1-{len(json_files)}): " + Fore.RESET
                ).strip()
                if selection.isdigit() and 1 <= int(selection) <= len(json_files):
                    export_file = os.path.join(export_path, json_files[int(selection) - 1])
                    verboseHandle.printConsoleInfo("Selected datasource file: " + export_file)
                    with open(export_file, 'r') as f:
                        exported_list = json.load(f) or []
                else:
                    verboseHandle.printConsoleError("Invalid selection; using default ORACLE config.")
            else:
                verboseHandle.printConsoleInfo("No JSON files found in: " + export_path)

        credential_fields = {"username", "password"}

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

        api_url = f"http://{diHost}:6080/api/v1/datasource/save-connection"
        for body in datasources_to_create:
            verboseHandle.printConsoleInfo("Creating datasource " + body["sorName"] + ", url=" + body["url"])
            logger.info("createDatasource POST " + api_url)
            response = requests.post(api_url, json=body, headers={"Content-Type": "application/json"})
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
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle CDC -> Create Datasource')
    logger.info('Menu -> DataEngine -> Oracle CDC -> Create Datasource')
    createDatasource()
