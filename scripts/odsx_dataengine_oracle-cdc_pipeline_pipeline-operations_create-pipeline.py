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
from utils.ods_cluster_config import config_get_dataIntegration_nodes, config_get_manager_node
from utils.odsx_keypress import userInputWrapper
from utils.odsx_print_tabular_data import printTabular
from utils.ods_app_config import readValuefromAppConfig
from utils.odsx_objectmanagement_utilities import getPivotHost
from utils.ods_ssh import executeRemoteCommandAndGetOutputValuePython36
from scripts.odsx_tieredstorage_undeploy import getManagerHost
from scripts.odsx_space_spacelist import listDeployed
from requests.auth import HTTPBasicAuth
from utils.odsx_db2feeder_utilities import getPasswordByHost, getUsernameByHost

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
    verboseHandle.printConsoleError(str({
        'type': type(e).__name__,
        'message': str(e),
        'trace': trace
    }))


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


def createPipeline(diManagerHost):
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

        di1_host = str(os.getenv("di1"))

        # Get pipeline name
        pipeline_name = userInputWrapper(Fore.YELLOW + "Enter new pipeline name: " + Fore.RESET).strip()
        if not pipeline_name:
            verboseHandle.printConsoleError("Pipeline name cannot be empty.")
            return

        # Verify pipeline name is not already taken
        verboseHandle.printConsoleInfo("Verifying pipeline name availability...")
        pl_check = subprocess.run(
            [f'{rootpath}dihctl', '-e', 'dev', 'show', 'pipelines', '--format', 'csv'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )
        pl_reader = csv.DictReader(io.StringIO(pl_check.stdout))
        existing_pipelines = [row.get("name", "") for row in pl_reader]
        if pipeline_name in existing_pipelines:
            verboseHandle.printConsoleError(f"Pipeline '{pipeline_name}' already exists. Please choose a different name.")
            return
        verboseHandle.printConsoleInfo(f"Pipeline name '{pipeline_name}' is available.")

        # Fetch space list from manager REST API
        managerNodes = config_get_manager_node()
        managerHost = getManagerHost(managerNodes)
        profile = str(readValuefromAppConfig("app.setup.profile"))
        logger.info("managerHost :" + str(managerHost))
        if profile == 'security':
            username = str(getUsernameByHost())
            password = str(getPasswordByHost())
            spaces_response = requests.get("http://" + str(managerHost) + ":8090/v2/spaces", auth=HTTPBasicAuth(username, password))
        else:
            spaces_response = requests.get("http://" + str(managerHost) + ":8090/v2/spaces")
        logger.info("response status of host :" + str(managerHost) + " status :" + str(spaces_response.status_code) + " Content: " + str(spaces_response.content))
        spaces_json = json.loads(spaces_response.text)
        if not spaces_json:
            verboseHandle.printConsoleError("No spaces found on cluster.")
            return
        space_headers = [
            Fore.YELLOW + "Sr No."     + Fore.RESET,
            Fore.YELLOW + "Space Name" + Fore.RESET,
        ]
        space_data = []
        for idx, sp in enumerate(spaces_json, start=1):
            space_data.append([
                Fore.GREEN + str(idx)         + Fore.RESET,
                Fore.GREEN + str(sp["name"])  + Fore.RESET,
            ])
        printTabular(None, space_headers, space_data)
        space_sel = userInputWrapper(Fore.YELLOW + f"Select space number (1-{len(spaces_json)}): " + Fore.RESET).strip()
        if not space_sel.isdigit() or not (1 <= int(space_sel) <= len(spaces_json)):
            verboseHandle.printConsoleError("Invalid space selection.")
            return
        space_name = str(spaces_json[int(space_sel) - 1]["name"]).strip()

        verboseHandle.printConsoleInfo(f"Selected space: {space_name}")
        logger.info(f"Selected space: {space_name}")

        sor_name = ""

        # Live datasources via dihctl
        verboseHandle.printConsoleInfo("Fetching live datasources...")
        logger.info("Fetching datasources list via dihctl")
        ds_result = subprocess.run(
            [f'{rootpath}dihctl', '-e', 'dev', 'show', 'datasources', '--format', 'csv'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )
        ds_reader  = csv.DictReader(io.StringIO(ds_result.stdout))
        datasources = list(ds_reader)
        if not datasources:
            verboseHandle.printConsoleWarning("No live datasources found. Using 'ORACLE' as default.")
            sor_name = "ORACLE"
        else:
            ds_headers = [
                Fore.YELLOW + "Sr No."          + Fore.RESET,
                Fore.YELLOW + "Datasource Name" + Fore.RESET,
                Fore.YELLOW + "DB Provider"     + Fore.RESET,
            ]
            ds_data = []
            for idx, ds in enumerate(datasources, start=1):
                ds_data.append([
                    Fore.GREEN + str(idx)                                        + Fore.RESET,
                    Fore.GREEN + str(ds.get("name") or ds.get("sorName") or "")  + Fore.RESET,
                    Fore.GREEN + str(ds.get("dbProvider", ""))                   + Fore.RESET,
                ])
            printTabular(None, ds_headers, ds_data)
            ds_selection = userInputWrapper(f"Select datasource number (1-{len(datasources)}): ").strip()
            if not ds_selection.isdigit() or not (1 <= int(ds_selection) <= len(datasources)):
                verboseHandle.printConsoleError("Invalid selection.")
                return
            selected_ds = datasources[int(ds_selection) - 1]
            sor_name = str(selected_ds.get("name") or selected_ds.get("sorName") or "ORACLE").strip()

        verboseHandle.printConsoleInfo(f"Selected datasource (SOR): {sor_name}")
        logger.info(f"Selected datasource: {sor_name}")

        # Fetch Oracle schemas for the selected datasource
        schemas_url = f"http://{di1_host}:6080/api/v2/datasource/{sor_name}/schemas"
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
            verboseHandle.printConsoleError(f"No schemas found for datasource '{sor_name}'.")
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

        # List available tables from the datasource
        schema_tables_url = f"http://{di1_host}:6080/api/v2/datasource/{sor_name}/tables?schemaName={oracle_schema}"
        verboseHandle.printConsoleInfo(f"Fetching available tables from datasource '{sor_name}' schema '{oracle_schema}'")
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
            tables.append({"sourceSchema": s_schema, "sourceTable": s_table})

        if not tables:
            verboseHandle.printConsoleWarning(f"No available tables found in datasource '{sor_name}'.")
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

        tbl_selection = userInputWrapper(f"Select table number(s) to add to pipeline '{pipeline_name}' (e.g. 1 or 1-3 or 1,4,5): ").strip()
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

        selected_tables      = [tables[i - 1] for i in selected_tbl_indices]
        source_schema        = selected_tables[0]["sourceSchema"]
        source_tables_list   = [tbl["sourceTable"] for tbl in selected_tables]
        selected_table_names = [f"{tbl['sourceSchema']}.{tbl['sourceTable']}" for tbl in selected_tables]
        verboseHandle.printConsoleInfo(f"Selected tables: {selected_table_names}")
        logger.info(f"Selected tables: {selected_table_names}")

        # Check if selected tables are already registered in the space
        try:
            objectMgmtHost = getPivotHost()
            obj_response = requests.get(
                f"http://{objectMgmtHost}:7001/list",
                headers={"Accept": "application/json"}
            )
            objectJson = obj_response.json()
            space_table_names = set()
            for space in objectJson:
                if str(space.get("spacename", "")).strip().upper() == space_name.strip().upper():
                    for obj in space.get("objects", []):
                        space_table_names.add(str(obj.get("tablename", "")).strip().upper())
            for tbl in selected_tables:
                if tbl["sourceTable"].strip().upper() in space_table_names:
                    verboseHandle.printConsoleError(f"Table '{tbl['sourceTable']}' is already available in space '{space_name}'.")
                    logger.error(f"Table '{tbl['sourceTable']}' already exists in space '{space_name}'.")
                    return
        except Exception as obj_ex:
            logger.warning(f"Could not check space table availability: {obj_ex}")

        # Create pipeline via REST API
        create_payload = {
            "name": pipeline_name,
            "sorName": sor_name,
            "cdcProvider": "IIDR",
            "spaceName": space_name,
            "batchWrite": 2000,
            "checkpointInterval": 6000
        }
        verboseHandle.printConsoleInfo(f"Creating pipeline '{pipeline_name}' in space '{space_name}'...")
        verboseHandle.printConsoleInfo(f"Payload: {json.dumps(create_payload, indent=2)}")
        logger.info(f"Creating pipeline: {json.dumps(create_payload)}")
        create_url = f"http://{iidrHost}:6080/api/v1/pipeline/"
        verboseHandle.printConsoleInfo(f"POST {create_url}")
        create_response = requests.post(
            create_url,
            headers={"accept": "*/*", "Content-Type": "application/json"},
            json=create_payload
        )
        if create_response.status_code not in (200, 201, 202):
            verboseHandle.printConsoleError(f"Failed to create pipeline. Status: {create_response.status_code} Response: {create_response.text}")
            logger.error(f"Pipeline creation failed [{create_response.status_code}]: {create_response.text}")
            return

        create_json = create_response.json()
        pipeline_id = create_json.get("pipelineId") or (create_json.get("data") or {}).get("pipelineId")
        if not pipeline_id:
            pl_list_resp = requests.get(f"http://{iidrHost}:6080/api/v1/pipeline/", headers={"accept": "*/*"})
            pl_list = pl_list_resp.json()
            if isinstance(pl_list, dict):
                pl_list = pl_list.get("data", [])
            pipeline_id = next((pl["pipelineId"] for pl in pl_list if pl.get("name") == pipeline_name), None)

        if not pipeline_id:
            verboseHandle.printConsoleError(f"Pipeline created but ID not found for: {pipeline_name}")
            return

        verboseHandle.printConsoleInfo(f"Pipeline '{pipeline_name}' created successfully. ID: {pipeline_id}")
        logger.info(f"Pipeline '{pipeline_name}' created. ID: {pipeline_id}")

        payload = {
            "sourceSchema": source_schema,
            "sourceTables": source_tables_list
        }
        verboseHandle.printConsoleInfo(f"Payload: {json.dumps(payload, indent=2)}")
        logger.info(f"Payload: {json.dumps(payload)}")

        # Add tables
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
            verboseHandle.printConsoleInfo(f"Tables {selected_table_names} added to pipeline '{pipeline_name}' successfully.")
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

        verboseHandle.printConsoleInfo(f"{pipeline_name} Pipeline created successfully")
        logger.info(f"{pipeline_name} Pipeline created successfully")

        # ── Optional column exclusion ────────────────────────────────────────

        edit_cols_confirm = userInputWrapper(
            Fore.YELLOW + "Do you want to remove columns for the added table(s)? (yes/no): " + Fore.RESET
        ).strip().lower()

        export_path = str(readValuefromAppConfig("app.dataengine.dihctl.pipelinefolderpath"))
        export_file = None
        exported_yaml = None
        selected_pl_tbl_name = None
        selected_pl_tbl_schema = None
        if edit_cols_confirm not in ("yes", "y"):
            verboseHandle.printConsoleInfo("Skipping column editing.")
        elif not export_path.strip():
            verboseHandle.printConsoleError("Export path cannot be empty. Skipping export.")
        elif not os.path.exists(export_path):
            verboseHandle.printConsoleError(f"Export path not found: {export_path}. Skipping export.")
        else:
            export_file = os.path.join(export_path, f"{pipeline_name}.yaml")
            export_cmd = f"{rootpath}dihctl -e dev export pipelines {pipeline_name} -o {export_file}"
            verboseHandle.printConsoleInfo(f"Exporting pipeline: {export_cmd}")
            logger.info(f"Running export: {export_cmd}")
            export_result = subprocess.run(export_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if export_result.returncode != 0:
                verboseHandle.printConsoleError(f"Export failed for '{pipeline_name}': {export_result.stderr}")
                logger.error(f"Export failed [{export_result.returncode}]: {export_result.stderr}")
                export_file = None
            else:
                verboseHandle.printConsoleInfo(f"Pipeline '{pipeline_name}' exported successfully to: {export_file}")
                logger.info(f"Export successful: {export_result.stdout}")
                with open(export_file, 'r') as f:
                    exported_yaml = yaml.safe_load(f)

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
                verboseHandle.printConsoleInfo(f"Tables in pipeline '{pipeline_name}':")
                printTabular(None, pl_tbl_headers, pl_tbl_data)

                pl_tbl_selection = userInputWrapper(
                    f"Select table number to edit columns (1-{len(pipeline_table_pipelines)}): "
                ).strip()
                if pl_tbl_selection.isdigit() and (1 <= int(pl_tbl_selection) <= len(pipeline_table_pipelines)):
                    selected_pl_tbl_idx  = int(pl_tbl_selection) - 1
                    selected_pl_tbl_name = str(pipeline_table_pipelines[selected_pl_tbl_idx].get("spaceTypeName", "")).strip()
                    matched_src          = next((t for t in selected_tables if t["sourceTable"] == selected_pl_tbl_name), None)
                    selected_pl_tbl_schema = matched_src["sourceSchema"] if matched_src else oracle_schema
                else:
                    verboseHandle.printConsoleError("Invalid table selection.")

        col_exclude_map = {}
        if edit_cols_confirm in ("yes", "y") and selected_pl_tbl_name:
            tbl_schema = selected_pl_tbl_schema
            tbl_name   = selected_pl_tbl_name
            cols_url   = f"http://{di1_host}:6080/api/v1/datasource/{sor_name}/table?schemaName={tbl_schema}&tableName={tbl_name}&refreshMetadata=false"
            verboseHandle.printConsoleInfo(f"Fetching columns for {tbl_schema}.{tbl_name} from datasource '{sor_name}'")
            logger.info(f"Fetching columns URL: {cols_url}")
            try:
                cols_response = requests.get(cols_url, headers={"accept": "*/*"})
                cols_response.raise_for_status()
                cols_json  = cols_response.json()
                table_data = cols_json.get("data", cols_json) if isinstance(cols_json, dict) else cols_json
                cols_raw   = table_data.get("tableColumns", []) if isinstance(table_data, dict) else table_data

                col_headers = [
                    Fore.YELLOW + "Sr No."      + Fore.RESET,
                    Fore.YELLOW + "Column Name" + Fore.RESET,
                    Fore.YELLOW + "Data Type"   + Fore.RESET,
                ]
                col_rows = []
                for cidx, col in enumerate(cols_raw, start=1):
                    col_rows.append([
                        Fore.GREEN + str(cidx)                              + Fore.RESET,
                        Fore.GREEN + str(col.get("columnName", "")).strip() + Fore.RESET,
                        Fore.GREEN + str(col.get("columnType", "")).strip() + Fore.RESET,
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

        if export_file and exported_yaml and col_exclude_map:
            table_pipelines      = exported_yaml["pipelines"][0]["tablePipelines"]
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
                    updated_exclude  = existing_exclude + [col for col in matched_cols if col not in existing_exclude]
                    exported_yaml["pipelines"][0]["tablePipelines"][tp_idx]["excludeFields"] = updated_exclude
                    modified_space_types.append(stn)
                    verboseHandle.printConsoleInfo(f"Updated excludeFields for space type '{stn}': {updated_exclude}")
                    logger.info(f"Updated excludeFields for space type '{stn}': {updated_exclude}")

            if modified_space_types:
                new_yaml_file = os.path.join(export_path, f"{pipeline_name}_updated.yaml")
                with open(new_yaml_file, 'w') as f:
                    yaml.dump(exported_yaml, f, default_flow_style=False, allow_unicode=True)
                verboseHandle.printConsoleInfo(f"Updated YAML saved to: {new_yaml_file}")
                logger.info(f"Updated YAML saved to: {new_yaml_file}")

                # Delete pipeline
                delete_cmd = f"{rootpath}dihctl -e dev delete pipelines {pipeline_name}"
                verboseHandle.printConsoleInfo(f"Running: {delete_cmd}")
                logger.info(f"Running: {delete_cmd}")
                delete_result = subprocess.run(delete_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                if delete_result.returncode != 0:
                    verboseHandle.printConsoleError(f"Delete pipeline failed: {delete_result.stderr}")
                    return
                verboseHandle.printConsoleInfo(f"Pipeline deleted successfully: {pipeline_name}")
                logger.info(f"Pipeline deleted successfully: {delete_result.stdout}")

                # Validate deletion
                max_del_retries  = 5
                pipeline_deleted = False
                for attempt in range(1, max_del_retries + 1):
                    verboseHandle.printConsoleInfo(f"Validating pipeline deletion for: {pipeline_name} (attempt {attempt}/{max_del_retries})")
                    logger.info(f"Validating pipeline deletion: attempt {attempt}/{max_del_retries}")
                    show_result = subprocess.run(
                        [f'{rootpath}dihctl', '-e', 'dev', 'show', 'pipelines', '--format', 'csv'],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
                    )
                    show_reader        = csv.DictReader(io.StringIO(show_result.stdout))
                    remaining_pipelines = [row.get("name", "") for row in show_reader]
                    if pipeline_name not in remaining_pipelines:
                        pipeline_deleted = True
                        verboseHandle.printConsoleInfo(f"Validation passed: pipeline '{pipeline_name}' confirmed deleted.")
                        logger.info(f"Validation passed: pipeline '{pipeline_name}' not found in show pipelines output.")
                        break
                    verboseHandle.printConsoleError(f"Validation failed: pipeline '{pipeline_name}' still exists. (attempt {attempt}/{max_del_retries})")
                    logger.error(f"Validation failed: pipeline still present. Attempt {attempt}/{max_del_retries}.")
                    time.sleep(10)
                if not pipeline_deleted:
                    verboseHandle.printConsoleError(f"Pipeline '{pipeline_name}' still exists after {max_del_retries} attempts. Aborting.")
                    return

                # # Unregister each modified space type
                # objectMgmtHost = getPivotHost()
                # for space_type_name in modified_space_types:
                #     verboseHandle.printConsoleInfo(f"Unregistering space type: {space_type_name}")
                #     logger.info(f"Unregistering space type: {space_type_name}")
                #     try:
                #         unreg_response = requests.post(
                #             f"http://{objectMgmtHost}:7001/unregistertype",
                #             data={"type": space_type_name},
                #             headers={"Accept": "application/json"}
                #         )
                #         if unreg_response.text.strip() == "success":
                #             verboseHandle.printConsoleInfo(f"Space type '{space_type_name}' unregistered successfully.")
                #             logger.info(f"Space type '{space_type_name}' unregistered successfully.")
                #         else:
                #             verboseHandle.printConsoleError(f"Failed to unregister space type '{space_type_name}': {unreg_response.text}")
                #             return
                #     except requests.exceptions.ConnectionError:
                #         verboseHandle.printConsoleError(f"Cannot connect to object management API at {objectMgmtHost}:7001 for unregister.")
                #         return

                # Import updated pipeline with excludeFields
                import_cmd = f"{rootpath}dihctl -e dev apply -f {new_yaml_file}"
                verboseHandle.printConsoleInfo(f"Running: {import_cmd}")
                logger.info(f"Running: {import_cmd}")
                import_result = subprocess.run(import_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                if import_result.returncode != 0:
                    verboseHandle.printConsoleError(f"Create pipeline failed: {import_result.stderr}")
                    return

    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle CDC -> Pipeline -> Pipeline Operations -> Create Pipeline')
    logger.info('Menu -> DataEngine -> Oracle CDC -> Pipeline -> Pipeline Operations -> Create Pipeline')
    diManagerHost = getDIServerHost()
    if diManagerHost:
        createPipeline(diManagerHost)
    else:
        verboseHandle.printConsoleError("No DI Manager host found.")
