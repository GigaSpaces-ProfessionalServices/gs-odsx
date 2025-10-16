ENV_CONFIG_PATH=$ENV_CONFIG
# Check if the environment variable is set
if [ -z "$ENV_CONFIG_PATH" ]; then
  echo "Error: $ENV_CONFIG_PATH is not set. Please set it before running this script."
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
gigainfluxpath=$(read_property "app.gigainfluxdata.path")
gigasharepath=$(read_property "app.gigashare.path")
gigadatapath=$(read_property "app.gigadata.path")
gigalogpath=$(read_property "app.gigalog.path")
gigaworkPath=$(read_property "app.gigawork.path")

#source $gigapath/setenv.sh

wantToRemoveKafka=$1
wantToRemoveZk=$2
wantToRemoveTelegraf=$3

if [ "$wantToRemoveKafka" == "y" ]; then
  systemctl stop odsxkafka.service
  sleep 2
  rm -rf $KAFKA_LOGS_PATH
  rm -rf $KAFKA_DATA_PATH
  rm -rf $KAFKAPATH
  rm -rf install install.tar $gigapath"/setenv.sh" /usr/local/bin/st*_kafka.sh /etc/systemd/system/kafka.service /etc/systemd/system/odsxkafka.service
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



#DIM - Services
systemctl stop di-mdm.service
systemctl stop di-manager.service

systemctl stop di-flink-taskmanager.service
systemctl stop di-flink-jobmanager.service
systemctl stop di-subscription-manager-iidr.service
systemctl daemon-reload
$gigapath"/di-flink/latest-flink/bin/stop-cluster.sh"
sleep 5

rm -f $gigapath"/di-mdm/latest-flink" $gigapath"/di-mdm/latest-di-mdm" $gigapath"/di-mdm/latest-di-manager" /etc/systemd/system/di-mdm.service /etc/systemd/system/di-manager.service
rm -rf $gigapath"/di-flink/*" $gigapath"/di-mdm/*" $gigapath"/di-manager/*" $gigapath"/di-processor/*" $gigapath"/di-subscription-manager/*"
rm -f /etc/systemd/system/di-flink-jobmanager.service /etc/systemd/system/di-flink-taskmanager.service
rm -rf $gigapath"/di-mdm/latest-di-processor" $gigapath"/di-mdm/latest-di-subscription-manager" /etc/systemd/system/di-mdm.service /etc/systemd/system/di-processor.service /etc/systemd/system/di-subscription-manager-iidr.service

systemctl daemon-reload
