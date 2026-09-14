# Set XDG_RUNTIME_DIR for systemctl --user over SSH
# Load shared read_property helper (no-op when piped over SSH; see lib_app_config.sh).
[ -r "$(dirname "$0")/lib_app_config.sh" ] && source "$(dirname "$0")/lib_app_config.sh"

export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus
# Wait for user systemd bus before any systemctl --user calls (linger race).
wait_for_user_bus

echo "Stopping InsightEdge"
#source setenv.sh
#echo $JAVA_HOME
#echo $PATH

#cd $GS_HOME
#sudo -s
#./bin/gs.sh host kill-agent --all
#systemctl --user daemon-reload
systemctl --user stop gsa.service

