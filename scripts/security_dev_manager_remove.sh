# Set XDG_RUNTIME_DIR for systemctl --user over SSH
# Load shared read_property helper (no-op when piped over SSH; see lib_app_config.sh).
[ -r "$(dirname "$0")/lib_app_config.sh" ] && source "$(dirname "$0")/lib_app_config.sh"

export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus

echo "Removing Server - Manager"
ENV_CONFIG_PATH=$ENV_CONFIG
# Check if the environment variable is set
if [ -z "$ENV_CONFIG_PATH" ]; then
  echo "Error: $ENV_CONFIG_PATH is not set. Please set it before running this script."
  exit 1
else
  echo "$ENV_CONFIG_PATH is set to: $ENV_CONFIG_PATH"
fi
ENV_CONFIG_PATH="$ENV_CONFIG_PATH/app.config"


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
  yum -y remove java*
  yum -y remove jdk*
  echo "Java Remove -Done!"
fi
if [ "$removeUnzip" == "y" ]; then
  echo "Removing Unzip"
  yum -y remove unzip
  echo "unzip Remove -Done!"
fi
#yum -y remove wget
#echo "wget Remove -Done!"
#rm -r install/*.zip
#Removing symlink
source setenv.sh
systemctl --user stop gsa.service
sleep 5
rm -rf $GS_HOME
rm -rf setenv.sh gs install install.tar $gigapath"/giga*" $gigaworkPath"/*" $gigapath/bin/start_gs*.sh $gigapath/bin/stop_gs*.sh $HOME/.config/systemd/user/gs*.service
find $gigalogpath/ -mindepth 1 ! -regex '^'$gigalogpath'/consul\|'$gigalogpath'/nginx\(/.*\)?' -delete
cd $gigapath
rm -f gigaspaces-smart-ods
echo "Remove symlink done!"
systemctl --user daemon-reload
# sed -i '/hard nofile/d' /etc/security/limits.conf
# sed -i '/soft nofile/d' /etc/security/limits.conf

echo "GS Remove -Done!"

