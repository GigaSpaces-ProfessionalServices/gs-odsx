set -x
echo "Starting Grafana Installation."
sourceInstallerDirectory=$1
gsConfigYamlTarget=$2
gsConfigSpaceboardTarget=$3
sourceInstallerEnvDirectory=$4
echo "sourceInstallerDirectory: "$sourceInstallerDirectory
echo "sourceInstallerEnvDirectory: "$sourceInstallerEnvDirectory

echo "Extracting install.tar..."
tar -xvf install.tar

home_dir=$(pwd)
installation_path=$sourceInstallerDirectory/grafana
echo "InstallationPath="$installation_path

installation_file=$(find $installation_path -name "*.rpm" -printf "%f\n")
echo "InstallationFile:"$installation_file

if [ -z "$installation_file" ]; then
    echo "Error: No RPM file found in $installation_path"
    exit 1
fi

echo "Installing Grafana RPM..."
sudo yum install -y $installation_path/$installation_file

echo "Copying configuration file to $gsConfigYamlTarget..."
sudo cp $installation_path/gs_config.yaml $gsConfigYamlTarget

echo "Configuring Grafana to allow HTML in dashboards..."
sudo sed -i -e 's|;disable_sanitize_html = false|disable_sanitize_html = true|g' /etc/grafana/grafana.ini

sleep 2

echo "Copying dashboard files to $gsConfigSpaceboardTarget..."
sudo cp -r $sourceInstallerEnvDirectory/grafana/dashboards/*.json $gsConfigSpaceboardTarget

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

sleep 2

echo "Enabling Grafana service..."
sudo systemctl enable grafana-server.service

sleep 2
echo "Starting Grafana service..."
sudo systemctl start grafana-server.service
sleep 5

echo "Grafana has been installed on host: $(hostname)"
echo "Installation complete!"
echo "Access Grafana at: http://$(hostname -I | awk '{print $1}'):3000"
