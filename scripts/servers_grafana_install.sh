echo "Starting Grafana Installation."
#echo "Extracting install.tar to "$targetDir
tar -xvf install.tar
home_dir=$(pwd)
installation_path=$home_dir/install/grafana
echo "InstallationPath="$installation_path
installation_file=$(find $installation_path -name "*.rpm" -printf "%f\n")
echo "InstallationFile:"$installation_file
yum install -y $installation_path/$installation_file
sleep 5