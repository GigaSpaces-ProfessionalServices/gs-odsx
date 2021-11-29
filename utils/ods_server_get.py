# to get server information
import requests


# curl -X GET --header 'Accept: application/json' 'http://localhost:8090/v2/hosts'

#    restManagerHost = "http://localhost:8090/v2/hosts"
# resp = requests.get(restManagerHost, headers={'Accept': 'application/json'})


def getServerDetails():
    return requests.get(_url('localhost', '8090'), headers={'Accept': 'application/json'})


def _url(host, port):
    return 'http://' + host + ':' + port + '/v2/hosts'
