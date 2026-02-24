set -x
echo "Starting Influxdb Installation."
#echo "Extracting install.tar to "$targetDir
dir=$1
sourceInstallerDirectory=$2
echo "sourceInstallerDirectory: "$sourceInstallerDirectory

echo "Extracting install.tar..."
tar -xvf install.tar

home_dir=$(pwd)
installation_path=$sourceInstallerDirectory/influx
echo "InstallationPath="$installation_path

installation_file=$(find $installation_path -name "*.rpm" -printf "%f\n")
echo "InstallationFile:"$installation_file

if [ -z "$installation_file" ]; then
    echo "Error: No RPM file found in $installation_path"
    exit 1
fi

echo "Installing InfluxDB RPM..."
sudo yum install -y $installation_path/$installation_file

echo "Configuring InfluxDB data directory to $dir/influxdb/..."
sudo sed -i "s|/var/lib/influxdb/|$dir/influxdb/|g" /etc/influxdb/influxdb.conf

#echo "Target Directory :"$1

if [ ! -d "$dir" ]; then
    echo "Creating directory $dir..."
    sudo mkdir -p $dir
    sudo chmod 777 $dir
fi

# Create influxdb subdirectories
echo "Creating InfluxDB data directories..."
sudo mkdir -p $dir/influxdb/data
sudo mkdir -p $dir/influxdb/meta
sudo mkdir -p $dir/influxdb/wal

if (sudo grep -v '^ *#' /etc/influxdb/influxdb.conf  | grep -q '\[data\]'); then
    echo "Updating InfluxDB configuration..."

    start=$( sudo grep -n  -v "^ *\(--\|#\)" /etc/influxdb/influxdb.conf  | grep '\[data\]' | cut -d: -f1 )
    end=$(  sudo grep -v '^ *#' /etc/influxdb/influxdb.conf | sed -n '/series-id-set-cache-size = 100/=' /etc/influxdb/influxdb.conf  )
    sudo sed -i "$start,$end s/^/#/" /etc/influxdb/influxdb.conf

    echo "" | sudo tee -a /etc/influxdb/influxdb.conf > /dev/null
    echo "# Influxdb config START" | sudo tee -a /etc/influxdb/influxdb.conf > /dev/null

    if [ -f "${ODSXARTIFACTS}/influx/config/influxdb.conf.template" ]; then
        cat ${ODSXARTIFACTS}/influx/config/influxdb.conf.template | sudo tee -a /etc/influxdb/influxdb.conf
    else
        echo "Warning: Template file ${ODSXARTIFACTS}/influx/config/influxdb.conf.template not found"
    fi

    echo "# Influxdb config END " | sudo tee -a /etc/influxdb/influxdb.conf
fi
sleep 5
sudo chown -R influxdb:influxdb $dir
sudo systemctl enable influxdb.service
sleep 2
sudo systemctl start influxdb.service
sleep 10
influx
create database mydb;
