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
  info "Copying file from "$installation_path_flink/$installation_file_flink +" to /dbagiga/di-flink \n"
  cp $installation_path_flink/$installation_file_flink /dbagiga/di-flink
  info "\nExtracting zip file...\n"
  tar -xzf /dbagiga/di-flink/$installation_file_flink --directory /dbagiga/di-flink/
  extracted_folder_flink=$(ls -I "*.tgz" /dbagiga/di-flink/)
  cd /dbagiga/di-flink/
  ln -s $extracted_folder_flink latest-flink
  cd
  sed -i -e 's|rest.address: localhost|#rest.address: localhost|g' /dbagiga/di-flink/latest-flink/conf/flink-conf.yaml
  sed -i -e 's|rest.bind-address: localhost|rest.bind-address: '$currentHost'|g' /dbagiga/di-flink/latest-flink/conf/flink-conf.yaml
  sed -i -e 's|taskmanager.numberOfTaskSlots: 1|taskmanager.numberOfTaskSlots: 10|g' /dbagiga/di-flink/latest-flink/conf/flink-conf.yaml
  if [ "$flinkJobManagerMemoryMetaspaceSize" != "None" ] ; then
    sed -i '/^jobmanager.memory.jvm-metaspace.size/d' /dbagiga/di-flink/latest-flink/conf/flink-conf.yaml
    echo "jobmanager.memory.jvm-metaspace.size: $flinkJobManagerMemoryMetaspaceSize" >> /dbagiga/di-flink/latest-flink/conf/flink-conf.yaml
  fi
  if [ "$flinkTaskManagerMemoryProcessSize" != "None" ] ; then
    sed -i '/^taskmanager.memory.process.size/d' /dbagiga/di-flink/latest-flink/conf/flink-conf.yaml
    echo "taskmanager.memory.process.size: $flinkTaskManagerMemoryProcessSize" >> /dbagiga/di-flink/latest-flink/conf/flink-conf.yaml
  fi
  sed -i -e 's|jobmanager.memory.process.size: 1600m|jobmanager.memory.process.size: 4000m|g' /dbagiga/di-flink/latest-flink/conf/flink-conf.yaml
  sed -i -e 's|/home/gsods|/dbagiga|g' /dbagiga/di-flink/latest-flink/conf/di-flink-jobmanager.service
  sed -i -e 's|/home/gsods|/dbagiga|g' /dbagiga/di-flink/latest-flink/conf/di-flink-taskmanager.service
#  sed -i -e 's|FLINK_HOME=/home/gsods/di-flink/latest-flink|FLINK_HOME=$flinkHome|g' /dbagiga/di-flink/latest-flink/conf/di-flink-jobmanager.service
#  sed -i -e 's|FLINK_LOG_DIR=/home/gsods/di-flink/latest-flink/log|FLINK_LOG_DIR=$flinkLogDir|g' /dbagiga/di-flink/latest-flink/conf/di-flink-jobmanager.service
#  sed -i -e 's|FLINK_HOME=/home/gsods/di-flink/latest-flink|FLINK_HOME=$flinkHome|g' /dbagiga/di-flink/latest-flink/conf/di-flink-taskmanager.service
#  sed -i -e 's|FLINK_LOG_DIR=/home/gsods/di-flink/latest-flink/log|FLINK_LOG_DIR=$flinkLogDir|g' /dbagiga/di-flink/latest-flink/conf/di-flink-taskmanager.service

  cp /dbagiga/di-flink/latest-flink/conf/di-flink-jobmanager.service /etc/systemd/system/
  cp /dbagiga/di-flink/latest-flink/conf/di-flink-taskmanager.service /etc/systemd/system/

  info "\n Installation Flink completed."
}

function installDIMatadata {
  info "\n Installing DI-MDM\n"
  installation_path_mdm=$sourceInstallerDirectory/data-integration/di-mdm
  installation_file_mdm=$(find $installation_path_mdm -name "di-mdm*.gz" -printf "%f\n")
  info "InstallationFile:"$installation_file_mdm"\n"
  mkdir -p /dbagiga/di-mdm
  mkdir -p /dbagigalogs/di-mdm
  chown gsods:gsods /dbagigalogs/di-mdm
  info "Copying file from "$installation_path_mdm/$installation_file_mdm +" to /dbagiga/di-mdm \n"
  cp $installation_path_mdm/$installation_file_mdm /dbagiga/di-mdm
  info "\nExtracting zip file...\n"
  tar -xzf /dbagiga/di-mdm/$installation_file_mdm --directory /dbagiga/di-mdm/
  extracted_folder_mdm=$(ls -I "*.gz" /dbagiga/di-mdm/)
  cd /dbagiga/di-mdm/
  info "Creating symlink for :"$extracted_folder_mdm
  ln -s $extracted_folder_mdm latest-di-mdm
  cd latest-di-mdm
  sed -i -e 's|/home/gsods/di-mdm/latest-di-mdm/logs|/dbagigalogs/di-mdm|g' config/di-mdm.service
  sed -i -e 's|/home/gsods|/dbagiga|g' config/di-mdm.service

  sed -i '/^spring.cloud.zookeeper.connectUrl/d' /dbagiga/di-mdm/latest-di-mdm/config/di-mdm-application.properties
  echo "">>/dbagiga/di-mdm/latest-di-mdm/config/di-mdm-application.properties
  echo "spring.cloud.zookeeper.connectUrl="$kafkaBrokerHost1":2181,"$kafkaBrokerHost3":2181,"$witnessHost":2181">>/dbagiga/di-mdm/latest-di-mdm/config/di-mdm-application.properties

  cd
  info "\nCopying service file\n"
  cp /dbagiga/di-mdm/latest-di-mdm/config/di-mdm.service /etc/systemd/system/
  systemctl daemon-reload
  systemctl enable di-mdm
  #systemctl start di-mdm
  info "\n Installation DI-MDM completed."
}

function installDIManager {
  info "\n Installing DI-Manager\n"
  installation_path_manager=$sourceInstallerDirectory/data-integration/di-manager
  installation_file_manager=$(find $installation_path_manager -name "di-manager*.gz" -printf "%f\n")
  info "InstallationFile:"$installation_file_manager"\n"
  mkdir -p /dbagiga/di-manager
  mkdir -p /dbagigalogs/di-manager
  chown gsods:gsods /dbagigalogs/di-manager
  info "Copying file from "$installation_path_manager/$installation_file_manager +" to /dbagiga/di-manager \n"
  cp $installation_path_manager/$installation_file_manager /dbagiga/di-manager
  info "\nExtracting zip file...\n"
  tar -xzf /dbagiga/di-manager/$installation_file_manager --directory /dbagiga/di-manager/
  extracted_folder_manager=$(ls -I "*.gz" /dbagiga/di-manager/)
  cd /dbagiga/di-manager/
  info "Creating symlink for :"$extracted_folder_manager
  ln -s $extracted_folder_manager latest-di-manager
  cd latest-di-manager
  sed -i -e 's|/home/gsods/di-manager/latest-di-manager/logs|/dbagigalogs/di-manager|g' config/di-manager.service
  sed -i -e 's|/home/gsods|/dbagiga|g' config/di-manager.service
  info "\ncurrentHost::"$kafkaBrokerHost1
  sed -i '/^mdm.server.url/d' /dbagiga/di-manager/latest-di-manager/config/di-manager-application.properties
  sed -i '/^mdm.server.fallback-url/d' /dbagiga/di-manager/latest-di-manager/config/di-manager-application.properties
  echo "mdm.server.url=$kafkaBrokerHost1">>/dbagiga/di-manager/latest-di-manager/config/di-manager-application.properties
  echo "mdm.server.fallback-url=$kafkaBrokerHost2">>/dbagiga/di-manager/latest-di-manager/config/di-manager-application.properties
  cd
  info "\nCopying service file\n"
  cp /dbagiga/di-manager/latest-di-manager/config/di-manager.service /etc/systemd/system/
  systemctl daemon-reload
  systemctl enable di-manager
  #systemctl start di-manager
  info "\n Installation DI-Manager completed.\n"
}

echo " kafkaBrokerHost1 "$2" kafkaBrokerHost2 "$3" kafkaBrokerHost3 "$4" witnessHost "$5" counter ID "$6" installtelegrafFlag "$1" baseFolderLocation "$7
installtelegrafFlag=$1
kafkaBrokerHost1=$2
kafkaBrokerHost2=$3
kafkaBrokerHost3=$4
witnessHost=$5
id=$6
baseFolderLocation=$7
dataFolderKafka=$8
dataFolderZK=$9
logsFolderKafka=${10}
logsFolderZK=${11}
wantInstallJava=${12}
sourceInstallerDirectory=${13}
flinkJobManagerMemoryMetaspaceSize=${15}
flinkTaskManagerMemoryProcessSize=${16}

if [ "$wantInstallJava" == "y" ]; then
    echo "Setup AirGapJava"
    installAirGapJava
fi
echo " dataFolderKafka "$8" dataFolderZK "$9" logsFolderKafka "$logsFolderKafka" logsFolderZK "$logsFolderZK" sourceInstallerDirectory "$sourceInstallerDirectory
echo "flinkJobManagerMemoryMetaspaceSize $flinkJobManagerMemoryMetaspaceSize, flinkTaskManagerMemoryProcessSize=$flinkTaskManagerMemoryProcessSize"
#cd /dbagiga/
tar -xvf install.tar
home_dir=$(pwd)
javaInstalled=$(java -version 2>&1 >/dev/null | egrep "\S+\s+version")
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
    echo "$kafka_home_path">>setenv.sh
    echo "export KAFKA_DATA_PATH="$dataFolderKafka >> setenv.sh
    echo "export KAFKA_LOGS_PATH="$logsFolderKafka >> setenv.sh

    cp $sourceInstallerDirectory"/kafka/jolokia-agent.jar" "$baseFolderLocation$extracted_folder/libs/"
fi

#zookeeper setup
if [[ $id != 2 ]]; then
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
    echo "$zk_home_path">>setenv.sh
    echo "export ZOOKEEPER_DATA_PATH="$dataFolderZK >> setenv.sh
    echo "export ZOOKEEPER_LOGS_PATH="$logsFolderZK >> setenv.sh

fi

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

sed -i -e 's|$ZOOKEEPERPATH/log/kafka|'$dataFolderZK'|g' $ZOOKEEPERPATH/conf/zoo.cfg
sed -i -e 's|/tmp/zookeeper|'$dataFolderZK'|g' $ZOOKEEPERPATH/conf/zoo.cfg
sed -i -e 's|${kafka.logs.dir}|'$logsFolderKafka'|g' $KAFKAPATH/config/log4j.properties
sed -i -e 's|zookeeper.log.dir=.|zookeeper.log.dir='$logsFolderZK'|g' $ZOOKEEPERPATH/conf/log4j.properties

if [[ ${#kafkaBrokerHost1} -ge 3 ]]; then
  # removing all existing properties
  if [[ $id != 2 ]]; then
  sed -i '/^server.1/d' $ZOOKEEPERPATH/conf/zoo.cfg
  sed -i '/^server.2/d' $ZOOKEEPERPATH/conf/zoo.cfg
  sed -i '/^server.3/d' $ZOOKEEPERPATH/conf/zoo.cfg
  sed -i '/^initLimit=/d' $ZOOKEEPERPATH/conf/zoo.cfg
  sed -i '/^syncLimit=/d' $ZOOKEEPERPATH/conf/zoo.cfg
  fi
  if [[ $id != 4 ]]; then
  sed -i '/^broker.id/d' $KAFKAPATH/config/server.properties
  sed -i '/^zookeeper.connect/d' $KAFKAPATH/config/server.properties
  fi

  # adding properties
  if [[ $id != 2 ]]; then
    echo "server.1="$kafkaBrokerHost1":2888:3888">>$ZOOKEEPERPATH/conf/zoo.cfg
    echo "server.2="$kafkaBrokerHost3":2888:3888">>$ZOOKEEPERPATH/conf/zoo.cfg
    echo "server.4="$witnessHost":2888:3888">>$ZOOKEEPERPATH/conf/zoo.cfg
    echo "initLimit=1000">>$ZOOKEEPERPATH/conf/zoo.cfg
    echo "syncLimit=1000">>$ZOOKEEPERPATH/conf/zoo.cfg
  fi

  if [[ $id != 4 ]]; then
    echo "broker.id="$id"">>$KAFKAPATH/config/server.properties
    echo "zookeeper.connect="$kafkaBrokerHost1":2181,"$kafkaBrokerHost3":2181,"$witnessHost":2181">>$KAFKAPATH/config/server.properties
    source setenv.sh
    sed -i -e '/listeners=PLAINTEXT:\/\/:9092/s/^#//g' $KAFKAPATH/config/server.properties
    sed -i -e '/advertised.listeners=PLAINTEXT:/s/^#//g' $KAFKAPATH/config/server.properties
    sed -i '/^offsets.topic.replication.factor/d' $KAFKAPATH/config/server.properties
    sed -i '/^transaction.state.log.replication.factor/d' $KAFKAPATH/config/server.properties
    sed -i '/^transaction.state.log.min.isr/d' $KAFKAPATH/config/server.properties
    sed -i '/^min.insync.replicas/d' $KAFKAPATH/config/server.properties
    sed -i '/^exec $base_dir/d' $KAFKAPATH/bin/kafka-server-start.sh

    echo "# Internal Topic Settings">>$KAFKAPATH/config/server.properties
    echo "offsets.topic.replication.factor=3">>$KAFKAPATH/config/server.properties
    echo "transaction.state.log.replication.factor=3">>$KAFKAPATH/config/server.properties
    echo "transaction.state.log.min.isr=3">>$KAFKAPATH/config/server.properties
    echo "min.insync.replicas=2">>$KAFKAPATH/config/server.properties

    echo "export JMX_PORT=9999" >> $KAFKAPATH/bin/kafka-server-start.sh
    echo "export RMI_HOSTNAME=127.0.0.1" >> $KAFKAPATH/bin/kafka-server-start.sh
    echo 'export KAFKA_JMX_OPTS="-javaagent:'$KAFKAPATH'/libs/jolokia-agent.jar=port=8778,host=$RMI_HOSTNAME -Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false -Djava.rmi.server.hostname=$RMI_HOSTNAME -Dcom.sun.management.jmxremote.rmi.port=$JMX_PORT"' >> $KAFKAPATH/bin/kafka-server-start.sh
    echo 'exec $base_dir/kafka-run-class.sh $EXTRA_ARGS kafka.Kafka "$@"' >> $KAFKAPATH/bin/kafka-server-start.sh

    installFlink
    installDIMatadata
    installDIManager
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
 # elif [[ $id == 4 ]]; then
 #   sed -i -e 's|advertised.listeners=PLAINTEXT://your.host.name:9092|advertised.listeners=PLAINTEXT://'$witnessHost':9092|g' $KAFKAPATH/config/server.properties
 #   sed -i -e '/advertised.listeners=PLAINTEXT/a advertised.host.name='$witnessHost'' $KAFKAPATH/config/server.properties
  fi
  if [[ $id != 2 ]]; then
    echo "$dataFolderZK"myid
    echo "$id">"$dataFolderZK"myid
  fi
  echo "added params"
fi

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
if [[ $id != 2 ]]; then
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
fi

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
fi

if [[ $installtelegrafFlag == "y" ]]; then
  # Install Telegraf
  echo "Installing Telegraf"
  installation_path=$sourceInstallerDirectory/telegraf
  echo "InstallationPath :"$installation_path
  installation_file=$(find $installation_path -name "*.rpm" -printf "%f\n")
  echo "Installation File :"$installation_file
  echo $installation_path"/"$installation_file
  yum install -y $installation_path"/"$installation_file
  cp $home_dir"/install/kafka/kafka.conf" /etc/telegraf/telegraf.d/
  sed -i -e 's|"http://KAFKA_SERVER_IP_ADDRESS:8778/jolokia"|"http://'$kafkaBrokerHost1':8778/jolokia","http://'$kafkaBrokerHost2':8778/jolokia","http://'$kafkaBrokerHost3':8778/jolokia"|g' /etc/telegraf/telegraf.d/kafka.conf
  sed -i -e 's|":2181"|"'$kafkaBrokerHost1':2181","'$witnessHost':2181","'$kafkaBrokerHost3':2181"|g' /etc/telegraf/telegraf.d/kafka.conf

fi

chown gsods:gsods -R $baseFolderLocation*
chown gsods:gsods -R $logsFolderKafka
chown gsods:gsods -R $dataFolderKafka
chown gsods:gsods -R $dataFolderZK

chmod 777 -R $baseFolderLocation
chmod 777 -R $logsFolderKafka
chmod 777 -R $dataFolderKafka
chmod 777 -R $dataFolderZK

#sudo service mongod stop
#sudo yum erase $(rpm -qa | grep mongodb-enterprise)
#sudo rm -r /var/log/mongodb
#sudo rm -r /var/lib/mongo

systemctl daemon-reload

