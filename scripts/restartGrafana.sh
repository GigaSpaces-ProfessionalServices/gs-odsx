# Set XDG_RUNTIME_DIR for systemctl --user over SSH
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus

systemctl --user stop grafana-server.service
sleep 2

systemctl --user enable grafana-server.service
sleep 5
systemctl --user start grafana-server.service