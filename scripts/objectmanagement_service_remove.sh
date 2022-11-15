#!/bin/bash

service_name='object-management.service'
serviceJarName='objectManagement.jar'

sudo systemctl stop $service_name
sudo systemctl disable $service_name
sudo rm /etc/systemd/system/$service_name
sudo systemctl daemon-reload
sudo systemctl reset-failed


echo "Object Management service removed!."