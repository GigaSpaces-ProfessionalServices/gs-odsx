#!/bin/bash
home_dir_sh=$(pwd)
service_name='object-management.service'
serviceJarName='objectManagement.jar'
log_location=/dbagigalogs/objectManagement/
space_name=$1
lookup_locator=$2
lookup_group=$3
serviceJar=$4
ddl_properties_file_path=$5
table_batch_file_path=$6
tier_criteria_file=$7
odsx_profile=$8
gs_username=$9
gs_password=${10}
appId=${11}
safeId=${12}
objectId=${13}

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
sed -i 's,$space_name,'$space_name',g' /tmp/$service_name
sed -i 's,$log_location,'$log_location',g' /tmp/$service_name
sed -i 's/$lookup_locator/'$lookup_locator'/g' /tmp/$service_name
sed -i 's,$lookup_group,'$lookup_group',g' /tmp/$service_name
sed -i 's,$ddl_properties_file_path,'$ddl_properties_file_path',g' /tmp/$service_name
sed -i 's,$table_batch_file_path,'$table_batch_file_path',g' /tmp/$service_name
sed -i 's,$tier_criteria_file,'$tier_criteria_file',g' /tmp/$service_name
sed -i 's,$odsx_profile,'$odsx_profile',g' /tmp/$service_name
#sed -i 's,$gs_username,'$gs_username',g' /tmp/$service_name
#sed -i 's,$gs_password,'$gs_password',g' /tmp/$service_name
sed -i 's,$app_id,'$appId',g' /tmp/$service_name
sed -i 's,$safe_id,'$safeId',g' /tmp/$service_name
sed -i 's,$object_id,'$objectId',g' /tmp/$service_name

sudo mv -f /tmp/$service_name /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable $service_name
sudo systemctl start $service_name
sudo sleep 10s
sudo systemctl restart $service_name 
echo "Object Management service setup - Completed!."