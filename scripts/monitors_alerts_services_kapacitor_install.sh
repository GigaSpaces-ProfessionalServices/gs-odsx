#!/bin/bash
#set -x
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
host=$2
port=$3
info "host: "$host
info "port: "$port
#info "sourceInstallerDirectory: "$sourceInstallerDirectory
installation_path=$sourceInstallerDirectory/kapacitor
info "InstallationPath="$installation_path"\n"
installation_file=$(find $installation_path -name "ka*.rpm" -printf "%f\n")
info "InstallationFile:"$installation_file"\n"
info "File:"$installation_path/$installation_file"\n"
yum install -y $installation_path/$installation_file

installation_file=$(find $installation_path -name "jq*.rpm" -printf "%f\n")
#echo "InstallationFile:"$installation_file
info "File:"$installation_path/$installation_file"\n"
yum install -y $installation_path/$installation_file

mkdir -p /etc/kapacitor/templates
info "Copying files from "$sourceInstallerDirectory/kapacitor/templates/" to /etc/kapacitor/templates/ \n"
cp $sourceInstallerDirectory/kapacitor/templates/*.json /etc/kapacitor/templates/

kapacitor_url='export KAPACITOR_URL=http://'$host:$port
echo "kapacitor_url:"$kapacitor_url
echo "$kapacitor_url" >> ~/.bash_profile
source ~/.bash_profile
source .bash_profile
systemctl daemon-reload
sleep 2
#For debug
#sed -i -e 's|#   endpoint = "example"|  endpoint = "debug"|g' /etc/kapacitor/kapacitor.conf
#sed -i -e 's|#   url = "http://example.com"|  url = "http://localhost:4242"|g' /etc/kapacitor/kapacitor.conf
#sed -i -e 's|#   alert-template-file = "/path/to/template/file"| alert-template-file = "/etc/kapacitor/templates/debug.json"|g' /etc/kapacitor/kapacitor.conf
info "\n Configuring kapacitor conf to /etc/kapacitor/kapacitor.conf"
cat $sourceInstallerDirectory/kapacitor/config/kapacitor.conf.template >> /etc/kapacitor/kapacitor.conf
sleep 2
