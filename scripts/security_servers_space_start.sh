# Set XDG_RUNTIME_DIR for systemctl --user over SSH
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus

echo "Starting space servers.."
source setenv.sh
#echo "GSC="$2
gsc=$2
if [ -z "$gsc" ]; then
  gsc=2
else
  gsc=$2
fi

#cd /home/ubuntu/gigaspaces-insightedge-enterprise-15.8.0/bin
#echo $GS_HOME
cd $GS_HOME
#pwd
#sudo -s
#nohup ./bin/gs.sh host run-agent --auto > /tmp/agent-console.log 2>&1 &
systemctl --user daemon-reload
systemctl --user start gsa.service
sleep 30
echo "Space servers started."
#source setenv.sh
#cd $GS_HOME/bin
#nohup ./gs.sh host run-agent --auto --gsc=2 > /tmp/agent-console.log 2>&1 &
