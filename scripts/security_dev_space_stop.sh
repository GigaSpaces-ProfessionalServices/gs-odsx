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
systemctl --user stop gsa.service
#systemctl --user stop gsc.service
