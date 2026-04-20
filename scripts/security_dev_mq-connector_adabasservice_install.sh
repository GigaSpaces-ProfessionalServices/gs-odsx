# Set XDG_RUNTIME_DIR for systemctl --user over SSH
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus

echo "Installation begin for mq-connector!!!"
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
APP_USER=$(read_property "app.server.user")
APP_USER=${APP_USER:-$(whoami)}

tar -xvf install.tar
targetDir=$1
hostConfig=$2 #10.0.0.66,10.0.0.147,10.0.0.134
connectionStr=$3 #10.0.0.66:2181,10.0.0.147:2181,10.0.0.134:2181
bootstrapAddress=$4 #10.0.0.66:9092,10.0.0.147:9092,10.0.0.134:9092
sourceAdabasJarFile=$5
mqHostname=$6
mqChannel=$7
mqManager=$8
queueName=$9
sslChipherSuite=${10}
mqPort=${11}

rootDir=$(dirname "$targetDir")
#targetDir was passed as $1
echo "targetDir:"$targetDir
logDir=$gigalogpath'/Adabas'
start_publisher_file='run-publisher.sh'
stop_publisher_file='stop-publisher.sh'
service_file='odsxadabas.service'
start_adabas_feeder_file='start_adabasFeeder.sh'
stop_adabas_feeder_file='stop_adabasFeeder.sh'
applicationYml=$targetDir'/config/application.yml'
keystoreFile='keystore.jks'
#if [ ! -d "$rootDir" ]; then
#     mkdir $rootDir
#fi
if [ ! -d "$targetDir/config" ]; then
     mkdir -p $targetDir/config
fi
if [ ! -d "$logDir" ]; then
     mkdir -p $logDir
fi
chmod 755 $rootDir
chmod 755 $targetDir
chmod 755 $logDir
echo "Dir created.."
cmd="$targetDir/run-publisher.sh -name adabasPublisher"
echo "$cmd">>$start_adabas_feeder_file
cmd="$targetDir/stop-publisher.sh"
echo "$cmd">>$stop_adabas_feeder_file

echo "File written!!"
home_dir_sh=$(pwd)
#echo "home dir : "$home_dir_sh

mv $home_dir_sh/install/mq-connector/*publisher.sh $targetDir
mv $home_dir_sh/install/mq-connector/config/*.yml $targetDir/config
mv $home_dir_sh/$sourceAdabasJarFile $targetDir
mv $home_dir_sh/$keystoreFile $targetDir/$keystoreFile

chown $APP_USER:$APP_USER $targetDir/*.sh
chown $APP_USER:$APP_USER $targetDir/config/*.*
chmod +x $targetDir/*.sh
chmod 755 $targetDir/config/*.*

mqHostname=$6
mqChannel=$7
mqManager=$8
queueName=$9
sslChipherSuite=${10}
mqPort=${11}
#echo "hostname"$hostname
#echo "mqChannel"$mqChannel
#echo "mqManager"$mqManager
sed -i -e 's|adabas-0.0.1-SNAPSHOT.jar|'$targetDir'/adabas-0.0.1-SNAPSHOT.jar|g' $targetDir/$start_publisher_file
sed -i -e 's|=keystore.jks|='$targetDir'/keystore.jks|g' $targetDir/$start_publisher_file

sed -i -e 's|    address: BAM,BAN,BAK|    address: '$hostConfig'|g' $applicationYml
sed -i -e 's|    connectionStr: BAM:2181,BAN:2181,BAK:2181|    connectionStr: '$connectionStr'|g' $applicationYml
sed -i -e 's|    bootstrapAddress: BAM:9092,BAN:9092,BAK:9092|    bootstrapAddress: '$bootstrapAddress'|g' $applicationYml
sed -i -e 's|  hostname: mqhostname|  hostname: '$mqHostname'|g' $applicationYml
sed -i -e 's|  channel: CLI.ODS_1|  channel: '$mqChannel'|g' $applicationYml
sed -i -e 's|  qManager: SBENAIM|  qManager: '$mqManager'|g' $applicationYml
sed -i -e 's|  queueName: ACPT.YY.ODS.MATACH_TRANSACTIONS.R|  queueName: '$queueName'|g' $applicationYml
sed -i -e 's|  sslChipherSuite: TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256|  sslChipherSuite: '$sslChipherSuite'|g' $applicationYml
sed -i -e 's|  port: 1414|  port: '$mqPort'|g' $applicationYml


mv $home_dir_sh/$start_adabas_feeder_file /tmp
mv $home_dir_sh/$stop_adabas_feeder_file /tmp
mv $home_dir_sh/install/$service_file /tmp
sed -i "s|WorkingDirectory=/dbagigasoft/Adabas|WorkingDirectory=$targetDir|g" /tmp/$service_file
#echo "Files moved to /tmp"

mv /tmp/st*_adabasFeeder.sh /giga/bin/

chmod +x /giga/bin/st*_adabasFeeder.sh

mv /tmp/$service_file $HOME/.config/systemd/user/
systemctl --user daemon-reload

chown $APP_USER:$APP_USER $rootDir
chown $APP_USER:$APP_USER $targetDir
chown $APP_USER:$APP_USER $targetDir/*
chown $APP_USER:$APP_USER $logDir


#rm -rf /dbagigasoft/Adabas/ /giga/bin/*_adabasFeeder.sh $HOME/.config/systemd/user/odsxadabas.service install install.tar /dbagigasoft setenv.sh
