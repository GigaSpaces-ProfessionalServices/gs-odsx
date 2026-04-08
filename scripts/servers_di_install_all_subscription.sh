#!/bin/bash
# set -x
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
info "Starting DI Installation.\n"
#echo "Extracting install.tar to "$targetDir
#echo " installtelegrafFlag "$1

function installAirGapJava {
  installation_path=$sourceInstallerDirectory/jdk
  installation_file=$(find $installation_path -name *.rpm -printf "%f\n")
  echo "Installation File :"$installation_file
  echo $installation_path"/"$installation_file
  rpm -ivh $installation_path"/"$installation_file
  sed -i '/export JAVA_HOME=/d' setenv.sh
  java_home_path="export JAVA_HOME='$(readlink -f /usr/bin/javac | sed "s:/bin/javac::")'"
  echo "$java_home_path">>setenv.sh
  echo "installAirGapJava -Done!"
}

function installDISubscription {
    info "\n Installing DI-Subscription-Manager\n"
    installation_path_manager=$sourceInstallerDirectory/data-integration/di-subscription-manager
    installation_file_manager=$(find $installation_path_manager -name "di-subscription-manager*.tgz" -printf "%f\n")
    info "InstallationFile:"$installation_file_manager"\n"
    mkdir -p /dbagiga/di-subscription-manager
    mkdir -p /dbagigalogs/di-subscription-manager
    mkdir -p /dbagigalogs/di-iidr
    chown gsods:gsods /dbagigalogs/di-iidr
    info "Copying file from "$installation_path_manager/$installation_file_manager +" to /dbagiga/di-subscription-manager \n"
    cp $installation_path_manager/$installation_file_manager /dbagiga/di-subscription-manager
    info "\nExtracting zip file...\n"
    tar -xzf /dbagiga/di-subscription-manager/$installation_file_manager --directory /dbagiga/di-subscription-manager/
    chown gsods:gsods /dbagiga/di-subscription-manager
    extracted_folder_manager=$(ls -I "*.tgz" /dbagiga/di-subscription-manager/)
    info "Creating symlink for :"$extracted_folder_manager

    # Create symlink in gsods home (install_new_version.sh expects /home/gsods/di-subscription-manager to exist)
     ln -snf /dbagiga/di-subscription-manager /home/gsods/di-subscription-manager

    # Patch service file log path in config template BEFORE install_new_version.sh deploys it to /etc/systemd/system/
     sed -i 's|logs/di-subscription-manager-iidr.log|/dbagigalogs/di-iidr/di-subscription-manager.log|g' \
        /dbagiga/di-subscription-manager/$extracted_folder_manager/config/di-subscription-manager-iidr.service

    # Write properties file from scratch matching QA server config
     mkdir -p $(dirname /dbagiga/di-subscription-manager.properties)
     tee /dbagiga/di-subscription-manager.properties > /dev/null << PROPEOF
##iidr.as##
iidr-as.hostname=${iidrHost}
iidr-as.port=10101
iidr-as.username=${iidrUsername}
iidr-as.password=${iidrPassword}
iidr-as.source-datastore.mirror_auto_restart_interval_seconds=15

datastore.save-credentials-in-mdm=false

###kafka properties
kafka.host=${kafkaBrokerHost1}
kafka.port=9092
kafka.topic.prefix=

###iidr kafka properties
iidr-kafka.host=${iidrHost}
iidr-kafka.port=11701
iidr-kafka.username=${iidrKafkaUsername}
iidr-kafka.password=${iidrKafkaPassword}
iidr-kafka.properties.manager.client.timeouts.connection.ms=10000
iidr-kafka.properties.manager.client.timeouts.read.ms=60000
iidr-kafka.properties.manager.server.url=http://${iidrHost}:6085
iidr-kafka.user-exit.properties.file.use-api=false
iidr-kafka.user-exit.properties.file.read-path=${iidrKafkaReadpath}
iidr-kafka.user-exit.properties.file.write-path=${iidrKafkaWritepath}

##mdm##
mdm.client.timeouts.connection.ms=10000
mdm.client.timeouts.read.ms=60000
mdm.url=/api/v1
mdm.server.url=http://${kafkaBrokerHost1}:6081

##subscription manager
subscription-manager.server.url=http://${iidrHost}:6082
subscription-manager.feature.supports-transaction=true
#mdm-waiting-timeout is in seconds
subscription-manager.mdm-availability-waiting-timeout-seconds=300
server.port=6082

##swagger-ui##
springdoc.api-docs.path=/api-docs
springdoc.swagger-ui.operationsSorter=method
springdoc.swagger-ui.path=/swagger-ui
springdoc.swagger-ui.request-timeout=10000 # Timeout value in milliseconds

logging.level.org.springframework.web.filter.CommonsRequestLoggingFilter=DEBUG
PROPEOF

    # install_new_version.sh: copies properties to config/, deploys service file to /etc/systemd/system/,
    # runs daemon-reload, enable, and starts the service
    cd /dbagiga/di-subscription-manager/$extracted_folder_manager/utils/
    ./install_new_version.sh /dbagiga/di-subscription-manager.properties
    chown -R gsods:gsods /home/gsods/di-subscription-manager/
    systemctl daemon-reload
    info "\n Installation DI-Subscription-Manager completed.\n"
}


iidrHost=$1
iidrUsername=$2
iidrPassword=$3
iidrKafkaUsername=$4
iidrKafkaPassword=$5
kafkaBrokerHost1=$6
sourceInstallerDirectory=$7
iidrKafkaReadpath=$8
iidrKafkaWritepath=$9

if [ "$wantInstallJava" == "y" ]; then
    echo "Setup AirGapJava"
    installAirGapJava
fi

[ ! -f install.tar ] &&  cp /root/install.tar . 2>/dev/null || true
tar -xvf install.tar
home_dir=$(pwd)
javaInstalled=$(java -version 2>&1 | egrep "\S+\s+version")
echo "">>setenv.sh

installDISubscription
sleep 10
