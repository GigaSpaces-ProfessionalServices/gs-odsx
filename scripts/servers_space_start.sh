echo "Starting InsightEdge.."
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
systemctl daemon-reload
systemctl start gsa.service
sleep 30
echo "InsightEdge started."
#source setenv.sh
#cd $GS_HOME/bin
#nohup ./gs.sh host run-agent --auto --gsc=2 > /tmp/agent-console.log 2>&1 &
