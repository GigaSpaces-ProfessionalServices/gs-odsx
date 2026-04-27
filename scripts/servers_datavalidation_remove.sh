# Set XDG_RUNTIME_DIR for systemctl --user over SSH
# Load shared read_property helper (no-op when piped over SSH; see lib_app_config.sh).
[ -r "$(dirname "$0")/lib_app_config.sh" ] && source "$(dirname "$0")/lib_app_config.sh"

export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus

ENV_CONFIG_PATH="${ENV_CONFIG}/app.config"
if [ -z "$ENV_CONFIG" ] || [ ! -f "$ENV_CONFIG_PATH" ]; then
    echo "Error: ENV_CONFIG not set or $ENV_CONFIG_PATH missing." >&2
    exit 1
fi
gigapath=$(read_property "app.giga.path")

source setenv.sh

systemctl --user stop odsxdatavalidation.service
sleep 2

#yum -y remove java*
#yum -y remove jdk*

rm -rf $HOME/install/data-validation $gigapath/bin/st*_data_validation.sh $HOME/.config/systemd/user/odsxdatavalidation.service
