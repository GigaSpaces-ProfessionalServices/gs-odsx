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

echo "Consul host="$1
serviceJarName=$2
home_dir_sh=$(pwd)
service_name='catalogue-service.service'
echo "serviceJarName:"$serviceJarName
consul_host=$1
log_location=$gigalogpath'/'

cp $home_dir_sh/systemServices/catalogue/$service_name /tmp/$service_name
cp $serviceJarName  $gigapath'/'

serviceJar=$(readlink --canonicalize $serviceJarName)
base_name=$(basename ${serviceJar})
echo "base_name"$base_name

echo sed -i 's,$serviceJar,'$gigapath/$base_name',g' /tmp/$service_name
sed -i 's,$consul_host,'$consul_host',g' /tmp/$service_name
sed -i 's,$log_location,'$log_location',g' /tmp/$service_name

sudo mv -f /tmp/$service_name /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable $service_name
sudo systemctl start $service_name

echo "Catalogue service setup - Completed!."