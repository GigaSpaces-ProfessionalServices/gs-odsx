#!/bin/bash

service_name='retention-manager.service'
serviceJarName='retention-manager.jar'

sudo systemctl stop $service_name
sudo systemctl disable $service_name
sudo rm /etc/systemd/system/$service_name
sudo systemctl daemon-reload
sudo systemctl reset-failed


echo "Retention Manager service removed!."