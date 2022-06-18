echo "Starting Influxdb Installation."
#echo "Extracting install.tar to "$targetDir
dir=$1
sourceInstallerDirectory=$2
echo "sourceInstallerDirectory: "$sourceInstallerDirectory
tar -xvf install.tar
home_dir=$(pwd)
installation_path=$sourceInstallerDirectory/influx
echo "InstallationPath="$installation_path
installation_file=$(find $installation_path -name "*.rpm" -printf "%f\n")
echo "InstallationFile:"$installation_file
yum install -y $installation_path/$installation_file

sed -i "s|/var/lib/influxdb/|$dir/influxdb/|g" /etc/influxdb/influxdb.conf
#echo "Target Directory :"$1

if [ ! -d "$dir" ]; then
     mkdir $dir
     chmod 777 $dir
fi
chown -R influxdb:influxdb $dir
systemctl enable influxdb.service
sleep 2
systemctl start influxdb.service
sleep 5
influx
create database mydb;