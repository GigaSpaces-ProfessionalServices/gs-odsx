#!/bin/bash
#source /home/dbsh/setenv.sh
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

validate_nonempty_paths gigapath gigalogpath

systemctl --user stop odsxadabas.service
systemctl --user disable odsxadabas.service
systemctl --user daemon-reload

rm -rf install install.tar /home/dbsh/install /home/dbsh/install.tar /home/dbsh/setenv.sh $gigapath/bin/st*_adabasFeeder.sh $HOME/.config/systemd/user/odsxadabas.service $gigapath/Adabas/* $gigalogpath/Adabas/*
