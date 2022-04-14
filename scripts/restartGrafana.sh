systemctl stop grafana-server.service
sleep 2

systemctl enable grafana-server.service
sleep 5
systemctl start grafana-server.service