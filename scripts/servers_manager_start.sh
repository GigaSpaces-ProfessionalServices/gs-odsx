# Set XDG_RUNTIME_DIR for systemctl --user over SSH
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus

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
# echo "Reloading systemd daemon..."
#systemctl --user daemon-reload
echo "Starting gsa.service..."
systemctl --user start gsa.service

sleep 30
echo "Manager server started."
#echo "Checking service status..."
#systemctl --user status gsa.service --no-pager
#source setenv.sh
#cd $GS_HOME/bin
#nohup ./gs.sh host run-agent --auto --gsc=2 > /tmp/agent-console.log 2>&1 &
