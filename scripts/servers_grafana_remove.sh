sudo systemctl stop grafana-server.service
sleep 5
sudo yum erase -y grafana
sudo systemctl daemon-reload