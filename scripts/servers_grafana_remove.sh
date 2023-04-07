systemctl stop grafana-server.service
sleep 5
yum erase -y grafana
sudo systemctl daemon-reload