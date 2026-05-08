import os
import json
import requests
import subprocess
from colorama import Fore, init
from scripts.logManager import LogManager
from utils.ods_cluster_config import config_get_dataIntegration_nodes
from utils.odsx_keypress import userInputWrapper
from utils.ods_app_config import readValuefromAppConfig, getYamlFilePathInsideFolder
from utils.odsx_print_tabular_data import printTabular
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


def importPipeline(diManagerHost):
    try:
        import_path = str(readValuefromAppConfig("app.dataengine.dihctl.pipelinefolderpath"))
        if not import_path.strip():

            verboseHandle.printConsoleError("File path cannot be empty.")
            return

        if not os.path.exists(import_path):
            verboseHandle.printConsoleError(f"Path not found: {import_path}")
            return

        files = [f for f in os.listdir(import_path) if os.path.isfile(os.path.join(import_path, f))]
        if not files:
            verboseHandle.printConsoleError(f"No files found in: {import_path}")
            return

        headers = [
            Fore.YELLOW + "Sr No."    + Fore.RESET,
            Fore.YELLOW + "File Name" + Fore.RESET,
        ]
        dataTable = []
        for idx, fname in enumerate(files, start=1):
            dataTable.append([
                Fore.GREEN + str(idx) + Fore.RESET,
                Fore.GREEN + fname    + Fore.RESET,
            ])
        printTabular(None, headers, dataTable)

        selection = userInputWrapper(f"Select file(s) to import (e.g. 1 or 1-3 or 1,4,5): ").strip()
        selected_indices = set()
        for part in selection.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-", 1)
                selected_indices.update(range(int(start.strip()), int(end.strip()) + 1))
            elif part.isdigit():
                selected_indices.add(int(part))
        selected_indices = sorted(i for i in selected_indices if 1 <= i <= len(files))
        if not selected_indices:
            verboseHandle.printConsoleError("Invalid selection.")
            return

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

        for idx in selected_indices:
            selected_file = files[idx - 1]
            verboseHandle.printConsoleInfo(f"Selected file: {selected_file}")
            logger.info(f"Selected file: {selected_file}")

            selected_file_path = os.path.join(import_path, selected_file)
            import_cmd = f"{rootpath}dihctl -e dev apply -f {selected_file_path}"
            verboseHandle.printConsoleInfo(f"Running: {import_cmd}")
            logger.info(f"Running: {import_cmd}")
            import_result = subprocess.run(import_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if import_result.returncode != 0:
                verboseHandle.printConsoleError(f"Import failed for '{selected_file}': {import_result.stderr}")
                continue
            verboseHandle.printConsoleInfo(f"Import successful for '{selected_file}':\n{import_result.stdout}")
            logger.info(f"Import successful: {import_result.stdout}")


    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle CDC Import Pipeline')
    logger.info('Menu -> DataEngine -> Oracle CDC Import Pipeline')
    diManagerHost = getDIServerHost()
    if diManagerHost:
        importPipeline(diManagerHost)
    else:
        verboseHandle.printConsoleError("No DI Manager host found.")
