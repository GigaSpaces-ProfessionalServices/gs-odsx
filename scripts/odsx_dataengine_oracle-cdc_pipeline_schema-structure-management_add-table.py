import os
import csv
import io
import json
import time
import yaml
import requests
import subprocess

from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_dataIntegration_nodes
from utils.odsx_keypress import userInputWrapper
from utils.odsx_print_tabular_data import printTabular
from utils.ods_app_config import readValuefromAppConfig
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


def addTable(diManagerHost):
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

        if not dataTable:
            verboseHandle.printConsoleWarning("No pipeline available.")
            return

        selection = userInputWrapper(f"Select pipeline number to add table (1-{len(pipelines)}): ").strip()
        if not selection.isdigit() or not (1 <= int(selection) <= len(pipelines)):
            verboseHandle.printConsoleError("Invalid selection.")
            return
        selected_pipeline  = pipelines[int(selection) - 1].get("name", "").strip()
        selected_status    = pipelines[int(selection) - 1].get("status", "").strip().upper()
        selected_sor_name  = pipelines[int(selection) - 1].get("sorName", "").strip()
        selected_space_name = pipelines[int(selection) - 1].get("spaceName", "").strip()
        verboseHandle.printConsoleInfo(f"Selected pipeline: {selected_pipeline} (status: {selected_status}, sor: {selected_sor_name})")
        logger.info(f"Selected pipeline: {selected_pipeline} (status: {selected_status})")
        if selected_status == "ERROR":
            verboseHandle.printConsoleError("Pipeline Is in ERROR state Cannot perform Add Table operation")
            logger.error(f"Pipeline '{selected_pipeline}' is in ERROR state.")
            return

        # Fetch pipeline ID from REST API
        verboseHandle.printConsoleInfo(f"Fetching pipeline ID for: {selected_pipeline}")
        logger.info(f"Fetching pipeline ID for: {selected_pipeline}")
        pl_list_response = requests.get(f"http://{iidrHost}:6080/api/v1/pipeline/", headers={"accept": "*/*"})
        pl_list_json = pl_list_response.json()
        pl_list = pl_list_json.get("data", pl_list_json) if isinstance(pl_list_json, dict) else pl_list_json
        pipeline_id = next((pl["pipelineId"] for pl in pl_list if pl.get("name") == selected_pipeline), None)
        if not pipeline_id:
            verboseHandle.printConsoleError(f"Pipeline ID not found for: {selected_pipeline}")
            return
        verboseHandle.printConsoleInfo(f"Pipeline ID: {pipeline_id}")
        logger.info(f"Pipeline ID: {pipeline_id}")

        # Fetch Oracle schemas for the selected datasource and let user choose
        di1_host = str(os.getenv("di1"))
        schemas_url = f"http://{di1_host}:6080/api/v2/datasource/{selected_sor_name}/schemas"
        verboseHandle.printConsoleInfo(f"Fetching schemas from: {schemas_url}")
        logger.info(f"Fetching schemas URL: {schemas_url}")
        schemas_response = requests.get(schemas_url, headers={"accept": "*/*"})
        schemas_response.raise_for_status()
        schemas_json = schemas_response.json()
        schemas_raw = schemas_json.get("data", schemas_json) if isinstance(schemas_json, dict) else schemas_json

        schemas = []
        for entry in schemas_raw:
            if isinstance(entry, str):
                schemas.append(entry.strip())
            else:
                name = str(entry.get("schemaName") or entry.get("name") or entry.get("schema", "")).strip()
                if name:
                    schemas.append(name)

        if not schemas:
            verboseHandle.printConsoleError(f"No schemas found for datasource '{selected_sor_name}'.")
            return

        schema_headers = [
            Fore.YELLOW + "Sr No."      + Fore.RESET,
            Fore.YELLOW + "Schema Name" + Fore.RESET,
        ]
        schema_data = []
        for idx, s in enumerate(schemas, start=1):
            schema_data.append([
                Fore.GREEN + str(idx) + Fore.RESET,
                Fore.GREEN + s        + Fore.RESET,
            ])
        printTabular(None, schema_headers, schema_data)

        schema_selection = userInputWrapper(f"Select schema number (1-{len(schemas)}): ").strip()
        if not schema_selection.isdigit() or not (1 <= int(schema_selection) <= len(schemas)):
            verboseHandle.printConsoleError("Invalid selection.")
            return
        oracle_schema = schemas[int(schema_selection) - 1]
        verboseHandle.printConsoleInfo(f"Selected Oracle schema: {oracle_schema}")
        logger.info(f"Selected Oracle schema: {oracle_schema}")

        # Fetch tables already attached to the selected pipeline
        tablepipeline_url = f"http://{di1_host}:6080/api/v2/pipeline/{pipeline_id}/tablepipeline"
        verboseHandle.printConsoleInfo(f"Fetching pipeline tables from: {tablepipeline_url}")
        logger.info(f"Fetching pipeline tables URL: {tablepipeline_url}")
        tp_response = requests.get(tablepipeline_url, headers={"accept": "*/*"})
        tp_response.raise_for_status()
        tp_json = tp_response.json()
        tp_raw = tp_json.get("data", tp_json) if isinstance(tp_json, dict) else tp_json
        attached_tables_upper = set()
        for tp in tp_raw:
            if isinstance(tp, str):
                attached_tables_upper.add(tp.strip().upper())
            else:
                t = str(tp.get("tableName") or tp.get("sourceTable") or tp.get("table", "")).strip().upper()
                s = str(tp.get("schemaName") or tp.get("sourceSchema") or tp.get("schema", "")).strip().upper()
                if t:
                    attached_tables_upper.add(t)
                if s and t:
                    attached_tables_upper.add(f"{s}.{t}")

        # List available tables from the datasource
        schema_tables_url = f"http://{di1_host}:6080/api/v2/datasource/{selected_sor_name}/tables?schemaName={oracle_schema}"
        verboseHandle.printConsoleInfo(f"Fetching available tables from datasource '{selected_sor_name}' schema '{oracle_schema}'")
        verboseHandle.printConsoleInfo(f"URL: {schema_tables_url}")
        logger.info(f"Fetching available tables URL: {schema_tables_url}")
        ds_tables_response = requests.get(schema_tables_url, headers={"accept": "*/*"})
        ds_tables_response.raise_for_status()
        ds_tables_json = ds_tables_response.json()
        ds_tables_raw = ds_tables_json.get("data", ds_tables_json) if isinstance(ds_tables_json, dict) else ds_tables_json

        tables = []
        for entry in ds_tables_raw:
            if isinstance(entry, str):
                s_schema = oracle_schema
                s_table  = entry.strip()
            else:
                s_schema = str(entry.get("schemaName") or entry.get("sourceSchema") or entry.get("schema", oracle_schema)).strip()
                s_table  = str(entry.get("tableName") or entry.get("sourceTable") or entry.get("table", "")).strip()
            if not s_table:
                continue
            if s_table.upper() in attached_tables_upper or f"{s_schema}.{s_table}".upper() in attached_tables_upper:
                continue
            tables.append({"sourceSchema": s_schema, "sourceTable": s_table})

        if not tables:
            verboseHandle.printConsoleWarning(f"No available tables found in datasource '{selected_sor_name}' (all may already be attached to the pipeline).")
            return

        tbl_headers = [
            Fore.YELLOW + "Sr No."        + Fore.RESET,
            Fore.YELLOW + "Source Schema" + Fore.RESET,
            Fore.YELLOW + "Source Table"  + Fore.RESET,
        ]
        tbl_data = []
        for idx, tbl in enumerate(tables, start=1):
            tbl_data.append([
                Fore.GREEN + str(idx)              + Fore.RESET,
                Fore.GREEN + tbl["sourceSchema"]   + Fore.RESET,
                Fore.GREEN + tbl["sourceTable"]    + Fore.RESET,
            ])
        printTabular(None, tbl_headers, tbl_data)

        tbl_selection = userInputWrapper(f"Select table number(s) to add to pipeline '{selected_pipeline}' (e.g. 1 or 1-3 or 1,4,5): ").strip()
        selected_tbl_indices = set()
        for part in tbl_selection.split(","):
            part = part.strip()
            if "-" in part:
                s, e = part.split("-", 1)
                if s.strip().isdigit() and e.strip().isdigit():
                    selected_tbl_indices.update(range(int(s.strip()), int(e.strip()) + 1))
            elif part.isdigit():
                selected_tbl_indices.add(int(part))
        selected_tbl_indices = sorted(i for i in selected_tbl_indices if 1 <= i <= len(tables))
        if not selected_tbl_indices:
            verboseHandle.printConsoleError("Invalid selection.")
            return

        selected_tables     = [tables[i - 1] for i in selected_tbl_indices]
        source_schema       = selected_tables[0]["sourceSchema"]
        source_tables_list  = [tbl["sourceTable"] for tbl in selected_tables]
        selected_table_names = [f"{tbl['sourceSchema']}.{tbl['sourceTable']}" for tbl in selected_tables]
        verboseHandle.printConsoleInfo(f"Selected tables: {selected_table_names}")
        logger.info(f"Selected tables: {selected_table_names}")

        # Ask if user wants to modify table names (space type names)
        modify_names_confirm = userInputWrapper(
            Fore.YELLOW + "Do you want to modify table names? (yes/no): " + Fore.RESET
        ).strip().lower()

        table_rename_map = {}
        if modify_names_confirm in ("yes", "y"):
            for tbl in selected_tables:
                new_name = userInputWrapper(
                    Fore.YELLOW + f"Enter new name for '{tbl['sourceTable']}' (press Enter to keep): " + Fore.RESET
                ).strip()
                table_rename_map[tbl['sourceTable']] = new_name if new_name else tbl['sourceTable']
        else:
            for tbl in selected_tables:
                table_rename_map[tbl['sourceTable']] = tbl['sourceTable']

        # Apply prefix from config, default STUD.
        prefix = str(readValuefromAppConfig("app.dataengine.dihctl.addpipeline.prefixname")).strip()
        if not prefix:
            prefix = "STUD."

        space_type_name_map = {}
        for tbl in selected_tables:
            name = table_rename_map[tbl['sourceTable']]
            if not name.upper().startswith(prefix.upper()):
                name = prefix + name
            space_type_name_map[tbl['sourceTable']] = name
            verboseHandle.printConsoleInfo(f"Table '{tbl['sourceTable']}' -> Space Type: '{name}'")
            logger.info(f"Table '{tbl['sourceTable']}' -> Space Type: '{name}'")

        # Check if selected tables (with final space type names) are already registered in the space
        try:
            objectMgmtHost = getPivotHost()
            obj_response = requests.get(
                f"http://{objectMgmtHost}:7001/list",
                headers={"Accept": "application/json"}
            )
            objectJson = obj_response.json()
            space_table_names = set()
            for space in objectJson:
                if str(space.get("spacename", "")).strip().upper() == selected_space_name.upper():
                    for obj in space.get("objects", []):
                        space_table_names.add(str(obj.get("tablename", "")).strip().upper())
            for tbl in selected_tables:
                final_name = space_type_name_map[tbl["sourceTable"]]
                if final_name.strip().upper() in space_table_names:
                    verboseHandle.printConsoleError(f"Table '{final_name}' is already available in space '{selected_space_name}'.")
                    logger.error(f"Table '{final_name}' already exists in space '{selected_space_name}'.")
                    return
        except Exception as obj_ex:
            logger.warning(f"Could not check space table availability: {obj_ex}")

        payload = {
            "sourceSchema": source_schema,
            "sourceTables": source_tables_list
        }
        verboseHandle.printConsoleInfo(f"Payload: {json.dumps(payload, indent=2)}")
        logger.info(f"Payload: {json.dumps(payload)}")

        # Confirm before stopping pipeline
        confirm = userInputWrapper(
            Fore.YELLOW + f"Pipeline '{selected_pipeline}' will be stopped, {len(selected_tables)} table(s) will be added, Continue? (yes/no): " + Fore.RESET
        ).strip().lower()
        if confirm not in ("yes", "y"):
            verboseHandle.printConsoleWarning("Operation cancelled by user.")
            return

        # Stop pipeline before adding table (only if currently running)
        if selected_status == "RUNNING":
            verboseHandle.printConsoleInfo(f"Stopping pipeline: {selected_pipeline} [{pipeline_id}]")
            logger.info(f"Stopping pipeline: {selected_pipeline} [{pipeline_id}]")
            stop_response = requests.post(
                f"http://{iidrHost}:6080/api/v1/pipeline/{pipeline_id}/stop",
                headers={"accept": "*/*", "Content-Type": "application/json"}
            )
            import time
            current_status = None
            check_count = 0
            elapsed_secs = 0
            poll_interval = 10
            verboseHandle.printConsoleInfo(f"Waiting for pipeline '{selected_pipeline}' to become INACTIVE, polling every {poll_interval}s")
            logger.info(f"Waiting for pipeline '{selected_pipeline}' to become INACTIVE, polling every {poll_interval}s")
            while current_status != "INACTIVE":
                time.sleep(poll_interval)
                check_count += 1
                elapsed_secs += poll_interval
                status_resp = requests.get(f"http://{iidrHost}:6080/api/v1/pipeline/", headers={"accept": "*/*"})
                status_list = status_resp.json()
                current_status = next(
                    (pl.get("status", "").strip().upper() for pl in status_list if pl.get("pipelineId") == pipeline_id),
                    None
                )
                verboseHandle.printConsoleInfo(f"Pipeline status: {current_status} (check #{check_count}, elapsed: {elapsed_secs}s)")
                logger.info(f"Pipeline status poll #{check_count} [{elapsed_secs}s]: {current_status}")
            verboseHandle.printConsoleInfo(f"Pipeline '{selected_pipeline}' is now INACTIVE. Proceeding.")
            logger.info(f"Pipeline '{selected_pipeline}' confirmed INACTIVE.")
        else:
            verboseHandle.printConsoleInfo(f"Pipeline '{selected_pipeline}' is not running (status: {selected_status}), skipping stop.")
            logger.info(f"Pipeline '{selected_pipeline}' status is '{selected_status}', stop skipped.")

        # Adding table
        add_url = f"http://{iidrHost}:6080/api/v1/pipeline/{pipeline_id}/add_tables"
        verboseHandle.printConsoleInfo(f"Calling POST {add_url}")
        logger.info(f"Calling POST {add_url}")
        add_response = requests.post(
            add_url,
            headers={"accept": "*/*", "Content-Type": "application/json"},
            json=payload
        )
        add_resp_json = {}
        try:
            add_resp_json = add_response.json()
        except Exception:
            pass
        add_api_status = str(add_resp_json.get("status", "")).strip().upper()
        failed_tables  = add_resp_json.get("failedTablesAndReasons", {}) if isinstance(add_resp_json, dict) else {}

        if add_response.status_code in (200, 201, 202, 204):
            verboseHandle.printConsoleInfo(f"Tables {selected_table_names} added to pipeline '{selected_pipeline}' successfully.")
            logger.info(f"Add table response [{add_response.status_code}]: {add_response.text}")
        elif add_api_status == "PART_OF_TABLES_ADDED_SUCCESSFULLY":
            for tbl_name, reason in failed_tables.items():
                verboseHandle.printConsoleWarning(f"Table '{tbl_name}' could not be added: {reason}")
                logger.warning(f"Table '{tbl_name}' add failed: {reason}")
            succeeded = [t for t in selected_tables if t["sourceTable"] not in failed_tables]
            if not succeeded:
                verboseHandle.printConsoleError("No tables were added successfully. Aborting.")
                logger.error("All tables failed to add.")
                return
            selected_tables      = succeeded
            source_tables_list   = [t["sourceTable"] for t in selected_tables]
            selected_table_names = [f"{t['sourceSchema']}.{t['sourceTable']}" for t in selected_tables]
            verboseHandle.printConsoleInfo(f"Tables added successfully: {selected_table_names}")
            logger.info(f"Tables added successfully: {selected_table_names}")
        else:
            verboseHandle.printConsoleError(f"Failed to add table. Status: {add_response.status_code} Response: {add_response.text}")
            logger.error(f"Add table failed [{add_response.status_code}]: {add_response.text}")
            return

        # Step 10: Rename space types with prefix and/or remove columns
        needs_rename = any(
            space_type_name_map[tbl["sourceTable"]] != tbl["sourceTable"]
            for tbl in selected_tables
        )

        edit_cols_confirm = userInputWrapper(
            Fore.YELLOW + "Do you want to remove columns for the added table(s)? (yes/no): " + Fore.RESET
        ).strip().lower()

        export_path = str(readValuefromAppConfig("app.dataengine.dihctl.pipelinefolderpath"))
        col_exclude_map = {}
        needs_yaml_update = needs_rename or edit_cols_confirm in ("yes", "y")

        if not needs_yaml_update:
            verboseHandle.printConsoleInfo("No YAML changes required. Skipping pipeline update.")
        elif not export_path.strip():
            verboseHandle.printConsoleError("Export path cannot be empty. Skipping pipeline update.")
        elif not os.path.exists(export_path):
            verboseHandle.printConsoleError(f"Export path not found: {export_path}. Skipping pipeline update.")
        else:
            export_file = os.path.join(export_path, f"{selected_pipeline}.yaml")
            export_cmd = f"{rootpath}dihctl -e dev export pipelines {selected_pipeline} -o {export_file}"
            verboseHandle.printConsoleInfo(f"Exporting pipeline: {export_cmd}")
            logger.info(f"Running export: {export_cmd}")
            export_result = subprocess.run(export_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if export_result.returncode != 0:
                verboseHandle.printConsoleError(f"Export failed for '{selected_pipeline}': {export_result.stderr}")
                logger.error(f"Export failed [{export_result.returncode}]: {export_result.stderr}")
            else:
                verboseHandle.printConsoleInfo(f"Pipeline '{selected_pipeline}' exported to: {export_file}")
                logger.info(f"Export successful: {export_result.stdout}")
                with open(export_file, 'r') as f:
                    exported_yaml = yaml.safe_load(f)

                # Rename spaceTypeName for newly added tables (apply prefix/user rename)
                table_pipelines = exported_yaml["pipelines"][0]["tablePipelines"]
                original_stn_map = {}  # {sourceTable: original spaceTypeName before rename}
                for tp_idx, tp in enumerate(table_pipelines):
                    stn = str(tp.get("spaceTypeName", "")).strip()
                    for tbl in selected_tables:
                        if stn.upper() == tbl["sourceTable"].upper():
                            original_stn_map[tbl["sourceTable"]] = stn
                            new_stn = space_type_name_map[tbl["sourceTable"]]
                            if new_stn != stn:
                                exported_yaml["pipelines"][0]["tablePipelines"][tp_idx]["spaceTypeName"] = new_stn
                                verboseHandle.printConsoleInfo(f"Renamed spaceTypeName: '{stn}' -> '{new_stn}'")
                                logger.info(f"Renamed spaceTypeName: '{stn}' -> '{new_stn}'")
                            break

                # Handle column removal
                selected_pl_tbl_name = None
                selected_pl_tbl_schema = None
                selected_src_tbl_name = None
                if edit_cols_confirm in ("yes", "y"):
                    pipeline_table_pipelines = exported_yaml["pipelines"][0]["tablePipelines"]
                    pl_tbl_headers = [
                        Fore.YELLOW + "Sr No."          + Fore.RESET,
                        Fore.YELLOW + "Space Type Name" + Fore.RESET,
                    ]
                    pl_tbl_data = []
                    for idx, tp in enumerate(pipeline_table_pipelines, start=1):
                        pl_tbl_data.append([
                            Fore.GREEN + str(idx)                         + Fore.RESET,
                            Fore.GREEN + str(tp.get("spaceTypeName", "")) + Fore.RESET,
                        ])
                    verboseHandle.printConsoleInfo(f"Tables in pipeline '{selected_pipeline}':")
                    printTabular(None, pl_tbl_headers, pl_tbl_data)

                    pl_tbl_selection = userInputWrapper(
                        f"Select table number to edit columns (1-{len(pipeline_table_pipelines)}): "
                    ).strip()
                    if pl_tbl_selection.isdigit() and (1 <= int(pl_tbl_selection) <= len(pipeline_table_pipelines)):
                        selected_pl_tbl_idx = int(pl_tbl_selection) - 1
                        selected_pl_tbl_name = str(pipeline_table_pipelines[selected_pl_tbl_idx].get("spaceTypeName", "")).strip()
                        # Find original source table (for columns API which uses source table name)
                        matched_src = next(
                            (t for t in selected_tables if space_type_name_map[t["sourceTable"]].upper() == selected_pl_tbl_name.upper()),
                            None
                        )
                        if not matched_src:
                            matched_src = next(
                                (t for t in selected_tables if t["sourceTable"].upper() == selected_pl_tbl_name.upper()),
                                None
                            )
                        selected_pl_tbl_schema = matched_src["sourceSchema"] if matched_src else oracle_schema
                        selected_src_tbl_name  = matched_src["sourceTable"] if matched_src else selected_pl_tbl_name
                    else:
                        verboseHandle.printConsoleError("Invalid table selection.")

                if edit_cols_confirm in ("yes", "y") and selected_pl_tbl_name:
                    tbl_schema = selected_pl_tbl_schema
                    tbl_name   = selected_src_tbl_name
                    cols_url   = f"http://{di1_host}:6080/api/v1/datasource/{selected_sor_name}/table?schemaName={tbl_schema}&tableName={tbl_name}&refreshMetadata=false"
                    verboseHandle.printConsoleInfo(f"Fetching columns for {tbl_schema}.{tbl_name} from datasource '{selected_sor_name}'")
                    logger.info(f"Fetching columns URL: {cols_url}")
                    try:
                        cols_response = requests.get(cols_url, headers={"accept": "*/*"})
                        cols_response.raise_for_status()
                        cols_json = cols_response.json()
                        table_data = cols_json.get("data", cols_json) if isinstance(cols_json, dict) else cols_json
                        cols_raw = table_data.get("tableColumns", []) if isinstance(table_data, dict) else table_data

                        col_headers = [
                            Fore.YELLOW + "Sr No."      + Fore.RESET,
                            Fore.YELLOW + "Column Name" + Fore.RESET,
                            Fore.YELLOW + "Data Type"   + Fore.RESET,
                        ]
                        col_rows = []
                        for cidx, col in enumerate(cols_raw, start=1):
                            col_name = str(col.get("columnName", "")).strip()
                            col_type = str(col.get("columnType", "")).strip()
                            col_rows.append([
                                Fore.GREEN + str(cidx) + Fore.RESET,
                                Fore.GREEN + col_name  + Fore.RESET,
                                Fore.GREEN + col_type  + Fore.RESET,
                            ])
                        verboseHandle.printConsoleInfo(f"Columns for {tbl_schema}.{tbl_name}:")
                        printTabular(None, col_headers, col_rows)
                        if col_rows:
                            col_remove_input = userInputWrapper(
                                Fore.YELLOW + f"Select column number(s) to remove from '{selected_pl_tbl_name}' (e.g. 1 or 1-3 or 1,4,5, or press Enter to skip): " + Fore.RESET
                            ).strip()
                            if col_remove_input:
                                rm_indices = set()
                                for part in col_remove_input.split(","):
                                    part = part.strip()
                                    if "-" in part:
                                        s_v, e_v = part.split("-", 1)
                                        rm_indices.update(range(int(s_v.strip()), int(e_v.strip()) + 1))
                                    elif part.isdigit():
                                        rm_indices.add(int(part))
                                rm_indices = sorted(i for i in rm_indices if 1 <= i <= len(cols_raw))
                                if rm_indices:
                                    cols_to_remove = [cols_raw[i - 1].get("columnName", "") for i in rm_indices]
                                    verboseHandle.printConsoleInfo(f"Columns to remove from '{selected_pl_tbl_name}': {cols_to_remove}")
                                    logger.info(f"Columns to remove from '{selected_pl_tbl_name}': {cols_to_remove}")
                                    confirm_remove = userInputWrapper(
                                        Fore.YELLOW + f"Confirm removing {cols_to_remove} from '{selected_pl_tbl_name}'? (yes/no): " + Fore.RESET
                                    ).strip().lower()
                                    if confirm_remove in ("yes", "y"):
                                        col_exclude_map[selected_pl_tbl_name] = cols_to_remove
                                    else:
                                        verboseHandle.printConsoleWarning(f"Column removal cancelled for '{selected_pl_tbl_name}'.")
                                        logger.info(f"User cancelled column removal for '{selected_pl_tbl_name}'.")
                    except Exception as col_ex:
                        verboseHandle.printConsoleError(f"Failed to fetch columns for {tbl_schema}.{tbl_name}: {col_ex}")
                        logger.error(f"Columns fetch failed for {tbl_schema}.{tbl_name}: {col_ex}")

                # Apply excludeFields and collect renamed space type names to unregister
                unregister_types = []
                table_pipelines_upd = exported_yaml["pipelines"][0]["tablePipelines"]
                for tp_idx, tp in enumerate(table_pipelines_upd):
                    stn = str(tp.get("spaceTypeName", "")).strip()
                    matched_cols = (
                        col_exclude_map.get(stn) or
                        col_exclude_map.get(stn.upper()) or
                        col_exclude_map.get(stn.lower())
                    )
                    if matched_cols:
                        existing_exclude = tp.get("excludeFields") or []
                        updated_exclude = existing_exclude + [col for col in matched_cols if col not in existing_exclude]
                        exported_yaml["pipelines"][0]["tablePipelines"][tp_idx]["excludeFields"] = updated_exclude
                        if stn not in unregister_types:
                            unregister_types.append(stn)
                        verboseHandle.printConsoleInfo(f"Updated excludeFields for space type '{stn}': {updated_exclude}")
                        logger.info(f"Updated excludeFields for space type '{stn}': {updated_exclude}")
                    # For renamed new tables: track the renamed spaceTypeName (STUD.TABLE_C) —
                    # the check below will skip unregister if this name is not yet registered.
                    is_renamed_table = any(
                        space_type_name_map[t["sourceTable"]].upper() == stn.upper()
                        for t in selected_tables
                    )
                    if is_renamed_table and stn not in unregister_types:
                        unregister_types.append(stn)

                new_yaml_file = os.path.join(export_path, f"{selected_pipeline}_updated.yaml")
                with open(new_yaml_file, 'w') as f:
                    yaml.dump(exported_yaml, f, default_flow_style=False, allow_unicode=True)
                verboseHandle.printConsoleInfo(f"Updated YAML saved to: {new_yaml_file}")
                logger.info(f"Updated YAML saved to: {new_yaml_file}")

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

                # Validate deletion
                max_del_retries = 5
                pipeline_deleted = False
                for attempt in range(1, max_del_retries + 1):
                    verboseHandle.printConsoleInfo(f"Validating pipeline deletion for: {selected_pipeline} (attempt {attempt}/{max_del_retries})")
                    logger.info(f"Validating pipeline deletion: attempt {attempt}/{max_del_retries}")
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
                    verboseHandle.printConsoleError(f"Validation failed: pipeline '{selected_pipeline}' still exists. (attempt {attempt}/{max_del_retries})")
                    logger.error(f"Validation failed: pipeline still present. Attempt {attempt}/{max_del_retries}.")
                    time.sleep(10)
                if not pipeline_deleted:
                    verboseHandle.printConsoleError(f"Pipeline '{selected_pipeline}' still exists after {max_del_retries} attempts. Aborting.")
                    return

                # Unregister space types (original names for renamed tables, current names for col-excluded tables)
                objectMgmtHost = getPivotHost()

                # Fetch currently registered types before unregistering
                registered_types = None
                try:
                    list_resp = requests.get(
                        f"http://{objectMgmtHost}:7001/list",
                        headers={"Accept": "application/json"}
                    )
                    registered_types = set()
                    for space in list_resp.json():
                        for obj in space.get("objects", []):
                            registered_types.add(str(obj.get("tablename", "")).strip().upper())
                    logger.info(f"Registered types fetched: {registered_types}")
                except Exception as list_ex:
                    logger.warning(f"Could not fetch registered types list: {list_ex}")

                for space_type_name in unregister_types:
                    if registered_types is not None and space_type_name.strip().upper() not in registered_types:
                        verboseHandle.printConsoleInfo(f"Space type '{space_type_name}' is not registered, skipping unregister.")
                        logger.info(f"Space type '{space_type_name}' not found in registered types, skipping unregister.")
                        continue
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
                            verboseHandle.printConsoleWarning(f"Unregister '{space_type_name}': {unreg_response.text}")
                            logger.warning(f"Unregister response for '{space_type_name}': {unreg_response.text}")
                    except requests.exceptions.ConnectionError:
                        verboseHandle.printConsoleError(f"Cannot connect to object management API at {objectMgmtHost}:7001 for unregister.")
                        return

                # Import updated pipeline
                import_cmd = f"{rootpath}dihctl -e dev apply -f {new_yaml_file}"
                verboseHandle.printConsoleInfo(f"Running: {import_cmd}")
                logger.info(f"Running: {import_cmd}")
                import_result = subprocess.run(import_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                if import_result.returncode != 0:
                    verboseHandle.printConsoleError(f"Create pipeline failed: {import_result.stderr}")
                    return
                verboseHandle.printConsoleInfo(f"Pipeline created successfully:\n{import_result.stdout}")
                logger.info(f"Pipeline created successfully: {import_result.stdout}")

    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle CDC Add Table')
    logger.info('Menu -> DataEngine -> Oracle CDC Add Table')
    diManagerHost = getDIServerHost()
    if diManagerHost:
        addTable(diManagerHost)
    else:
        verboseHandle.printConsoleError("No DI Manager host found.")
