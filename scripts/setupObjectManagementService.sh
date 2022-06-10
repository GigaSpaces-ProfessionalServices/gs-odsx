#!/bin/bash

function getAppPropertyValue() {
    ENV=${1:-dev}
    grep "${1}" $2|cut -d'=' -f2
}

home_dir_sh=$(pwd)
cp $home_dir_sh/../install/odsxobjectmanagement.service /tmp/odsxobjectmanagement.service

applicativeUser=$(getAppPropertyValue app.server.user $home_dir_sh/../config/app.config)

if [ -z "$applicativeUser" ]
then
      applicativeUser=gsods
fi

objectManagementJar=$home_dir_sh/../install/objectmanagement/objectManagement.jar
objectManagementJar=$(readlink --canonicalize $objectManagementJar)

sed -i 's/gsods/'$applicativeUser'/g' /tmp/odsxobjectmanagement.service
sed -i 's,$objectManagementJar,'$objectManagementJar',g' /tmp/odsxobjectmanagement.service

sudo mv -f /tmp/odsxobjectmanagement.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable odsxobjectmanagement.service
sudo systemctl start odsxobjectmanagement.service

echo "Object Management service setup - Completed!."