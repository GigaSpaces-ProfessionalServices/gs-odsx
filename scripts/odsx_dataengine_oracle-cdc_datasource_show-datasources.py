import os
import subprocess
import csv
import io
from scripts.logManager import LogManager
from colorama import Fore
from utils.odsx_print_tabular_data import printTabular
from utils.ods_cluster_config import config_get_dataIntegration_nodes
from utils.ods_ssh import executeRemoteCommandAndGetOutputValuePython36

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


def handleException(e):
    verboseHandle.printConsoleInfo("handleException()")
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


def showDatasources():
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
            [f'{rootpath}dihctl', '-e', 'dev', 'show', 'datasources', '--format', 'csv'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )
        reader = csv.DictReader(io.StringIO(result.stdout))
        datasources = list(reader)

        if not datasources:
            verboseHandle.printConsoleWarning("No datasource available.")
            return

        sample = datasources[0] if datasources else {}
        col_keys = list(sample.keys())

        headers = [Fore.YELLOW + "Sr No." + Fore.RESET] + [Fore.YELLOW + k + Fore.RESET for k in col_keys]

        dataTable = []
        for idx, ds in enumerate(datasources, start=1):
            row = [Fore.GREEN + str(idx) + Fore.RESET]
            for k in col_keys:
                row.append(Fore.GREEN + ds.get(k, "") + Fore.RESET)
            dataTable.append(row)

        printTabular(None, headers, dataTable)

    except Exception as e:
        handleException(e)


if __name__ == '__main__':
    verboseHandle.printConsoleWarning('Menu -> DataEngine -> Oracle CDC Show Datasources')
    logger.info('Menu -> DataEngine -> Oracle CDC Show Datasources')
    showDatasources()
