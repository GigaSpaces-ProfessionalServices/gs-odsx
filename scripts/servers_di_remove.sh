#!/bin/bash
# Set XDG_RUNTIME_DIR for systemctl --user over SSH
# Load shared read_property helper (no-op when piped over SSH; see lib_app_config.sh).
[ -r "$(dirname "$0")/lib_app_config.sh" ] && source "$(dirname "$0")/lib_app_config.sh"

export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus

set -x

ENV_CONFIG_PATH=$ENV_CONFIG
if [ -z "$ENV_CONFIG_PATH" ]; then
  echo "Error: ENV_CONFIG is not set. Please set it before running this script."
  exit 1
else
  echo "$ENV_CONFIG_PATH is set to: $ENV_CONFIG_PATH"
fi
ENV_CONFIG_PATH="$ENV_CONFIG_PATH/app.config"


gigapath=$(read_property "app.giga.path")
gigalogpath=$(read_property "app.gigalog.path")

# Source setenv.sh (written to working dir during install) to load
# KAFKAPATH, KAFKA_DATA_PATH, KAFKA_LOGS_PATH, ZOOKEEPERPATH, etc.
source setenv.sh 2>/dev/null || true

wantToRemoveKafka=$1
wantToRemoveZk=$2

if [ "$wantToRemoveKafka" == "y" ]; then
  systemctl --user stop odsxkafka.service || true
  sleep 2
  [ -n "$KAFKA_LOGS_PATH" ] && rm -rf $KAFKA_LOGS_PATH
  [ -n "$KAFKA_DATA_PATH" ] && rm -rf $KAFKA_DATA_PATH
  [ -n "$KAFKAPATH" ]       && rm -rf $KAFKAPATH
  rm -f $gigapath/kafka_latest
  rm -rf install install.tar ~/setenv.sh $gigapath/bin/st*_kafka.sh \
              $HOME/.config/systemd/user/kafka.service $HOME/.config/systemd/user/odsxkafka.service
fi

if [ "$wantToRemoveZk" == "y" ]; then
  systemctl --user stop odsxzookeeper.service || true
  sleep 2
  [ -n "$ZOOKEEPER_DATA_PATH" ] && rm -rf $ZOOKEEPER_DATA_PATH
  [ -n "$ZOOKEEPER_LOGS_PATH" ] && rm -rf $ZOOKEEPER_LOGS_PATH
  [ -n "$ZOOKEEPERPATH" ]       && rm -rf $ZOOKEEPERPATH
  rm -f $gigapath/zookeeper_latest
  rm -rf $gigapath/bin/st*_zookeeper.sh $HOME/.config/systemd/user/odsxzookeeper.service
fi


# Stop all DI services before removing files
systemctl --user stop di-transformations.service || true
systemctl --user stop di-manager.service || true
systemctl --user stop di-mdm.service || true
systemctl --user stop di-flink-taskmanager.service || true
systemctl --user stop di-flink-jobmanager.service || true
systemctl --user stop di-subscription-manager-iidr.service || true
systemctl --user daemon-reload

# Stop Flink cluster gracefully before removing files
bash $gigapath/di-flink/latest-flink/bin/stop-cluster.sh || true
sleep 5

# Remove $HOME symlinks created during install
# (use rm -f not rm -rf to remove the symlink itself, not its target)
rm -f $HOME/di-flink
rm -f $HOME/di-mdm
rm -f $HOME/di-manager
rm -f $HOME/di-processor
rm -f $HOME/di-transformations
rm -f $HOME/di-subscription-manager
# Remove the actual directory created for flink checkpoints/savepoints
rm -rf $HOME/latest-flink

# Remove DI service files
rm -f $HOME/.config/systemd/user/di-flink-jobmanager.service
rm -f $HOME/.config/systemd/user/di-flink-taskmanager.service
rm -f $HOME/.config/systemd/user/di-mdm.service
rm -f $HOME/.config/systemd/user/di-manager.service
rm -f $HOME/.config/systemd/user/di-processor.service
rm -f $HOME/.config/systemd/user/di-transformations.service
rm -f $HOME/.config/systemd/user/di-subscription-manager-iidr.service

# Remove DI installation directories
rm -rf $gigapath/di-flink
rm -rf $gigapath/di-mdm
rm -rf $gigapath/di-manager
rm -rf $gigapath/di-processor
rm -rf $gigapath/di-transformations
rm -rf $gigapath/di-subscription-manager

# Remove DI log directories
rm -rf $gigalogpath/di-flink
rm -rf $gigalogpath/di-mdm
rm -rf $gigalogpath/di-manager
rm -rf $gigalogpath/di-processor
rm -rf $gigalogpath/di-transformations
rm -rf $gigalogpath/di-subscription-manager

# Remove properties files written during install
rm -f $gigapath/di-mdm.properties
rm -f $gigapath/di-manager.properties
rm -f $gigapath/di-processor.properties
rm -f $gigapath/di-transformations.properties
rm -f $gigapath/di-subscription-manager.properties

systemctl --user daemon-reload
echo "DI removal completed on host: $(hostname)"
