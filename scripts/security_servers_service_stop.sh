echo "Stopping InsightEdge Service"
source setenv.sh
cd $GS_HOME
systemctl stop gsa.service
