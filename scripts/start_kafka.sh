#!/bin/sh
# Start Zookeeper
nohup $KAFKAPATH/bin/zookeeper-server-start.sh $KAFKAPATH/config/zookeeper.properties &
sleep

# Verify Zookeeper is started or not


# Start Kafka
nohup $KAFKAPATH/bin/kafka-server-start.sh $KAFKAPATH/config/server.properties  &
sleep 30

# Verify Kafka is started or not
