sourceInstallerDirectory=$1

#cp $sourceInstallerDirectory/grafana/gs_config.yaml /etc/grafana/provisioning/dashboards/
cp -r $sourceInstallerDirectory/grafana/dashboards/*.json  /usr/share/grafana/conf/provisioning/dashboards/