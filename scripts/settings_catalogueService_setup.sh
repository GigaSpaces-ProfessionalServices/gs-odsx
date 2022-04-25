#!/bin/bash
echo "Consul host="$1

home_dir_sh=$(pwd)
service_name='catalogue-service.service'
serviceJarName='catalogue-service.jar'
consul_host=$1
log_location=$home_dir_sh/logs
cp $home_dir_sh/systemServices/catalogue/$service_name /tmp/$service_name

serviceJar=$home_dir_sh/systemServices/catalogue/$serviceJarName
serviceJar=$(readlink --canonicalize $serviceJar)

sed -i 's,$serviceJar,'$serviceJar',g' /tmp/$service_name
sed -i 's,$consul_host,'$consul_host',g' /tmp/$service_name
sed -i 's,$log_location,'$log_location',g' /tmp/$service_name

sudo mv -f /tmp/$service_name /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable $service_name
sudo systemctl start $service_name

echo "Catalogue service setup - Completed!."