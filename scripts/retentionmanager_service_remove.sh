#!/bin/bash
# Set XDG_RUNTIME_DIR for systemctl --user over SSH
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus


service_name='retention-manager.service'
serviceJarName='retention-manager.jar'

systemctl --user stop $service_name
systemctl --user disable $service_name
rm $HOME/.config/systemd/user/$service_name
systemctl --user daemon-reload
systemctl --user reset-failed


echo "Retention Manager service removed!."