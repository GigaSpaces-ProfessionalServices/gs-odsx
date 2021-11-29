#!/usr/bin/env python3
import requests,json
from os import  path

def _url(host="localhost", port="8090", spaceName="demo"):
    return 'http://' + host + ':' + port + '/v2/pus/'

def ods_space_deploy_pu(host,puPath):
    #host='18.117.114.238'
    #puPath="https://tapangigaspaces.s3.us-east-2.amazonaws.com/odsx/BillBuddy_Space.jar"
    data = json.dumps({
        "resource": puPath,
        "topology": {
            "schema": "partitioned",
            "partitions": 1,
            "backupsPerPartition": 0
        },
        "name": "space"
    })
    if(path.exists(puPath)):
        print('YES')
    response = requests.post(_url(host, '8090'), headers={'Accept': 'text/plain','Content-Type': 'application/json'} ,data=data )
    print(response.status_code)
    print(response.content)
    print(response.headers)

if __name__ == "__main__":
    ods_space_deploy_pu(host='',puPath='')
