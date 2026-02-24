echo "Stopping InsightEdge"
source setenv.sh
#echo $JAVA_HOME
#echo $PATH
cd $GS_HOME
#sudo -s
#./bin/gs.sh host kill-agent --all
#systemctl daemon-reload
echo "Stopping gsa.service..."
sudo systemctl stop gsa.service

echo "Waiting for service to stop..."
sleep 5
echo "Checking service status..."
sudo systemctl status gsa.service --no-pager || true
echo "InsightEdge stopped."
