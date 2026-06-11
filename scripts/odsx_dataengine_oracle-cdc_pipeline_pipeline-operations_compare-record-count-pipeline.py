#!/usr/bin/env python3

import os
import re
import subprocess
import requests
import csv
import io
from colorama import Fore
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_dataIntegration_nodes, config_get_manager_node, config_get_iidrOracleAgent_node
from utils.ods_app_config import readValuefromAppConfig
from utils.odsx_keypress import userInputWrapper
from utils.odsx_print_tabular_data import printTabular
from utils.ods_ssh import executeRemoteCommandAndGetOutputValuePython36
from utils.odsx_db2feeder_utilities import getUsernameByHost, getPasswordByHost

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger

GS_MANAGER_PORT = "8090"


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


def getManagerHost():
    managerNodes = config_get_manager_node()
    for node in managerNodes:
        host = os.getenv(node.ip)
        if host:
            return host
    return ""


def getSpaceTypeCounts(managerHost, spaceName):
    """Fetch all type entry counts for a space using objectsTypeInfo endpoint.
    Returns a dict of {objectName: entries}."""
    try:
        import json as _json
        username = str(getUsernameByHost())
        password = str(getPasswordByHost())
        url = f"http://{managerHost}:{GS_MANAGER_PORT}/v2/spaces/{spaceName}/objectsTypeInfo"
        curl_cmd = ["curl", "-s", "-X", "GET", "--header", "Accept: application/json",
                    "-u", f"{username}:{password}", url]
        # verboseHandle.printConsoleInfo("curl cmd: curl -s -X GET --header 'Accept: application/json' -u <credentials> " + url)
        result = subprocess.run(curl_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if result.returncode != 0:
            verboseHandle.printConsoleError(f"  [Space] curl failed: {result.stderr}")
            return {}
        raw = result.stdout.strip()
        # verboseHandle.printConsoleInfo("  [Space] curl response: " + raw)
        if not raw or raw.startswith("<"):
            verboseHandle.printConsoleError("  [Space] curl returned HTML instead of JSON — check port/path")
            return {}
        try:
            data = _json.loads(raw)
        except Exception:
            verboseHandle.printConsoleError(f"  [Space] non-JSON response: {raw[:300]!r}")
            return {}
        counts = {}
        for item in data.get("objectTypesMetadata", []):
            obj_name = item.get("objectName", "")
            entries = item.get("entries", 0)
            if obj_name:
                counts[obj_name] = entries
                # verboseHandle.printConsoleInfo(f"  [Space] objectName={obj_name}  entries={entries}")
        logger.info(f"Space type counts for {spaceName}: {counts}")
        verboseHandle.printConsoleInfo(f"  [Space] found {len(counts)} type(s)")
        return counts
    except Exception as e:
        verboseHandle.printConsoleError(f"  [Space] error: {e}")
        logger.warning(f"getSpaceTypeCounts error: {e}")
        return {}


def getDatasourceCredentials(iidrHost, sorName):
    """Fetch connection details from the DI manager datasource API for the given sorName."""
    try:
        resp = requests.get(f"http://{iidrHost}:6080/api/v1/datasource/",
                            headers={"accept": "*/*"},
                            proxies={"http": None, "https": None}, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"Could not fetch datasources: {resp.status_code}")
            return None
        for ds in resp.json():
            if str(ds.get("sorName", "")).upper() == str(sorName).upper():
                return ds
        logger.warning(f"Datasource '{sorName}' not found in DI manager.")
        return None
    except Exception as e:
        logger.warning(f"getDatasourceCredentials error: {e}")
        return None


def _parseOracleConnFromUrl(url):
    """
    Parse host, port, service from a datasource URL.
    Handles:
      - iidr://host:port          -> host, port=1521 (Oracle default), service=""
      - jdbc:oracle:thin:@host:port:sid
      - jdbc:oracle:thin:@//host:port/service
    Returns (host, port, service).
    """
    url = str(url).strip()
    # jdbc:oracle:thin:@//host:port/service
    m = re.match(r'jdbc:oracle:thin:@//([^:/]+):(\d+)/([^/?\s]+)', url, re.IGNORECASE)
    if m:
        return m.group(1), m.group(2), m.group(3)
    # jdbc:oracle:thin:@host:port:sid
    m = re.match(r'jdbc:oracle:thin:@([^:/]+):(\d+):([^/?\s]+)', url, re.IGNORECASE)
    if m:
        return m.group(1), m.group(2), m.group(3)
    # iidr://host:port  or  iidr://host:port/service
    m = re.match(r'iidr://([^:/]+)(?::(\d+))?(?:/([^/?\s]*))?', url, re.IGNORECASE)
    if m:
        host = m.group(1)
        service = m.group(3) or ""
        return host, "1521", service
    # fallback: treat entire URL as host
    return url, "1521", ""


def getOracleTables(iidrHost, sorName, schema):
    """SSH to the Oracle host and return all table names for the given schema."""
    ds = getDatasourceCredentials(iidrHost, sorName)

    ds_url = (ds.get("url", "") if ds else "")
    oracle_host, oracle_port, service = _parseOracleConnFromUrl(ds_url) if ds_url else ("", "1521", "")

    username = str(ds.get("username", "") if ds else "").strip()
    password = str(ds.get("password", "") if ds else "").strip()
    if not username:
        username = str(readValuefromAppConfig("app.cdc.datasource.username")).strip()
    if not password:
        password = str(readValuefromAppConfig("app.cdc.datasource.password")).strip()
    oracle_user = str(readValuefromAppConfig("app.cdc.datasource.oracle.username") or "").strip()

    if not service and oracle_host:
        try:
            sid_output = executeRemoteCommandAndGetOutputValuePython36(
                oracle_host, 'root', f"su - {oracle_user} -c 'echo $ORACLE_SID'")
            oracle_sid = str(sid_output).strip()
            if oracle_sid:
                service = oracle_sid
        except Exception:
            pass

    if not oracle_host:
        verboseHandle.printConsoleError("  [Oracle] cannot parse host from datasource url")
        return []

    if service:
        conn_str = f"{username}/{password}@{oracle_host}:{oracle_port}/{service}"
    else:
        conn_str = f"{username}/{password}"

    sql_cmd = (
        f"printf \"SELECT table_name FROM all_tables WHERE owner='{ schema.upper() }' "
        f"ORDER BY table_name;\\nEXIT;\\n\" | sqlplus -S {conn_str}"
    )
    remote_cmd = f"su - {oracle_user} -c \"{sql_cmd}\""
    verboseHandle.printConsoleInfo(f"  [Oracle] listing tables for schema {schema.upper()} on {oracle_host}")
    logger.info(f"getOracleTables SSH to {oracle_host}: {remote_cmd}")
    try:
        output = executeRemoteCommandAndGetOutputValuePython36(oracle_host, 'root', remote_cmd)
        output = str(output).strip()
        logger.info(f"Oracle tables output: {output!r}")
        tables = []
        for line in output.splitlines():
            line = line.strip()
            if (not line or line.upper() == "TABLE_NAME"
                    or line.startswith("-")
                    or "row" in line.lower()
                    or "ERROR" in line
                    or "ORA-" in line
                    or "SP2-" in line):
                continue
            if re.match(r'^[A-Z0-9_$#]+$', line.upper()):
                tables.append(line.upper())
        return tables
    except Exception as e:
        verboseHandle.printConsoleError(f"  [Oracle] SSH error listing tables: {e}")
        logger.warning(f"getOracleTables SSH error: {e}")
        return []


def getOracleCount(iidrHost, sorName, schema, table):
    """SSH to iidrOracleAgent, su - oracle, run sqlplus, feed SELECT COUNT(*)."""
    username = str(readValuefromAppConfig("app.cdc.datasource.username") or "").strip()
    password = str(readValuefromAppConfig("app.cdc.datasource.password") or "").strip()
    oracle_user = str(readValuefromAppConfig("app.cdc.datasource.oracle.username") or "").strip()

    # Get iidrOracleAgent: IP for SSH, name (hostname) for commands
    oracle_agent_ip   = ""
    oracle_agent_name = ""
    try:
        oracle_nodes = config_get_iidrOracleAgent_node("config/cluster.config")
        for node in oracle_nodes:
            ip = os.getenv(node.ip) or ""
            if ip:
                oracle_agent_ip   = ip
                oracle_agent_name = str(node.name).strip() or ip
                break
    except Exception as ex:
        logger.warning(f"getOracleCount iidrOracleAgent config error: {ex}")

    if not oracle_agent_ip:
        verboseHandle.printConsoleError("  [Oracle] No iidrOracleAgent host found in cluster.config")
        return "N/A"

    full_table   = f"{schema}.{table}" if schema else table
    oracle_agent_name = str(readValuefromAppConfig("app.cdc.datasource.tns.host") or "").strip()
    oracle_port       = str(readValuefromAppConfig("app.cdc.datasource.tns.port") or "1521").strip()
    oracle_service    = str(readValuefromAppConfig("app.cdc.datasource.tns.service") or "").strip()
    conn_str     = f"{username}/{password}@//{oracle_agent_name}:{oracle_port}/{oracle_service}"
    sql_query    = f"SELECT COUNT(*) FROM {full_table};"
    sqlplus_cmd  = f"sqlplus {conn_str}"

    # verboseHandle.printConsoleInfo("  [Oracle CMD] Commands to be executed:")
    # verboseHandle.printConsoleInfo(f"    1 - ssh {oracle_agent_ip}")
    # verboseHandle.printConsoleInfo(f"    2 - su - oracle")
    # verboseHandle.printConsoleInfo(f"    3 - {sqlplus_cmd}")
    # verboseHandle.printConsoleInfo(f"    4 - {sql_query}")
    logger.info(f"getOracleCount SSH={oracle_agent_ip} sqlplus={sqlplus_cmd} query={sql_query}")

    try:
        # Step 1: SSH to oracle_agent_ip
        # Step 2: su - oracle, step 3: sqlplus (via su -c)
        # Step 4: feed SQL via stdin
        remote_cmd = f'su - {oracle_user} -c "{sqlplus_cmd}"'
        pem_file = str(readValuefromAppConfig("cluster.pemFile") or "").strip()
        use_pem  = str(readValuefromAppConfig("cluster.usingPemFile") or "").strip()
        if use_pem == 'True' and pem_file:
            ssh_args = ['ssh', '-i', pem_file, f'root@{oracle_agent_ip}', remote_cmd]
        else:
            ssh_args = ['ssh', oracle_agent_ip, remote_cmd]

        proc = subprocess.Popen(
            ssh_args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        sql_output, sql_err = proc.communicate(input=f"{sql_query}\nEXIT;\n")
        sql_output = (sql_output or "").strip()
        if sql_err:
            logger.warning(f"getOracleCount stderr: {sql_err.strip()!r}")
        logger.info(f"Oracle sqlplus output: {sql_output!r}")

        count = "N/A"
        for line in sql_output.splitlines():
            if re.match(r'^\d+$', line.strip()):
                count = int(line.strip())
                break

        if count == "N/A":
            logger.info("getOracleCount: retrying with schema-based connection...")
            conn_str    = f"{username}/{password}@{schema}"
            sqlplus_cmd = f"sqlplus {conn_str}"
            remote_cmd  = f'su - {oracle_user} -c "{sqlplus_cmd}"'
            if use_pem == 'True' and pem_file:
                ssh_args = ['ssh', '-i', pem_file, f'root@{oracle_agent_ip}', remote_cmd]
            else:
                ssh_args = ['ssh', oracle_agent_ip, remote_cmd]
            logger.info(
                f"getOracleCount retry SSH={oracle_agent_ip} sqlplus={sqlplus_cmd} query={sql_query}")
            proc2 = subprocess.Popen(
                ssh_args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            sql_output2, sql_err2 = proc2.communicate(input=f"{sql_query}\nEXIT;\n")
            sql_output2 = (sql_output2 or "").strip()
            if sql_err2:
                logger.warning(f"getOracleCount stderr (retry): {sql_err2.strip()!r}")
            logger.info(f"Oracle sqlplus output (retry): {sql_output2!r}")
            for line in sql_output2.splitlines():
                if re.match(r'^\d+$', line.strip()):
                    count = int(line.strip())
                    break

        return count
    except Exception as e:
        verboseHandle.printConsoleError(f"  [Oracle] SSH error: {e}")
        logger.warning(f"getOracleCount SSH error: {e}")
        return "N/A"


def compareRecordCountPipelineMenu():
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
        login_result = subprocess.run(login_cmd, shell=True, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, universal_newlines=True)
        if login_result.returncode != 0:
            verboseHandle.printConsoleError(f"Login failed: {login_result.stderr}")
            return

        result = subprocess.run(
            [f'{rootpath}dihctl', '-e', 'dev', 'show', 'pipelines', '--format', 'csv'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )
        reader = csv.DictReader(io.StringIO(result.stdout))
        pipelines = list(reader)

        if not pipelines:
            verboseHandle.printConsoleWarning("No pipelines available.")
            return

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

        selection = userInputWrapper(f"Select pipeline number to compare (1-{len(pipelines)}): ").strip()
        if not selection.isdigit() or not (1 <= int(selection) <= len(pipelines)):
            verboseHandle.printConsoleError("Invalid selection.")
            return

        selected = pipelines[int(selection) - 1]
        selected_name = selected.get("name", "").strip()
        space_name = selected.get("spaceName", "").strip()
        sor_name = selected.get("sorName", "ORACLE").strip()
        selected_status = selected.get("status", "").strip().upper()
        verboseHandle.printConsoleInfo(f"Selected pipeline: {selected_name}")
        logger.info(f"Selected pipeline: {selected_name}")
        if selected_status == "ERROR":
            verboseHandle.printConsoleError(f"Pipeline Is in ERROR state Cannot perform compare operation")
            logger.error(f"Pipeline '{selected_name}' is in ERROR state.")
            return

        # Fetch table pipelines for the selected pipeline
        pl_response = requests.get(f"http://{iidrHost}:6080/api/v1/pipeline/",
                                   headers={"accept": "*/*"},
                                   proxies={"http": None, "https": None})
        pl_list = pl_response.json()
        pipeline_id = next((pl["pipelineId"] for pl in pl_list if pl.get("name") == selected_name), None)
        if not pipeline_id:
            verboseHandle.printConsoleError(f"Pipeline ID not found for: {selected_name}")
            return

        tables_response = requests.get(
            f"http://{iidrHost}:6080/api/v1/pipeline/{pipeline_id}/tablepipeline",
            headers={"accept": "*/*"},
            proxies={"http": None, "https": None}
        )
        tables_response.raise_for_status()
        table_pipelines = tables_response.json()

        if not table_pipelines:
            verboseHandle.printConsoleWarning(f"No tables found for pipeline '{selected_name}'.")
            return

        managerHost = getManagerHost()
        verboseHandle.printConsoleInfo(f"GigaSpaces manager host: {managerHost or 'NOT FOUND'}")
        if not managerHost:
            verboseHandle.printConsoleWarning("No GigaSpaces manager host found. Space counts will show N/A.")

        verboseHandle.printConsoleInfo(f"\nFetching counts for pipeline '{selected_name}' (space: {space_name})...")

        space_type_counts = getSpaceTypeCounts(managerHost, space_name) if managerHost else {}

        # Collect unique schemas in this pipeline and list available Oracle tables per schema
        unique_schemas = sorted({
            tp.get("sourceSchema", "").upper()
            for tp in table_pipelines
            if tp.get("sourceSchema", "")
        })
        for schema_name in unique_schemas:
            verboseHandle.printConsoleInfo(f"\n  [Oracle] Tables available in schema {schema_name}:")
            oracle_tables = getOracleTables(iidrHost, sor_name, schema_name)
            # if oracle_tables:
            #     for tbl in oracle_tables:
            #         verboseHandle.printConsoleInfo(f"    - {schema_name}.{tbl}")
            # else:
            #     verboseHandle.printConsoleWarning(f"  [Oracle] Could not retrieve table list for schema {schema_name}")

        cmp_headers = [
            Fore.YELLOW + "Sr No."          + Fore.RESET,
            Fore.YELLOW + "Space Type Name" + Fore.RESET,
            Fore.YELLOW + "Oracle Table"    + Fore.RESET,
            Fore.YELLOW + "Space Count"     + Fore.RESET,
            Fore.YELLOW + "Oracle Count"    + Fore.RESET,
            Fore.YELLOW + "Match"           + Fore.RESET,
            ]
        cmp_data = []
        # verboseHandle.printConsoleInfo(f"  [Space] type={space_type_counts}")

        for idx, tp in enumerate(table_pipelines, start=1):
            space_type = tp.get("spaceTypeName", "")
            source_schema = tp.get("sourceSchema", "")
            source_table = tp.get("sourceTable", tp.get("sourceTables", ""))

            # verboseHandle.printConsoleInfo("Source table - " + source_table + " - space_type_counts - " + str(space_type_counts.get(str(source_table), "N/A")))

            # verboseHandle.printConsoleInfo(f"  [Space] type={space_type}")
            oracle_label = f"{source_schema}.{source_table}" if source_schema else source_table
            space_count = space_type_counts.get(oracle_label, space_type_counts.get(space_type, "N/A"))
            # verboseHandle.printConsoleInfo(f"  [Space] lookup key={oracle_label}  space_count={space_count}")
            oracle_count = getOracleCount(iidrHost, sor_name, source_schema, source_table)

            if isinstance(space_count, int) and isinstance(oracle_count, int):
                match_str = Fore.GREEN + "True" + Fore.RESET if space_count == oracle_count else Fore.RED + "False" + Fore.RESET
                space_color = Fore.GREEN if space_count == oracle_count else Fore.RED
                oracle_color = Fore.GREEN if space_count == oracle_count else Fore.RED
            else:
                match_str = Fore.YELLOW + "False" + Fore.RESET
                space_color = Fore.YELLOW
                oracle_color = Fore.YELLOW

            cmp_data.append([
                Fore.GREEN  + str(idx)                     + Fore.RESET,
                Fore.GREEN  + str(space_type)              + Fore.RESET,
                Fore.GREEN  + str(oracle_label)            + Fore.RESET,
                space_color + str(space_count)             + Fore.RESET,
                oracle_color + str(oracle_count)           + Fore.RESET,
                match_str,
                ])

        printTabular(None, cmp_headers, cmp_data)

    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle CDC Compare Record Count Pipeline')
    logger.info('Menu -> DataEngine -> Oracle CDC Compare Record Count Pipeline')
    compareRecordCountPipelineMenu()
