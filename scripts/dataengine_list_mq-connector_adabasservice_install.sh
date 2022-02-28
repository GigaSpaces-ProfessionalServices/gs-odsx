echo "Installation begin for mq-connector!!!"
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
influxhost=${12}

rootDir='/dbagigasoft'
#targetDir='/dbagigasoft/Adabas'
echo "targetDir:"$targetDir
logDir='/dbagigalogs/Adabas'
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
chmod 777 $rootDir
chmod 777 $targetDir
chmod 777 $logDir
echo "Dir created.."
cmd="/dbagigasoft/Adabas/run-publisher.sh -name adabasPublisher"
echo "$cmd">>$start_adabas_feeder_file
cmd="/dbagigasoft/Adabas/stop-publisher.sh"
echo "$cmd">>$stop_adabas_feeder_file

echo "File written!!"
home_dir_sh=$(pwd)
#echo "home dir : "$home_dir_sh

mv $home_dir_sh/install/mq-connector/*publisher.sh $targetDir
mv $home_dir_sh/install/mq-connector/config/*.yml $targetDir/config
mv $home_dir_sh/$sourceAdabasJarFile $targetDir
mv $home_dir_sh/$keystoreFile $targetDir/$keystoreFile

chown gsods:gsods $targetDir/*.sh
chown gsods:gsods $targetDir/config/*.*
chmod +x $targetDir/*.sh
chmod 777 $targetDir/config/*.*

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
sed -i -e 's|<influxhost>|'$influxhost'|g' $applicationYml


mv $home_dir_sh/$start_adabas_feeder_file /tmp
mv $home_dir_sh/$stop_adabas_feeder_file /tmp
mv $home_dir_sh/install/$service_file /tmp
#echo "Files moved to /tmp"

mv /tmp/st*_adabasFeeder.sh /usr/local/bin/

chmod +x /usr/local/bin/st*_adabasFeeder.sh

mv /tmp/$service_file /etc/systemd/system/
systemctl daemon-reload

chown gsods:gsods $rootDir
chown gsods:gsods $targetDir
chown gsods:gsods $targetDir/*
chown gsods:gsods $logDir


#rm -rf /dbagigasoft/Adabas/ /usr/local/bin/*_adabasFeeder.sh /etc/systemd/system/odsxadabas.service install install.tar /dbagigasoft setenv.sh
