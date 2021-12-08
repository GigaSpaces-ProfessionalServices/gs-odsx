echo "Starting DI Installation."
#echo "Extracting install.tar to "$targetDir
cd /home/dbsh
tar -xvf install.tar
home_dir=$(pwd)
javaInstalled=$(java -version 2>&1 >/dev/null | egrep "\S+\s+version")
if [[ ${#javaInstalled} -eq 0 ]]; then
  installation_path=$home_dir/install/java
  installation_file=$(find $installation_path -name *.rpm -printf "%f\n")
  echo "Installation File :"$installation_file
  echo $installation_path"/"$installation_file
  rpm -ivh $installation_path"/"$installation_file
  sed -i '/export JAVA_HOME=/d' setenv.sh
  java_home_path="export JAVA_HOME='$(readlink -f /usr/bin/javac | sed "s:/bin/javac::")'"
  echo "">>setenv.sh
  echo "$java_home_path">>setenv.sh
  echo "installAirGapJava -Done!"
else
  echo "Java already installed.!!!"
fi

# Step for KAFKA Unzip and Set KAFKAPATH
echo "Install AirGapKafka"
installation_path=$home_dir/install/kafka
echo "InstallationPath="$installation_path
installation_file=$(find $installation_path -name "*.tgz" -printf "%f\n")
echo "InstallationFile:"$installation_file
tar -xvzf $installation_path"/"$installation_file -C  /root
var=$installation_file
echo "var"$var
replace=""
extracted_folder=${var//'.tgz'/$replace}
sed -i '/export KAFKAPATH/d' setenv.sh
echo "extracted_folder: "$extracted_folder
kafka_home_path="export KAFKAPATH=/root/"$extracted_folder
echo "$kafka_home_path">>setenv.sh
source setenv.sh

echo " param1 "$1" param2 "$2" param3 "$3" counter ID "$4
masterHost=$1
standbyHost=$2
witnessHost=$3
id=$4

# Configuration of log dir
source setenv.sh
echo "kafkaPath :"$KAFKAPATH
mkdir $KAFKAPATH/log
mkdir $KAFKAPATH/log/kafka
mkdir $KAFKAPATH/log/zookeeper
sed -i -e 's|$KAFKAPATH/log/kafka|'$KAFKAPATH'/log/zookeeper|g' $KAFKAPATH/config/zookeeper.properties
sed -i -e 's|/tmp/zookeeper|'$KAFKAPATH'/log/zookeeper|g' $KAFKAPATH/config/zookeeper.properties

if [[ ${#masterHost} -ge 3 ]]; then
  echo "server.1="$masterHost":2888:3888">>$KAFKAPATH/config/zookeeper.properties
  echo "server.2="$standbyHost":2888:3888">>$KAFKAPATH/config/zookeeper.properties
  echo "server.3="$witnessHost":2888:3888">>$KAFKAPATH/config/zookeeper.properties
  echo "initLimit=1000">>$KAFKAPATH/config/zookeeper.properties
  echo "syncLimit=1000">>$KAFKAPATH/config/zookeeper.properties

  echo "broker.id="$id"">>$KAFKAPATH/config/server.properties
  echo "zookeeper.connect="$masterHost":2181,"$standbyHost":2181,"$witnessHost":2181">>$KAFKAPATH/config/server.properties

  source setenv.sh
  sed -i -e '/listeners=PLAINTEXT:\/\/:9092/s/^#//g' $KAFKAPATH/config/server.properties
  sed -i -e '/advertised.listeners=PLAINTEXT:/s/^#//g' $KAFKAPATH/config/server.properties

  if [[ $id == 1 ]]; then
    sed -i -e 's|advertised.listeners=PLAINTEXT://your.host.name:9092|advertised.listeners=PLAINTEXT://'$masterHost':9092|g' $KAFKAPATH/config/server.properties
    sed -i -e '/advertised.listeners=PLAINTEXT/a advertised.host.name='$masterHost'' $KAFKAPATH/config/server.properties
  elif [[ $id == 2 ]]; then
    sed -i -e 's|advertised.listeners=PLAINTEXT://your.host.name:9092|advertised.listeners=PLAINTEXT://'$standbyHost':9092|g' $KAFKAPATH/config/server.properties
    sed -i '/advertised.listeners=PLAINTEXT/a advertised.host.name='$standbyHost'' $KAFKAPATH/config/server.properties
  elif [[ $id == 3 ]]; then
    sed -i -e 's|advertised.listeners=PLAINTEXT://your.host.name:9092|advertised.listeners=PLAINTEXT://'$witnessHost':9092|g' $KAFKAPATH/config/server.properties
    sed -i -e '/advertised.listeners=PLAINTEXT/a advertised.host.name='$witnessHost'' $KAFKAPATH/config/server.properties
  fi
  echo "$id">>$KAFKAPATH/log/zookeeper/myid
fi

#sed -i -e 's|$KAFKAPATH/log/kafka|'$KAFKAPATH'/log/kafka|g' $KAFKAPATH/config/server.properties
sed -i -e 's|log.dirs=/tmp/kafka-logs|log.dirs=/var/log/kafka|g' $KAFKAPATH/config/server.properties

start_kafka_file="start_kafka.sh"
start_zookeeper_file="start_zookeeper.sh"
stop_kafka_file="stop_kafka.sh"
stop_zookeeper_file="stop_zookeeper.sh"
kafka_service_file="odsxkafka.service"
zookeeper_service_file="odsxzookeeper.service"

source setenv.sh
cmd="nohup $KAFKAPATH/bin/zookeeper-server-start.sh $KAFKAPATH/config/zookeeper.properties &"
echo "$cmd">>$start_zookeeper_file
cmd="sleep 5"
echo "$cmd">>$start_kafka_file
cmd="nohup $KAFKAPATH/bin/kafka-server-start.sh $KAFKAPATH/config/server.properties  &"
echo "$cmd">>$start_kafka_file
source setenv.sh
# stop KAFKA
cmd="nohup $KAFKAPATH/bin/kafka-server-stop.sh $KAFKAPATH/config/server.properties  &"
echo "$cmd">>$stop_kafka_file
cmd="sleep 5"
echo "$cmd">>$stop_kafka_file
# stop Zookeeper
cmd="nohup $KAFKAPATH/bin/zookeeper-server-stop.sh $KAFKAPATH/config/zookeeper.properties &"
echo "$cmd">>$stop_zookeeper_file

home_dir_sh=$(pwd)
source $home_dir_sh/setenv.sh

mv $home_dir_sh/st*_kafka.sh /tmp
mv $home_dir_sh/st*_zookeeper.sh /tmp

mv $home_dir_sh/install/$kafka_service_file /tmp
mv $home_dir_sh/install/$zookeeper_service_file /tmp

mv /tmp/st*_kafka.sh /usr/local/bin/
mv /tmp/st*_zookeeper.sh /usr/local/bin/

chmod +x /usr/local/bin/st*_kafka.sh
chmod +x /usr/local/bin/st*_zookeeper.sh

mv /tmp/$kafka_service_file /etc/systemd/system/
mv /tmp/$zookeeper_service_file /etc/systemd/system/

# Install Telegraf
echo "Installing Telegraf"
installation_path=$home_dir/install/telegraf
echo "InstallationPath :"$installation_path
installation_file=$(find $installation_path -name *.rpm -printf "%f\n")
echo "Installation File :"$installation_file
echo $installation_path"/"$installation_file
yum install -y $installation_path"/"$installation_file

