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
cefLoggingJarInput=$1
cefLoggingJarInputTarget=$2
springLdapCoreJarInput=$3
springLdapJarInput=$4
vaultSupportJarInput=$5
javaPasswordJarInput=$6
springTargetJarInput=$7
info "stopping gs...\n"
systemctl stop gsa
sleep 30
cd /dbagiga
oldGSPath=$(readlink -f gigaspaces-smart-ods)
info "Current GS "$oldGSPath"\n"
rm -rf $oldGSPath
rm -f gigaspaces-smart-ods
mv /dbagiga/gigaspaces-smart-ods-old /dbagiga/gigaspaces-smart-ods
rm -f /dbagiga/gs_jars/*
info "Copying required jars...\n"
#echo ""$cefLoggingJarInput $cefLoggingJarInputTarget
cp $cefLoggingJarInput $cefLoggingJarInputTarget
#echo ""$springLdapCoreJarInput $springLdapJarInput $vaultSupportJarInput $javaPasswordJarInput $springTargetJarInput
cp $springLdapCoreJarInput $springLdapJarInput $vaultSupportJarInput $javaPasswordJarInput $springTargetJarInput
#echo ""/dbagiga/gigaspaces-smart-ods/lib/optional/security/* /dbagiga/gs_jars
cp /dbagiga/gigaspaces-smart-ods/lib/optional/security/* /dbagiga/gs_jars
chown -R $applicativeUser:$applicativeUser /dbagiga/*
sleep 10
info "starting gs...\n"
systemctl start gsa
sleep 30