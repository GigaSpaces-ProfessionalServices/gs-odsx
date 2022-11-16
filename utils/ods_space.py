#!/usr/bin/env python3
from distutils.log import debug
from math import floor
import subprocess
from colorama import Back, Fore, Style
import requests,json
from os import  path
from utils.ods_app_config import readValuefromAppConfig
from requests.auth import HTTPBasicAuth
from utils.ods_ssh import executeRemoteCommandAndGetOutput

defualt_port = '8090'


def _url(host="localhost", port="8090", spaceName="demo"):
    return 'http://' + host + ':' + port + '/v2/pus/'

def ods_space_deploy_pu(host,puPath):
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


def list_types(manager,space_name,isSecure=False,username=None,password=None):
    url = f"http://{manager}:{defualt_port}/v2/spaces/{space_name}/instances/{space_name}~1_1/statistics/types"
    if(isSecure==True and username is not None and password is not None):
        response_data = requests.get(url,auth = HTTPBasicAuth(username, password), verify=False)
    else:
        response_data = requests.get(url, verify=False)
    types = []
    excluded = ['java.lang.Object']
    for _t in response_data.json():
        if _t in excluded:
            continue
        types.append(_t)
    return types


def build_sqlite_query(types):
    query = "select ("
    for t in types:
        query += f"select count(*) from '{t}') + ("
        #query += f'select count(*) from "\''
        #query +=t
        #query +="'\") + ("
    return query.rstrip(' + (')

def get_sqlite_object_count(manager, the_host, space_name, instance_id,isSecure=False,username=None,password=None):
    sqlite_cmd = f"sqlite3 /dbagigadata/tiered-storage/bllspace/sqlite_db_{space_name}_container{instance_id}:{space_name}"
    
    select_cmd = f"'{build_sqlite_query(list_types(manager, space_name,isSecure,username,password))}'"
    remote_cmd = f'"{sqlite_cmd} {select_cmd}"'
    #print("remote_cmd => "+str(remote_cmd))
    sh_cmd = f"ssh {the_host} {remote_cmd}"

    pemFileName = readValuefromAppConfig("cluster.pemFile")
    isConnectUsingPem = readValuefromAppConfig("cluster.usingPemFile")
    if(isConnectUsingPem=='True'):
        sh_cmd = "ssh -i " + pemFileName + " root@" + the_host + " " + remote_cmd
    else:
        sh_cmd = "ssh" +" " + the_host + " " + remote_cmd
    the_response = str(subprocess.run([sh_cmd], shell=True, stdout=subprocess.PIPE).stdout)
    #print("the_response-------------->"+the_response)
    return int(the_response.strip("\\n'").strip("b'"))


def get_sqlite_id(item_id,space_name,num):
    if item_id == f"{space_name}~{num}_1":
        return f"{num}"
    if item_id == f"{space_name}~{num}_2":
        return f"{num}_1"

def getAllObjPrimaryCount(host,space_name,isSecure=False,username=None,password=None):
    headers = {'Accept': 'application/json'}
    url = f"http://{host}:{defualt_port}/v2/spaces"
    if(isSecure==True and username is not None and password is not None):
        response_data = requests.get(url, headers=headers,auth = HTTPBasicAuth(username, password), verify=False)
    else:
        response_data = requests.get(url, headers=headers, verify=False)
    #print("response_data =>"+str(response_data.json()))
    num_partitions = 0
    for space in response_data.json():
        if space['name'] == space_name:
            num_partitions = space['topology']['partitions']
    url = f"http://{host}:{defualt_port}/v2/spaces/{space_name}/instances"
    if(isSecure==True and username is not None and password is not None):
        response = requests.get(url, headers=headers,auth = HTTPBasicAuth(username, password), verify=False)
    else:
        response = requests.get(url, headers=headers, verify=False)
    p_total_count, b_total_count = 0, 0
    if num_partitions > 0:
        for num in range(1,num_partitions + 1):
            # get instances params
            primary, backup = False, False
            P = Back.BLUE + Fore.BLACK + " P " + Style.RESET_ALL
            B = Back.LIGHTWHITE_EX + Fore.BLACK + " B " + Style.RESET_ALL
            for item in response.json():
                if f"{space_name}~{num}_" in item['id']:
                    if item['mode'] == 'PRIMARY':
                        p_id = item['id']
                        p_host_id = item['hostId']
                        p_sqlite_id = get_sqlite_id(item['id'],space_name,num)
                        p_count = get_sqlite_object_count(host, p_host_id, space_name, p_sqlite_id,isSecure,username,password)
                        p_total_count += p_count
                        primary = True
        
      
    return p_total_count



def verifyPrimaryBackupObjCount(host,space_name,isSecure=False,username=None,password=None):
    headers = {'Accept': 'application/json'}
    url = f"http://{host}:{defualt_port}/v2/spaces"
    if(isSecure==True and username is not None and password is not None):
        response_data = requests.get(url, headers=headers,auth = HTTPBasicAuth(username, password), verify=False)
    else:
        response_data = requests.get(url, headers=headers, verify=False)
    num_partitions = 0
    for space in response_data.json():
        if space['name'] == space_name:
            num_partitions = space['topology']['partitions']
    url = f"http://{host}:{defualt_port}/v2/spaces/{space_name}/instances"
    if(isSecure==True and username is not None and password is not None):
        response = requests.get(url, headers=headers,auth = HTTPBasicAuth(username, password), verify=False)
    else:
        response = requests.get(url, headers=headers, verify=False)
    p_total_count, b_total_count = 0, 0
    if(num_partitions > 0):
        for num in range(1,num_partitions + 1):
            # get instances params
            primary, backup = False, False
            P = Back.BLUE + Fore.BLACK + " P " + Style.RESET_ALL
            B = Back.LIGHTWHITE_EX + Fore.BLACK + " B " + Style.RESET_ALL
            for item in response.json():
                if f"{space_name}~{num}_" in item['id']:
                    if item['mode'] == 'PRIMARY':
                        p_id = item['id']
                        p_host_id = item['hostId']
                        p_sqlite_id = get_sqlite_id(item['id'],space_name,num)
                        p_count = get_sqlite_object_count(host, p_host_id, space_name, p_sqlite_id,isSecure,username,password)
                        p_total_count += p_count
                        primary = True
                    if item['mode'] == 'BACKUP':
                        b_id = item['id']
                        b_host_id = item['hostId']
                        b_sqlite_id = get_sqlite_id(item['id'],space_name,num)
                        
                        b_count = get_sqlite_object_count(host, b_host_id, space_name, b_sqlite_id,isSecure,username,password)
                        b_total_count += b_count
                        backup = True
                if primary and backup:
                    break
            if not primary:
                p_id = 'NONE'
            if not backup:
                b_id = 'NONE'
        
            p_total_display = f"{Fore.MAGENTA}{p_total_count:,}{Style.RESET_ALL}"
            b_total_display = f"{Fore.MAGENTA}{b_total_count:,}{Style.RESET_ALL}"
            
            #print(f"{'Total number of records in PRIMARY instances:':<46}{p_total_display:<10}")
            #print(f"{'Total number of records in BACKUP instances:':<46}{b_total_display:<10}")
    if(p_total_count == b_total_count):
        return True
    
    return False
    

if __name__ == "__main__":
    ods_space_deploy_pu(host='',puPath='')
