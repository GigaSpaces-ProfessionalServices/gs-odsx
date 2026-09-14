#!/bin/bash
# Set XDG_RUNTIME_DIR for systemctl --user over SSH
# Load shared read_property helper (no-op when piped over SSH; see lib_app_config.sh).
[ -r "$(dirname "$0")/lib_app_config.sh" ] && source "$(dirname "$0")/lib_app_config.sh"

export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus
# Wait for user systemd bus before any systemctl --user calls (linger race).
wait_for_user_bus

ENV_CONFIG_PATH=$ENV_CONFIG
# Check if the environment variable is set
if [ -z "$ENV_CONFIG_PATH" ]; then
  echo "Error: $ENV_CONFIG_PATH is not set. Please set it before running this script."
  exit 1
else
  echo "$ENV_CONFIG_PATH is set to: $ENV_CONFIG_PATH"
fi
ENV_CONFIG_PATH="$ENV_CONFIG_PATH/app.config"


gigapath=$(read_property "app.giga.path")
gigainfluxpath=$(read_property "app.gigainfluxdata.path")
gigasharepath=$(read_property "app.gigashare.path")
gigadatapath=$(read_property "app.gigadata.path")
gigalogpath=$(read_property "app.gigalog.path")
gigaworkPath=$(read_property "app.gigawork.path")

home_dir_sh=$(pwd)
service_name='object-management.service'
serviceJarName='objectManagement.jar'
log_location=$gigalogpath"/objectManagement/"
space_name=$1
lookup_locator=$2
lookup_group=$3
serviceJar=$4
ddl_properties_file_path=$5
table_batch_file_path=$6
tier_criteria_file=$7
adapter_property_file=$8
batch_index_file=$9
polling_container_file=${10}
odsx_profile=${11}
gs_username=${12}
vaultJar=${13}
passProperty=${14}
useVault=${15}
dblocation=${16}

function getAppPropertyValue() {
    ENV=${1:-dev}
    grep "${1}" $2|cut -d'=' -f2
}

if [ ! -d "$log_location" ]; then
  mkdir $log_location
fi



home_dir_sh=$(pwd)
cp $home_dir_sh/install/$service_name /tmp/$service_name

cp $serviceJar $gigapath"/"


serviceJar=$(readlink --canonicalize $serviceJar)
base_name=$(basename ${serviceJar})

sed -i 's,$serviceJar,'$gigapath/$base_name',g' /tmp/$service_name
sed -i 's,$space_name,'$space_name',g' /tmp/$service_name
sed -i 's,$log_location,'$log_location',g' /tmp/$service_name
sed -i 's/$lookup_locator/'$lookup_locator'/g' /tmp/$service_name
sed -i 's,$lookup_group,'$lookup_group',g' /tmp/$service_name
sed -i 's,$ddl_properties_file_path,'$ddl_properties_file_path',g' /tmp/$service_name
sed -i 's,$table_batch_file_path,'$table_batch_file_path',g' /tmp/$service_name
sed -i 's,$tier_criteria_file,'$tier_criteria_file',g' /tmp/$service_name
sed -i 's,$adapter_property_file,'$adapter_property_file',g' /tmp/$service_name
sed -i 's,$batch_index_file,'$batch_index_file',g' /tmp/$service_name
sed -i 's,$polling_container_file,'$polling_container_file',g' /tmp/$service_name
sed -i 's,$odsx_profile,'$odsx_profile',g' /tmp/$service_name
sed -i 's,$gs_username,'$gs_username',g' /tmp/$service_name
sed -i 's,$vaultJar,'$vaultJar',g' /tmp/$service_name
sed -i 's,$vaultDbPath,'$dblocation',g' /tmp/$service_name
sed -i 's,$passPropertyName,'$passProperty',g' /tmp/$service_name
if [ "$useVault" != "false" ]; then
    #echo  "export VAULT_MANAGER_PASS=\$(java -Dapp.db.path=$dblocation -jar $vaultJar --get $passProperty)" > $gigapath/bin/objectmanagement_service.sh
    echo  "export VAULT_MANAGER_PASS=" > $gigapath/bin/objectmanagement_service.sh
else
    echo  "export VAULT_MANAGER_PASS=$passProperty" > $gigapath/bin/objectmanagement_service.sh
fi
#echo  "export VAULT_MANAGER_PASS=\$(java -Dapp.db.path=$dblocation -jar $vaultJar --get $passProperty)" > $gigapath/bin/objectmanagement_service.sh
echo  "/usr/bin/java -Dcom.gigaspaces.logger.RollingFileHandler.filename-pattern.gs.logs=$log_location -jar $gigapath/$base_name --log.location=$log_location --space.name=$space_name --lookup.locator=$lookup_locator --lookup.group=$lookup_group --table.batch.file.path=$table_batch_file_path --ddl.properties.file.path=$ddl_properties_file_path --tier.criteria.file=$tier_criteria_file --adapter.property.file=$adapter_property_file --batch.index.file=$batch_index_file --polling.container.file=$polling_container_file --odsx.profile=$odsx_profile --gs.username=$gs_username --gs.password=\$VAULT_MANAGER_PASS" >> $gigapath/bin/objectmanagement_service.sh
chmod +x $gigapath/bin/objectmanagement_service.sh
mv -f /tmp/$service_name $HOME/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable $service_name
systemctl --user start $service_name
sleep 10s
systemctl --user restart $service_name 
echo "Object Management service setup - Completed!."
