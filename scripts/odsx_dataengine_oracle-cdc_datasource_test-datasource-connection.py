#!/usr/bin/env python3

import os
import re
import json
import yaml
import requests
import subprocess
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_app_config import readValuefromAppConfig
from utils.ods_cluster_config import config_get_dataIntegration_nodes, config_get_iidrOracleAgent_node
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


def _parseOracleConn(url):
    """Return (host, port, service) from a datasource URL.

    Handles iidr://host:port, jdbc:oracle:thin:@//host:port/service,
    and jdbc:oracle:thin:@host:port:sid.
    """
    url = str(url).strip()
    m = re.match(r'jdbc:oracle:thin:@//([^:/]+):(\d+)/([^/?\s]+)', url, re.IGNORECASE)
    if m:
        return m.group(1), m.group(2), m.group(3)
    m = re.match(r'jdbc:oracle:thin:@([^:/]+):(\d+):([^/?\s]+)', url, re.IGNORECASE)
    if m:
        return m.group(1), m.group(2), m.group(3)
    m = re.match(r'iidr://([^:/]+)(?::(\d+))?(?:/([^/?\s]*))?', url, re.IGNORECASE)
    if m:
        return m.group(1), "1521", (m.group(3) or "")
    return url, "1521", ""


def _host_from_url(url):
    """Extract the DI/IIDR host from a datasource URL.

    Handles:
      iidr://host:port
      jdbc:oracle:thin:@//host:port/service
      jdbc:oracle:thin:@host:port:sid
    """
    url = str(url).strip()
    m = re.match(r'iidr://([^:/]+)', url, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.match(r'jdbc:oracle:thin:@//([^:/]+)', url, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.match(r'jdbc:oracle:thin:@([^:/]+)', url, re.IGNORECASE)
    if m:
        return m.group(1)
    return ""


def _load_datasource_file(fpath):
    """Load a single JSON or YAML datasource file; return list of datasource dicts."""
    fname = os.path.basename(fpath)
    try:
        with open(fpath, 'r') as f:
            if fname.endswith('.json'):
                data = json.load(f)
            else:
                data = yaml.safe_load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
    except Exception as ex:
        verboseHandle.printConsoleError(f"Failed to read '{fname}': {ex}")
        logger.error(f"_load_datasource_file error for '{fname}': {ex}")
    return []


def testDatasourceConnections():
    try:
        # MDM discovery — used only for the 1st connection as the fallback DI host
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

        username = str(readValuefromAppConfig("app.cdc.datasource.username") or "").strip()
        password = str(readValuefromAppConfig("app.cdc.datasource.password") or "").strip()
        verboseHandle.printConsoleInfo(f"Using credentials from app.config — username: {username}")
        logger.info(f"testDatasourceConnections username: {username}")

        datasource_path = str(readValuefromAppConfig("app.dataengine.dihctl.datasourcefolderpath") or "").strip()
        if not datasource_path:
            verboseHandle.printConsoleError(
                "Datasource folder path not configured (app.dataengine.dihctl.datasourcefolderpath).")
            return
        if not os.path.exists(datasource_path):
            verboseHandle.printConsoleError(f"Datasource folder not found: {datasource_path}")
            return

        files = sorted(
            f for f in os.listdir(datasource_path)
            if os.path.isfile(os.path.join(datasource_path, f))
            and (f.endswith('.json') or f.endswith('.yaml') or f.endswith('.yml'))
        )

        if not files:
            verboseHandle.printConsoleWarning(f"No datasource files (JSON/YAML) found in: {datasource_path}")
            return

        entries = []  # list of (filename, datasource_dict)
        for fname in files:
            fpath = os.path.join(datasource_path, fname)
            for ds in _load_datasource_file(fpath):
                entries.append((fname, ds))

        if not entries:
            verboseHandle.printConsoleWarning("No valid datasource entries found in any file.")
            return

        # Display all found datasources
        list_headers = [
            Fore.YELLOW + "Sr No."      + Fore.RESET,
            Fore.YELLOW + "File"        + Fore.RESET,
            Fore.YELLOW + "SOR Name"    + Fore.RESET,
            Fore.YELLOW + "DB Provider" + Fore.RESET,
            Fore.YELLOW + "URL"         + Fore.RESET,
        ]
        list_table = []
        for idx, (fname, ds) in enumerate(entries, start=1):
            list_table.append([
                Fore.GREEN + str(idx)                      + Fore.RESET,
                Fore.GREEN + fname                         + Fore.RESET,
                Fore.GREEN + str(ds.get("sorName", ""))    + Fore.RESET,
                Fore.GREEN + str(ds.get("dbProvider", "")) + Fore.RESET,
                Fore.GREEN + str(ds.get("url", ""))        + Fore.RESET,
            ])
        verboseHandle.printConsoleInfo(f"Found {len(entries)} datasource(s) in: {datasource_path}")
        printTabular(None, list_headers, list_table)

        selection = userInputWrapper(
            f"Select datasource(s) to test (e.g. 1 or 1-{len(entries)} or 1,2): "
        ).strip()
        selected_indices = set()
        for part in selection.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-", 1)
                if start.strip().isdigit() and end.strip().isdigit():
                    selected_indices.update(range(int(start.strip()), int(end.strip()) + 1))
            elif part.isdigit():
                selected_indices.add(int(part))
        selected_indices = sorted(i for i in selected_indices if 1 <= i <= len(entries))
        if not selected_indices:
            verboseHandle.printConsoleError("Invalid selection.")
            return
        entries = [entries[i - 1] for i in selected_indices]

        logger.info("testDatasourceConnections starting connection tests")

        result_headers = [
            Fore.YELLOW + "Sr No."       + Fore.RESET,
            Fore.YELLOW + "SOR Name"     + Fore.RESET,
            Fore.YELLOW + "DI Host"      + Fore.RESET,
            Fore.YELLOW + "URL"          + Fore.RESET,
            Fore.YELLOW + "Login Status" + Fore.RESET,
        ]
        result_table = []
        successful = []  # (idx, sor_name, ds_host) for schema listing

        # Pass 1: test all logins and collect results
        for idx, (fname, ds) in enumerate(entries, start=1):
            sor_name = str(ds.get("sorName", "")).strip()
            url      = str(ds.get("url", "")).strip()

            ds_host = _host_from_url(url) or iidrHost
            api_url = f"http://{ds_host}:6080/api/v1/datasource/save-connection"

            payload = {
                "sorName":        sor_name,
                "dbProvider":     str(ds.get("dbProvider", "ORACLE")),
                "url":            url,
                "username":       username,
                "password":       password,
                "additionalInfo": str(ds.get("additionalInfo", "")),
                "offlineMode":    bool(ds.get("offlineMode", False)),
            }

            logger.info(f"testDatasource POST {api_url} sorName={sor_name} url={url}")
            try:
                response = requests.post(
                    api_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    proxies={"http": None, "https": None},
                    timeout=30
                )
                if response.status_code in (200, 201):
                    status_str = Fore.GREEN + "LOGIN SUCCESS" + Fore.RESET
                    logger.info(f"testDatasource '{sor_name}' success: {response.status_code}")
                    successful.append((idx, sor_name, ds_host))
                else:
                    status_str = Fore.RED + f"LOGIN FAILED ({response.status_code})" + Fore.RESET
                    logger.error(
                        f"testDatasource '{sor_name}' failed: {response.status_code} {response.text}")

            except requests.exceptions.ConnectionError as ce:
                status_str = Fore.RED + "CONNECTION ERROR" + Fore.RESET
                logger.error(f"testDatasource '{sor_name}' connection error: {ce}")

            except requests.exceptions.Timeout:
                status_str = Fore.RED + "TIMEOUT" + Fore.RESET
                logger.error(f"testDatasource '{sor_name}' timed out")

            result_table.append([
                Fore.GREEN + str(idx) + Fore.RESET,
                Fore.GREEN + sor_name + Fore.RESET,
                Fore.GREEN + ds_host  + Fore.RESET,
                Fore.GREEN + url      + Fore.RESET,
                status_str,
            ])

        # Print login summary first
        verboseHandle.printConsoleInfo("--- Datasource Login Test Results ---")
        printTabular(None, result_headers, result_table)

        # Pass 2: fetch schemas for each successful login
        for idx, sor_name, ds_host in successful:
            verboseHandle.printConsoleInfo(
                f"[{idx}/{len(entries)}] Testing '{sor_name}' — host: {ds_host}")
            verboseHandle.printConsoleInfo(f"  [OK] '{sor_name}' login successful.")

            schemas_url = f"http://{ds_host}:6080/api/v2/datasource/{sor_name}/schemas"
            verboseHandle.printConsoleInfo(f"  Fetching schemas from: {schemas_url}")
            logger.info(f"testDatasource schemas GET {schemas_url}")
            try:
                schemas_resp = requests.get(
                    schemas_url,
                    headers={"accept": "*/*"},
                    proxies={"http": None, "https": None},
                    timeout=30
                )
                schemas_resp.raise_for_status()
                schemas_json = schemas_resp.json()
                schemas_raw = (
                    schemas_json.get("data", schemas_json)
                    if isinstance(schemas_json, dict) else schemas_json
                )

                schemas = []
                for entry in schemas_raw:
                    if isinstance(entry, str):
                        name = entry.strip()
                    else:
                        name = str(
                            entry.get("schemaName") or entry.get("name") or entry.get("schema", "")
                        ).strip()
                    if name:
                        schemas.append(name)

                if schemas:
                    schema_headers = [
                        Fore.YELLOW + "Sr No."      + Fore.RESET,
                        Fore.YELLOW + "Schema Name" + Fore.RESET,
                    ]
                    schema_data = [
                        [Fore.GREEN + str(s_idx) + Fore.RESET,
                         Fore.GREEN + s_name     + Fore.RESET]
                        for s_idx, s_name in enumerate(schemas, start=1)
                    ]
                    verboseHandle.printConsoleInfo(
                        f"  Available schemas for '{sor_name}' ({len(schemas)} found):")
                    printTabular(None, schema_headers, schema_data)
                    logger.info(f"testDatasource '{sor_name}' schemas: {schemas}")

                    # Schema selection
                    schema_sel = userInputWrapper(
                        f"  Select schema number to list tables (1-{len(schemas)}): "
                    ).strip()
                    if not schema_sel.isdigit() or not (1 <= int(schema_sel) <= len(schemas)):
                        verboseHandle.printConsoleError("  Invalid schema selection. Skipping table listing.")
                    else:
                        selected_schema = schemas[int(schema_sel) - 1]
                        verboseHandle.printConsoleInfo(f"  Selected schema: {selected_schema}")
                        logger.info(f"testDatasource '{sor_name}' selected schema: {selected_schema}")

                        tables_url = (
                            f"http://{ds_host}:6080/api/v2/datasource/{sor_name}"
                            f"/tables?schemaName={selected_schema}"
                        )
                        verboseHandle.printConsoleInfo(f"  Fetching tables from: {tables_url}")
                        logger.info(f"testDatasource tables GET {tables_url}")
                        try:
                            tables_resp = requests.get(
                                tables_url,
                                headers={"accept": "*/*"},
                                proxies={"http": None, "https": None},
                                timeout=30
                            )
                            tables_resp.raise_for_status()
                            tables_json = tables_resp.json()
                            tables_raw = (
                                tables_json.get("data", tables_json)
                                if isinstance(tables_json, dict) else tables_json
                            )

                            tables = []
                            for t_entry in tables_raw:
                                if isinstance(t_entry, str):
                                    t_name = t_entry.strip()
                                    t_schema = selected_schema
                                else:
                                    t_name   = str(
                                        t_entry.get("tableName") or
                                        t_entry.get("sourceTable") or
                                        t_entry.get("table", "")
                                    ).strip()
                                    t_schema = str(
                                        t_entry.get("schemaName") or
                                        t_entry.get("sourceSchema") or
                                        t_entry.get("schema", selected_schema)
                                    ).strip()
                                if t_name:
                                    tables.append((t_schema, t_name))

                            if tables:
                                tbl_headers = [
                                    Fore.YELLOW + "Sr No."      + Fore.RESET,
                                    Fore.YELLOW + "Schema Name" + Fore.RESET,
                                    Fore.YELLOW + "Table Name"  + Fore.RESET,
                                ]
                                tbl_data = [
                                    [Fore.GREEN + str(t_idx) + Fore.RESET,
                                     Fore.GREEN + t_schema   + Fore.RESET,
                                     Fore.GREEN + t_name     + Fore.RESET]
                                    for t_idx, (t_schema, t_name) in enumerate(tables, start=1)
                                ]
                                verboseHandle.printConsoleInfo(
                                    f"  Tables in schema '{selected_schema}' ({len(tables)} found):")
                                printTabular(None, tbl_headers, tbl_data)
                                logger.info(
                                    f"testDatasource '{sor_name}' schema '{selected_schema}' "
                                    f"tables: {[t for _, t in tables]}")

                                # Table selection → get record count
                                tbl_sel = userInputWrapper(
                                    f"  Select table number to get record count (1-{len(tables)}): "
                                ).strip()
                                if not tbl_sel.isdigit() or not (1 <= int(tbl_sel) <= len(tables)):
                                    verboseHandle.printConsoleError(
                                        "  Invalid table selection. Skipping record count.")
                                else:
                                    sel_t_schema, sel_t_name = tables[int(tbl_sel) - 1]
                                    full_table = f"{sel_t_schema}.{sel_t_name}"
                                    verboseHandle.printConsoleInfo(
                                        f"  Selected table: {full_table}")
                                    logger.info(
                                        f"testDatasource '{sor_name}' selected table: {full_table}")

                                    # Get iidrOracleAgent hostname from cluster.config
                                    oracle_agent_host = ""
                                    oracle_agent_name = ""
                                    try:
                                        oracle_nodes = config_get_iidrOracleAgent_node(
                                            "config/cluster.config")
                                        for node in oracle_nodes:
                                            h = os.getenv(node.ip) or ""
                                            if h:
                                                oracle_agent_host = h
                                                oracle_agent_name = str(node.name).strip() or h
                                                break
                                    except Exception as ex:
                                        logger.warning(
                                            f"testDatasource iidrOracleAgent config error: {ex}")

                                    if not oracle_agent_host:
                                        verboseHandle.printConsoleError(
                                            "  No iidrOracleAgent host found in cluster.config")
                                    else:
                                        oracle_host    = str(readValuefromAppConfig("app.cdc.datasource.tns.host") or "").strip()
                                        oracle_port    = str(readValuefromAppConfig("app.cdc.datasource.tns.port") or "1521").strip()
                                        oracle_service = str(readValuefromAppConfig("app.cdc.datasource.tns.service") or "").strip()
                                        oracle_user    = str(readValuefromAppConfig("app.cdc.datasource.oracle.username") or "").strip()
                                        conn_str = (
                                            f"{username}/{password}"
                                            f"@//{oracle_host}:{oracle_port}/{oracle_service}"
                                        )

                                        sql_query    = f"SELECT COUNT(*) FROM {full_table};"
                                        sqlplus_cmd  = f"sqlplus {conn_str}"
                                        su_cmd       = f"su - {oracle_user}"
                                        # verboseHandle.printConsoleInfo(
                                        #     "  [Oracle CMD] Commands to be executed:")
                                        # verboseHandle.printConsoleInfo(
                                        #     f"    1 - ssh {oracle_agent_host}")
                                        # verboseHandle.printConsoleInfo(
                                        #     f"    2 - {su_cmd}")
                                        # verboseHandle.printConsoleInfo(
                                        #     f"    3 - {sqlplus_cmd}")
                                        # verboseHandle.printConsoleInfo(
                                        #     f"    4 - {sql_query}")
                                        # logger.info(
                                        #     f"testDatasource: SSH={oracle_agent_host} "
                                        #     f"su={su_cmd} sqlplus={sqlplus_cmd} query={sql_query}")

                                        try:
                                            # Step 1: SSH to oracle_agent_host
                                            # Step 2: su - oracle, then run sqlplus (step 3)
                                            # Step 4: feed SQL query via stdin to sqlplus
                                            remote_cmd = f'su - {oracle_user} -c "{sqlplus_cmd}"'
                                            pem_file = str(readValuefromAppConfig("cluster.pemFile") or "").strip()
                                            use_pem  = str(readValuefromAppConfig("cluster.usingPemFile") or "").strip()
                                            if use_pem == 'True' and pem_file:
                                                ssh_args = ['ssh', '-i', pem_file,
                                                            f'root@{oracle_agent_host}',
                                                            remote_cmd]
                                            else:
                                                ssh_args = ['ssh', oracle_agent_host, remote_cmd]

                                            logger.info(f"testDatasource SSH args: {ssh_args}")
                                            proc = subprocess.Popen(
                                                ssh_args,
                                                stdin=subprocess.PIPE,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE,
                                                universal_newlines=True
                                            )
                                            sql_input = f"{sql_query}\nEXIT;\n"
                                            sql_output, sql_err = proc.communicate(input=sql_input)
                                            sql_output = (sql_output or "").strip()
                                            if sql_err:
                                                logger.warning(f"sqlplus stderr: {sql_err.strip()!r}")
                                            logger.info(f"sqlplus output: {sql_output!r}")

                                            count = "N/A"
                                            for line in sql_output.splitlines():
                                                if re.match(r'^\d+$', line.strip()):
                                                    count = int(line.strip())
                                                    break

                                            if count == "N/A":
                                                # verboseHandle.printConsoleInfo(
                                                #     "  [Oracle] Count N/A — retrying with schema-based connection...")
                                                conn_str    = f"{username}/{password}@{sel_t_schema}"
                                                sqlplus_cmd = f"sqlplus {conn_str}"
                                                remote_cmd  = f'su - {oracle_user} -c "{sqlplus_cmd}"'
                                                if use_pem == 'True' and pem_file:
                                                    ssh_args = ['ssh', '-i', pem_file,
                                                                f'root@{oracle_agent_host}',
                                                                remote_cmd]
                                                else:
                                                    ssh_args = ['ssh', oracle_agent_host, remote_cmd]
                                                # verboseHandle.printConsoleInfo(
                                                #     "  [Oracle CMD] Commands to be executed:")
                                                # verboseHandle.printConsoleInfo(
                                                #     f"    1 - ssh {oracle_agent_host}")
                                                # verboseHandle.printConsoleInfo(
                                                #     f"    2 - {su_cmd}")
                                                # verboseHandle.printConsoleInfo(
                                                #     f"    3 - {sqlplus_cmd}")
                                                # verboseHandle.printConsoleInfo(
                                                #     f"    4 - {sql_query}")
                                                # logger.info(
                                                #     f"testDatasource retry: SSH={oracle_agent_host} "
                                                #     f"su={su_cmd} sqlplus={sqlplus_cmd} query={sql_query}")
                                                proc2 = subprocess.Popen(
                                                    ssh_args,
                                                    stdin=subprocess.PIPE,
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE,
                                                    universal_newlines=True
                                                )
                                                sql_output2, sql_err2 = proc2.communicate(
                                                    input=sql_input)
                                                sql_output2 = (sql_output2 or "").strip()
                                                if sql_err2:
                                                    logger.warning(
                                                        f"sqlplus stderr (retry): {sql_err2.strip()!r}")
                                                logger.info(
                                                    f"sqlplus output (retry): {sql_output2!r}")
                                                for line in sql_output2.splitlines():
                                                    if re.match(r'^\d+$', line.strip()):
                                                        count = int(line.strip())
                                                        break

                                            count_headers = [
                                                Fore.YELLOW + "Table"         + Fore.RESET,
                                                Fore.YELLOW + "Total Records" + Fore.RESET,
                                            ]
                                            count_data = [[
                                                Fore.GREEN + full_table  + Fore.RESET,
                                                Fore.GREEN + str(count)  + Fore.RESET,
                                            ]]
                                            printTabular(None, count_headers, count_data)
                                            logger.info(
                                                f"testDatasource '{sor_name}' "
                                                f"table '{full_table}' count: {count}")

                                        except Exception as ce:
                                            verboseHandle.printConsoleError(
                                                f"  [Oracle] SSH error getting count: {ce}")
                                            logger.error(
                                                f"testDatasource COUNT(*) SSH error: {ce}")
                            else:
                                verboseHandle.printConsoleWarning(
                                    f"  No tables found in schema '{selected_schema}'.")
                                logger.warning(
                                    f"testDatasource '{sor_name}' schema '{selected_schema}' has no tables")

                        except requests.exceptions.HTTPError as the:
                            verboseHandle.printConsoleError(
                                f"  [ERROR] Failed to fetch tables for schema '{selected_schema}': {the}")
                            logger.error(f"testDatasource '{sor_name}' tables HTTP error: {the}")
                        except requests.exceptions.ConnectionError as tce:
                            verboseHandle.printConsoleError(
                                f"  [ERROR] Cannot reach tables API for '{sor_name}': {tce}")
                            logger.error(f"testDatasource '{sor_name}' tables connection error: {tce}")
                        except Exception as te:
                            verboseHandle.printConsoleError(
                                f"  [ERROR] Unexpected error fetching tables for '{sor_name}': {te}")
                            logger.error(f"testDatasource '{sor_name}' tables unexpected error: {te}")
                else:
                    verboseHandle.printConsoleWarning(
                        f"  No schemas found for datasource '{sor_name}'.")
                    logger.warning(f"testDatasource '{sor_name}' schemas list is empty")

            except requests.exceptions.HTTPError as he:
                verboseHandle.printConsoleError(
                    f"  [ERROR] Failed to fetch schemas for '{sor_name}': {he}")
                logger.error(f"testDatasource '{sor_name}' schemas HTTP error: {he}")
            except requests.exceptions.ConnectionError as sce:
                verboseHandle.printConsoleError(
                    f"  [ERROR] Cannot reach schemas API for '{sor_name}': {sce}")
                logger.error(f"testDatasource '{sor_name}' schemas connection error: {sce}")
            except Exception as se:
                verboseHandle.printConsoleError(
                    f"  [ERROR] Unexpected error fetching schemas for '{sor_name}': {se}")
                logger.error(f"testDatasource '{sor_name}' schemas unexpected error: {se}")

    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle CDC -> Datasource -> Test Connection')
    logger.info('Menu -> DataEngine -> Oracle CDC -> Datasource -> Test Connection')
    testDatasourceConnections()
