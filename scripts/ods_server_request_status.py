# to quiesce space
import os
import time

import requests

from scripts.logManager import LogManager

verboseHandle = LogManager(os.path.basename(__file__))
logger = verboseHandle.logger


# curl -X POST --header 'Content-Type: application/json' --header 'Accept: text/plain' 'http://localhost:8090/v2/pus/demo/quiesce'

#    restManagerHost = "http://localhost:8090/v2/hosts"
# resp = requests.get(restManagerHost, headers={'Accept': 'application/json'})


def _url(host, port, requestId):
    return 'http://' + host + ':' + port + '/v2/requests/' + requestId


def getRequestStatus(requestId, host="localhost", verbose=False):
    if verbose:
        verboseHandle.setVerboseFlag()
    # print(requestId)
    # requestId = userInputWrapper("Enter request Id: ")
    response = requests.get(_url(host, "8090", requestId), headers={'Accept': 'application/json'})
    # print(response)
    if response.status_code == 200:
        if response.json()["status"] == "successful":
            logger.info("Request processed successfully for requestId " + requestId)
            return "Request processed successfully"
        elif response.json()["status"] == "running":
            logger.info("Request is executing now [ " + str(response.json()["description"]) + " ]")
            time.sleep(5)
            getRequestStatus(requestId,host,verbose)
        else:
            logger.error("Request failed with error " + str(response.json()["error"]))
            return "Request failed with error " + response.json()["error"]
    '''elif response.status_code == 404 :
        print("Could not find request by id.")
        return "Could not find request by id"
    else:
        print("Error! Please try again.")
        return "Error! Please try again."
    '''
