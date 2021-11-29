from scripts.odsx_utilities_copyfiles import copyFile
from scripts.odsx_utilities_copyfiles import validateHost
from utils.ods_ssh import executeRemoteCommandAndGetOutput

print("Running test cases for copy file utility")
# Test - 1 validating connection to host
print("Starting Test - 1 validating connection to host")
destHost = "52.30.228.173"
srcPath = "unit-test/testFileCopyUtility.txt"
destPath = "/home/ec2-user"
if validateHost(destHost):
    print("test passed")
else:
    print("test failed")

# Test - 2 copying correct file to host
print("Starting Test - 2 copying correct file to host")
destHost = ["52.30.228.173"]
if copyFile(destHost, srcPath, destPath, True):
    print("test passed")
    print("removing copied file from the host")
    executeRemoteCommandAndGetOutput(destHost[0], "ec2-user", "rm " + destPath + "/testFileCopyUtility.txt")
    print("removed")
else:
    print("test failed")

# Test - 3 copying incorrect file to host
print("Starting Test - 3 copying incorrect file to host")
srcPath = "unit-test/testFileCopyUtility.txt1"
if not copyFile(destHost, srcPath, destPath, True):
    print("test passed")
else:
    print("test failed")
