echo "Starting Grafana Installation."
#echo "Extracting install.tar to "$targetDir
sourceInstallerDirectory=$1
echo "sourceInstallerDirectory: "$sourceInstallerDirectory
tar -xvf install.tar
home_dir=$(pwd)
installation_path=$sourceInstallerDirectory/grafana
echo "InstallationPath="$installation_path
installation_file=$(find $installation_path -name "*.rpm" -printf "%f\n")
echo "InstallationFile:"$installation_file
yum install -y $installation_path/$installation_file
cp $installation_path/gs_config.yaml /etc/grafana/provisioning/dashboards/
sed -i -e 's|;disable_sanitize_html = false|disable_sanitize_html = true|g' /etc/grafana/grafana.ini
sleep 5