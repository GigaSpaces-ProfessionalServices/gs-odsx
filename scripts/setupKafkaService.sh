#!/bin/bash
# Set XDG_RUNTIME_DIR for systemctl --user over SSH
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus


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


mv -f /tmp/odsxkafka.service $HOME/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable odsxkafka.service
systemctl --user start odsxkafka.service

echo "DI Kafka service setup - Completed!."