#!/bin/bash
# Post installation Script- GLobal Config
#########################################
di_server1=$1
iidr_host=$2
manager_host1=$3
spaceLookupGroups=$4
di_all_servers=$5

mdmUrl="$di_server1:6081"
managerUrl="$di_server1:6080"
flinkUrl="http://$di_server1:8081"
diSsubscriptionManager="http://$iidr_host:6082"
diProcessorJar="/home/gsods/di-processor/latest-di-processor/lib/job-2.3.9.jar"
bootstrapServers="$di_all_servers"
kafkaGroupId="diprocessor"
#spaceLookupGroups="xap-16.4.0"
spaceLookupLocators="$manager_host1"
########################################
echo;echo
#read -p "exec 1 Configure Flink"
echo "exec 1 Configure Flink"

# 1 Configure Flink
mycurl=$( echo -e "curl -s --location \"${mdmUrl}/api/v1/global-config/flink\" --header 'Content-Type: application/json' --data '{ \"restEndpoint\": \"${flinkUrl}\", \"diProcessorJar\": \"${diProcessorJar}\" }' |jq" )
eval $mycurl
echo;echo
#read -p "exec 2 Configure Kafka"
echo "exec 2 Configure Kafka"

# 2 Configure Kafka

mycurl=$( echo -e "curl -s --location '${mdmUrl}/api/v1/global-config/kafka' --header 'Content-Type: application/json' --data '{\"bootstrapServers\":[\"${bootstrapServers}\"],\"groupId\":\"${kafkaGroupId}\"}'")
eval $mycurl |jq

echo;echo
#read -p "exec 3 Configure Space Common"
echo "exec 3 Configure Space Common"

# 3 Configure Space Common

mycurl=$(echo -e "curl -s --location '${mdmUrl}/api/v1/global-config/space' --header 'Content-Type: application/json' --data '{\"lookupGroups\": \"${spaceLookupGroups}\",\"lookupLocators\":\"${spaceLookupLocators}\"}'")
eval $mycurl |jq

echo;echo
#read -p "exec 4 Configure DI Subscription Manager"
echo "exec 4 Configure DI Subscription Manager"

# 4 Configure DI Subscription Mananger

curl -s -X 'POST' \
  'http://'$mdmUrl'/api/v1/global-config/subscription-managers' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -d '{
    "iidr": {
        "url": "'$diSsubscriptionManager'",
        "features": {
            "supportsTransaction": true
        }
    }
}' |jq

echo;echo
#read -p "exec 5 Configure IIDR extraction"
echo "exec 5 Configure IIDR extraction"


# 5 Configure IIDR extraction

mycurl=$(echo -e "curl -s --location '${mdmUrl}/api/v1/global-config/iidr-extraction' --header 'Content-Type: application/json' --data '{\"cdcOperations\": {
      \"insert\": {
        \"conditions\": null,
        \"defaultOperation\": true
},
      \"update\": {
        \"conditions\": [
          {
            \"value\": \"UP\",
            \"selector\": \"$.A_ENTTYP.string\"
          }
        ],
        \"defaultOperation\": false
      },
      \"delete\": {
        \"conditions\": [
          {
            \"value\": \"DL\",
            \"selector\": \"$.A_ENTTYP.string\"
          }
        ],
        \"defaultOperation\": false
      }
    },
    \"tableNameExtractionJsonPath\": \"$.A_OBJECT.string\",
    \"schemaNameExtractionJsonPath\": \"$.A_LIBRARY.string\",
    \"dataFormat\": \"JSON\"
  }'")

eval $mycurl |jq

echo;echo
#read -p "exec 6 Get All Global Configuration"
echo "exec 6 Get All Global Configuration"

# 6 Get All Global Configuration

curl -s --location "${mdmUrl}/api/v1/global-config/" \
--header 'Accept: */*'|jq

echo;echo
#read -p "exec 7 Get About MDM"
echo "exec 7 Get About MDM"

# 7 Get About MDM

curl -s --location "${mdmUrl}/api/v1/about" \
--header 'Accept: */*'


echo;echo
#read -p "exec 8 Get About Manager"
echo "exec 8 Get About Manager"

# 8 Get About Manager

curl -s --location "${managerUrl}/api/v1/about" \
--header 'Accept: */*'


echo;echo
#read -p "exec 9 Update di-processor jar"
echo "exec 9 Update di-processor jar"

# 9 Update di-processor jar

curl -s --location "${mdmUrl}/api/v1/global-config/flink/di-processor-jar" \
--header 'Content-Type: text/plain' \
--data "${diProcessorJar}"


echo;echo
#read -p "exec 10 Get di-processor jar"
echo "exec 10 Get di-processor jar"

# 9 Get di-processor jar

curl -s --location "${mdmUrl}/api/v1/global-config/flink/di-processor-jar"

echo

