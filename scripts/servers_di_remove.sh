#!/bin/bash
set -x

ENV_CONFIG_PATH=$ENV_CONFIG
if [ -z "$ENV_CONFIG_PATH" ]; then
  echo "Error: ENV_CONFIG is not set. Please set it before running this script."
  exit 1
else
  echo "$ENV_CONFIG_PATH is set to: $ENV_CONFIG_PATH"
fi
ENV_CONFIG_PATH="$ENV_CONFIG_PATH/app.config"

read_property() {
  local prop_name="$1"
  local prop_value
  prop_value=$(grep "^$prop_name=" "$ENV_CONFIG_PATH" | awk -F'=' '{print $2}')
  echo "$prop_value"
}

gigapath=$(read_property "app.giga.path")
gigalogpath=$(read_property "app.gigalog.path")

# Source setenv.sh (written to working dir during install) to load
# KAFKAPATH, KAFKA_DATA_PATH, KAFKA_LOGS_PATH, ZOOKEEPERPATH, etc.
source setenv.sh 2>/dev/null || true

wantToRemoveKafka=$1
wantToRemoveZk=$2
wantToRemoveTelegraf=$3

# Stop all DI services before removing files (suppress "not loaded" noise)
sudo systemctl stop dih-admin.service 2>/dev/null || true
sudo systemctl stop di-transformations.service 2>/dev/null || true
sudo systemctl stop di-manager.service 2>/dev/null || true
sudo systemctl stop di-mdm.service 2>/dev/null || true
sudo systemctl stop di-flink-taskmanager.service 2>/dev/null || true
sudo systemctl stop di-flink-jobmanager.service 2>/dev/null || true
sudo systemctl stop di-subscription-manager-iidr.service 2>/dev/null || true
sudo systemctl daemon-reload

# Stop Flink cluster gracefully before removing files (only if installed)
if [ -f $gigapath/di-flink/latest-flink/bin/stop-cluster.sh ]; then
  bash $gigapath/di-flink/latest-flink/bin/stop-cluster.sh || true
  sleep 5
fi

if [ "$wantToRemoveKafka" == "y" ]; then
  systemctl stop odsxkafka.service 2>/dev/null || true
  sleep 2
  [ -n "$KAFKA_LOGS_PATH" ] && [ -d "$KAFKA_LOGS_PATH" ] && sudo rm -rf $KAFKA_LOGS_PATH
  [ -n "$KAFKA_DATA_PATH" ] && [ -d "$KAFKA_DATA_PATH" ] && sudo rm -rf $KAFKA_DATA_PATH
  [ -n "$KAFKAPATH" ]       && [ -d "$KAFKAPATH" ]       && sudo rm -rf $KAFKAPATH
  [ -L $gigapath/kafka_latest ] && rm -f $gigapath/kafka_latest
  rm -f /usr/local/bin/st*_kafka.sh
  [ -f /etc/systemd/system/kafka.service ]     && rm -f /etc/systemd/system/kafka.service
  [ -f /etc/systemd/system/odsxkafka.service ] && rm -f /etc/systemd/system/odsxkafka.service
  [ -f install.tar ] && rm -f install.tar
  [ -d install ]     && sudo rm -rf install
fi

# Remove setenv.sh only when both Kafka and ZooKeeper are being removed
if [ "$wantToRemoveKafka" == "y" ] && [ "$wantToRemoveZk" == "y" ]; then
  [ -f /root/setenv.sh ] && sudo rm -f /root/setenv.sh
fi

if [ "$wantToRemoveZk" == "y" ]; then
  systemctl stop odsxzookeeper.service 2>/dev/null || true
  sleep 2
  [ -n "$ZOOKEEPER_DATA_PATH" ] && [ -d "$ZOOKEEPER_DATA_PATH" ] && sudo rm -rf $ZOOKEEPER_DATA_PATH
  [ -n "$ZOOKEEPER_LOGS_PATH" ] && [ -d "$ZOOKEEPER_LOGS_PATH" ] && sudo rm -rf $ZOOKEEPER_LOGS_PATH
  [ -n "$ZOOKEEPERPATH" ]       && [ -d "$ZOOKEEPERPATH" ]       && sudo rm -rf $ZOOKEEPERPATH
  [ -L $gigapath/zookeeper_latest ] && rm -f $gigapath/zookeeper_latest
  rm -f /usr/local/bin/st*_zookeeper.sh
  [ -f /etc/systemd/system/odsxzookeeper.service ]    && rm -f /etc/systemd/system/odsxzookeeper.service
fi

if [ "$wantToRemoveTelegraf" == "y" ]; then
  systemctl stop telegraf 2>/dev/null || true
  yum -y remove telegraf
  sleep 2
fi

# Remove /home/gsods symlinks created during install
[ -L /home/gsods/di-flink ]              && rm -f /home/gsods/di-flink
[ -L /home/gsods/di-mdm ]               && rm -f /home/gsods/di-mdm
[ -L /home/gsods/di-manager ]           && rm -f /home/gsods/di-manager
[ -L /home/gsods/di-processor ]         && rm -f /home/gsods/di-processor
[ -L /home/gsods/di-transformations ]   && rm -f /home/gsods/di-transformations
[ -L /home/gsods/dih-admin ]            && rm -f /home/gsods/dih-admin
[ -L /home/gsods/di-subscription-manager ] && rm -f /home/gsods/di-subscription-manager
[ -d /home/gsods/latest-flink ]         && sudo rm -rf /home/gsods/latest-flink

# Remove DI service files
[ -f /etc/systemd/system/di-flink-jobmanager.service ]         && rm -f /etc/systemd/system/di-flink-jobmanager.service
[ -f /etc/systemd/system/di-flink-taskmanager.service ]        && rm -f /etc/systemd/system/di-flink-taskmanager.service
[ -f /etc/systemd/system/di-mdm.service ]                      && rm -f /etc/systemd/system/di-mdm.service
[ -f /etc/systemd/system/di-manager.service ]                  && rm -f /etc/systemd/system/di-manager.service
[ -f /etc/systemd/system/di-processor.service ]                && rm -f /etc/systemd/system/di-processor.service
[ -f /etc/systemd/system/di-transformations.service ]          && rm -f /etc/systemd/system/di-transformations.service
[ -f /etc/systemd/system/dih-admin.service ]                   && rm -f /etc/systemd/system/dih-admin.service
[ -f /etc/systemd/system/di-subscription-manager-iidr.service ] && rm -f /etc/systemd/system/di-subscription-manager-iidr.service

# Remove DI installation directories
[ -d $gigapath/di-flink ]               && sudo rm -rf $gigapath/di-flink
[ -d $gigapath/di-mdm ]                 && sudo rm -rf $gigapath/di-mdm
[ -d $gigapath/di-manager ]             && sudo rm -rf $gigapath/di-manager
[ -d $gigapath/di-processor ]           && sudo rm -rf $gigapath/di-processor
[ -d $gigapath/di-transformations ]     && sudo rm -rf $gigapath/di-transformations
[ -d $gigapath/dih-admin ]              && sudo rm -rf $gigapath/dih-admin
[ -d $gigapath/di-subscription-manager ] && sudo rm -rf $gigapath/di-subscription-manager

# Remove DI log directories
[ -d $gigalogpath/di-flink ]           && sudo rm -rf $gigalogpath/di-flink
[ -d $gigalogpath/di-mdm ]             && sudo rm -rf $gigalogpath/di-mdm
[ -d $gigalogpath/di-manager ]         && sudo rm -rf $gigalogpath/di-manager
[ -d $gigalogpath/di-processor ]       && sudo rm -rf $gigalogpath/di-processor
[ -d $gigalogpath/di-transformations ] && sudo rm -rf $gigalogpath/di-transformations
[ -d $gigalogpath/dih-admin ]          && sudo rm -rf $gigalogpath/dih-admin
[ -d $gigalogpath/di-subscription-manager ] && sudo rm -rf $gigalogpath/di-subscription-manager

# Remove properties files written during install
[ -f $gigapath/di-mdm.properties ]                  && sudo rm -f $gigapath/di-mdm.properties
[ -f $gigapath/di-manager.properties ]              && sudo rm -f $gigapath/di-manager.properties
[ -f $gigapath/di-processor.properties ]            && sudo rm -f $gigapath/di-processor.properties
[ -f $gigapath/di-transformations.properties ]      && sudo rm -f $gigapath/di-transformations.properties
[ -f $gigapath/di-transformations-application.properties ]               && sudo rm -f $gigapath/di-transformations-application.properties
[ -f $gigapath/dih-admin.properties ]               && sudo rm -f $gigapath/dih-admin.properties
[ -f $gigapath/di-subscription-manager.properties ] && sudo rm -f $gigapath/di-subscription-manager.properties

sudo systemctl daemon-reload
echo "DI removal completed on host: $(hostname)"
