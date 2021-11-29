import os
import subprocess

from scripts.logManager import LogManager
#from scripts.odsx_servers_cdc_install import unquiesceSpace

logerHandle = LogManager(os.path.basename(__file__))
logger = logerHandle

cr8FilePath = "/home/dbsh/cr8/latest_cr8/utils/CR8_ctl.sh"

logger.printConsoleInfo("Running test cases for installing CDC")

# Test - 1 Provide target server with unreachable IP
# print("Starting Test - 1 Install CDC on a target server with unreachable IP")
# if unquiesceSpace("unreachable") != 202:
#     logger.printConsoleInfo("Test passed")
# else:
#     logger.printConsoleError("Test failed")

# # Test - 2 Provide target server with correct IP
# print("Starting Test - 2 Install CDC on a target server with reachable IP")
# if unquiesceSpace("localhost") == 202:
#     logger.printConsoleInfo("Test passed")
# else:
#     logger.printConsoleError("Test failed")

cmd = ["scripts/servers_cdc_install.sh"]
process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
output, error = process.communicate()
#encoding = 'utf-8'
#output.decode(encoding)

# Test - 1 Install CDC
print("Starting Test - 1 Check that CR8 is installed or not")
if os.path.isfile(cr8FilePath):
    logger.printConsoleInfo("Test passed")
else:
    logger.printConsoleError("Test failed")


cmd = ["scripts/servers_cdc_uninstall.sh"]
process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
output, error = process.communicate()
#encoding = 'utf-8'
#output.decode(encoding)

# Test - 2 Uninstall CDC
print("Starting Test - 2 Check that CR8 is uninstalled or not")
if os.path.isfile(cr8FilePath) != True:
    logger.printConsoleInfo("Test passed")
else:
    logger.printConsoleError("Test failed")

print("All test completed")
