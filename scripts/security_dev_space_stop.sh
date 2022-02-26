echo "Stopping InsightEdge"
source setenv.sh
#echo $JAVA_HOME
#echo $PATH
cd $GS_HOME
#sudo -s
#./bin/gs.sh host kill-agent --all
#systemctl daemon-reload
systemctl stop gsa.service
#systemctl stop gsc.service
