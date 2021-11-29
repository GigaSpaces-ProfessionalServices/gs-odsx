echo "Starting DI Installation."
#echo "Extracting install.tar to "$targetDir
tar -xvf install.tar
home_dir=$(pwd)
installation_path=$home_dir/install/java
installation_file=$(find $installation_path -name *.rpm -printf "%f\n")
echo "Installation File :"$installation_file
echo $installation_path"/"$installation_file
rpm -ivh $installation_path"/"$installation_file
java_home_path="export JAVA_HOME='$(readlink -f /usr/bin/javac | sed "s:/bin/javac::")'"
echo "">>setenv.sh
echo "$java_home_path">>setenv.sh
echo "installAirGapJava -Done!"

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
echo "extracted_folder: "$extracted_folder
kafka_home_path="export KAFKAPATH=/root/"$extracted_folder
echo "$kafka_home_path">>setenv.sh
source setenv.sh

source setenv.sh
echo "kafkaPath :"$KAFKAPATH
mkdir $KAFKAPATH/log
mkdir $KAFKAPATH/log/kafka
mkdir $KAFKAPATH/log/zookeeper
sed -i -e 's|$KAFKAPATH/log/kafka|'$KAFKAPATH'/log/zookeeper|g' $KAFKAPATH/config/zookeeper.properties
sed -i -e 's|$KAFKAPATH/log/kafka|'$KAFKAPATH'/log/kafka|g' $KAFKAPATH/config/server.properties

start_kafka_file="start_kafka.sh"
stop_kafka_file="stop_kafka.sh"
kafka_service_file="odsxkafka.service"

source setenv.sh
cmd="nohup $KAFKAPATH/bin/zookeeper-server-start.sh $KAFKAPATH/config/zookeeper.properties &"
echo "$cmd">>$start_kafka_file
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
echo "$cmd">>$stop_kafka_file

home_dir_sh=$(pwd)
source $home_dir_sh/setenv.sh

mv $home_dir_sh/st*_kafka.sh /tmp
mv $home_dir_sh/install/$kafka_service_file /tmp
mv /tmp/st*_kafka.sh /usr/local/bin/
chmod +x /usr/local/bin/st*_kafka.sh
mv /tmp/$kafka_service_file /etc/systemd/system/



