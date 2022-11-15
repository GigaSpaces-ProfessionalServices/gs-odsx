sourceInstallerDirectory=$1
gsConfigSpaceboardTarget=$2
#cp $sourceInstallerDirectory/grafana/gs_config.yaml /etc/grafana/provisioning/dashboards/
cp -r $sourceInstallerDirectory/grafana/dashboards/*.json  $gsConfigSpaceboardTarget