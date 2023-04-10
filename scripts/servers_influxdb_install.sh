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

if (grep -v '^ *#' /etc/influxdb/influxdb.conf  | grep -q '\[data\]'); then

    start=$( grep -n  -v "^ *\(--\|#\)" /etc/influxdb/influxdb.conf  | grep '\[data\]' | cut -d: -f1 )
    end=$(  grep -v '^ *#' /etc/influxdb/influxdb.conf | sed -n '/series-id-set-cache-size = 100/=' /etc/influxdb/influxdb.conf  )
    sed -i "$start,$end s/^/#/" /etc/influxdb/influxdb.conf

    echo "" >> /etc/influxdb/influxdb.conf
    echo "# Influxdb config START" >> /etc/influxdb/influxdb.conf
    cat /dbagigashare/current/influx/config/influxdb.conf.template >> /etc/influxdb/influxdb.conf
    echo "# Influxdb config END " >> /etc/influxdb/influxdb.conf

fi
sleep 5
chown -R influxdb:influxdb $dir
systemctl enable influxdb.service
sleep 2
systemctl start influxdb.service
sleep 10
influx
create database mydb;