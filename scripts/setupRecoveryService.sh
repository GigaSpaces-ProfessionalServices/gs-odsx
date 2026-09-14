#!/bin/bash
# Set XDG_RUNTIME_DIR for systemctl --user over SSH
# Load shared read_property helper (no-op when piped over SSH; see lib_app_config.sh).
[ -r "$(dirname "$0")/lib_app_config.sh" ] && source "$(dirname "$0")/lib_app_config.sh"

export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus
# Wait for user systemd bus before any systemctl --user calls (linger race).
wait_for_user_bus


function getAppPropertyValue() {
    ENV=${1:-dev}
    grep "${1}" $2|cut -d'=' -f2
}

home_dir_sh=$(pwd)
cp $home_dir_sh/../node_rebalancer/odsxrecovery.service /tmp/odsxrecovery.service

applicativeUser=$(getAppPropertyValue app.server.user $home_dir_sh/../config/app.config)
managerServers=$(getAppPropertyValue app.manager.hosts $home_dir_sh/../config/app.config)
if [ -z "$managerServers" ]
then
      echo "manager servers not found in app.config file. Please setup manager servers"
      exit
fi
if [ -z "$applicativeUser" ]
then
      applicativeUser=gsods
fi

recoverLoggingConfigFile=$home_dir_sh/../config/recovery_logging.properties
recoverLoggingConfigFile=$(readlink --canonicalize $recoverLoggingConfigFile)

nodeRebalancerJar=$home_dir_sh/../node_rebalancer/node-rebalancer.jar
nodeRebalancerJar=$(readlink --canonicalize $nodeRebalancerJar)

clusterConfigFile=$home_dir_sh/../config/cluster.config
clusterConfigFile=$(readlink --canonicalize $clusterConfigFile)


echo $recoverLoggingConfigFile
sed -i 's/gsods/'$applicativeUser'/g' /tmp/odsxrecovery.service
sed -i 's/$managerServers/'$managerServers'/g' /tmp/odsxrecovery.service
sed -i 's,$recoverLoggingConfigFile,'$recoverLoggingConfigFile',g' /tmp/odsxrecovery.service
sed -i 's,$nodeRebalancerJar,'$nodeRebalancerJar',g' /tmp/odsxrecovery.service
sed -i 's,$clusterConfigFile,'$clusterConfigFile',g' /tmp/odsxrecovery.service

mv -f /tmp/odsxrecovery.service $HOME/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable odsxrecovery.service
systemctl --user start odsxrecovery.service

echo "Recovery service setup - Completed!."