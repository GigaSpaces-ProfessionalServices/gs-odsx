# Set XDG_RUNTIME_DIR for systemctl --user over SSH
# Load shared read_property helper (no-op when piped over SSH; see lib_app_config.sh).
[ -r "$(dirname "$0")/lib_app_config.sh" ] && source "$(dirname "$0")/lib_app_config.sh"

export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus

echo "Starting Data Validation Agent Installation."
ENV_CONFIG_PATH=$ENV_CONFIG
# Check if the environment variable is set
if [ -z "$ENV_CONFIG_PATH" ]; then
  echo "Error: $ENV_CONFIG_PATH is not set. Please set it before running this script."
  exit 1
else
  echo "$ENV_CONFIG_PATH is set to: $ENV_CONFIG_PATH"
fi
ENV_CONFIG_PATH="$ENV_CONFIG_PATH/app.config"


gigasharepath=$(read_property "app.gigashare.path")
gigapath=$(read_property "app.giga.path")

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

start_data_validation_file="start_data_validation_agent.sh"
stop_data_validation_file="stop_data_validation_agent.sh"
data_validation_service_file="odsxdatavalidationagent.service"

#Replace keytab path according to agent machine
#sed -i '/keyTab/c\keyTab=\'$home_dir'"/UTKA02E.keytab\"' $home_dir/SQLJDBCDriver.conf

cp $sourceDvServerJar $home_dir/install/data-validation/

# start data validation service
source setenv.sh
cmd="java -Djava.security.auth.login.config=$gigasharepath/env_config/security/SQLJDBCDriver.conf -jar $home_dir/install/data-validation/$serverJarFileName --spring.config.location=$home_dir/install/data-validation/application.properties"
echo "$cmd">>$start_data_validation_file
# stop data validation service
cmd="pkill -9 -f "$serverJarFileName
echo "$cmd">>$stop_data_validation_file

home_dir_sh=$(pwd)
source $home_dir_sh/setenv.sh

mv $home_dir_sh/st*_data_validation_agent.sh /tmp

mv $home_dir_sh/install/$data_validation_service_file /tmp

mv /tmp/st*_data_validation_agent.sh $gigapath/bin/

chmod +x $gigapath/bin/st*_data_validation_agent.sh

mv /tmp/$data_validation_service_file $HOME/.config/systemd/user/

restorecon $HOME/.config/systemd/user/$data_validation_service_file

systemctl --user daemon-reload
systemctl --user enable $data_validation_service_file

