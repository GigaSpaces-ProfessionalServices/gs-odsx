#source /dbagiga/setenv.sh

systemctl stop odsxkafka.service
sleep 2
systemctl stop odsxzookeeper.service
sleep 2
systemctl stop telegraf
yum -y remove telegraf
sleep 2

rm -rf $KAFKA_LOGS_PATH
rm -rf $KAFKA_DATA_PATH
rm -rf $KAFKAPATH

rm -rf $ZOOKEEPER_DATA_PATH
rm -rf $ZOOKEEPER_LOGS_PATH
rm -rf $ZOOKEEPERPATH

rm -rf install install.tar /dbagiga/setenv.sh /usr/local/bin/st*_kafka.sh /etc/systemd/system/kafka.service
rm -rf /usr/local/bin/st*_zookeeper.sh /etc/systemd/system/odsxkafka.service /etc/systemd/system/odsxzookeeper.service

#DIM - Services
systemctl stop di-mdm.service
systemctl stop di-manager.service
systemctl daemon-reload
/dbagiga/di-flink/latest-flink/bin/stop-cluster.sh
sleep 5

rm -f /dbagiga/di-mdm/latest-flink /dbagiga/di-mdm/latest-di-mdm /dbagiga/di-mdm/latest-di-manager /etc/systemd/system/di-mdm.service /etc/systemd/system/di-manager.service
rm -rf /dbagiga/di-flink/* /dbagiga/di-mdm/* /dbagiga/di-manager/*
