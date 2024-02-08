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
  cp $sourceInstallerDirectory/telegraf/scripts/pivot/space-status.gc-state.sh /usr/local/bin/
  cp $sourceInstallerDirectory/telegraf/scripts/pivot/pipeline-state.sh /usr/local/bin/
  cp $sourceInstallerDirectory/telegraf/scripts/pivot/test.sh /usr/local/bin/
  sed -i -e 's|mgr1,mgr2,mgr3|'$managerHost'|g' /usr/local/bin/test.sh
fi
chmod +x /usr/local/bin/*.sh
cp $sourceInstallerDirectory/telegraf/jars/readFromShob-1.0.0.jar /usr/local/bin/

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
