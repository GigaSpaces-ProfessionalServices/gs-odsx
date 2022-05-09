#!/bin/bash

home_dir_sh=$(pwd)
service_name='catalogue-service.service'
serviceJarName='catalogue-service.jar'

sudo systemctl stop $service_name
sudo systemctl disable $service_name
sudo rm /etc/systemd/system/$service_name
sudo systemctl daemon-reload
sudo systemctl reset-failed


echo "Catalogue service removed!."