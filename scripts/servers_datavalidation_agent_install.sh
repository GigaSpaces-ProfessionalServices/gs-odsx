echo "Starting Data Validation Installation."
#echo "Extracting install.tar to "$targetDir
cd /home/gsods
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
  java_home_path="export JAVA_HOME='$(readlink -f /usr/bin/javac | sed "s:/bin/javac::")'"
  echo "$java_home_path">>setenv.sh
  echo "Java already installed.!!!"
fi

start_data_validation_file="start_data_validation.sh"
stop_data_validation_file="stop_data_validation.sh"
data_validation_service_file="odsxdatavalidation.service"

#Replace keytab path according to agent machine
sed -i '/keyTab/c\keyTab=\"/home/gsods/UTKA02E.keytab\"' $home_dir/SQLJDBCDriver.conf

# start data validation service
source setenv.sh
cmd="java -Djava.security.auth.login.config=$home_dir/SQLJDBCDriver.conf -jar $home_dir/install/data-validation/data-validator-agent-0.0.1-SNAPSHOT.jar"
echo "$cmd">>$start_data_validation_file
# stop data validation service
cmd="pkill -9 -f data-validator-agent-0.0.1-SNAPSHOT.jar"
echo "$cmd">>$stop_data_validation_file

home_dir_sh=$(pwd)
source $home_dir_sh/setenv.sh

mv $home_dir_sh/st*_data_validation.sh /tmp

mv $home_dir_sh/install/$data_validation_service_file /tmp

mv /tmp/st*_data_validation.sh /usr/local/bin/

chmod +x /usr/local/bin/st*_data_validation.sh

mv /tmp/$data_validation_service_file /etc/systemd/system/

