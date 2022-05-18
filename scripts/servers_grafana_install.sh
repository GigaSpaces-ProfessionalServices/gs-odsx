echo "Starting Grafana Installation."
#echo "Extracting install.tar to "$targetDir
tar -xvf install.tar
home_dir=$(pwd)
installation_path=$home_dir/dbagigashare/current/GRAFANA
echo "InstallationPath="$installation_path
installation_file=$(find $installation_path -name "*.rpm" -printf "%f\n")
echo "InstallationFile:"$installation_file
yum install -y $installation_path/$installation_file
mv $installation_path/gs_config.yaml /etc/grafana/provisioning/dashboards/
sed -i -e 's|;disable_sanitize_html = false|disable_sanitize_html = true|g' /etc/grafana/grafana.ini
sleep 5