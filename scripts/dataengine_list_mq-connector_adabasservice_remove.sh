#!/bin/bash
#source /home/dbsh/setenv.sh
# Set XDG_RUNTIME_DIR for systemctl --user over SSH
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus

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

systemctl --user stop odsxadabas.service
systemctl --user disable odsxadabas.service
systemctl --user daemon-reload

rm -rf install install.tar dbagigashare /home/dbsh/install /home/dbsh/install.tar /home/dbsh/setenv.sh /giga/bin/st*_adabasFeeder.sh $HOME/.config/systemd/user/odsxadabas.service $gigapath"/Adabas/*" $gigalogpath"/Adabas/*"
