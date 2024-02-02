#!/bin/bash


# prints colored text
print_style () {

    if [ "$2" == "debug" ] ; then
        COLOR="96m";
    elif [ "$2" == "info" ] ; then
        COLOR="92m";
    elif [ "$2" == "warning" ] ; then
        COLOR="93m";
    elif [ "$2" == "error" ] ; then
        COLOR="91m";
    else #default color
        COLOR="0m";
    fi

    STARTCOLOR="\e[$COLOR";
    ENDCOLOR="\e[0m";

    printf "$STARTCOLOR%b$ENDCOLOR" "$1";
}

debug() {
    print_style "$1" "debug";
}

info() {
    print_style "$1" "info";
}

warning() {
    print_style "$1" "warning";
}

error() {
    print_style "$1" "error";
}

printNoColor() {
    print_style "$1" "error";
}

sourceInstallerDirectory=$1
hostType=$2
#echo "sourceInstallerDirectory: "$sourceInstallerDirectory
cp $sourceInstallerDirectory/telegraf/scripts/space/telegraf_wal-size.sh /usr/local/bin/
sleep 5
#cat "" >> /etc/telegraf/telegraf.conf

#if (! grep -q "inputs.exec" /etc/telegraf/telegraf.conf); then
if [ "$hostType" == "space" ]; then
  echo "" >> /etc/telegraf/telegraf.conf
  echo "# Telegraf config START" >> /etc/telegraf/telegraf.conf
  cat $sourceInstallerDirectory/telegraf/config/space/space.telegraf.conf >> /etc/telegraf/telegraf.conf
  echo "# Telegraf config END " >> /etc/telegraf/telegraf.conf
fi
#fi

info " Stopping service\n"
systemctl stop telegraf
sleep 5
systemctl daemon-reload
info " Starting service\n"
systemctl start telegraf

sleep 5
