#!/bin/sh
#echo "Rebalancing request received for host "$2
locatorsConfig=$1
host=$2
zone=$3
gscCount=$4
currWorkingDir=$5

#echo "Executing Rebalancer. This will take few minutes"

java -Djava.util.logging.config.file=$currWorkingDir/config/recovery_rebalance_logging.properties -cp "./node_rebalancer/node-rebalancer.jar"  com.gigaspaces.odsx.noderebalancer.RunRebalancer  -locators $locatorsConfig   -hostIp $host -zone $zone -gscCount $gscCount  &
jarPID=$!
sleep 4m
kill $jarPID
echo "Rebalancing has completed successfully"