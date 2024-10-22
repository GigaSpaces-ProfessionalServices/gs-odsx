#!/bin/bash
### ENV variables ###
objectType=$1
MANAGER=$2
GS_USER="gsods"
diManagerURL=$3 #"10.0.1.201:6080"
iidrHost=$4 #"10.0.1.137:6082"  #only di-subscription manager is running here
dataSource="ORACLE"
AS_HOME=/giga/iidr/as
AS_HOST=$5 #"10.0.1.129" # IIDR Access Server, IIDR Kafka Agent, IIDR DB Agent, KAFKA SERVER & ZK, ORACLE DB.
AS_PORT=$6
AS_USER=$7 #"admin" #bring from vault
AS_PASS=$8 #"admin11" #bring from vault
spaceName=$9 #"dih-tau-space"
########################

get_pipeline_id_by_object_type() {
  local objectType=$1  # The objectType passed as an argument

  # Fetch all pipeline IDs
  local pipelineId=$(curl -sX 'GET' "http://$diManagerURL/api/v1/pipeline/" -H 'accept: */*' | jq -r '.[].pipelineId')

  # Loop through each pipeline ID
  for plID in ${pipelineId[@]}; do
    # Check if the objectType exists for the current pipeline ID
    local objectTypePL=$(curl -sX 'GET' "http://$diManagerURL/api/v1/pipeline/$plID/tablepipeline" -H 'accept: */*' | \
      jq -r '.[] | select(.spaceTypeName == "'"$objectType"'") | .spaceTypeName' | wc -l)

    # If objectType matches, return the plID
    if [[ $objectTypePL -ne 0 ]]; then
      echo "$plID"
      return 0
    fi
  done

  echo "No pipeline found with objectType: $objectType"
  return 1
}

get_pipeline_status_by_plid() {
    local plId=$1
    curl -sX 'GET' \
     "http://$diManagerURL/api/v1/pipeline/$plId/status" \
     -H 'accept: */*' | jq -r '.responseStatus'
}

updateTableDefinition() {
    local DATASOURCE=$1
    local SOURCE_SCHEMA=$2
    local SOURCE_TABLE=$3
    local SUBSCRIPTION=$4

    if [[ -z $1 ]] || [[ -z $2 ]] || [[ -z $3 ]] || [[ -z $4 ]];then
      echo "Please provide all details:   ./updateTableDefinition.sh <DATASOURCE> <SOURCE_SCHEMA> <SOURCE_TABLE> <SUBSCRIPTION>"
      exit;
    fi

    sudo -u $GS_USER $AS_HOME/bin/chcclp <<EOF
    chcclp session set to cdc;
    set verbose;
    connect server hostname "${AS_HOST}" port "${AS_PORT}" username "${AS_USER}" password "${AS_PASS}";
    connect datastore name "${DATASOURCE}";
    list table columns schema "${SOURCE_SCHEMA}" table "${SOURCE_TABLE}";
    readd replication table schema "${SOURCE_SCHEMA}" table "${SOURCE_TABLE}";
    describe subscription name "${SUBSCRIPTION}";
    disconnect server;
    exit;
EOF
echo
}

############ MAIN ############

plId=$(get_pipeline_id_by_object_type "$objectType")

# Stop the pipeline
echo "Stopping the pipeline: $plName [$plId] ..."
echo "Response: $(curl -sX 'POST' \
  "http://$diManagerURL/api/v1/pipeline/$plId/stop" \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -d '' | jq -r '.status')"
echo "Sleeping 10 sec ..."
sleep 10
status=$(get_pipeline_status_by_plid "${plId}")
if [[ $status == "RUNNING" ]];then
    echo "PL failed to stop. Abortted."
    exit
else echo "PL is not running."
fi


# Delete a table from PL
echo "Deleting the $objectType from $plId ..."
curl -X 'DELETE' \
  "http://$diManagerURL/api/v1/pipeline/$plId/tablepipeline/$objectType" \
  -H 'accept: */*'


# Re-add the table to the PL
plName=$(curl -sX 'GET'   "http://$diManagerURL/api/v1/pipeline/$plId"   -H 'accept: */*' |jq -r .name)
schema="${objectType%%.*}"
table="${objectType##*.}"
echo
echo "Re-adding $schema.$table to $plName pipeline ..."
result=$(curl -sX 'POST'  "http://$diManagerURL/api/v1/pipeline/$plId/tablepipeline" \
    -H "accept: */*" \
    -H "Content-Type: application/json" \
    -d '{
      "sourceSchema": "'"$schema"'",
      "sourceTable": "'"$table"'",
      "spaceTypeName": "'"$schema.$table"'",
      "store": true
    }'| jq -r '.message')

  if [[ $result == "Success" ]];then
    echo
    echo ">> $schema.$table table successfuly added to $plName."
    # Flag table for refresh
    subName=$(curl -sX 'GET'   "http://$diManagerURL/api/v1/pipeline/$plId" -H 'accept: */*' |jq -r '.subscriptionName')
    echo "schema: $schema   table:$table   dataSource:$dataSource   subName:$subName"
    echo "Table is being flagged for refresh ..."
      output=$(curl -sX 'POST' \
      "http://$iidrHost/api/v1/$dataSource/subscriptions/$subName/refresh" \
      -H 'accept: */*' \
      -H 'Content-Type: application/json' \
      -d '{
      "schema": "'"$schema"'",
      "table": "'"$table"'",
      "forceRefresh": true
       }'|jq -r '.status')
    [[ "${output}" = "SUCCESS" ]] && echo $output || { echo "Failed to flag for refresh [$table]."; exit 1; }

  else
    echo "$table table could not be added. Skipping ..."
    exit
  fi

# Update table definition
# call function: updateTableDefinition <DATASOURCE> <SOURCE_SCHEMA> <SOURCE_TABLE> <SUBSCRIPTION>"
updateTableDefinition $dataSource $schema $table $subName


####################### Replace with odsx cli ####################################################
# Drop the space object type before starting the PL ----> move to odsx CLI
#  auto_objectunregistertype $objectType
/usr/bin/expect -c '
proc send_each_char {str} {
      set delay 0.1  ; # Adjust the delay as needed
      foreach char [split $str ""] {
          send -- $char
          sleep $delay
      }
      send -- "\r"  ; # Simulate pressing Enter
  }

  cd /dbagiga/gs-odsx
  spawn ./odsx.py object objectmanagement registration list
  expect -re ".*Select object to show more details.*"
  sleep .1
  send_each_char 99
  sleep .1
  expect eof
' |grep  $objectType | awk -F'|' '{gsub(/^[ \t]+|[ \t]+$/, "", $8); print "Count for '$objectType' before unregister type :" $8}'

./odsx.py object objectmanagement registration unregistertype $objectType
############################################################################


# Start the pipeline
echo "Starting the pipeline: $plName [$plId] ..."
  curl -sX 'POST' \
  "http://$diManagerURL/api/v1/pipeline/$plId/start" \
  -H 'accept: */*' \
        -H 'Content-Type: application/json' \
        -d '{
            "reconciliationPolicy": "NONE",
            "kafkaRunParameters": {
                "CDC": {
                    "kafkaOffsetStrategy": "COMMITTED",
                    "kafkaOffset": -1
                }
            }
        }'|jq -r '.status'
echo "Sleeping 10 sec ..."
sleep 10
# Validate PL status
echo "$plName pipeline [$plId] status:" $(get_pipeline_status_by_plid $plId)

