#!/usr/bin/env python3

import requests
import subprocess


def postJSONRequest(jsonData, url):
    jsonHeaders = {
        'Content-type': 'application/json',
    }
    r = requests.post(url, headers=jsonHeaders, data=jsonData)
    return r.text


# curl -X PUT --header 'Content-Type: multipart/form-data' --header 'Accept: text/plain' -F "file=@demoSpace.jar" "http://localhost:8090/v2/pus/resources"
def uploadFile(fileName, url):
    try:
        filesToUpload = {"file": open(fileName, 'rb')}
        headers = {'Accept': 'text/plain'}  # , 'Slug': fileName}
        r = requests.put(url, files=filesToUpload, headers=headers)
        print(r.text)
        print(r.json)
        print(r)
    except:
        return "Exception while uploading '" + fileName + "'"

    return r.text


def uploadFileUsingCurl(fileName, url):
    cmd = ["curl", "-X", "PUT", "--header", "Content-Type: multipart/form-data", "--header", "Accept: text/plain", "-F",
           "file=@" + fileName, url]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output, error = process.communicate()

    encoding = 'utf-8'

    return output.decode(encoding)

# if __name__=="__main__":
#    print(uploadFile("/home/jay/work/gigaspace/bofLeumi/intellij-ide/odsx-Bank-Leumi/scripts/demoSpace.jar",
#                     "http://localhost:8090/v2/pus/resources"))
