#!/bin/bash
set -x

source setenv.sh 2>/dev/null || true

wantToRemoveKafka=$1
wantToRemoveZk=$2
wantToRemoveTelegraf=$3

if [ "$wantToRemoveKafka" == "y" ]; then
  systemctl stop odsxkafka.service
  sleep 2
  rm -rf $KAFKA_LOGS_PATH
  rm -rf $KAFKA_DATA_PATH
  rm -rf $KAFKAPATH
  rm -rf install install.tar /dbagiga/setenv.sh /usr/local/bin/st*_kafka.sh /etc/systemd/system/kafka.service /etc/systemd/system/odsxkafka.service
fi

if [ "$wantToRemoveZk" == "y" ]; then
  systemctl stop odsxzookeeper.service
  sleep 2
  rm -rf $ZOOKEEPER_DATA_PATH
  rm -rf $ZOOKEEPER_LOGS_PATH
  rm -rf $ZOOKEEPERPATH
  rm -rf /usr/local/bin/st*_zookeeper.sh /etc/systemd/system/odsxzookeeper.service
fi
if [ "$wantToRemoveTelegraf" == "y" ]; then
  systemctl stop telegraf
  yum -y remove telegraf
  sleep 2
fi


# Stop all DI services before removing files
systemctl stop dih-admin.service || true
systemctl stop di-transformations.service || true
systemctl stop di-manager.service || true
systemctl stop di-mdm.service || true
systemctl stop di-flink-taskmanager.service || true
systemctl stop di-flink-jobmanager.service || true
systemctl stop di-subscription-manager-iidr.service || true
systemctl daemon-reload

# Stop Flink cluster gracefully before removing files
 bash /dbagiga/di-flink/latest-flink/bin/stop-cluster.sh || true
sleep 5

# Remove /home/gsods symlinks created during install
# (use rm -f not rm -rf to remove the symlink itself, not its target)
 rm -f /home/gsods/di-flink
 rm -f /home/gsods/di-mdm
 rm -f /home/gsods/di-manager
 rm -f /home/gsods/di-processor
 rm -f /home/gsods/di-transformations
 rm -f /home/gsods/dih-admin
 rm -f /home/gsods/di-subscription-manager
# Remove the actual directory created for flink checkpoints/savepoints
 rm -rf /home/gsods/latest-flink

# Remove DI service files
 rm -f /etc/systemd/system/di-flink-jobmanager.service
 rm -f /etc/systemd/system/di-flink-taskmanager.service
 rm -f /etc/systemd/system/di-mdm.service
 rm -f /etc/systemd/system/di-manager.service
 rm -f /etc/systemd/system/di-processor.service
 rm -f /etc/systemd/system/di-transformations.service
 rm -f /etc/systemd/system/di-subscription-manager-iidr.service

# Remove DI installation directories
 rm -rf /dbagiga/di-flink
 rm -rf /dbagiga/di-mdm
 rm -rf /dbagiga/di-manager
 rm -rf /dbagiga/di-processor
 rm -rf /dbagiga/di-transformations
 rm -rf /dbagiga/dih-admin
 rm -rf /dbagiga/di-subscription-manager

# Remove DI log directories
 rm -rf /dbagigalogs/di-flink
 rm -rf /dbagigalogs/di-mdm
 rm -rf /dbagigalogs/di-manager
 rm -rf /dbagigalogs/di-processor
 rm -rf /dbagigalogs/di-transformations
 rm -rf /dbagigalogs/dih-admin
 rm -rf /dbagigalogs/di-subscription-manager

# Remove properties files written during install
 rm -f /dbagiga/di-mdm.properties
 rm -f /dbagiga/di-manager.properties
 rm -f /dbagiga/di-processor.properties
 rm -f /dbagiga/di-transformations.properties
 rm -f /dbagiga/dih-admin.properties
 rm -f /dbagiga/di-subscription-manager.properties

 systemctl daemon-reload
echo "DI removal completed on host: $(hostname)"
