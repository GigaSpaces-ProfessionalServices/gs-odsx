# Set XDG_RUNTIME_DIR for systemctl --user over SSH
# Load shared read_property helper (no-op when piped over SSH; see lib_app_config.sh).
[ -r "$(dirname "$0")/lib_app_config.sh" ] && source "$(dirname "$0")/lib_app_config.sh"

export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus
# Wait for user systemd bus before any systemctl --user calls (linger race).
wait_for_user_bus

echo "Starting manager servers.."
source setenv.sh
#echo $GS_HOME
gsc=$2
if [ -z "$gsc" ]; then
  gsc=2
else
  gsc=$2
fi
cd $GS_HOME
#pwd
#sudo -s
#nohup ./bin/gs.sh host run-agent --auto > /tmp/agent-console.log 2>&1 &
systemctl --user daemon-reload
systemctl --user start gsa.service

sleep 30
echo "Manager servers started."
#source setenv.sh
#cd $GS_HOME/bin
#nohup ./gs.sh host run-agent --auto --gsc=2 > /tmp/agent-console.log 2>&1 &
