#!/bin/bash

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

sudo mv -f /tmp/odsxhealthcheck.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable odsxhealthcheck.service
sudo systemctl start odsxhealthcheck.service

echo "Health Monitor service setup - Completed!."