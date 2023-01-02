#!/bin/bash
home_dir_sh=$(pwd)
tar -xvf install.tar
service_name='space-update-cache-policy.service'
serviceJarName='tierdirectcall.jar'
log_location=/dbagigalogs/spaceupdatecachepolicy/
serviceJar=$1
tieredCriteriaConfigFilePath=$2
xapWorkLocation=$3
function getAppPropertyValue() {
    ENV=${1:-dev}
    grep "${1}" $2|cut -d'=' -f2
}

if [ ! -d "$log_location" ]; then
  mkdir $log_location
fi



home_dir_sh=$(pwd)
cp $home_dir_sh/install/$service_name /tmp/$service_name

cp $serviceJar /dbagiga/


serviceJar=$(readlink --canonicalize $serviceJar)
base_name=$(basename ${serviceJar})

sed -i 's,$serviceJar,'/dbagiga/$base_name',g' /tmp/$service_name
sed -i 's,$tieredCriteriaConfigFilePath,'$tieredCriteriaConfigFilePath',g' /tmp/$service_name
sed -i 's,$xapWorkLocation,'$xapWorkLocation',g' /tmp/$service_name
sed -i 's,$log_location,'$log_location',g' /tmp/$service_name

sudo mv -f /tmp/$service_name /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable $service_name
sudo systemctl start $service_name
sudo sleep 10s
sudo systemctl restart $service_name
echo "space update cache policy service setup - Completed!."