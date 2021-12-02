source setenv.sh

systemctl stop odsxkafka.service
sleep 2

systemctl stop odsxzookeeper.service
sleep 2

systemctl stop telegraf
yum -y remove telegraf
sleep 2

yum -y remove java*
yum -y remove jdk*

rm -rf install install.tar $KAFKAPATH setenv.sh /usr/local/bin/st*_kafka.sh /etc/systemd/system/kafka.service
rm -rf /usr/local/bin/st*_zookeeper.sh /etc/systemd/system/odsxkafka.service /etc/systemd/system/odsxzookeeper.service