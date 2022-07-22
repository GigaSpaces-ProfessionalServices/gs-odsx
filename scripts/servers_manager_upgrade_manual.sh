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
sourcePath=$4
cefLoggingJarInput=$5
cefLoggingJarInputTarget=$6
springLdapCoreJarInput=$7
springLdapJarInput=$8
vaultSupportJarInput=$9
javaPasswordJarInput=${10}
springTargetJarInput=${11}
info "stopping gs...\n"
systemctl stop gsa
sleep 30
#echo "path:"$(pwd)
source setenv.sh
cd -P $GS_HOME
currentGSPath=$(pwd)
#echo "currentGSPath "$currentGSPath
currentGSName=$(basename $currentGSPath)
#echo "currentGSName "$currentGSName
# mkdir -p /dbagiga/rollback/$currentGSName
# cp -r $currentGSPath/ /dbagiga/rollback/
cd ..
parentPathGS=$(pwd)
#echo "dir"$(pwd)
ln -s $currentGSName gigaspaces-smart-ods-old
newPackagenameWithoutExt="${newPackagename%.*}"
cd
#echo "parentPathGS:"$parentPathGS
unzip -q $sourcePath -d $parentPathGS
cd -P $parentPathGS
rm gigaspaces-smart-ods
info "changing version to $newPackagenameWithoutExt\n"
#echo "newPackagenameWithoutExt"$newPackagenameWithoutExt
info "creating symlink \n"
ln -s $newPackagenameWithoutExt gigaspaces-smart-ods
cd -P $GS_HOME
#echo ""$(pwd)
cp $currentGSPath/bin/setenv-overrides.sh bin/
#cp -r $currentGSPath/work .
#echo "GS_HOME"$GS_HOME" "$currentGSPath
cp $currentGSPath/gs-license.txt .
#cd
#echo ""$cefLoggingJarInput $cefLoggingJarInputTarget
info "copying required jars...\n"
cp $cefLoggingJarInput $cefLoggingJarInputTarget
cd
rm -f /dbagiga/gs_jars/*
#echo ""$springLdapCoreJarInput $springLdapJarInput $vaultSupportJarInput $javaPasswordJarInput $springTargetJarInput
cp $springLdapCoreJarInput $springLdapJarInput $vaultSupportJarInput $javaPasswordJarInput $springTargetJarInput
#echo ""/dbagiga/gigaspaces-smart-ods/lib/optional/security/* /dbagiga/gs_jars
cp /dbagiga/gigaspaces-smart-ods/lib/optional/security/* /dbagiga/gs_jars
chown -R $applicativeUser:$applicativeUser /dbagiga/*
sleep 10
info "starting gs...\n"
systemctl start gsa
sleep 30