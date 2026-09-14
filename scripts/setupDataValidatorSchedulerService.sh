#!/bin/bash
# Set XDG_RUNTIME_DIR for systemctl --user over SSH
# Load shared read_property helper.
[ -r "$(dirname "$0")/lib_app_config.sh" ] && source "$(dirname "$0")/lib_app_config.sh"

export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus
# Wait for user systemd bus before any systemctl --user calls (linger race).
wait_for_user_bus

ENV_CONFIG_PATH="${ENV_CONFIG}/app.config"
if [ -z "$ENV_CONFIG" ] || [ ! -f "$ENV_CONFIG_PATH" ]; then
    echo "Error: ENV_CONFIG not set or $ENV_CONFIG_PATH missing." >&2
    exit 1
fi
gigapath=$(read_property "app.giga.path")

portNumber=$1
timeRestart=$2
ipAddress=$3
measurmentArray=$4
#echo $restartTime
home_dir_sh=$(pwd)
#echo $home_dir_sh

cp $home_dir_sh/install/data-validation/datavalidator-measurment.service /tmp/datavalidator-measurment.service
cp $home_dir_sh/scripts/servers_datavalidation_schedulerservice.sh $gigapath/bin/

#echo $portNumber
#echo $measurmentArray
chmod 333 $gigapath/bin/servers_datavalidation_schedulerservice.sh

sed -i 's,$portNumber,'$portNumber',g' /tmp/datavalidator-measurment.service
sed -i 's,$timeRestart,'$timeRestart',g' /tmp/datavalidator-measurment.service
sed -i 's,$ipAddress,'$ipAddress',g' /tmp/datavalidator-measurment.service
sed -i 's|$measurmentArray|'$measurmentArray'|g' /tmp/datavalidator-measurment.service

mv -f /tmp/datavalidator-measurment.service $HOME/.config/systemd/user/

service="datavalidator-measurment.service"

if systemctl --user is-active --quiet datavalidator-measurment.service; then
    systemctl --user stop --quiet datavalidator-measurment.service
    systemctl --user disable --quiet datavalidator-measurment.service
    systemctl --user daemon-reload
fi
sleep 5
systemctl --user daemon-reload
systemctl --user enable datavalidator-measurment.service
#systemctl --user start datavalidator-measurment.service