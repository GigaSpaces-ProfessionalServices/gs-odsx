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
info "stopping gs...\n"
systemctl stop gsa
sleep 30
cd /dbagiga
oldGSPath=$(readlink -f gigaspaces-smart-ods)
info "Current GS "$oldGSPath
rm -rf $oldGSPath
rm -f gigaspaces-smart-ods
mv /dbagiga/gigaspaces-smart-ods-old /dbagiga/gigaspaces-smart-ods
sleep 10
info "starting gs...\n"
systemctl start gsa
sleep 30