echo "Stopping InsightEdge"
source setenv.sh
cd $GS_HOME
systemctl stop gsa.service
