#!/bin/bash
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

function installFlink() {
  info "\nInstalling Flink\n"
  installation_path_flink=$sourceInstallerDirectory/data-integration/di-flink
  installation_file_flink=$(find $installation_path_flink -name "flink*.tgz" -printf "%f\n")
  info "InstallationFile:"$installation_file_flink"\n"
  mkdir -p /dbagiga/di-flink
  mkdir -p /dbagigalogs/di-flink
  #mkdir -p /home/gsods/di-flink
  info "Copying file from "$installation_path_flink/$installation_file_flink +" to /dbagiga/di-flink \n"
  cp $installation_path_flink/$installation_file_flink /dbagiga/di-flink
  info "\nExtracting zip file...\n"
  tar -xzf /dbagiga/di-flink/$installation_file_flink --directory /dbagiga/di-flink/
  chown -R gsods:gsods /dbagiga/di-flink/
  extracted_folder_flink=$(ls -I "*.tgz" /dbagiga/di-flink/)
  cd /dbagiga/di-flink/
  ln -s /dbagiga/di-flink/ /home/gsods/di-flink
  ln -s /dbagiga/di-flink/$extracted_folder_flink /home/gsods/di-flink/latest-flink
  mkdir -p /home/gsods/di-flink/latest-flink/data/savepoints
  mkdir -p /home/gsods/di-flink/latest-flink/data/checkpoints

  mv /dbagiga/di-flink/$extracted_folder_flink/conf/flink-conf.yaml /dbagiga/di-flink/$extracted_folder_flink/conf/flink-conf.yaml_orig

  echo "">>/dbagiga/di-flink/$extracted_folder_flink/conf/flink-conf.yaml
  echo "jobmanager.rpc.address: localhost">>/dbagiga/di-flink/$extracted_folder_flink/conf/flink-conf.yaml
  echo "jobmanager.rpc.port: 6123">>/dbagiga/di-flink/$extracted_folder_flink/conf/flink-conf.yaml
  echo "jobmanager.bind-host: localhost">>/dbagiga/di-flink/$extracted_folder_flink/conf/flink-conf.yaml
  echo "jobmanager.memory.process.size: 4000m">>/dbagiga/di-flink/$extracted_folder_flink/conf/flink-conf.yaml
  echo "taskmanager.bind-host: localhost">>/dbagiga/di-flink/$extracted_folder_flink/conf/flink-conf.yaml
  echo "taskmanager.host: localhost">>/dbagiga/di-flink/$extracted_folder_flink/conf/flink-conf.yaml
  echo "taskmanager.memory.process.size: 4000m">>/dbagiga/di-flink/$extracted_folder_flink/conf/flink-conf.yaml
  echo "taskmanager.numberOfTaskSlots: 10">>/dbagiga/di-flink/$extracted_folder_flink/conf/flink-conf.yaml
  echo "parallelism.default: 1">>/dbagiga/di-flink/$extracted_folder_flink/conf/flink-conf.yaml
  echo "jobmanager.execution.failover-strategy: region">>/dbagiga/di-flink/$extracted_folder_flink/conf/flink-conf.yaml
  echo "jobmanager.memory.jvm-metaspace.size: 1500m">>/dbagiga/di-flink/$extracted_folder_flink/conf/flink-conf.yaml
  echo "state.savepoints.dir: file:///home/gsods/di-flink/latest-flink/data/savepoints">>/dbagiga/di-flink/$extracted_folder_flink/conf/flink-conf.yaml
  echo "state.checkpoints.dir: file:///home/gsods/di-flink/latest-flink/data/checkpoints">>/dbagiga/di-flink/$extracted_folder_flink/conf/flink-conf.yaml
  #sed -i -e 's|/home/gsods|/dbagiga|g' /home/gsods/di-flink/latest-flink/conf/di-flink-jobmanager.service
  #sed -i -e 's|/home/gsods|/dbagiga|g' /home/gsods/di-flink/latest-flink/conf/di-flink-taskmanager.service
  chmod +x /home/gsods/di-flink/latest-flink/bin/*
  cp $installation_path_flink/di-flink-jobmanager.service /etc/systemd/system/
  cp $installation_path_flink/*.jar /home/gsods/di-flink/latest-flink/lib/
  cp $installation_path_flink/di-flink-taskmanager.service /etc/systemd/system/
  mkdir -p /home/gsods/latest-flink/data/checkpoints/ /home/gsods/latest-flink/data/savepoints/
  chown -R gsods:gsods /home/gsods/di-flink/
  restorecon /etc/systemd/system/di-*
  sudo systemctl daemon-reload
  sudo systemctl restart di-flink-taskmanager.service
  sudo systemctl restart di-flink-jobmanager.service

  rm -f /dbagiga/di-flink/di-flink
  info "\n Installation Flink completed."
}

function installDIMatadata {
  info "\n Installing DI-MDM\n"
  installation_path_mdm=$sourceInstallerDirectory/data-integration/di-mdm
  installation_file_mdm=$(find $installation_path_mdm -name "di-mdm*.gz" -printf "%f\n")
  info "InstallationFile:"$installation_file_mdm"\n"
  mkdir -p /dbagiga/di-mdm
  mkdir -p /dbagigalogs/di-mdm
  #mkdir -p /home/gsods/di-mdm
  cp $installation_path_mdm/$installation_file_mdm /dbagiga/di-mdm
  info "\nExtracting zip file...\n"
  tar -xzf /dbagiga/di-mdm/$installation_file_mdm --directory /dbagiga/di-mdm/
  chown -R gsods:gsods /dbagiga/di-mdm/
  extracted_folder_mdm=$(ls -I "*.gz" /dbagiga/di-mdm/)
  cd /dbagiga/di-mdm/
  info "Creating symlink for :"$extracted_folder_mdm
  ln -s /dbagiga/di-mdm/ /home/gsods/di-mdm
  ln -s /dbagiga/di-mdm/$extracted_folder_mdm /home/gsods/di-mdm/latest-di-mdm
  #echo "">>/dbagiga/di-mdm.properties
  echo "spring.profiles.active=zookeeper">/dbagiga/di-mdm.properties
  echo "zookeeper.connectUrl="$kafkaBrokerHost1":2181">>/dbagiga/di-mdm.properties
  #  if [ "$kafkaBrokerCount" == 1 ]; then
  #  echo "zookeeper.connectUrl="$kafkaBrokerHost1":2181">>/home/gsods/di-mdm/latest-di-mdm/config/di-mdm-application.properties
  #else
  #  echo "zookeeper.connectUrl="$kafkaBrokerHost1":2181,"$kafkaBrokerHost2":2181,"$kafkaBrokerHost3":2181">>/home/gsods/di-mdm/latest-di-mdm/config/di-mdm-application.properties
  #fi

  cd /home/gsods/di-mdm/latest-di-mdm/utils
  chown -R gsods:gsods /home/gsods/di-mdm/
  sudo ./install_new_version.sh /dbagiga/di-mdm.properties
  rm -f /dbagiga/di-mdm/di-mdm
}

function installDIManager {
  info "\n Installing DI-Manager\n"
  installation_path_manager=$sourceInstallerDirectory/data-integration/di-manager
  installation_file_manager=$(find $installation_path_manager -name "di-manager*.gz" -printf "%f\n")
  info "InstallationFile:"$installation_file_manager"\n"
  mkdir -p /dbagiga/di-manager
  mkdir -p /dbagigalogs/di-manager
  #mkdir -p /home/gsods/di-manager
  info "Copying file from "$installation_path_manager/$installation_file_manager +" to /dbagiga/di-manager \n"
  cp $installation_path_manager/$installation_file_manager /dbagiga/di-manager
  info "\nExtracting zip file...\n"
  tar -xzf /dbagiga/di-manager/$installation_file_manager --directory /dbagiga/di-manager/
  chown -R gsods:gsods /dbagiga/di-manager/
  extracted_folder_manager=$(ls -I "*.gz" /dbagiga/di-manager/)
  cd /dbagiga/di-manager/
  info "Creating symlink for :"$extracted_folder_manager
  ln -s /dbagiga/di-manager/ /home/gsods/di-manager
  ln -s /dbagiga/di-manager/$extracted_folder_manager /home/gsods/di-manager/latest-di-manager

  #echo "">/dbagiga/di-manager.properties
  echo "springdoc.api-docs.path=/api-docs">/dbagiga/di-manager.properties
  echo "springdoc.swagger-ui.path=/swagger-ui">>/dbagiga/di-manager.properties
  echo "springdoc.swagger-ui.operationsSorter=method">>/dbagiga/di-manager.properties
  sed -i '/^mdm.server.url/d' /dbagiga/di-manager.properties
  echo "mdm.server.url=http://$kafkaBrokerHost1:6081">>/dbagiga/di-manager.properties
  sed -i '/^mdm.server.fallback-url/d' /dbagiga/di-manager.properties
  if [ "$kafkaBrokerCount" == 1 ]; then
    echo "mdm.server.fallback-url=http://$kafkaBrokerHost1:6081">>/dbagiga/di-manager.properties
  else
    echo "mdm.server.fallback-url=http://$kafkaBrokerHost2:6081">>/dbagiga/di-manager.properties
  fi
  echo "server.port=6080">>/dbagiga/di-manager.properties
  echo "mdm.client.timeouts.connection.ms=10000">>/dbagiga/di-manager.properties
  echo "mdm.client.timeouts.read.ms=60000">>/dbagiga/di-manager.properties
  cd /home/gsods/di-manager/latest-di-manager/utils/
  chown -R gsods:gsods /home/gsods/di-manager/
  sudo ./install_new_version.sh /dbagiga/di-manager.properties
  rm -f /dbagiga/di-manager/di-manager
  info "\n Installation DI-Manager completed.\n"
}


function installDIProcessor {
    info "\n Installing DI-Processor\n"
    installation_path_manager=$sourceInstallerDirectory/data-integration/di-processor
    installation_file_manager=$(find $installation_path_manager -name "di-processor*.tgz" -printf "%f\n")
    info "InstallationFile:"$installation_file_manager"\n"
    mkdir -p /dbagiga/di-processor
    mkdir -p /dbagigalogs/di-processor
    info "Copying file from "$installation_path_manager/$installation_file_manager +" to /dbagiga/di-processor \n"
    cp $installation_path_manager/$installation_file_manager /dbagiga/di-processor
    info "\nExtracting zip file...\n"
    tar -xzf /dbagiga/di-processor/$installation_file_manager --directory /dbagiga/di-processor/
    chown gsods:gsods /dbagigalogs/di-processor
    extracted_folder_manager=$(ls -I "*.tgz" /dbagiga/di-processor/)
    cd /dbagiga/di-processor/
    info "Creating symlink for :"$extracted_folder_manager
    ln -s /dbagiga/di-processor/ /home/gsods/di-processor
    ln -s /dbagiga/di-processor/$extracted_folder_manager /home/gsods/di-processor/latest-di-processor

    echo "mdm.server.url=http://$kafkaBrokerHost1:6081">/dbagiga/di-processor.properties
    if [ "$kafkaBrokerCount" == 1 ]; then
      echo "mdm.server.fallback-url=http://$kafkaBrokerHost1:6081">>/dbagiga/di-processor.properties
    else
      echo "mdm.server.fallback-url=http://$kafkaBrokerHost2:6081">>/dbagiga/di-processor.properties
    fi
    #cd /home/gsods/di-mdm/latest-di-mdm/utils/
    #chmod +x *.sh
    #./deploy.sh $installation_path_manager/$installation_file_manager /dbagiga/di-processor.properties

    cd /home/gsods/di-processor/latest-di-processor/utils/
    chown -R gsods:gsods /home/gsods/di-processor/
    sudo ./install_new_version.sh /dbagiga/di-processor.properties
    rm -f /dbagiga/di-processor/di-processor
}

function installDISubscription {
    info "\n Installing DI-Subscription-Manager\n"
    installation_path_manager=$sourceInstallerDirectory/data-integration/di-subscription-manager
    installation_file_manager=$(find $installation_path_manager -name "di-subscription-manager*.tgz" -printf "%f\n")
    info "InstallationFile:"$installation_file_manager"\n"
    mkdir -p /dbagiga/di-subscription-manager
    mkdir -p /dbagigalogs/di-subscription-manager
    chown gsods:gsods /dbagigalogs/di-subscription-manager
    info "Copying file from "$installation_path_manager/$installation_file_manager +" to /dbagiga/di-subscription-manager \n"
    cp $installation_path_manager/$installation_file_manager /dbagiga/di-subscription-manager
    info "\nExtracting zip file...\n"
    tar -xzf /dbagiga/di-subscription-manager/$installation_file_manager --directory /dbagiga/di-subscription-manager/
    extracted_folder_manager=$(ls -I "*.gz" /dbagiga/di-subscription-manager/)
    cd /dbagiga/di-subscription-manager/
    info "Creating symlink for :"$extracted_folder_manager
    ln -s $extracted_folder_manager /home/gsods/di-subscription-manager
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
    echo "kafka.host=gstest-di1.tau.ac.il" >> /dbagiga/di-subscription-manager.properties
    echo "kafka.port=9092" >> /dbagiga/di-subscription-manager.properties
    echo "kafka.topic.prefix=" >> /dbagiga/di-subscription-manager.properties
    echo "" >> /dbagiga/di-subscription-manager.properties
    echo "###iidr kafka properties" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.host=gstest-iidr1.tau.ac.il" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.port=11701" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.username=tsuser" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.password=<password>" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.properties.manager.client.timeouts.connection.ms=10000" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.properties.manager.client.timeouts.read.ms=60000" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.properties.manager.server.url=http://$iidrHost:6085" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.user-exit.properties.file.use-api=false" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.user-exit.properties.file.read-path=/giga/iidr/kafka/instance/KAFKA/conf" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.user-exit.properties.file.write-path=/giga/iidr/kafka/instance/KAFKA/conf" >> /dbagiga/di-subscription-manager.properties
    echo "" >> /dbagiga/di-subscription-manager.properties
    echo "##mdm##" >> /dbagiga/di-subscription-manager.properties
    echo "mdm.client.timeouts.connection.ms=10000" >> /dbagiga/di-subscription-manager.properties
    echo "mdm.client.timeouts.read.ms=60000" >> /dbagiga/di-subscription-manager.properties
    echo "mdm.url=/api/v1" >> /dbagiga/di-subscription-manager.properties
    echo "mdm.server.url=http://$kafkaBrokerHost1:6081" >> /dbagiga/di-subscription-manager.properties
    echo "" >> /dbagiga/di-subscription-manager.properties
    echo "##subscription manager" >> /dbagiga/di-subscription-manager.properties
    echo "subscription-manager.server.url=http://:gstest-iidr1.tau.ac.il:6082" >> /dbagiga/di-subscription-manager.properties
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
    cd /home/gsods/di-subscription-manager/latest-di-subscription-manager/utils
    sudo ./install_new_version.sh /dbagiga/di-subscription-manager.properties
    systemctl daemon-reload
    systemctl enable di-subscription-manager
    systemctl restart di-subscription-manager
    #systemctl start di-manager
    info "\n Installation DI-Manager completed.\n"
}

installtelegrafFlag=$1
kafkaBrokerCount=$2
if [ "$kafkaBrokerCount" == 1 ]; then
  echo "Processing for single node installation."
  echo "nodeListSize" $2" kafkaBrokerHost1 "$3" counter ID "$4" installtelegrafFlag "$1" baseFolderLocation "$5" sourceInstallerDirectory"
  kafkaBrokerHost1=$3
  id=$4
  baseFolderLocation=$5
  dataFolderKafka=$6
  dataFolderZK=$7
  logsFolderKafka=$8
  logsFolderZK=$9
  wantInstallJava=${10}
  sourceInstallerDirectory=${11}
  currentHost=${12}
  flinkJobManagerMemoryMetaspaceSize=${13}
  flinkTaskManagerMemoryProcessSize=${14}
  dimMdmFlinkInstallon1bFlag="y"
  zkClientPort=${15}
  zkInitLimit=${16}
  zkSyncLimit=${17}
  zkTickTime=${18}
  iidrHost=${19}
  iidrUsername=${20}
  iidrPassword=${21}

  echo " dataFolderKafka "$6" dataFolderZK "$7" logsFolderKafka "$8" logsFolderZK "$9" currentHost:"$currentHost
fi
if [ "$kafkaBrokerCount" == 3 ]; then
  echo "Processing for 3 node installation"
  echo "nodeListSize" $2" kafkaBrokerHost1 "$3" kafkaBrokerHost2 "$4" kafkaBrokerHost3 "$5" counter ID "$6" installtelegrafFlag "$1" baseFolderLocation "$7
  kafkaBrokerHost1=$3
  kafkaBrokerHost2=$4
  kafkaBrokerHost3=$5
  id=$6
  baseFolderLocation=$7
  dataFolderKafka=$8
  dataFolderZK=$9
  logsFolderKafka=${10}
  logsFolderZK=${11}
  wantInstallJava=${12}
  sourceInstallerDirectory=${13}
  currentHost=${14}
  flinkJobManagerMemoryMetaspaceSize=${15}
  flinkTaskManagerMemoryProcessSize=${16}
  dimMdmFlinkInstallon1bFlag=${17}
  zkClientPort=${18}
  zkInitLimit=${19}
  zkSyncLimit=${20}
  zkTickTime=${21}
  iidrHost=${22}
  iidrUsername=${23}
  iidrPassword=${24}

  echo " dataFolderKafka "$8" dataFolderZK "$9" logsFolderKafka "${10}" logsFolderZK "${11}" currentHost:"$currentHost
  echo "flinkJobManagerMemoryMetaspaceSize $flinkJobManagerMemoryMetaspaceSize, flinkTaskManagerMemoryProcessSize=$flinkTaskManagerMemoryProcessSize"
fi

if [ "$wantInstallJava" == "y" ]; then
    echo "Setup AirGapJava"
    installAirGapJava
fi
echo " dataFolderKafka "$8" dataFolderZK "$9" logsFolderKafka "$logsFolderKafka" logsFolderZK "$logsFolderZK" sourceInstallerDirectory "$sourceInstallerDirectory
tar -xvf install.tar
home_dir=$(pwd)
javaInstalled=$(java -di-flink-jobmanager.serviceversion 2>&1 >/dev/null | egrep "\S+\s+version")
echo "">>setenv.sh

# Step for KAFKA Unzip and Set KAFKAPATH
if [[ $id != 4 ]]; then
    echo "Install AirGapKafka"
    installation_path=$sourceInstallerDirectory/kafka
    echo "InstallationPath="$installation_path
    installation_file=$(find $installation_path -name "*.tgz" -printf "%f\n")
    echo "InstallationFile:"$installation_file
    mkdir -p $baseFolderLocation
    mkdir -p $dataFolderKafka
    mkdir -p $logsFolderKafka
    tar -xzf $installation_path"/"$installation_file -C $baseFolderLocation
    var=$installation_file
    echo "var"$var
    replace=""
    extracted_folder=${var//'.tgz'/$replace}
    sed -i '/export KAFKAPATH/d' setenv.sh
    sed -i '/export KAFKA_DATA_PATH/d' setenv.sh
    sed -i '/export KAFKA_LOGS_PATH/d' setenv.sh
    echo "extracted_folder: "$extracted_folder
    kafka_home_path="export KAFKAPATH="$baseFolderLocation$extracted_folder
    ln -s $baseFolderLocation$extracted_folder /dbagiga/kafka_latest
    echo "$kafka_home_path">>setenv.sh
    echo "export KAFKA_DATA_PATH="$dataFolderKafka >> setenv.sh
    echo "export KAFKA_LOGS_PATH="$logsFolderKafka >> setenv.sh
fi

#zookeeper setup
#if [[ $id != 2 ]]; then
    installation_path=$sourceInstallerDirectory/zk
    echo "InstallationPath="$installation_path
    installation_file=$(find $installation_path -name "*.gz" -printf "%f\n")
    echo "InstallationFile:"$installation_file
    mkdir -p $baseFolderLocation
    mkdir -p $dataFolderZK
    mkdir -p $logsFolderZK
    tar -xzf $installation_path"/"$installation_file -C $baseFolderLocation
    var=$installation_file
    echo "var"$var
    replace=""
    extracted_folder=${var//'.tar.gz'/$replace}
    zk_home_path="export ZOOKEEPERPATH="$baseFolderLocation$extracted_folder
    ln -s $baseFolderLocation$extracted_folder /dbagiga/zookeeper_latest
    echo "$zk_home_path">>setenv.sh
    echo "export ZOOKEEPER_DATA_PATH="$dataFolderZK >> setenv.sh
    echo "export ZOOKEEPER_LOGS_PATH="$logsFolderZK >> setenv.sh

#fi

# Configuration of log dir
source setenv.sh
echo "kafkaPath :"$KAFKAPATH
#mkdir -p $KAFKAPATH/log
#mkdir -p $KAFKAPATH/log/kafka
#mkdir -p $KAFKAPATH/log/zookeeper

rm -rf $dataFolderZK
rm -rf $logsFolderKafka
rm -rf $dataFolderKafka


mkdir -p $dataFolderZK
mkdir -p $logsFolderKafka
mkdir -p $dataFolderKafka

cp $ZOOKEEPERPATH/conf/zoo_sample.cfg $ZOOKEEPERPATH/conf/zoo.cfg

sed -i -e 's|/tmp/zookeeper|'$dataFolderZK'|g' $ZOOKEEPERPATH/conf/zoo.cfg

sed -i -e 's|$ZOOKEEPERPATH/log/kafka|'$dataFolderZK'|g' $ZOOKEEPERPATH/conf/zoo.cfg
#sed -i -e 's|${kafka.logs.dir}|'$logsFolderKafka'|g' $KAFKAPATH/config/log4j.properties
#sed -i -e 's|zookeeper.log.dir=.|zookeeper.log.dir='$logsFolderZK'|g' $ZOOKEEPERPATH/conf/log4j.properties

#if [[ ${#kafkaBrokerHost1} -ge 3 ]]; then
  # removing all existing properties
  if [[ $id != 2 ]]; then
  sed -i '/^server.1/d' $ZOOKEEPERPATH/conf/zoo.cfg
  sed -i '/^server.2/d' $ZOOKEEPERPATH/conf/zoo.cfg
  sed -i '/^server.3/d' $ZOOKEEPERPATH/conf/zoo.cfg
  sed -i '/^initLimit=/d' $ZOOKEEPERPATH/conf/zoo.cfg
  sed -i '/^syncLimit=/d' $ZOOKEEPERPATH/conf/zoo.cfg
  sed -i '/^tickTime=/d' $ZOOKEEPERPATH/conf/zoo.cfg
  fi
  if [[ $id != 4 ]]; then
  sed -i '/^broker.id/d' $KAFKAPATH/config/server.properties
  sed -i '/^zookeeper.connect/d' $KAFKAPATH/config/server.properties
  fi
  echo "kafkaBrokerCount: "$kafkaBrokerCount
  if [ "$kafkaBrokerCount" == 3 ]; then
    echo "server.1="$kafkaBrokerHost1":2888:3888">>$ZOOKEEPERPATH/conf/zoo.cfg
    echo "server.2="$kafkaBrokerHost2":2888:3888">>$ZOOKEEPERPATH/conf/zoo.cfg
    echo "server.3="$kafkaBrokerHost3":2888:3888">>$ZOOKEEPERPATH/conf/zoo.cfg
    echo "initLimit="$zkInitLimit>>$ZOOKEEPERPATH/conf/zoo.cfg
    echo "syncLimit="$zkSyncLimit>>$ZOOKEEPERPATH/conf/zoo.cfg
    echo "tickTime="$zkTickTime>>$ZOOKEEPERPATH/conf/zoo.cfg
    echo "4lw.commands.whitelist=ruok,stat,mntr">>$ZOOKEEPERPATH/conf/zoo.cfg
    echo "zookeeper.connect="$kafkaBrokerHost1":2181,"$kafkaBrokerHost2":2181,"$kafkaBrokerHost3":2181">>$KAFKAPATH/config/server.properties

    sed -i '/^offsets.topic.replication.factor/d' $KAFKAPATH/config/server.properties
    echo "offsets.topic.replication.factor=3">>$KAFKAPATH/config/server.properties
    sed -i '/^transaction.state.log.replication.factor/d' $KAFKAPATH/config/server.properties
    echo "transaction.state.log.replication.factor=3">>$KAFKAPATH/config/server.properties
    sed -i '/^transaction.state.log.min.isr/d' $KAFKAPATH/config/server.properties
    echo "transaction.state.log.min.isr=3">>$KAFKAPATH/config/server.properties
    sed -i '/^exec $base_dir/d' $KAFKAPATH/bin/kafka-server-start.sh
    echo "min.insync.replicas=2">>$KAFKAPATH/config/server.properties

  fi
  if [ "$kafkaBrokerCount" == 1 ]; then
    echo "server.1="$kafkaBrokerHost1":2888:3888">>$ZOOKEEPERPATH/conf/zoo.cfg
    echo "initLimit="$zkInitLimit>>$ZOOKEEPERPATH/conf/zoo.cfg
    echo "syncLimit="$zkSyncLimit>>$ZOOKEEPERPATH/conf/zoo.cfg
    echo "zookeeper.connect="$kafkaBrokerHost1":2181">>$KAFKAPATH/config/server.properties
    echo "tickTime="$zkTickTime>>$ZOOKEEPERPATH/conf/zoo.cfg
    echo "4lw.commands.whitelist=ruok,stat,mntr">>$ZOOKEEPERPATH/conf/zoo.cfg

    sed -i '/^offsets.topic.replication.factor/d' $KAFKAPATH/config/server.properties
    echo "offsets.topic.replication.factor=1">>$KAFKAPATH/config/server.properties
    sed -i '/^transaction.state.log.replication.factor/d' $KAFKAPATH/config/server.properties
    echo "transaction.state.log.replication.factor=1">>$KAFKAPATH/config/server.properties
    sed -i '/^transaction.state.log.min.isr/d' $KAFKAPATH/config/server.properties
    echo "transaction.state.log.min.isr=1">>$KAFKAPATH/config/server.properties

  fi
  if [[ $id != 4 ]]; then
    echo "broker.id="$id"">>$KAFKAPATH/config/server.properties
    source setenv.sh
    sed -i -e '/listeners=PLAINTEXT:\/\/:9092/s/^#//g' $KAFKAPATH/config/server.properties
    sed -i -e '/advertised.listeners=PLAINTEXT:/s/^#//g' $KAFKAPATH/config/server.properties
    sed -i '/^min.insync.replicas/d' $KAFKAPATH/config/server.properties
    sed -i '/^exec $base_dir/d' $KAFKAPATH/bin/kafka-server-start.sh
    echo "log.segment.bytes=1073741824">>$KAFKAPATH/config/server.properties

    echo "export JMX_PORT=9999" >> $KAFKAPATH/bin/kafka-server-start.sh
    echo "export RMI_HOSTNAME=127.0.0.1" >> $KAFKAPATH/bin/kafka-server-start.sh
    echo 'exec $base_dir/kafka-run-class.sh $EXTRA_ARGS kafka.Kafka "$@"' >> $KAFKAPATH/bin/kafka-server-start.sh
  fi
  if [[ $id == 1 ]]; then
    sed -i -e 's|advertised.listeners=PLAINTEXT://your.host.name:9092|advertised.listeners=PLAINTEXT://'$kafkaBrokerHost1':9092|g' $KAFKAPATH/config/server.properties
    sed -i -e '/advertised.listeners=PLAINTEXT/a advertised.host.name='$kafkaBrokerHost1'' $KAFKAPATH/config/server.properties
  elif [[ $id == 2 ]]; then
    sed -i -e 's|advertised.listeners=PLAINTEXT://your.host.name:9092|advertised.listeners=PLAINTEXT://'$kafkaBrokerHost2':9092|g' $KAFKAPATH/config/server.properties
    sed -i -e '/advertised.listeners=PLAINTEXT/a advertised.host.name='$kafkaBrokerHost2'' $KAFKAPATH/config/server.properties
  elif [[ $id == 3 ]]; then
    sed -i -e 's|advertised.listeners=PLAINTEXT://your.host.name:9092|advertised.listeners=PLAINTEXT://'$kafkaBrokerHost3':9092|g' $KAFKAPATH/config/server.properties
    sed -i -e '/advertised.listeners=PLAINTEXT/a advertised.host.name='$kafkaBrokerHost3'' $KAFKAPATH/config/server.properties
  fi
    echo "$dataFolderZK"myid
    echo "$id">"$dataFolderZK"myid
  echo "added params"

#sed -i -e 's|$KAFKAPATH/log/kafka|'$KAFKAPATH'/log/kafka|g' $KAFKAPATH/config/server.properties
sed -i -e 's|log.dirs=/tmp/kafka-logs|log.dirs='$dataFolderKafka'|g' $KAFKAPATH/config/server.properties
rm -f /var/log/kafka/*
start_kafka_file="start_kafka.sh"
start_zookeeper_file="start_zookeeper.sh"
stop_kafka_file="stop_kafka.sh"
stop_zookeeper_file="stop_zookeeper.sh"
kafka_service_file="odsxkafka.service"
zookeeper_service_file="odsxzookeeper.service"

source setenv.sh
echo "line 149 === $id"
cmd="$ZOOKEEPERPATH/bin/zkServer.sh --config $ZOOKEEPERPATH/conf start"
echo "$cmd">>$start_zookeeper_file

# stop Zookeeper
cmd="$ZOOKEEPERPATH/bin/zookeeper-server-stop.sh --config $ZOOKEEPERPATH/conf stop"
echo "$cmd">>$stop_zookeeper_file

source setenv.sh
home_dir_sh=$(pwd)
source $home_dir_sh/setenv.sh

mv $home_dir_sh/st*_zookeeper.sh /tmp
mv $home_dir_sh/install/zookeeper/$zookeeper_service_file /tmp
mv /tmp/st*_zookeeper.sh /usr/local/bin/
chmod +x /usr/local/bin/st*_zookeeper.sh
mv /tmp/$zookeeper_service_file /etc/systemd/system/

if [[ $id != 4 ]]; then
  echo "line 168 === $id"
  cmd="$KAFKAPATH/bin/kafka-server-start.sh $KAFKAPATH/config/server.properties"
  echo "$cmd">>$start_kafka_file

  # stop KAFKA
  cmd="$KAFKAPATH/bin/kafka-server-stop.sh $KAFKAPATH/config/server.properties"
  echo "$cmd">>$stop_kafka_file
  source setenv.sh

  home_dir_sh=$(pwd)
  source $home_dir_sh/setenv.sh
  if [[ $id == 2 ]]; then
    echo "removing zookeeper service dependency $id"
    sed -i '/^Requires=odsxzookeeper.service/d' $home_dir_sh/install/kafka/$kafka_service_file
  fi
  mv $home_dir_sh/st*_kafka.sh /tmp
  mv $home_dir_sh/install/kafka/$kafka_service_file /tmp
  mv /tmp/st*_kafka.sh /usr/local/bin/
  chmod +x /usr/local/bin/st*_kafka.sh
  mv /tmp/$kafka_service_file /etc/systemd/system/
  if [ $id == 1 ]; then
    chown gsods:gsods -R $baseFolderLocation*
    chown gsods:gsods -R $logsFolderKafka
    chown gsods:gsods -R $dataFolderKafka
    chown gsods:gsods -R $dataFolderZK

    chmod 777 -R $baseFolderLocation
    chmod 777 -R $logsFolderKafka
    chmod 777 -R $dataFolderKafka
    chmod 777 -R $dataFolderZK

    restorecon /etc/systemd/system/odsx*
    systemctl daemon-reload
    sudo systemctl enable --now odsxzookeeper.service
    sudo systemctl enable --now odsxkafka.service
    systemctl daemon-reload
    installDIMatadata
    installDIManager
    installFlink
    installDIProcessor
  fi
fi



if [[ $id != 1 ]]; then
  chown gsods:gsods -R $baseFolderLocation*
  chown gsods:gsods -R $logsFolderKafka
  chown gsods:gsods -R $dataFolderKafka
  chown gsods:gsods -R $dataFolderZK

  chmod 777 -R $baseFolderLocation
  chmod 777 -R $logsFolderKafka
  chmod 777 -R $dataFolderKafka
  chmod 777 -R $dataFolderZK
  restorecon /etc/systemd/system/odsx*
  systemctl daemon-reload
  sudo systemctl enable --now odsxzookeeper.service
  sudo systemctl enable --now odsxkafka.service
  systemctl daemon-reload
fi
