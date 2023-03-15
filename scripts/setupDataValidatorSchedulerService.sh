#!/bin/bash

portNumber=$1
timeRestart=$2
ipAddress=$3
measurmentArray=$4
#echo $restartTime
home_dir_sh=$(pwd)
#echo $home_dir_sh

cp $home_dir_sh/install/data-validation/datavalidator-measurment.service /tmp/datavalidator-measurment.service
cp $home_dir_sh/scripts/servers_datavalidation_schedulerservice.sh /usr/local/bin/

#echo $portNumber
#echo $measurmentArray
chmod 333 /usr/local/bin/servers_datavalidation_schedulerservice.sh

sed -i 's,$portNumber,'$portNumber',g' /tmp/datavalidator-measurment.service
sed -i 's,$timeRestart,'$timeRestart',g' /tmp/datavalidator-measurment.service
sed -i 's,$ipAddress,'$ipAddress',g' /tmp/datavalidator-measurment.service
sed -i 's|$measurmentArray|'$measurmentArray'|g' /tmp/datavalidator-measurment.service

sudo mv -f /tmp/datavalidator-measurment.service /etc/systemd/system/

service="datavalidator-measurment.service"

if systemctl is-active --quiet datavalidator-measurment.service; then
    sudo systemctl stop --quiet datavalidator-measurment.service
    sudo systemctl disable --quiet datavalidator-measurment.service
    sudo systemctl daemon-reload
fi
sleep 5
sudo systemctl daemon-reload
sudo systemctl enable datavalidator-measurment.service
#sudo systemctl start datavalidator-measurment.service