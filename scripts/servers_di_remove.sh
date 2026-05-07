#!/bin/bash
# set -x

source setenv.sh 2>/dev/null || true

wantToRemoveKafka=$1
wantToRemoveZk=$2
wantToRemoveTelegraf=$3

# Stop all DI services before removing files (suppress "not loaded" noise)
systemctl stop dih-admin.service 2>/dev/null || true
systemctl stop di-transformations.service 2>/dev/null || true
systemctl stop di-manager.service 2>/dev/null || true
systemctl stop di-mdm.service 2>/dev/null || true
systemctl stop di-flink-taskmanager.service 2>/dev/null || true
systemctl stop di-flink-jobmanager.service 2>/dev/null || true
systemctl stop di-subscription-manager-iidr.service 2>/dev/null || true
systemctl daemon-reload

# Stop Flink cluster gracefully before removing files (only if installed)
if [ -f /dbagiga/di-flink/latest-flink/bin/stop-cluster.sh ]; then
  bash /dbagiga/di-flink/latest-flink/bin/stop-cluster.sh || true
  sleep 5
fi

if [ "$wantToRemoveKafka" == "y" ]; then
  systemctl stop odsxkafka.service 2>/dev/null || true
  sleep 2
  [ -n "$KAFKA_LOGS_PATH" ] && [ -d "$KAFKA_LOGS_PATH" ] && rm -rf $KAFKA_LOGS_PATH
  [ -n "$KAFKA_DATA_PATH" ] && [ -d "$KAFKA_DATA_PATH" ] && rm -rf $KAFKA_DATA_PATH
  [ -n "$KAFKAPATH" ]       && [ -d "$KAFKAPATH" ]       && rm -rf $KAFKAPATH
  [ -L /dbagiga/kafka_latest ] && rm -f /dbagiga/kafka_latest
  rm -f /usr/local/bin/st*_kafka.sh
  [ -f /etc/systemd/system/kafka.service ]     && rm -f /etc/systemd/system/kafka.service
  [ -f /etc/systemd/system/odsxkafka.service ] && rm -f /etc/systemd/system/odsxkafka.service
  [ -f install.tar ] && rm -f install.tar
  [ -d install ]     && rm -rf install
fi

# Remove setenv.sh only when both Kafka and ZooKeeper are being removed
if [ "$wantToRemoveKafka" == "y" ] && [ "$wantToRemoveZk" == "y" ]; then
  [ -f /dbagiga/setenv.sh ] && rm -f /dbagiga/setenv.sh
fi

if [ "$wantToRemoveZk" == "y" ]; then
  systemctl stop odsxzookeeper.service 2>/dev/null || true
  sleep 2
  [ -n "$ZOOKEEPER_DATA_PATH" ] && [ -d "$ZOOKEEPER_DATA_PATH" ] && rm -rf $ZOOKEEPER_DATA_PATH
  [ -n "$ZOOKEEPER_LOGS_PATH" ] && [ -d "$ZOOKEEPER_LOGS_PATH" ] && rm -rf $ZOOKEEPER_LOGS_PATH
  [ -n "$ZOOKEEPERPATH" ]       && [ -d "$ZOOKEEPERPATH" ]       && rm -rf $ZOOKEEPERPATH
  [ -L /dbagiga/zookeeper_latest ] && rm -f /dbagiga/zookeeper_latest
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
[ -d /home/gsods/latest-flink ]         && rm -rf /home/gsods/latest-flink

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
[ -d /dbagiga/di-flink ]               && rm -rf /dbagiga/di-flink
[ -d /dbagiga/di-mdm ]                 && rm -rf /dbagiga/di-mdm
[ -d /dbagiga/di-manager ]             && rm -rf /dbagiga/di-manager
[ -d /dbagiga/di-processor ]           && rm -rf /dbagiga/di-processor
[ -d /dbagiga/di-transformations ]     && rm -rf /dbagiga/di-transformations
[ -d /dbagiga/dih-admin ]              && rm -rf /dbagiga/dih-admin
[ -d /dbagiga/di-subscription-manager ] && rm -rf /dbagiga/di-subscription-manager

# Remove DI log directories
[ -d /dbagigalogs/di-flink ]           && rm -rf /dbagigalogs/di-flink
[ -d /dbagigalogs/di-mdm ]             && rm -rf /dbagigalogs/di-mdm
[ -d /dbagigalogs/di-manager ]         && rm -rf /dbagigalogs/di-manager
[ -d /dbagigalogs/di-processor ]       && rm -rf /dbagigalogs/di-processor
[ -d /dbagigalogs/di-transformations ] && rm -rf /dbagigalogs/di-transformations
[ -d /dbagigalogs/dih-admin ]          && rm -rf /dbagigalogs/dih-admin
[ -d /dbagigalogs/di-subscription-manager ] && rm -rf /dbagigalogs/di-subscription-manager

# Remove properties files written during install
[ -f /dbagiga/di-mdm.properties ]                  && rm -f /dbagiga/di-mdm.properties
[ -f /dbagiga/di-manager.properties ]              && rm -f /dbagiga/di-manager.properties
[ -f /dbagiga/di-processor.properties ]            && rm -f /dbagiga/di-processor.properties
[ -f /dbagiga/di-transformations.properties ]      && rm -f /dbagiga/di-transformations.properties
[ -f /dbagiga/di-transformations-application.properties ]               && rm -f /dbagiga/di-transformations-application.properties
[ -f /dbagiga/dih-admin.properties ]               && rm -f /dbagiga/dih-admin.properties
[ -f /dbagiga/di-subscription-manager.properties ] && rm -f /dbagiga/di-subscription-manager.properties

systemctl daemon-reload
echo "DI removal completed on host: $(hostname)"
