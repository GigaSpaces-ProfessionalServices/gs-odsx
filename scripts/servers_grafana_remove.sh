systemctl stop grafana-server.service
sleep 5
yum erase -y grafana
rm -rf install install.tar