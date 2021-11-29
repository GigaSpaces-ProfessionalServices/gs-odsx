echo "Starting InsightEdge.."
source setenv.sh
#cd /home/ubuntu/gigaspaces-insightedge-enterprise-15.8.0/bin
#echo $GS_HOME
cd $GS_HOME
#pwd
nohup ./bin/gs.sh host run-agent --auto --gsc=2 > /tmp/agent-console.log 2>&1 &
sleep 30
echo "InsightEdge started."
#source setenv.sh
#cd $GS_HOME/bin
#nohup ./gs.sh host run-agent --auto --gsc=2 > /tmp/agent-console.log 2>&1 &
