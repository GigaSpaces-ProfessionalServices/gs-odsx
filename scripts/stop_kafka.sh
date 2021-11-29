#!/bin/sh

# stop Kafka
nohup $KAFKAPATH/bin/kafka-server-stop.sh $KAFKAPATH/config/server.properties  &
sleep 30

# stop Zookeeper
nohup $KAFKAPATH/bin/zookeeper-server-stop.sh $KAFKAPATH/config/zookeeper.properties &
sleep 30

