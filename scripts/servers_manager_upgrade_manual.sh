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

destinationPath=$1
newPackagename=$2
applicativeUser=$3
info "stopping gs...\n"
systemctl stop gsa
sleep 30
source setenv.sh
cd -P $GS_HOME
currentGSPath=$(pwd)
currentGSName=$(basename $currentGSPath)
# mkdir -p /dbagiga/rollback/$currentGSName
# cp -r $currentGSPath/ /dbagiga/rollback/
cd ..
parentPathGS=$(pwd)
newPackagenameWithoutExt="${newPackagename%.*}"
cd
unzip -q install/gs/upgrade/$newPackagename -d $parentPathGS
cd -P $parentPathGS
rm gigaspaces-smart-ods
info "changing version to $newPackagenameWithoutExt\n"
ln -s $newPackagenameWithoutExt gigaspaces-smart-ods
cd -P $GS_HOME
cp $currentGSPath/bin/setenv-overrides.sh bin/
cp -r $currentGSPath/work .
chown -R $applicativeUser:$applicativeUser *
sleep 10
info "starting gs...\n"
systemctl start gsa
sleep 30