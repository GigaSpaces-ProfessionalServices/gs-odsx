#!/bin/bash
# Set XDG_RUNTIME_DIR for systemctl --user over SSH
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus


function getAppPropertyValue() {
    ENV=${1:-dev}
    grep "${1}" $2|cut -d'=' -f2
}

home_dir_sh=$(pwd)
cp $home_dir_sh/../systemServices/healthCheck/odsxhealthcheck.service /tmp/odsxhealthcheck.service

applicativeUser=$(getAppPropertyValue app.server.user $home_dir_sh/../config/app.config)
managerServers=$(getAppPropertyValue app.manager.hosts $home_dir_sh/../config/app.config)

if [ -z "$applicativeUser" ]
then
      applicativeUser=gsods
fi

healthCheckJar=$home_dir_sh/../systemServices/healthCheck/healthCheck.jar
healthCheckJar=$(readlink --canonicalize $healthCheckJar)

healthCheckServiceFile=$home_dir_sh/../systemServices/healthCheck/servicesList.yml
healthCheckServiceFile=$(readlink --canonicalize $healthCheckServiceFile)


sed -i 's/gsods/'$applicativeUser'/g' /tmp/odsxhealthcheck.service
sed -i 's,$healthCheckJar,'$healthCheckJar',g' /tmp/odsxhealthcheck.service
sed -i 's,$healthCheckServiceFile,'$healthCheckServiceFile',g' /tmp/odsxhealthcheck.service

mv -f /tmp/odsxhealthcheck.service $HOME/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable odsxhealthcheck.service
systemctl --user start odsxhealthcheck.service

echo "Health Monitor service setup - Completed!."