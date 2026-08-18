echo "Starting service servers.."
source setenv.sh
cd $GS_HOME
systemctl daemon-reload
systemctl start gsa.service
sleep 30
echo "Service servers started."
