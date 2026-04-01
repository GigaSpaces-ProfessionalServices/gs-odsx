# Set XDG_RUNTIME_DIR for systemctl --user over SSH
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus

echo "Stopping InsightEdge"
source setenv.sh
#echo $JAVA_HOME
#echo $PATH
cd $GS_HOME
#sudo -s
#./bin/gs.sh host kill-agent --all
#systemctl --user daemon-reload
echo "Stopping gsa.service..."
systemctl --user stop gsa.service

echo "Waiting for service to stop..."
sleep 5
echo "Checking service status..."
systemctl --user status gsa.service --no-pager || true
echo "InsightEdge stopped."
