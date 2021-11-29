#!/bin/bash

function getAppPropertyValue() {
    ENV=${1:-dev}
    grep "${1}" $2|cut -d'=' -f2
}

home_dir_sh=$(pwd)
cp $home_dir_sh/../install/kafka.service /tmp/odsxkafka.service

applicativeUser=$(getAppPropertyValue app.server.user $home_dir_sh/../config/app.config)
managerServers=$(getAppPropertyValue app.manager.hosts $home_dir_sh/../config/app.config)

if [ -z "$applicativeUser" ]
then
      applicativeUser=gsods
fi

clusterConfigFile=$home_dir_sh/../config/cluster.config
clusterConfigFile=$(readlink --canonicalize $clusterConfigFile)


echo $recoverLoggingConfigFile
sed -i 's/gsods/'$applicativeUser'/g' /tmp/odsxkafka.service


sudo mv -f /tmp/odsxkafka.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable odsxkafka.service
sudo systemctl start odsxkafka.service

echo "DI Kafka service setup - Completed!."