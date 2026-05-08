import os
import json
import yaml
import requests
from colorama import Fore
import subprocess, csv, io
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_dataIntegration_nodes
from utils.odsx_keypress import userInputWrapper
from utils.odsx_print_tabular_data import printTabular
from utils.ods_app_config import readValuefromAppConfig, getYamlFilePathInsideFolder
from utils.odsx_objectmanagement_utilities import getPivotHost
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


def removeColumn(diManagerHost):
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

    selection = userInputWrapper(f"Select pipeline number to export (1-{len(pipelines)}): ").strip()
    if not selection.isdigit() or not (1 <= int(selection) <= len(pipelines)):
        verboseHandle.printConsoleError("Invalid selection.")
        return
    selected_pipeline = pipelines[int(selection) - 1].get("name", "")
    selected_status = pipelines[int(selection) - 1].get("status", "").strip().upper()
    verboseHandle.printConsoleInfo(f"Selected pipeline: {selected_pipeline}")
    logger.info(f"Selected pipeline: {selected_pipeline}")

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

    table_pipelines = exported_yaml["pipelines"][0]["tablePipelines"]

    tp_headers = [
        Fore.YELLOW + "Sr No."          + Fore.RESET,
        Fore.YELLOW + "Space Type Name" + Fore.RESET,
    ]
    tp_data = []
    for idx, tp in enumerate(table_pipelines, start=1):
        tp_data.append([
            Fore.GREEN + str(idx)                         + Fore.RESET,
            Fore.GREEN + str(tp.get("spaceTypeName", "")) + Fore.RESET,
        ])
    printTabular(None, tp_headers, tp_data)

    tp_selection = userInputWrapper(f"Select Space Type Name (1-{len(table_pipelines)}): ").strip()
    if not tp_selection.isdigit() or not (1 <= int(tp_selection) <= len(table_pipelines)):
        verboseHandle.printConsoleError("Invalid selection.")
        return
    selected_tp_idx = int(tp_selection) - 1
    space_type_name = table_pipelines[selected_tp_idx].get("spaceTypeName", "")
    verboseHandle.printConsoleInfo("Selected Space Type Name : " + space_type_name)
    logger.info("Selected Space Type Name : " + space_type_name)

    data = []
    counter = 1
    dataColumnsDict = {}
    dataTableColumnsDict = {}
    dataTableColumnsPropDict = {}
    dataTableColumnsPropIndexDict = {}

    objectMgmtHost = getPivotHost()
    try:
        response = requests.get('http://' + objectMgmtHost + ':7001/list',
                                headers={'Accept': 'application/json'})
        response.raise_for_status()
        if not response.text.strip():
            verboseHandle.printConsoleError(f"Empty response from object management API at {objectMgmtHost}:7001/list")
            return
        objectJson = json.loads(response.text)
    except requests.exceptions.ConnectionError:
        verboseHandle.printConsoleError(f"Cannot connect to object management API at {objectMgmtHost}:7001")
        return
    except requests.exceptions.HTTPError as e:
        verboseHandle.printConsoleError(f"HTTP error from object management API: {e}")
        return
    except json.JSONDecodeError as e:
        verboseHandle.printConsoleError(f"Invalid JSON from object management API: {e}")
        return
    tableListfilePath = str(getYamlFilePathInsideFolder(".object.config.ddlparser.ddlBatchFileName")).replace("//", "/")
    ddlAndPropertiesBasePath = os.path.dirname(tableListfilePath) + "/"
    spaceName = readValuefromAppConfig("app.objectmanagement.space")
    if spaceName is None or spaceName == "" or len(str(spaceName)) < 0:
        spaceName = readValuefromAppConfig("app.tieredstorage.pu.spacename")

    list_headers = [
        Fore.YELLOW + "Sr Num"      + Fore.RESET,
        Fore.YELLOW + "Space Name"  + Fore.RESET,
        Fore.YELLOW + "Object Name" + Fore.RESET,
    ]
    list_data = []
    for spaces in objectJson:
        for object in spaces["objects"]:
            dataArray = [
                Fore.GREEN + str(counter)               + Fore.RESET,
                Fore.GREEN + str(spaces["spacename"])   + Fore.RESET,
                Fore.GREEN + str(object["tablename"])   + Fore.RESET,
            ]
            if (str(object["tablename"]).strip() == str(space_type_name).strip()):
                dataColumnsDict.update({counter: object["columns"]})
                dataTableColumnsDict.update({counter: object["tablename"]})
                counter += 1
                list_data.append(dataArray)
    printTabular(None, list_headers, list_data)

    counter = 1
    headers = [
        Fore.YELLOW + "Sr Num"        + Fore.RESET,
        Fore.YELLOW + "Name"          + Fore.RESET,
        Fore.YELLOW + "Data Type"     + Fore.RESET,
        Fore.YELLOW + "Space Id"      + Fore.RESET,
        Fore.YELLOW + "Space Routing" + Fore.RESET,
        Fore.YELLOW + "Indexes"       + Fore.RESET,
        Fore.YELLOW + "Tier Criteria" + Fore.RESET,
    ]
    columns = dataColumnsDict.get(1)
    if columns is None:
        verboseHandle.printConsoleWarning(f"Space type '{space_type_name}' not found in object management registration.")
        return
    if columns is not None:
        for col in columns:
            dataArray = [
                Fore.GREEN + str(counter)                  + Fore.RESET,
                Fore.GREEN + str(col["columnname"])        + Fore.RESET,
                Fore.GREEN + str(col["columntype"])        + Fore.RESET,
                Fore.GREEN + str(col["spaceId"])           + Fore.RESET,
                Fore.GREEN + str(col["spaceRouting"])      + Fore.RESET,
                Fore.GREEN + str(col["spaceIndex"])        + Fore.RESET,
                Fore.GREEN + str(col["tierCriteria"])      + Fore.RESET,
            ]
            dataTableColumnsPropDict.update({counter: col["columnname"]})
            dataTableColumnsPropIndexDict.update({counter: col["spaceIndex"]})
            counter += 1
            data.append(dataArray)
        printTabular(None, headers, data)
        objectMgmtPropertyInput = str(userInputWrapper(Fore.YELLOW + "Choose property from list (e.g. 1 or 1-3 or 1,4,5) : " + Fore.RESET)).strip()
        selected_indices = set()
        for part in objectMgmtPropertyInput.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-", 1)
                selected_indices.update(range(int(start.strip()), int(end.strip()) + 1))
            else:
                selected_indices.add(int(part))
        selected_columns = [dataTableColumnsPropDict.get(i) for i in sorted(selected_indices) if dataTableColumnsPropDict.get(i) is not None]
        verboseHandle.printConsoleInfo("Selected columns : " + str(selected_columns))
        logger.info("Selected columns : " + str(selected_columns))


        confirm = userInputWrapper(Fore.YELLOW + "This will stop current running pipeline, Remove the Space type and reimport new pipeline after removing column. Continue? (yes/no): " + Fore.RESET).strip().lower()
        if confirm not in ("yes", "y"):
            verboseHandle.printConsoleWarning("Operation cancelled by user.")
            return


        existing_exclude = exported_yaml["pipelines"][0]["tablePipelines"][selected_tp_idx].get("excludeFields") or []
        updated_exclude = existing_exclude + [col for col in selected_columns if col not in existing_exclude]
        exported_yaml["pipelines"][0]["tablePipelines"][selected_tp_idx]["excludeFields"] = updated_exclude

        new_yaml_file = os.path.join(export_path, f"{selected_pipeline}_updated.yaml")
        with open(new_yaml_file, 'w') as f:
            yaml.dump(exported_yaml, f, default_flow_style=False, allow_unicode=True)
        verboseHandle.printConsoleInfo(f"Updated YAML saved to: {new_yaml_file}")
        logger.info(f"Updated YAML saved to: {new_yaml_file}")

        # Stop pipeline
        verboseHandle.printConsoleInfo(f"Fetching pipeline ID for: {selected_pipeline}")
        logger.info(f"Fetching pipeline ID for: {selected_pipeline}")
        pl_list_response = requests.get(f"http://{iidrHost}:6080/api/v1/pipeline/", headers={"accept": "*/*"})
        pl_list = pl_list_response.json()
        pipeline_id = next((pl["pipelineId"] for pl in pl_list if pl.get("name") == selected_pipeline), None)
        if not pipeline_id:
            verboseHandle.printConsoleError(f"Pipeline ID not found for: {selected_pipeline}")
            return
        if selected_status == "INACTIVE":
            verboseHandle.printConsoleInfo(f"Pipeline '{selected_pipeline}' is already INACTIVE. Skipping stop.")
            logger.info(f"Pipeline '{selected_pipeline}' is already INACTIVE. Skipping stop.")
        else:
            verboseHandle.printConsoleInfo(f"Stopping pipeline: {selected_pipeline} [{pipeline_id}]")
            logger.info(f"Stopping pipeline: {selected_pipeline} [{pipeline_id}]")
            stop_response = requests.post(f"http://{iidrHost}:6080/api/v1/pipeline/{pipeline_id}/stop", headers={"accept": "*/*", "Content-Type": "application/json"})
            stop_status = stop_response.json().get("status", "unknown")
            verboseHandle.printConsoleInfo(f"Stop pipeline response status: {stop_status}")
            logger.info(f"Stop pipeline response status: {stop_status}")


        # Delete pipeline
        delete_cmd = f"{rootpath}dihctl -e dev delete pipelines {selected_pipeline}"
        verboseHandle.printConsoleInfo(f"Running: {delete_cmd}")
        logger.info(f"Running: {delete_cmd}")
        delete_result = subprocess.run(delete_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if delete_result.returncode != 0:
            verboseHandle.printConsoleError(f"Delete pipeline failed: {delete_result.stderr}")
            return
        verboseHandle.printConsoleInfo(f"Pipeline deleted successfully: {selected_pipeline}")
        logger.info(f"Pipeline deleted successfully: {delete_result.stdout}")

        # Validate deletion by running show pipelines and checking the pipeline is absent (retry up to 5 times)
        max_retries = 5
        pipeline_deleted = False
        for attempt in range(1, max_retries + 1):
            verboseHandle.printConsoleInfo(f"Validating pipeline deletion for: {selected_pipeline} (attempt {attempt}/{max_retries})")
            logger.info(f"Validating pipeline deletion for: {selected_pipeline} (attempt {attempt}/{max_retries})")
            show_result = subprocess.run(
                [f'{rootpath}dihctl', '-e', 'dev', 'show', 'pipelines', '--format', 'csv'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
            )
            show_reader = csv.DictReader(io.StringIO(show_result.stdout))
            remaining_pipelines = [row.get("name", "") for row in show_reader]
            if selected_pipeline not in remaining_pipelines:
                pipeline_deleted = True
                verboseHandle.printConsoleInfo(f"Validation passed: pipeline '{selected_pipeline}' confirmed deleted.")
                logger.info(f"Validation passed: pipeline '{selected_pipeline}' not found in show pipelines output.")
                break
            verboseHandle.printConsoleError(f"Validation failed: pipeline '{selected_pipeline}' still exists after deletion. (attempt {attempt}/{max_retries})")
            logger.error(f"Validation failed: pipeline '{selected_pipeline}' still present. Attempt {attempt}/{max_retries}.")
        if not pipeline_deleted:
            verboseHandle.printConsoleError(f"Pipeline '{selected_pipeline}' still exists after {max_retries} attempts. Aborting.")
            logger.error(f"Pipeline '{selected_pipeline}' not deleted after {max_retries} validation attempts.")
            return

        # Unregister the space type
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

        # Create pipeline
        import_cmd = f"{rootpath}dihctl -e dev apply -f {new_yaml_file}"
        verboseHandle.printConsoleInfo(f"Running: {import_cmd}")
        logger.info(f"Running: {import_cmd}")
        import_result = subprocess.run(import_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if import_result.returncode != 0:
            verboseHandle.printConsoleError(f"Create pipeline failed: {import_result.stderr}")
            return
        verboseHandle.printConsoleInfo(f"Pipeline created successfully:\n{import_result.stdout}")
        logger.info(f"Pipeline created successfully: {import_result.stdout}")



if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle CDC Remove Column')
    logger.info('Menu -> DataEngine -> Oracle CDC Remove Column')
    diManagerHost = getDIServerHost()
    if diManagerHost:
        removeColumn(diManagerHost)
    else:
        verboseHandle.printConsoleError("No DI Manager host found.")
