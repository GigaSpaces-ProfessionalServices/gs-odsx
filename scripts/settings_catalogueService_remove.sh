#!/bin/bash
# Set XDG_RUNTIME_DIR for systemctl --user over SSH
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus


home_dir_sh=$(pwd)
service_name='catalogue-service.service'
serviceJarName='catalogue-service.jar'

systemctl --user stop $service_name
systemctl --user disable $service_name
rm $HOME/.config/systemd/user/$service_name
systemctl --user daemon-reload
systemctl --user reset-failed


echo "Catalogue service removed!."