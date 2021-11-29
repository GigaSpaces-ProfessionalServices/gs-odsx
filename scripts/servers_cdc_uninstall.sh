#!/bin/bash
#CentOS 7.2 Installation Script
#source ./consoleLog.sh

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

info "Removing cr8 package"
sudo yum remove cr8-2.0.9-245.x86_64 -y
sudo rm -f /tmp/cr8-2.0.9-245.x86_64.rpm

info "Removing misc directory"
sudo rm -rf /root/misc

info "Removing Swap"

#For Removing Swap
sudo swapoff -v /swapfile
sudo sed '/^\/swapfile/d' < /etc/fstab > /tmp/fstab
sudo mv /tmp/fstab /etc/fstab
sudo rm -f /swapfile

info "Removing user 'dbsh'"
sudo userdel --remove dbsh

info "Removing package 'wget'"
sudo yum remove wget -y
