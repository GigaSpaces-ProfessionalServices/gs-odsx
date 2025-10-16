#!/bin/bash
#source /home/dbsh/setenv.sh
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
gigalogpath=$(read_property "app.gigalog.path")

systemctl stop odsxadabas.service
systemctl disable odsxadabas.service
systemctl daemon-reload

rm -rf install install.tar dbagigashare /home/dbsh/install /home/dbsh/install.tar /home/dbsh/setenv.sh /usr/local/bin/st*_adabasFeeder.sh /etc/systemd/system/odsxadabas.service $gigapath"/Adabas/*" $gigalogpath"/Adabas/*"
