#!/bin/bash
echo "Starting DI Installation."
#echo "Extracting install.tar to "$targetDir
#echo " installtelegrafFlag "$1

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
echo " dataFolderKafka "$8" dataFolderZK "$9" logsFolderKafka "$logsFolderKafka" logsFolderZK "$logsFolderZK
cd /dbagiga/
tar -xvf install.tar
home_dir=$(pwd)
javaInstalled=$(java -version 2>&1 >/dev/null | egrep "\S+\s+version")
echo "">>setenv.sh
if [[ ${#javaInstalled} -eq 0 ]]; then
  installation_path=$home_dir/install/java
  installation_file=$(find $installation_path -name *.rpm -printf "%f\n")
  echo "Installation File :"$installation_file
  echo $installation_path"/"$installation_file
  rpm -ivh $installation_path"/"$installation_file
  sed -i '/export JAVA_HOME=/d' setenv.sh
  java_home_path="export JAVA_HOME='$(readlink -f /usr/bin/javac | sed "s:/bin/javac::")'"

  echo "$java_home_path">>setenv.sh
  echo "installAirGapJava -Done!"
else
  echo "Java already installed.!!!"
fi

sed -i '/^kafka_/d' setenv.sh
sed -i '/^kafka-/d' setenv.sh

# Step for KAFKA Unzip and Set KAFKAPATH
if [[ $id != 4 ]]; then
    echo "Install AirGapKafka"
    installation_path=$home_dir/install/kafka
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

    cp $home_dir"/install/jolokia/jolokia-agent.jar" "$baseFolderLocation$extracted_folder/libs/"
fi

#zookeeper setup
if [[ $id != 2 ]]; then
    installation_path=$home_dir/install/zookeeper
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
    sed -i '/export ZOOKEEPERPATH/d' setenv.sh
    sed -i '/export ZOOKEEPER_DATA_PATH/d' setenv.sh
    sed -i '/export ZOOKEEPER_LOGS_PATH/d' setenv.sh

    echo "$zk_home_path">>setenv.sh
    echo "export ZOOKEEPER_DATA_PATH="$dataFolderZK >> setenv.sh
    echo "export ZOOKEEPER_LOGS_PATH="$logsFolderZK >> setenv.sh

fi

# Configuration of log dir
source setenv.sh
echo "kafkaPath :"$KAFKAPATH
echo "zookeeperPath :"$ZOOKEEPERPATH
#mkdir -p $KAFKAPATH/log
#mkdir -p $KAFKAPATH/log/kafka
#mkdir -p $KAFKAPATH/log/zookeeper

rm -rf $dataFolderZK
rm -rf $logsFolderKafka
rm -rf $dataFolderKafka


mkdir -p $dataFolderZK
mkdir -p $logsFolderKafka
mkdir -p $dataFolderKafka

if [[ ${#kafkaBrokerHost1} -ge 3 ]]; then
  # removing all existing properties
  if [[ $id != 2 ]]; then
    cp $ZOOKEEPERPATH/conf/zoo_sample.cfg $ZOOKEEPERPATH/conf/zoo.cfg
    sed -i '/^server.1/d' $ZOOKEEPERPATH/conf/zoo.cfg
    sed -i '/^server.2/d' $ZOOKEEPERPATH/conf/zoo.cfg
    sed -i '/^server.3/d' $ZOOKEEPERPATH/conf/zoo.cfg
    sed -i '/^initLimit=/d' $ZOOKEEPERPATH/conf/zoo.cfg
    sed -i '/^syncLimit=/d' $ZOOKEEPERPATH/conf/zoo.cfg
    sed -i -e 's|$ZOOKEEPERPATH/log/kafka|'$dataFolderZK'|g' $ZOOKEEPERPATH/conf/zoo.cfg
    sed -i -e 's|/tmp/zookeeper|'$dataFolderZK'|g' $ZOOKEEPERPATH/conf/zoo.cfg
    sed -i -e 's|zookeeper.log.dir=.|zookeeper.log.dir='$logsFolderZK'|g' $ZOOKEEPERPATH/conf/log4j.properties
  fi
  if [[ $id != 4 ]]; then
    sed -i '/^broker.id/d' $KAFKAPATH/config/server.properties
    sed -i '/^zookeeper.connect/d' $KAFKAPATH/config/server.properties
    sed -i -e 's|${kafka.logs.dir}|'$logsFolderKafka'|g' $KAFKAPATH/config/log4j.properties
  fi

  # adding properties
  if [[ $id != 2 ]]; then
    echo "server.1="$kafkaBrokerHost1":2888:3888">>$ZOOKEEPERPATH/conf/zoo.cfg
    echo "server.3="$kafkaBrokerHost3":2888:3888">>$ZOOKEEPERPATH/conf/zoo.cfg
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
  mv $home_dir_sh/install/$zookeeper_service_file /tmp
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
    sed -i '/^Requires=odsxzookeeper.service/d' $home_dir_sh/install/$kafka_service_file
  fi
  mv $home_dir_sh/st*_kafka.sh /tmp
  mv $home_dir_sh/install/$kafka_service_file /tmp
  mv /tmp/st*_kafka.sh /usr/local/bin/
  chmod +x /usr/local/bin/st*_kafka.sh
  mv /tmp/$kafka_service_file /etc/systemd/system/
fi

if [[ $installtelegrafFlag == "y" ]]; then
  # Install Telegraf
  echo "Installing Telegraf"
  installation_path=$home_dir/install/telegraf
  echo "InstallationPath :"$installation_path
  installation_file=$(find $installation_path -name *.rpm -printf "%f\n")
  echo "Installation File :"$installation_file
  echo $installation_path"/"$installation_file
  yum install -y $installation_path"/"$installation_file
  cp $home_dir"/install/jolokia/kafka.conf" /etc/telegraf/telegraf.d/
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

