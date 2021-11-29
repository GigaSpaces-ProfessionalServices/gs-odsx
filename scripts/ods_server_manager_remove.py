from utils.ods_server_get import getServerDetails

resp = getServerDetails();
print(resp.json())
