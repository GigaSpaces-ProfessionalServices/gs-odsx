echo "Starting Influxdb Installation."
#echo "Extracting install.tar to "$targetDir
tar -xvf install.tar
home_dir=$(pwd)
installation_path=$home_dir/install/influxdb
echo "InstallationPath="$installation_path
installation_file=$(find $installation_path -name "*.rpm" -printf "%f\n")
echo "InstallationFile:"$installation_file
yum install -y $installation_path/$installation_file
dir=$1
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