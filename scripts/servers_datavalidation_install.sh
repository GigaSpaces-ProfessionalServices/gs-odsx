echo "Starting Data Validation Server Installation."
#echo "Extracting install.tar to "$targetDir
sourceInstallerDirectory=$1
targetInstallDir=$2
sourceDvServerJar=$3
echo "sourceInstallerDirectory:"$sourceInstallerDirectory
echo "targetInstallDir:"$targetInstallDir
echo "sourceDvServerJar:"$sourceDvServerJar
serverJarFileName=$(basename $sourceDvServerJar)
echo "serverJarFile Name:"$serverJarFileName
cd $targetInstallDir
tar -xvf install.tar
home_dir=$(pwd)
javaInstalled=$(java -version 2>&1 >/dev/null | egrep "\S+\s+version")
if [[ ${#javaInstalled} -eq 0 ]]; then
  installation_path=$sourceInstallerDirectory/jdk
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

start_data_validation_file="start_data_validation_server.sh"
stop_data_validation_file="stop_data_validation_server.sh"
data_validation_service_file="odsxdatavalidationserver.service"

cp $sourceDvServerJar $home_dir/install/data-validation/

# start data validation service
source setenv.sh
cmd="java -jar $home_dir/install/data-validation/data-validator-server-0.0.1-SNAPSHOT.jar --spring.config.location=$home_dir/install/data-validation/application.properties"
echo "$cmd">>$start_data_validation_file
# stop data validation service
cmd="pkill -9 -f data-validator-server-0.0.1-SNAPSHOT.jar"
echo "$cmd">>$stop_data_validation_file

home_dir_sh=$(pwd)
source $home_dir_sh/setenv.sh

mv $home_dir_sh/st*_data_validation_server.sh /tmp

mv $home_dir_sh/install/$data_validation_service_file /tmp

mv /tmp/st*_data_validation_server.sh /usr/local/bin/

chmod +x /usr/local/bin/st*_data_validation_server.sh

mv /tmp/$data_validation_service_file /etc/systemd/system/

restorecon /etc/systemd/system/$data_validation_service_file

sudo systemctl daemon-reload
sudo systemctl enable $data_validation_service_file



