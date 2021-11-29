# Test - 1 Start space after stop
from scripts.odsx_space_stop import quiesceSpace

print("Running test cases for stop server space")
print("Starting Test - 1 Start space after stop without dry run")
if quiesceSpace("demo", "localhost", "false") == 202:
    print("test passed")
else:
    print("test failed")

# Test - 2 Start with dryrun
print("Starting Test - 2 Start with dry run")
if quiesceSpace("demo", "localhost", "true") == 202:
    print("test passed")
else:
    print("test failed")

# Test - 3 Start space with wrong space name
print("Starting Test - 3 Start space with wrong space name")
if quiesceSpace("demo1", "localhost", "false") != 202:
    print("test passed")
else:
    print("test failed")

print("All test completed")
