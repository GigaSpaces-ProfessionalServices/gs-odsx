import os
import csv
import io
import json
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

        selection = userInputWrapper(f"Select pipeline number to add table (1-{len(pipelines)}): ").strip()
        if not selection.isdigit() or not (1 <= int(selection) <= len(pipelines)):
            verboseHandle.printConsoleError("Invalid selection.")
            return
        selected_pipeline  = pipelines[int(selection) - 1].get("name", "")
        selected_status    = pipelines[int(selection) - 1].get("status", "").strip().upper()
        selected_sor_name  = pipelines[int(selection) - 1].get("sorName", "")
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

        # # Export pipeline YAML to get tables currently attached to the pipeline
        # export_path = str(readValuefromAppConfig("app.dataengine.dihctl.pipelinefolderpath"))
        # if not export_path.strip() or not os.path.exists(export_path):
        #     verboseHandle.printConsoleError(f"Export path not found: {export_path}")
        #     return
        # export_file = os.path.join(export_path, f"{selected_pipeline}.yaml")
        # export_cmd = f"{rootpath}dihctl -e dev export pipelines {selected_pipeline} -o {export_file}"
        # verboseHandle.printConsoleInfo(f"Running: {export_cmd}")
        # logger.info(f"Running: {export_cmd}")
        # export_result = subprocess.run(export_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        # if export_result.returncode != 0:
        #     verboseHandle.printConsoleError(f"Export failed: {export_result.stderr}")
        #     return
        # with open(export_file, 'r') as f:
        #     exported_yaml = yaml.safe_load(f)
        # existing_table_pipelines = exported_yaml["pipelines"][0]["tablePipelines"]
        # existing_space_types = [str(tp.get("spaceTypeName", "")).strip() for tp in existing_table_pipelines]
        #
        # verboseHandle.printConsoleInfo(f"Tables currently attached to pipeline '{selected_pipeline}':")
        # existing_headers = [
        #     Fore.YELLOW + "Sr No."          + Fore.RESET,
        #     Fore.YELLOW + "Space Type Name" + Fore.RESET,
        # ]
        # existing_data = []
        # for idx, stn in enumerate(existing_space_types, start=1):
        #     existing_data.append([
        #         Fore.GREEN + str(idx) + Fore.RESET,
        #         Fore.GREEN + stn      + Fore.RESET,
        #     ])
        # printTabular(None, existing_headers, existing_data)

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
            stop_status = stop_response.json().get("status", "unknown")
            verboseHandle.printConsoleInfo(f"Stop pipeline response status: {stop_status}")
            logger.info(f"Stop pipeline response status: {stop_status}")

            # Wait until pipeline is fully INACTIVE before proceeding
            import time
            max_wait = 60
            poll_interval = 5
            elapsed = 0
            verboseHandle.printConsoleInfo(f"Waiting for pipeline '{selected_pipeline}' to become INACTIVE...")
            logger.info(f"Polling pipeline status, max_wait={max_wait}s, interval={poll_interval}s")
            while elapsed < max_wait:
                time.sleep(poll_interval)
                elapsed += poll_interval
                status_resp = requests.get(f"http://{iidrHost}:6080/api/v1/pipeline/", headers={"accept": "*/*"})
                status_list = status_resp.json()
                current_status = next(
                    (pl.get("status", "").strip().upper() for pl in status_list if pl.get("pipelineId") == pipeline_id),
                    None
                )
                verboseHandle.printConsoleInfo(f"Pipeline status: {current_status} ({elapsed}s elapsed)")
                logger.info(f"Pipeline status poll [{elapsed}s]: {current_status}")
                if current_status and current_status != "RUNNING":
                    break
            else:
                verboseHandle.printConsoleError(f"Pipeline '{selected_pipeline}' did not stop within {max_wait}s. Aborting.")
                logger.error(f"Pipeline '{selected_pipeline}' still RUNNING after {max_wait}s polling.")
                return
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
        if add_response.status_code in (200, 201, 202, 204):
            verboseHandle.printConsoleInfo(f"Tables {selected_table_names} added to pipeline '{selected_pipeline}' successfully.")
            logger.info(f"Add table response [{add_response.status_code}]: {add_response.text}")
        else:
            verboseHandle.printConsoleError(f"Failed to add table. Status: {add_response.status_code} Response: {add_response.text}")
            logger.error(f"Add table failed [{add_response.status_code}]: {add_response.text}")
            return

        # Ask user whether to remove columns
        edit_cols_confirm = userInputWrapper(
            Fore.YELLOW + "Do you want to remove columns for the added table(s)? (yes/no): " + Fore.RESET
        ).strip().lower()

        # Export pipeline to list available tables before asking about column editing
        export_path = str(readValuefromAppConfig("app.dataengine.dihctl.pipelinefolderpath"))
        export_file = None
        exported_yaml = None
        selected_pl_tbl_name = None
        selected_pl_tbl_schema = None
        if not export_path.strip():
            verboseHandle.printConsoleError("Export path cannot be empty. Skipping export.")
        elif not os.path.exists(export_path):
            verboseHandle.printConsoleError(f"Export path not found: {export_path}. Skipping export.")
        else:
            export_file = os.path.join(export_path, f"{selected_pipeline}.yaml")
            export_cmd = f"{rootpath}dihctl -e dev export pipelines {selected_pipeline} -o {export_file}"
            verboseHandle.printConsoleInfo(f"Exporting pipeline: {export_cmd}")
            logger.info(f"Running export: {export_cmd}")
            export_result = subprocess.run(export_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if export_result.returncode != 0:
                verboseHandle.printConsoleError(f"Export failed for '{selected_pipeline}': {export_result.stderr}")
                logger.error(f"Export failed [{export_result.returncode}]: {export_result.stderr}")
                export_file = None
            else:
                verboseHandle.printConsoleInfo(f"Pipeline '{selected_pipeline}' exported successfully to: {export_file}")
                logger.info(f"Export successful: {export_result.stdout}")
                with open(export_file, 'r') as f:
                    exported_yaml = yaml.safe_load(f)

                # List all tables currently in the pipeline
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
                    matched_src = next((t for t in selected_tables if t["sourceTable"] == selected_pl_tbl_name), None)
                    selected_pl_tbl_schema = matched_src["sourceSchema"] if matched_src else oracle_schema
                else:
                    verboseHandle.printConsoleError("Invalid table selection.")
                    selected_pl_tbl_name = None
                    selected_pl_tbl_schema = None

        # List columns for each added table from the Oracle datasource
        col_exclude_map = {}  # {tableName: [columnName, ...]}
        if edit_cols_confirm in ("yes", "y") and selected_pl_tbl_name:
            tbl_schema = selected_pl_tbl_schema
            tbl_name   = selected_pl_tbl_name
            cols_url   = f"http://{di1_host}:6080/api/v1/datasource/{selected_sor_name}/table?schemaName={tbl_schema}&tableName={tbl_name}&refreshMetadata=false"
            verboseHandle.printConsoleInfo(f"Fetching columns for {tbl_schema}.{tbl_name} from datasource '{selected_sor_name}'")
            logger.info(f"Fetching columns URL: {cols_url}")
            try:
                cols_response = requests.get(cols_url, headers={"accept": "*/*"})
                cols_response.raise_for_status()
                cols_json = cols_response.json()
                table_data = cols_json.get("data", cols_json) if isinstance(cols_json, dict) else cols_json
                if isinstance(table_data, dict):
                    cols_raw = table_data.get("tableColumns", [])
                else:
                    cols_raw = table_data

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
                        Fore.YELLOW + f"Select column number(s) to remove from '{tbl_name}' (e.g. 1 or 1-3 or 1,4,5, or press Enter to skip): " + Fore.RESET
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
                            verboseHandle.printConsoleInfo(f"Columns to remove from '{tbl_name}': {cols_to_remove}")
                            logger.info(f"Columns to remove from '{tbl_name}': {cols_to_remove}")
                            confirm_remove = userInputWrapper(
                                Fore.YELLOW + f"Confirm removing {cols_to_remove} from '{tbl_name}'? (yes/no): " + Fore.RESET
                            ).strip().lower()
                            if confirm_remove in ("yes", "y"):
                                col_exclude_map[tbl_name] = cols_to_remove
                            else:
                                verboseHandle.printConsoleWarning(f"Column removal cancelled for '{tbl_name}'.")
                                logger.info(f"User cancelled column removal for '{tbl_name}'.")
            except Exception as col_ex:
                verboseHandle.printConsoleError(f"Failed to fetch columns for {tbl_schema}.{tbl_name}: {col_ex}")
                logger.error(f"Columns fetch failed for {tbl_schema}.{tbl_name}: {col_ex}")
        else:
            verboseHandle.printConsoleInfo("Skipping column editing.")
            logger.info("User skipped column editing.")

        if export_file and exported_yaml and col_exclude_map:
            table_pipelines = exported_yaml["pipelines"][0]["tablePipelines"]
            modified_space_types = []
            for tp_idx, tp in enumerate(table_pipelines):
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
                    modified_space_types.append(stn)
                    verboseHandle.printConsoleInfo(f"Updated excludeFields for space type '{stn}': {updated_exclude}")
                    logger.info(f"Updated excludeFields for space type '{stn}': {updated_exclude}")

            if modified_space_types:
                new_yaml_file = os.path.join(export_path, f"{selected_pipeline}_updated.yaml")
                with open(new_yaml_file, 'w') as f:
                    yaml.dump(exported_yaml, f, default_flow_style=False, allow_unicode=True)
                verboseHandle.printConsoleInfo(f"Updated YAML saved to: {new_yaml_file}")
                logger.info(f"Updated YAML saved to: {new_yaml_file}")

                # # Stop pipeline
                # verboseHandle.printConsoleInfo(f"Stopping pipeline: {selected_pipeline} [{pipeline_id}]")
                # logger.info(f"Stopping pipeline: {selected_pipeline} [{pipeline_id}]")
                # stop_rc_response = requests.post(
                #     f"http://{iidrHost}:6080/api/v1/pipeline/{pipeline_id}/stop",
                #     headers={"accept": "*/*", "Content-Type": "application/json"}
                # )
                # stop_rc_status = stop_rc_response.json().get("status", "unknown")
                # verboseHandle.printConsoleInfo(f"Stop pipeline response status: {stop_rc_status}")
                # logger.info(f"Stop pipeline response status: {stop_rc_status}")

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
                if not pipeline_deleted:
                    verboseHandle.printConsoleError(f"Pipeline '{selected_pipeline}' still exists after {max_del_retries} attempts. Aborting.")
                    return

                # Unregister each modified space type
                objectMgmtHost = getPivotHost()
                for space_type_name in modified_space_types:
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
                            return
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
