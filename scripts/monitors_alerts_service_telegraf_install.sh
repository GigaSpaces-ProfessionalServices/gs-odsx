# Load shared read_property helper (no-op when piped over SSH; see lib_app_config.sh).
[ -r "$(dirname "$0")/lib_app_config.sh" ] && source "$(dirname "$0")/lib_app_config.sh"

ENV_CONFIG_PATH="${ENV_CONFIG}/app.config"
if [ -z "$ENV_CONFIG" ] || [ ! -f "$ENV_CONFIG_PATH" ]; then
    echo "Error: ENV_CONFIG not set or $ENV_CONFIG_PATH missing." >&2
    exit 1
fi
gigapath=$(read_property "app.giga.path")

echo "Starting Telegraf Installation."
sourceInstallerDirectory=$1
managerHost=$2
hostType=$3
home_dir=$(pwd)
installation_path=$sourceInstallerDirectory/telegraf
echo "InstallationPath="$installation_path
installation_file=$(find $installation_path -name "*.rpm" -printf "%f\n")
echo "InstallationFile:"$installation_file
#yum install -y $installation_path/$installation_file
systemctl stop telegraf
sleep 5
if [ "$hostType" == "pivot" ]; then
  cp $sourceInstallerDirectory/telegraf/scripts/pivot/*.sh $gigapath/bin/
  #cp $sourceInstallerDirectory/telegraf/scripts/pivot/space-status.gc-state.sh $gigapath/bin/
  #cp $sourceInstallerDirectory/telegraf/scripts/pivot/pipeline-state.sh $gigapath/bin/
  #cp $sourceInstallerDirectory/telegraf/scripts/pivot/test.sh $gigapath/bin/
  # test.sh removed — pipeline-state.sh falls back gracefully when absent
fi
chmod +x $gigapath/bin/*.sh
cp $sourceInstallerDirectory/telegraf/jars/readFromShob-1.0.0.jar $gigapath/bin/

sleep 5

#cmd= $(grep -r 'inputs.exec' /etc/telegraf/telegraf.conf)
#if (grep -v '^ *#' /etc/telegraf/telegraf.conf  | grep -q 1 "inputs.exec"); then

#  echo "Already Exist"

#else
if [ "$hostType" == "pivot" ]; then
  echo "" >> /etc/telegraf/telegraf.conf
  echo "# Telegraf config START" >> /etc/telegraf/telegraf.conf
  cat $sourceInstallerDirectory/telegraf/config/pivot/pivot.telegraf.conf >> /etc/telegraf/telegraf.conf
  echo "# Telegraf config END " >> /etc/telegraf/telegraf.conf
fi
#fi

systemctl daemon-reload
echo "Starting service"
systemctl start telegraf
sleep 5
