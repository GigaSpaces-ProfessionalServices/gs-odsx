echo "Removing Server - Space"
ENV_CONFIG_PATH=$ENV_CONFIG
# Check if the environment variable is set
if [ -z "$ENV_CONFIG_PATH" ]; then
  echo "Error: $ENV_CONFIG_PATH is not set. Please set it before running this script."
  exit 1
else
  echo "$ENV_CONFIG_PATH is set to: $ENV_CONFIG_PATH"
fi
ENV_CONFIG_PATH="$ENV_CONFIG_PATH/app.config"

read_property() {
  local prop_name="$1"
  local prop_value

  prop_value=$(grep "^$prop_name=" "$ENV_CONFIG_PATH" | awk -F'=' '{print $2}')
  echo "$prop_value"
}

gigapath=$(read_property "app.giga.path")
gigainfluxpath=$(read_property "app.gigainfluxdata.path")
gigasharepath=$(read_property "app.gigashare.path")
gigadatapath=$(read_property "app.gigadata.path")
gigalogpath=$(read_property "app.gigalog.path")
gigaworkPath=$(read_property "app.gigawork.path")

removeJava=$1
#echo "removeJava :"$removeJava
removeUnzip=$2
#echo "removeUnzip :"$removeUnzip

homeDir=$(pwd)
source setenv.sh
#sudo su
if [ "$removeJava" == "y" ]; then
  echo "Removing Java"
  sudo yum -y remove java*
  sudo yum -y remove jdk*
  echo "Java Remove -Done!"
fi
if [ "$removeUnzip" == "y" ]; then
  echo "Removing Unzip"
  sudo yum -y remove unzip
  echo "unzip Remove -Done!"
fi
#yum -y remove wget
#echo "wget Remove -Done!"
#rm -r install/*.zip
source setenv.sh
echo "Stopping gsc.service..."
sudo systemctl stop gsc.service
echo "Stopping gsa.service..."
sudo systemctl stop gsa.service
sleep 5
echo "Removing GigaSpaces installation..."
sudo rm -rf $GS_HOME
echo "Removing additional files and directories..."
sudo rm -rf setenv.sh gs install install.tar $gigapath/giga* $gigadatapath/* $gigaworkPath/* /usr/local/bin/start_gs*.sh /usr/local/bin/stop_gs*.sh /etc/systemd/system/gs*.service
echo "Cleaning log directories..."
sudo find $gigalogpath/ -mindepth 1 ! -regex '^'$gigalogpath'/consul\(/.*\)?' -delete
cd $gigapath
echo "Removing symlink and config files..."
sudo rm -f gigaspaces-smart-ods $gigapath/gs_config/metrics.xml
echo "Remove symlink done!"
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload
echo "Cleaning /etc/security/limits.conf..."
sudo sed -i '/hard nofile/d' /etc/security/limits.conf
sudo sed -i '/soft nofile/d' /etc/security/limits.conf
echo "GS Remove -Done!"
