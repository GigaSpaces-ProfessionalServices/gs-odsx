#!/bin/bash
ENV_CONFIG_PATH=$ENV_CONFIG
# Check if the environment variable is set
if [ -z "$ENV_CONFIG_PATH" ]; then
  echo "Error: $ENV_CONFIG_PATH is not set. Please set it before running this script."
  exit 1
else
  echo "$ENV_CONFIG_PATH is set to: $ENV_CONFIG_PATH"
fi
ENV_CONFIG_PATH="$ENV_CONFIG_PATH/app.config"

read_property() {
  local prop_name="$1"
  local prop_value

  prop_value=$(grep "^$prop_name=" "$ENV_CONFIG_PATH" | awk -F'=' '{print $2}')
  echo "$prop_value"
}

gigapath=$(read_property "app.giga.path")
gigainfluxpath=$(read_property "app.gigainfluxdata.path")
gigasharepath=$(read_property "app.gigashare.path")
gigadatapath=$(read_property "app.gigadata.path")
gigalogpath=$(read_property "app.gigalog.path")
gigaworkPath=$(read_property "app.gigawork.path")

home_dir_sh=$(pwd)
service_name='retention-manager.service'
serviceJarName='retention-manager.jar'
log_location=$gigalogpath/retention-manager/
space_name=$1
manager_host=$2
db_location=$3
influxdb_host=$4
scheduler_config=$5
scheduler_interval=$6
scheduler_minute=$7
scheduler_hour=$8
retentionJar=$9
lookup_group=${10}

if [ ! -d "$log_location" ]; then
  mkdir $log_location
fi

if [ ! -f "$db_location" ]; then
    mkdir $gigaworkPath/sqlite
    cp $home_dir_sh/systemServices/retentionManager/retention-manager.db $gigaworkPath/sqlite/

fi

serviceJar=$retentionJar

cp $home_dir_sh/install/$service_name /tmp/$service_name
cp $serviceJar $gigapath/

#echo "serviceJar: "$serviceJar
serviceJar=$(readlink --canonicalize $serviceJar)
base_name=$(basename ${serviceJar})
#echo "base_name:"$base_name

sed -i 's,$serviceJar,'$gigapath/$base_name',g' /tmp/$service_name
sed -i 's,$db_location,'$db_location',g' /tmp/$service_name
sed -i 's,$space_name,'$space_name',g' /tmp/$service_name
sed -i 's,$manager_host,'$manager_host',g' /tmp/$service_name
sed -i 's,$log_location,'$log_location',g' /tmp/$service_name
sed -i 's,$influxdb_host,'$influxdb_host',g' /tmp/$service_name
sed -i 's,$scheduler_minute,'$scheduler_minute',g' /tmp/$service_name
sed -i 's,$scheduler_hour,'$scheduler_hour',g' /tmp/$service_name
sed -i 's,$scheduler_config,'$scheduler_config',g' /tmp/$service_name
sed -i 's,$scheduler_interval,'$scheduler_interval',g' /tmp/$service_name
sed -i 's,$lookup_group,'$lookup_group',g' /tmp/$service_name

sudo mv -f /tmp/$service_name /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable $service_name
sudo systemctl start $service_name
sudo sleep 10s
sudo systemctl restart $service_name 

#echo "Retention Manager service setup - Completed!."