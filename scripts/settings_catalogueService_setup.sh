#!/bin/bash
echo "Consul host="$1
serviceJarName=$2
home_dir_sh=$(pwd)
service_name='catalogue-service.service'
echo "serviceJarName:"$serviceJarName
consul_host=$1
log_location=/dbagigalogs/

cp $home_dir_sh/systemServices/catalogue/$service_name /tmp/$service_name
cp $serviceJarName  /dbagiga/

serviceJar=$(readlink --canonicalize $serviceJarName)
base_name=$(basename ${serviceJar})
echo "base_name"$base_name

sed -i 's,$serviceJar,'/dbagiga/$base_name',g' /tmp/$service_name
sed -i 's,$consul_host,'$consul_host',g' /tmp/$service_name
sed -i 's,$log_location,'$log_location',g' /tmp/$service_name

sudo mv -f /tmp/$service_name /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable $service_name
sudo systemctl start $service_name

echo "Catalogue service setup - Completed!."