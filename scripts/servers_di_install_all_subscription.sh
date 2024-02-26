#!/bin/bash
#set -x
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
    #chown gsods:gsods /dbagigalogs/di-subscription-manager
    info "Copying file from "$installation_path_manager/$installation_file_manager +" to /dbagiga/di-subscription-manager \n"
    cp $installation_path_manager/$installation_file_manager /dbagiga/di-subscription-manager
    info "\nExtracting zip file...\n"
    tar -xzf /dbagiga/di-subscription-manager/$installation_file_manager --directory /dbagiga/di-subscription-manager/
    chown gsods:gsods /dbagiga/di-subscription-manager
    extracted_folder_manager=$(ls -I "*.tgz" /dbagiga/di-subscription-manager/)
    cd /dbagiga/di-subscription-manager/
    info "Creating symlink for :"$extracted_folder_manager

    ln -s /dbagiga/di-subscription-manager/ /home/gsods/di-subscription-manager
    #ln -s $extracted_folder_manager /home/gsods/di-subscription-manager/
    ln -s /dbagiga/di-subscription-manager/$extracted_folder_manager /home/gsods/di-subscription-manager/latest-di-subscription-manager

    echo "##iidr.as##" > /dbagiga/di-subscription-manager.properties
    echo "iidr-as.hostname=$iidrHost" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-as.port=10101" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-as.username=$iidrUsername" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-as.password=$iidrPassword" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-as.source-datastore.mirror_auto_restart_interval_seconds=15" >> /dbagiga/di-subscription-manager.properties
    echo "" >> /dbagiga/di-subscription-manager.properties
    echo "datastore.save-credentials-in-mdm=false" >> /dbagiga/di-subscription-manager.properties
    echo "" >> /dbagiga/di-subscription-manager.properties
    echo "###kafka properties" >> /dbagiga/di-subscription-manager.properties
    echo "kafka.host=$kafkaBrokerHost1" >> /dbagiga/di-subscription-manager.properties
    echo "kafka.port=9092" >> /dbagiga/di-subscription-manager.properties
    echo "kafka.topic.prefix=" >> /dbagiga/di-subscription-manager.properties
    echo "" >> /dbagiga/di-subscription-manager.properties
    echo "###iidr kafka properties" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.host=$iidrHost" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.port=11701" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.username=$iidrKafkaUsername" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.password=$iidrKafkaPassword" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.properties.manager.client.timeouts.connection.ms=10000" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.properties.manager.client.timeouts.read.ms=60000" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.properties.manager.server.url=http://$iidrHost:6085" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.user-exit.properties.file.use-api=false" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.user-exit.properties.file.read-path=$iidrKafkaReadpath" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.user-exit.properties.file.write-path=$iidrKafkaWritepath" >> /dbagiga/di-subscription-manager.properties
    echo "" >> /dbagiga/di-subscription-manager.properties
    echo "##mdm##" >> /dbagiga/di-subscription-manager.properties
    echo "mdm.client.timeouts.connection.ms=10000" >> /dbagiga/di-subscription-manager.properties
    echo "mdm.client.timeouts.read.ms=60000" >> /dbagiga/di-subscription-manager.properties
    echo "mdm.url=/api/v1" >> /dbagiga/di-subscription-manager.properties
    echo "mdm.server.url=http://$kafkaBrokerHost1:6081" >> /dbagiga/di-subscription-manager.properties
    echo "" >> /dbagiga/di-subscription-manager.properties
    echo "##subscription manager" >> /dbagiga/di-subscription-manager.properties
    echo "subscription-manager.server.url=http://:$iidrHost:6082" >> /dbagiga/di-subscription-manager.properties
    echo "subscription-manager.feature.supports-transaction=true" >> /dbagiga/di-subscription-manager.properties
    echo "#mdm-waiting-timeout is in seconds" >> /dbagiga/di-subscription-manager.properties
    echo "subscription-manager.mdm-availability-waiting-timeout-seconds=300" >> /dbagiga/di-subscription-manager.properties
    echo "server.port=6082" >> /dbagiga/di-subscription-manager.properties

    echo "##swagger-ui##" >> /dbagiga/di-subscription-manager.properties
    echo "springdoc.api-docs.path=/api-docs" >> /dbagiga/di-subscription-manager.properties
    echo "springdoc.swagger-ui.operationsSorter=method" >> /dbagiga/di-subscription-manager.properties
    echo "springdoc.swagger-ui.path=/swagger-ui" >> /dbagiga/di-subscription-manager.properties
    echo "springdoc.swagger-ui.request-timeout=10000 # Timeout value in milliseconds" >> /dbagiga/di-subscription-manager.properties
    echo "" >> /dbagiga/di-subscription-manager.properties
    echo "logging.level.org.springframework.web.filter.CommonsRequestLoggingFilter=DEBUG" >> /dbagiga/di-subscription-manager.properties
    sed -i -e 's|logs/di-subscription-manager.log|/dbagigalogs/di-iidr/di-subscription-manager.log|g' /etc/systemd/system/di-subscription-manager-iidr.service
    cd /home/gsods/di-subscription-manager/latest-di-subscription-manager/utils/
    ./install_new_version.sh /dbagiga/di-subscription-manager.properties
    chown -R gsods:gsods /home/gsods/di-subscription-manager/
    systemctl daemon-reload
    systemctl enable di-subscription-manager
    systemctl restart di-subscription-manager
    #systemctl start di-manager
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

tar -xvf install.tar
home_dir=$(pwd)
javaInstalled=$(java -di-flink-jobmanager.serviceversion 2>&1 >/dev/null | egrep "\S+\s+version")
echo "">>setenv.sh

installDISubscription
sleep 10