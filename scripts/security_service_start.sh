echo "Starting InsightEdge.."
source setenv.sh
#echo "GSC="$2
gsc=$2
if [ -z "$gsc" ]; then
  gsc=2
else
  gsc=$2
fi

cd $GS_HOME
systemctl daemon-reload
systemctl start gsa.service
sleep 30
echo "InsightEdge started."
