import os
import requests
import json
import yaml
import subprocess, csv, io

from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_dataIntegration_nodes
from utils.odsx_keypress import userInputWrapper
from utils.odsx_print_tabular_data import printTabular
from utils.ods_app_config import readValuefromAppConfig, getYamlFilePathInsideFolder

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


def addNewColumn(diManagerHost):
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

    # confirm = userInputWrapper(Fore.YELLOW + "This will stop current running pipeline and reimport new pipeline after adding column. Continue? (yes/no): " + Fore.RESET).strip().lower()
    # if confirm not in ("yes", "y"):
    #     verboseHandle.printConsoleWarning("Operation cancelled by user.")
    #     return

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

    with open(export_file, 'r') as f:
        exported_yaml = yaml.safe_load(f)

    existing_exclude = exported_yaml["pipelines"][0]["tablePipelines"][0].get("excludeFields") or []

    ef_headers = [
        Fore.YELLOW + "Sr No."       + Fore.RESET,
        Fore.YELLOW + "Exclude Field" + Fore.RESET,
    ]
    ef_data = []
    for idx, field in enumerate(existing_exclude, start=1):
        ef_data.append([
            Fore.GREEN + str(idx)    + Fore.RESET,
            Fore.GREEN + str(field)  + Fore.RESET,
        ])
    printTabular(None, ef_headers, ef_data)

    ef_input = str(userInputWrapper(Fore.YELLOW + "Choose fields to remove from excludeFields (e.g. 1 or 1-3 or 1,4,5) : " + Fore.RESET)).strip()
    selected_indices = set()
    for part in ef_input.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            selected_indices.update(range(int(start.strip()), int(end.strip()) + 1))
        else:
            selected_indices.add(int(part))

    fields_to_remove = [existing_exclude[i - 1] for i in sorted(selected_indices) if 1 <= i <= len(existing_exclude)]
    verboseHandle.printConsoleInfo("Fields to remove : " + str(fields_to_remove))
    logger.info("Fields to remove : " + str(fields_to_remove))

    updated_exclude = [f for f in existing_exclude if f not in fields_to_remove]
    exported_yaml["pipelines"][0]["tablePipelines"][0]["excludeFields"] = updated_exclude

    new_yaml_file = os.path.join(export_path, f"{selected_pipeline}_updated.yaml")
    with open(new_yaml_file, 'w') as f:
        yaml.dump(exported_yaml, f, default_flow_style=False, allow_unicode=True)
    verboseHandle.printConsoleInfo(f"Updated YAML saved to: {new_yaml_file}")
    logger.info(f"Updated YAML saved to: {new_yaml_file}")

    # delete_cmd = f"{rootpath}dihctl -e dev delete pipelines {selected_pipeline} --delete-pipelines"
    # verboseHandle.printConsoleInfo(f"Running: {delete_cmd}")
    # logger.info(f"Running: {delete_cmd}")
    # delete_result = subprocess.run(delete_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    # if delete_result.returncode != 0:
    #     verboseHandle.printConsoleError(f"Delete pipeline failed: {delete_result.stderr}")
    #     return
    # verboseHandle.printConsoleInfo(f"Pipeline deleted successfully: {selected_pipeline}")
    # logger.info(f"Pipeline deleted successfully: {delete_result.stdout}")
    #
    # import_cmd = f"{rootpath}dihctl -e dev apply -s -f {new_yaml_file}"
    # verboseHandle.printConsoleInfo(f"Running: {import_cmd}")
    # logger.info(f"Running: {import_cmd}")
    # import_result = subprocess.run(import_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    # if import_result.returncode != 0:
    #     verboseHandle.printConsoleError(f"Create pipeline failed: {import_result.stderr}")
    #     return
    # verboseHandle.printConsoleInfo(f"Pipeline created successfully:\n{import_result.stdout}")
    # logger.info(f"Pipeline created successfully: {import_result.stdout}")


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle CDC Add New Column')
    logger.info('Menu -> DataEngine -> Oracle CDC Add New Column')
    diManagerHost = getDIServerHost()
    if diManagerHost:
        addNewColumn(diManagerHost)
    else:
        verboseHandle.printConsoleError("No DI Manager host found.")
