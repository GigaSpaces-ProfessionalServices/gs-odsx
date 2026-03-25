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

if [ "$wantToRemoveKafka" == "y" ]; then
  sudo systemctl stop odsxkafka.service || true
  sleep 2
  [ -n "$KAFKA_LOGS_PATH" ] && sudo rm -rf $KAFKA_LOGS_PATH
  [ -n "$KAFKA_DATA_PATH" ] && sudo rm -rf $KAFKA_DATA_PATH
  [ -n "$KAFKAPATH" ]       && sudo rm -rf $KAFKAPATH
  sudo rm -f $gigapath/kafka_latest
  sudo rm -rf install install.tar ~/setenv.sh /usr/local/bin/st*_kafka.sh \
              /etc/systemd/system/kafka.service /etc/systemd/system/odsxkafka.service
fi

if [ "$wantToRemoveZk" == "y" ]; then
  sudo systemctl stop odsxzookeeper.service || true
  sleep 2
  [ -n "$ZOOKEEPER_DATA_PATH" ] && sudo rm -rf $ZOOKEEPER_DATA_PATH
  [ -n "$ZOOKEEPER_LOGS_PATH" ] && sudo rm -rf $ZOOKEEPER_LOGS_PATH
  [ -n "$ZOOKEEPERPATH" ]       && sudo rm -rf $ZOOKEEPERPATH
  sudo rm -f $gigapath/zookeeper_latest
  sudo rm -rf /usr/local/bin/st*_zookeeper.sh /etc/systemd/system/odsxzookeeper.service
fi


# Stop all DI services before removing files
sudo systemctl stop di-transformations.service || true
sudo systemctl stop di-manager.service || true
sudo systemctl stop di-mdm.service || true
sudo systemctl stop di-flink-taskmanager.service || true
sudo systemctl stop di-flink-jobmanager.service || true
sudo systemctl stop di-subscription-manager-iidr.service || true
sudo systemctl daemon-reload

# Stop Flink cluster gracefully before removing files
sudo bash $gigapath/di-flink/latest-flink/bin/stop-cluster.sh || true
sleep 5

# Remove /home/gsods symlinks created during install
# (use rm -f not rm -rf to remove the symlink itself, not its target)
sudo rm -f /home/gsods/di-flink
sudo rm -f /home/gsods/di-mdm
sudo rm -f /home/gsods/di-manager
sudo rm -f /home/gsods/di-processor
sudo rm -f /home/gsods/di-transformations
sudo rm -f /home/gsods/di-subscription-manager
# Remove the actual directory created for flink checkpoints/savepoints
sudo rm -rf /home/gsods/latest-flink

# Remove DI service files
sudo rm -f /etc/systemd/system/di-flink-jobmanager.service
sudo rm -f /etc/systemd/system/di-flink-taskmanager.service
sudo rm -f /etc/systemd/system/di-mdm.service
sudo rm -f /etc/systemd/system/di-manager.service
sudo rm -f /etc/systemd/system/di-processor.service
sudo rm -f /etc/systemd/system/di-transformations.service
sudo rm -f /etc/systemd/system/di-subscription-manager-iidr.service

# Remove DI installation directories
sudo rm -rf $gigapath/di-flink
sudo rm -rf $gigapath/di-mdm
sudo rm -rf $gigapath/di-manager
sudo rm -rf $gigapath/di-processor
sudo rm -rf $gigapath/di-transformations
sudo rm -rf $gigapath/di-subscription-manager

# Remove DI log directories
sudo rm -rf $gigalogpath/di-flink
sudo rm -rf $gigalogpath/di-mdm
sudo rm -rf $gigalogpath/di-manager
sudo rm -rf $gigalogpath/di-processor
sudo rm -rf $gigalogpath/di-transformations
sudo rm -rf $gigalogpath/di-subscription-manager

# Remove properties files written during install
sudo rm -f $gigapath/di-mdm.properties
sudo rm -f $gigapath/di-manager.properties
sudo rm -f $gigapath/di-processor.properties
sudo rm -f $gigapath/di-transformations.properties
sudo rm -f $gigapath/di-subscription-manager.properties

sudo systemctl daemon-reload
echo "DI removal completed on host: $(hostname)"
