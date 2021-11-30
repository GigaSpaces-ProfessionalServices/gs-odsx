echo "Stopping InsightEdge"
source setenv.sh
#echo $JAVA_HOME
#echo $PATH

cd $GS_HOME
#sudo -s
#./bin/gs.sh host kill-agent --all
#systemctl daemon-reload
sudo systemctl stop gs.service

