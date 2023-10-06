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
gigaDir=$4
sourcePath=$5
cefLoggingJarInput=$6
cefLoggingJarInputTarget=$7
springLdapCoreJarInput=$8
springLdapJarInput=$9
vaultSupportJarInput=${10}
javaPasswordJarInput=${11}
springTargetJarInput=${12}

info "stopping gs...\n"
systemctl stop gsa
sleep 30
#echo "path:"$(pwd)
source setenv.sh
cd -P $GS_HOME
currentGSPath=$(pwd)
#echo "currentGSPath "$currentGSPath
currentGSName=$(basename $currentGSPath)
info "currentGSName "$currentGSName
# mkdir -p /dbagiga/rollback/$currentGSName
# cp -r $currentGSPath/ /dbagiga/rollback/
cd ..
parentPathGS=$(pwd)
#echo "parentPathGS: "$parentPathGS
if [ -d "gigaspaces-smart-ods-old" ]; then
  cd -P $gigaDir/gigaspaces-smart-ods-old
  previousGSPath=$(pwd)
  previousGSName=$(basename $previousGSPath)
  cd $gigaDir
  info "previousGSPath "$previousGSName
  rm -f gigaspaces-smart-ods-old
  rm -rf $previousGSName
fi
#echo "dir"$(pwd)
rm -f gigaspaces-smart-ods-old
#echo ""$currentGSName "gigaspaces-smart-ods-old"
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
rm -f $gigaDir/gs_jars/*
#echo ""$springLdapCoreJarInput $springLdapJarInput $vaultSupportJarInput $javaPasswordJarInput $springTargetJarInput
cp $springLdapCoreJarInput $springLdapJarInput $vaultSupportJarInput $javaPasswordJarInput $springTargetJarInput
#echo ""/dbagiga/gigaspaces-smart-ods/lib/optional/security/* /dbagiga/gs_jars
cp $gigaDir/gigaspaces-smart-ods/lib/optional/security/* $gigaDir/gs_jars
chown -R $applicativeUser:$applicativeUser $gigaDir/*
sleep 10
info "starting gs...\n"
systemctl start gsa
sleep 30