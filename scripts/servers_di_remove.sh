source /home/dbsh/setenv.sh

systemctl stop odsxkafka.service
sleep 2

systemctl stop odsxzookeeper.service
sleep 2

systemctl stop telegraf
yum -y remove telegraf
sleep 2

yum -y remove java
yum -y remove jdk*

rm -rf $KAFKA_LOGS_PATH
rm -rf $KAFKA_DATA_PATH
rm -rf $KAFKAPATH

rm -rf $ZOOKEEPER_DATA_PATH
rm -rf $ZOOKEEPER_LOGS_PATH
rm -rf $ZOOKEEPERPATH

rm -rf /home/dbsh/install /home/dbsh/dbagigashare dbagigashare /home/dbsh/install.tar setenv.sh /usr/local/bin/st*_kafka.sh /etc/systemd/system/kafka.service
rm -rf /usr/local/bin/st*_zookeeper.sh /etc/systemd/system/odsxkafka.service /etc/systemd/system/odsxzookeeper.service

