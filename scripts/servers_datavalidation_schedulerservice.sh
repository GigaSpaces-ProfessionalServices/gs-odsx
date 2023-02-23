#!/bin/bash

portNumber=$1
timeRestart=$2
ipAddress=$3
measurmentArray=$4

while sleep $timeRestart;do
  items=$(echo "$measurmentArray" | jq -c -r '.[]')

  for item in ${items}; do
       data1=$(echo "$item" | jq -r '.measurementIdA')
       data2=$(echo "$item" | jq -r '.measurementIdB')
       data3=$(echo "$item" | jq -r '.executionTime')
#
      echo "....................................."

      resultc=$(curl -X GET  "http://$ipAddress:$portNumber/measurement/compare/${data1}/${data2}?executionTime=${data3}&influxdbResultStore=true" | jq -r '.response')
      echo
      echo
      echo "-----------------------------------------------------------------------------"

      a=$(echo "$resultc" | jq -r '.result')
      echo "Test Result: $a"

      if [ $a == 'pending' ]; then
        echo "Test is scheduled"
      elif [ $a == 'FAIL' ]; then
        failedResult=$(echo "$resultc" | jq -r '.errorSummary')
        echo "Details: $failedResult"
      else
        b=$(echo "$resultc" | jq -r '.query')
        echo "Query: $b"

        c=$(echo "$resultc" | jq -r '.summary')
        echo "Details: $c"
      fi
      echo "-----------------------------------------------------------------------------"
  done;

done
