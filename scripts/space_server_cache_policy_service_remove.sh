#!/bin/bash

service_name='space-update-cache-policy.service'
serviceJarName='tierdirectcall.jar'

sudo systemctl stop $service_name
sudo systemctl disable $service_name
sudo rm /etc/systemd/system/$service_name /dbagiga/$serviceJarName

sudo systemctl daemon-reload
sudo systemctl reset-failed


echo "space-update-cache-policy service removed!."