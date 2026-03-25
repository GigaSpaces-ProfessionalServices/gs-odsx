#!/bin/bash
set -x
echo "scripts/servers_di_install_all.sh"
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

print_style () {
    if [ "$2" == "debug" ] ; then
        COLOR="96m";
    elif [ "$2" == "info" ] ; then
        COLOR="92m";
    elif [ "$2" == "warning" ] ; then
        COLOR="93m";
    elif [ "$2" == "error" ] ; then
        COLOR="91m";
    else #default color
        COLOR="0m";
    fi

    STARTCOLOR="\e[$COLOR";
    ENDCOLOR="\e[0m";

    printf "$STARTCOLOR%b$ENDCOLOR" "$1";
}
debug() {
    print_style "$1" "debug";
}
info() {
    print_style "$1" "info";
}
warning() {
    print_style "$1" "warning";
}
error() {
    print_style "$1" "error";
}
printNoColor() {
    print_style "$1" "error";
}
info "Starting DI Installation.\n"

function installAirGapJava {
  installation_path=$sourceInstallerDirectory/jdk
  installation_file=$(find $installation_path -name "*.rpm" -printf "%f\n" | sort -V | tail -1)
  echo "Installation File :"$installation_file
  echo $installation_path"/"$installation_file
  sudo rpm -ivh $installation_path"/"$installation_file
  sed -i '/export JAVA_HOME=/d' setenv.sh
  java_home_path="export JAVA_HOME='$(readlink -f /usr/bin/javac | sed "s:/bin/javac::")'"
  echo "$java_home_path">>setenv.sh
  echo "installAirGapJava -Done!"
}

function installRemoteJava {
  # Set default Java version to 17 if not specified
  if [ -z "$openJdkVersion" ]; then
    openJdkVersion="17"
    echo "openJdkVersion not set, defaulting to: $openJdkVersion"
  fi
  echo "os:"$osType
  if [ "$osType" == "centos" ] || [ "$osType" == "Red Hat Enterprise Linux" ] ; then
      if [ "$openJdkVersion" == "1.8" ] ||  [ "$openJdkVersion" == "8" ]; then
        echo "centos 1.8"
          sudo yum -y install java-1.8.0-openjdk
          sudo yum -y install java-1.8.0-openjdk-devel
    elif [ "$openJdkVersion" == "11" ] ; then
        echo "centos 11"
        sudo yum -y install java-11-openjdk
        sudo yum -y install java-11-openjdk-devel
        fi
    elif [ "$osType" == "ubuntu" ]; then
      if [ "$openJdkVersion" == "1.8" ]  ||  [ "$openJdkVersion" == "8" ]; then
        echo "ubuntu 1.8"
          sudo apt-get update
          sudo apt -y install openjdk-8-jdk
      elif [ "$openJdkVersion" == "11" ]; then
        echo "ubuntu 11"
          sudo apt-get update
          sudo apt -y install openjdk-11-jdk
          #sudo apt-get install openjdk-11-jdk
      fi
    elif [ "$osType" == "awsLinux2" ] || [ "$osType" == "Amazon Linux" ] || [ "$osType" == "Amazon Linux2" ]; then
      if [ "$openJdkVersion" == "1.8" ] ||  [ "$openJdkVersion" == "8" ]; then
        echo "awsLinux2 11"
          sudo amazon-linux-extras enable corretto8
          yum clean metadata
          sudo yum -y install java-1.8.0-amazon-corretto
      elif [ "$openJdkVersion" == "11" ]; then
        echo "elseif awsLinux2 11"
          sudo amazon-linux-extras install -y java-openjdk11
      fi
    else
      if [ "$openJdkVersion" == "1.8" ] ||  [ "$openJdkVersion" == "8" ]; then
        echo "if ubuntu 11"
          sudo yum -y install java-1.8.0-openjdk
          sudo yum -y install java-1.8.0-openjdk-devel
    elif [ "$openJdkVersion" == "11" ]; then
        echo "else ubuntu 11"
        sudo yum -y install java-11-openjdk
        sudo yum -y install java-11-openjdk-devel
    elif [ "$openJdkVersion" == "17" ]; then
        echo "else ubuntu 11"
        sudo yum -y install java-17-openjdk
        sudo yum -y install java-17-openjdk-devel
        fi
  fi
    echo "Installation Remote JDK - Done!"
}

function installFlink() {
  info "\nInstalling Flink\n"
  installation_path_flink=$sourceInstallerDirectory/data-integration/di-flink
  installation_file_flink=$(find $installation_path_flink -name "flink*.tgz" -printf "%f\n" | sort -V | tail -1)
  info "InstallationFile:"$installation_file_flink"\n"
  sudo mkdir -p $gigapath/di-flink
  sudo mkdir -p $gigalogpath/di-iidr/di-flink
  info "Copying file from "$installation_path_flink/$installation_file_flink +" to "$gigapath"/di-flink \n"
  sudo cp $installation_path_flink/$installation_file_flink $gigapath/di-flink
  info "\nExtracting zip file...\n"
  sudo tar -xzf $gigapath/di-flink/$installation_file_flink --directory $gigapath/di-flink/

  # Change ownership to current user so we can modify config files
  current_user=$(whoami)
  sudo chown -R $current_user:$current_user $gigapath/di-flink/

  extracted_folder_flink=$(ls -I "*.tgz" $gigapath/di-flink/)
  cd $gigapath/di-flink/
  sudo ln -s $gigapath/di-flink/ /home/gsods/di-flink
  sudo ln -s $gigapath/di-flink/$extracted_folder_flink /home/gsods/di-flink/latest-flink
  sudo mkdir -p /home/gsods/di-flink/latest-flink/data/savepoints
  sudo mkdir -p /home/gsods/di-flink/latest-flink/data/checkpoints

  # Flink 2.x renamed flink-conf.yaml to config.yaml; handle both
  flink_conf_dir="$gigapath/di-flink/$extracted_folder_flink/conf"
  if [ -f "$flink_conf_dir/flink-conf.yaml" ]; then
    flink_conf_file="$flink_conf_dir/flink-conf.yaml"
  else
    flink_conf_file="$flink_conf_dir/config.yaml"
  fi
  mv "$flink_conf_file" "${flink_conf_file}_orig"

  echo "">>$flink_conf_file
  echo "jobmanager.rpc.address: localhost">>$flink_conf_file
  echo "jobmanager.rpc.port: 6123">>$flink_conf_file
  echo "jobmanager.bind-host: localhost">>$flink_conf_file
  echo "jobmanager.memory.process.size: 4000m">>$flink_conf_file
  echo "taskmanager.bind-host: localhost">>$flink_conf_file
  echo "taskmanager.host: localhost">>$flink_conf_file
  echo "taskmanager.memory.process.size: $flinkTaskManagerMemoryProcessSize">>$flink_conf_file
  echo "taskmanager.numberOfTaskSlots: 10">>$flink_conf_file
  echo "parallelism.default: 1">>$flink_conf_file
  echo "jobmanager.execution.failover-strategy: region">>$flink_conf_file
  echo "jobmanager.memory.jvm-metaspace.size: $flinkJobManagerMemoryMetaspaceSize">>$flink_conf_file
  echo "state.savepoints.dir: file:///home/gsods/di-flink/latest-flink/data/savepoints">>$flink_conf_file
  echo "state.checkpoints.dir: file:///home/gsods/di-flink/latest-flink/data/checkpoints">>$flink_conf_file
  chmod +x $gigapath/di-flink/$extracted_folder_flink/bin/*
  sudo cp $installation_path_flink/di-flink-jobmanager.service /etc/systemd/system/
  sudo cp $installation_path_flink/di-flink-taskmanager.service /etc/systemd/system/
  # Fix QA-server paths in service files to match this environment
  sudo sed -i 's|latest-di-flink|latest-flink|g' /etc/systemd/system/di-flink-jobmanager.service
  sudo sed -i 's|latest-di-flink|latest-flink|g' /etc/systemd/system/di-flink-taskmanager.service
  sudo sed -i "s|FLINK_LOG_DIR=[^ ]*|FLINK_LOG_DIR=$gigalogpath/di-iidr/di-flink|g" /etc/systemd/system/di-flink-jobmanager.service
  sudo sed -i "s|FLINK_LOG_DIR=[^ ]*|FLINK_LOG_DIR=$gigalogpath/di-iidr/di-flink|g" /etc/systemd/system/di-flink-taskmanager.service
  # Copy extra JARs if present in gigashare (optional — skip if missing)
  sudo cp $installation_path_flink/*.jar $gigapath/di-flink/$extracted_folder_flink/lib/ 2>/dev/null || true
  sudo mkdir -p /home/gsods/latest-flink/data/checkpoints/ /home/gsods/latest-flink/data/savepoints/

  # Set final ownership to gsods
  sudo chown -R gsods:gsods $gigapath/di-flink/
  sudo chown -R gsods:gsods /home/gsods/di-flink/
  sudo chown -R gsods:gsods $gigalogpath/di-iidr/di-flink
  sudo restorecon /etc/systemd/system/di-* 2>/dev/null || true
  sudo systemctl daemon-reload
  sudo systemctl restart di-flink-taskmanager.service
  sudo systemctl restart di-flink-jobmanager.service

  rm -f $gigapath/di-flink/di-flink
  info "\n Installation Flink completed."
}

function installDIMatadata {
  info "\n Installing DI-MDM\n"
  installation_path_mdm=$sourceInstallerDirectory/data-integration/di-mdm
  installation_file_mdm=$(find $installation_path_mdm -name "di-mdm*.gz" -printf "%f\n" | sort -V | tail -1)
  info "InstallationFile:"$installation_file_mdm"\n"
  sudo mkdir -p $gigapath/di-mdm
  sudo mkdir -p $gigalogpath/di-mdm       # Fixed: was $gigapathlogs (typo)
  sudo cp $installation_path_mdm/$installation_file_mdm $gigapath/di-mdm
  info "\nExtracting zip file...\n"
  sudo tar -xzf $gigapath/di-mdm/$installation_file_mdm --directory $gigapath/di-mdm/

  # Change ownership to current user so we can modify config files
  current_user=$(whoami)
  sudo chown -R $current_user:$current_user $gigapath/di-mdm/

  extracted_folder_mdm=$(ls -I "*.gz" $gigapath/di-mdm/)
  cd $gigapath/di-mdm/
  info "Creating symlink for :"$extracted_folder_mdm
  sudo ln -s $gigapath/di-mdm/ /home/gsods/di-mdm
  sudo ln -s $gigapath/di-mdm/$extracted_folder_mdm /home/gsods/di-mdm/latest-di-mdm
  echo "spring.profiles.active=zookeeper">$gigapath/di-mdm.properties
  echo "zookeeper.connectUrl="$kafkaBrokerHost1":2181">>$gigapath/di-mdm.properties

  # Set final ownership to gsods
  sudo chown -R gsods:gsods $gigapath/di-mdm/
  sudo chown -R gsods:gsods /home/gsods/di-mdm/
  # Use absolute path - cannot cd into /home/gsods/ (mode 700)
  sudo bash $gigapath/di-mdm/$extracted_folder_mdm/utils/install_new_version.sh $gigapath/di-mdm.properties
  rm -f $gigapath/di-mdm/di-mdm

  # Create global-${currentHost}.env for di-mdm global_config.sh
  sudo tee $gigapath/di-mdm/$extracted_folder_mdm/utils/global-${currentHost}.env > /dev/null << ENVEOF
MDM_URL=http://${kafkaBrokerHost1}:6081
FLINK_URL=http://${kafkaBrokerHost1}:8081
SPACE_LOOKUP_GROUPS=${spaceLookupGroups}
SPACE_LOOKUP_LOCATORS=${spaceLookupLocators}
KAFKA_BOOTSTRAP_SERVERS=${kafkaBrokerHost1}:9092
ENVEOF
  sudo chown gsods:gsods $gigapath/di-mdm/$extracted_folder_mdm/utils/global-${currentHost}.env
  info "\n Created global-${currentHost}.env in di-mdm utils for global_config.sh.\n"
}

function installDIManager {
  info "\n Installing DI-Manager\n"
  installation_path_manager=$sourceInstallerDirectory/data-integration/di-manager
  installation_file_manager=$(find $installation_path_manager -name "di-manager*.gz" -printf "%f\n" | sort -V | tail -1)
  info "InstallationFile:"$installation_file_manager"\n"
  sudo mkdir -p $gigapath/di-manager
  sudo mkdir -p $gigalogpath/di-manager
  info "Copying file from "$installation_path_manager/$installation_file_manager +" to "$gigapath"/di-manager \n"
  sudo cp $installation_path_manager/$installation_file_manager $gigapath/di-manager
  info "\nExtracting zip file...\n"
  sudo tar -xzf $gigapath/di-manager/$installation_file_manager --directory $gigapath/di-manager/

  # Change ownership to current user so we can modify config files
  current_user=$(whoami)
  sudo chown -R $current_user:$current_user $gigapath/di-manager/

  extracted_folder_manager=$(ls -I "*.gz" $gigapath/di-manager/)
  cd $gigapath/di-manager/
  info "Creating symlink for :"$extracted_folder_manager
  sudo ln -s $gigapath/di-manager/ /home/gsods/di-manager
  sudo ln -s $gigapath/di-manager/$extracted_folder_manager /home/gsods/di-manager/latest-di-manager

  echo "springdoc.api-docs.path=/api-docs">$gigapath/di-manager.properties
  echo "springdoc.swagger-ui.path=/swagger-ui">>$gigapath/di-manager.properties
  echo "springdoc.swagger-ui.operationsSorter=method">>$gigapath/di-manager.properties
  sed -i '/^mdm.server.url/d' $gigapath/di-manager.properties
  echo "mdm.server.url=http://$kafkaBrokerHost1:6081">>$gigapath/di-manager.properties
  sed -i '/^mdm.server.fallback-url/d' $gigapath/di-manager.properties
  if [ "$kafkaBrokerCount" == 1 ]; then
    echo "mdm.server.fallback-url=http://$kafkaBrokerHost1:6081">>$gigapath/di-manager.properties
  else
    echo "mdm.server.fallback-url=http://$kafkaBrokerHost2:6081">>$gigapath/di-manager.properties
  fi
  echo "server.port=6080">>$gigapath/di-manager.properties
  echo "mdm.client.timeouts.connection.ms=10000">>$gigapath/di-manager.properties
  echo "mdm.client.timeouts.read.ms=60000">>$gigapath/di-manager.properties

  # Set final ownership to gsods
  sudo chown -R gsods:gsods $gigapath/di-manager/
  sudo chown -R gsods:gsods /home/gsods/di-manager/
  # Use absolute path - cannot cd into /home/gsods/ (mode 700)
  sudo bash $gigapath/di-manager/$extracted_folder_manager/utils/install_new_version.sh $gigapath/di-manager.properties
  rm -f $gigapath/di-manager/di-manager
  info "\n Installation DI-Manager completed.\n"
}


function installDIProcessor {
    info "\n Installing DI-Processor\n"
    installation_path_manager=$sourceInstallerDirectory/data-integration/di-processor
    installation_file_manager=$(find $installation_path_manager -name "di-processor*.tgz" -printf "%f\n" | sort -V | tail -1)
    info "InstallationFile:"$installation_file_manager"\n"
    sudo mkdir -p $gigapath/di-processor
    sudo mkdir -p $gigalogpath/di-processor
    info "Copying file from "$installation_path_manager/$installation_file_manager +" to $gigapath/di-processor \n"
    sudo cp $installation_path_manager/$installation_file_manager $gigapath/di-processor
    info "\nExtracting zip file...\n"
    sudo tar -xzf $gigapath/di-processor/$installation_file_manager --directory $gigapath/di-processor/

    # Change ownership to current user so we can modify config files
    current_user=$(whoami)
    sudo chown -R $current_user:$current_user $gigapath/di-processor/

    extracted_folder_manager=$(ls -I "*.tgz" $gigapath/di-processor/)
    cd $gigapath/di-processor/
    info "Creating symlink for :"$extracted_folder_manager
    sudo ln -s $gigapath/di-processor/ /home/gsods/di-processor
    sudo ln -s $gigapath/di-processor/$extracted_folder_manager /home/gsods/di-processor/latest-di-processor

    echo "mdm.server.url=http://$kafkaBrokerHost1:6081">$gigapath/di-processor.properties
    if [ "$kafkaBrokerCount" == 1 ]; then
      echo "mdm.server.fallback-url=http://$kafkaBrokerHost1:6081">>$gigapath/di-processor.properties
    else
      echo "mdm.server.fallback-url=http://$kafkaBrokerHost2:6081">>$gigapath/di-processor.properties
    fi

    # Set final ownership to gsods
    sudo chown gsods:gsods $gigalogpath/di-processor
    sudo chown -R gsods:gsods $gigapath/di-processor/
    sudo chown -R gsods:gsods /home/gsods/di-processor/
    # Use absolute path - cannot cd into /home/gsods/ (mode 700)
    sudo bash $gigapath/di-processor/$extracted_folder_manager/utils/install_new_version.sh $gigapath/di-processor.properties
    rm -f $gigapath/di-processor/di-processor
}

function installDITransformations {
  info "\n Installing DI-Transformations\n"
  installation_path=$sourceInstallerDirectory/data-integration/di-transformations
  installation_file=$(find $installation_path -name "di-transformations*.tgz" -printf "%f\n" | sort -V | tail -1)
  info "InstallationFile:"$installation_file"\n"
  sudo mkdir -p $gigapath/di-transformations
  sudo mkdir -p $gigalogpath/di-transformations
  sudo cp $installation_path/$installation_file $gigapath/di-transformations
  info "\nExtracting zip file...\n"
  sudo tar -xzf $gigapath/di-transformations/$installation_file --directory $gigapath/di-transformations/

  current_user=$(whoami)
  sudo chown -R $current_user:$current_user $gigapath/di-transformations/

  extracted_folder_transformations=$(ls -I "*.tgz" $gigapath/di-transformations/)
  cd $gigapath/di-transformations/
  info "Creating symlink for :"$extracted_folder_transformations
  sudo ln -s $gigapath/di-transformations/ /home/gsods/di-transformations
  sudo ln -s $gigapath/di-transformations/$extracted_folder_transformations /home/gsods/di-transformations/latest-di-transformations

  # Derive XAP manager host from spaceLookupLocators (strip :4174)
  xapManagerHost=${spaceLookupLocators%:4174}

  sudo tee $gigapath/di-transformations.properties > /dev/null << TRANEOF
graphql.graphiql.enabled=true
graphql.servlet.exception-handlers-enabled=true

transformations.rest.swagger-parsers.cache.size=10
transformations.rest.swagger-parsers.cache.expireAfterAccessInHours=1
transformations.rest.swagger-parsers.cache.expireAfterWriteInHours=24

transformations.rest.swagger-config-files.location-dir=/tmp/swagger-upload-dir
spring.servlet.multipart.max-file-size=10MB
spring.servlet.multipart.max-request-size=10MB

mdm.client.timeouts.connection.ms=10000
mdm.client.timeouts.read.ms=60000
mdm.server.fallback-url=http://${kafkaBrokerHost1}:6081
mdm.server.url=http://${kafkaBrokerHost1}:6081

manager.client.timeouts.connection.ms=10000
manager.client.timeouts.read.ms=60000
manager.server.fallback-url=http://${kafkaBrokerHost1}:6080
manager.server.url=http://${kafkaBrokerHost1}:6080

xap-manager.client.timeouts.connection.ms=10000
xap-manager.client.timeouts.read.ms=60000
xap-manager.server.url=http://${xapManagerHost}:8090

logging.level.com.gigaspaces.di.transformations.client=DEBUG
logging.level.org.springframework.web.filter.CommonsRequestLoggingFilter=DEBUG

server.port=6090
TRANEOF

  # Patch log path in service file BEFORE install_new_version.sh deploys it to /etc/systemd/system/
  sudo sed -i "s|latest-di-transformations/logs/di-transformations.log|${gigalogpath}/di-transformations/di-transformations.log|g" \
      $gigapath/di-transformations/$extracted_folder_transformations/config/di-transformations.service

  sudo chown -R gsods:gsods $gigapath/di-transformations/
  sudo chown -R gsods:gsods /home/gsods/di-transformations/
  sudo bash $gigapath/di-transformations/$extracted_folder_transformations/utils/install_new_version.sh $gigapath/di-transformations.properties
  sudo restorecon /etc/systemd/system/di-transformations.service 2>/dev/null || true
  sudo systemctl daemon-reload
  rm -f $gigapath/di-transformations/di-transformations
  info "\n Installation DI-Transformations completed.\n"
}

function installDISubscription {
    info "\n Installing DI-Subscription-Manager\n"
    installation_path_manager=$sourceInstallerDirectory/data-integration/di-subscription-manager
    installation_file_manager=$(find $installation_path_manager -name "di-subscription-manager*.tgz" -printf "%f\n" | sort -V | tail -1)
    info "InstallationFile:"$installation_file_manager"\n"
    sudo mkdir -p $gigapath/di-subscription-manager
    sudo mkdir -p $gigalogpath/di-subscription-manager
    sudo chown gsods:gsods $gigalogpath/di-subscription-manager
    info "Copying file from "$installation_path_manager/$installation_file_manager +" to "$gigapath"/di-subscription-manager \n"
    sudo cp $installation_path_manager/$installation_file_manager $gigapath/di-subscription-manager
    info "\nExtracting zip file...\n"
    sudo tar -xzf $gigapath/di-subscription-manager/$installation_file_manager --directory $gigapath/di-subscription-manager/

    # Change ownership to current user so we can modify config files
    current_user=$(whoami)
    sudo chown -R $current_user:$current_user $gigapath/di-subscription-manager/

    extracted_folder_manager=$(ls -I "*.tgz" $gigapath/di-subscription-manager/)
    cd $gigapath/di-subscription-manager/
    info "Creating symlink for :"$extracted_folder_manager
    sudo ln -s $extracted_folder_manager /home/gsods/di-subscription-manager
    sudo ln -s $gigapath/di-subscription-manager/$extracted_folder_manager /home/gsods/di-subscription-manager/latest-di-subscription-manager

    echo "##iidr.as##" > $gigapath/di-subscription-manager.properties
    echo "iidr-as.hostname=$iidrHost" >> $gigapath/di-subscription-manager.properties
    echo "iidr-as.port=10101" >> $gigapath/di-subscription-manager.properties
    echo "iidr-as.username=$iidrUsername" >> $gigapath/di-subscription-manager.properties
    echo "iidr-as.password=$iidrPassword" >> $gigapath/di-subscription-manager.properties
    echo "iidr-as.source-datastore.mirror_auto_restart_interval_seconds=15" >> $gigapath/di-subscription-manager.properties
    echo "" >> $gigapath/di-subscription-manager.properties
    echo "datastore.save-credentials-in-mdm=false" >> $gigapath/di-subscription-manager.properties
    echo "" >> $gigapath/di-subscription-manager.properties
    echo "###kafka properties" >> $gigapath/di-subscription-manager.properties
    echo "kafka.host=gstest-di1.tau.ac.il" >> $gigapath/di-subscription-manager.properties
    echo "kafka.port=9092" >> $gigapath/di-subscription-manager.properties
    echo "kafka.topic.prefix=" >> $gigapath/di-subscription-manager.properties
    echo "" >> $gigapath/di-subscription-manager.properties
    echo "###iidr kafka properties" >> $gigapath/di-subscription-manager.properties
    echo "iidr-kafka.host=gstest-iidr1.tau.ac.il" >> $gigapath/di-subscription-manager.properties
    echo "iidr-kafka.port=11701" >> $gigapath/di-subscription-manager.properties
    echo "iidr-kafka.username=tsuser" >> $gigapath/di-subscription-manager.properties
    echo "iidr-kafka.password=<password>" >> $gigapath/di-subscription-manager.properties
    echo "iidr-kafka.properties.manager.client.timeouts.connection.ms=10000" >> $gigapath/di-subscription-manager.properties
    echo "iidr-kafka.properties.manager.client.timeouts.read.ms=60000" >> $gigapath/di-subscription-manager.properties
    echo "iidr-kafka.properties.manager.server.url=http://$iidrHost:6085" >> $gigapath/di-subscription-manager.properties
    echo "iidr-kafka.user-exit.properties.file.use-api=false" >> $gigapath/di-subscription-manager.properties
    echo "iidr-kafka.user-exit.properties.file.read-path=/giga/iidr/kafka/instance/KAFKA/conf" >> $gigapath/di-subscription-manager.properties
    echo "iidr-kafka.user-exit.properties.file.write-path=/giga/iidr/kafka/instance/KAFKA/conf" >> $gigapath/di-subscription-manager.properties
    echo "" >> $gigapath/di-subscription-manager.properties
    echo "##mdm##" >> $gigapath/di-subscription-manager.properties
    echo "mdm.client.timeouts.connection.ms=10000" >> $gigapath/di-subscription-manager.properties
    echo "mdm.client.timeouts.read.ms=60000" >> $gigapath/di-subscription-manager.properties
    echo "mdm.url=/api/v1" >> $gigapath/di-subscription-manager.properties
    echo "mdm.server.url=http://$kafkaBrokerHost1:6081" >> $gigapath/di-subscription-manager.properties
    echo "" >> $gigapath/di-subscription-manager.properties
    echo "##subscription manager" >> $gigapath/di-subscription-manager.properties
    echo "subscription-manager.server.url=http://:gstest-iidr1.tau.ac.il:6082" >> $gigapath/di-subscription-manager.properties
    echo "subscription-manager.feature.supports-transaction=true" >> $gigapath/di-subscription-manager.properties
    echo "#mdm-waiting-timeout is in seconds" >> $gigapath/di-subscription-manager.properties
    echo "subscription-manager.mdm-availability-waiting-timeout-seconds=300" >> $gigapath/di-subscription-manager.properties
    echo "server.port=6082" >> $gigapath/di-subscription-manager.properties

    echo "##swagger-ui##" >> $gigapath/di-subscription-manager.properties
    echo "springdoc.api-docs.path=/api-docs" >> $gigapath/di-subscription-manager.properties
    echo "springdoc.swagger-ui.operationsSorter=method" >> $gigapath/di-subscription-manager.properties
    echo "springdoc.swagger-ui.path=/swagger-ui" >> $gigapath/di-subscription-manager.properties
    echo "springdoc.swagger-ui.request-timeout=10000 # Timeout value in milliseconds" >> $gigapath/di-subscription-manager.properties
    echo "" >> $gigapath/di-subscription-manager.properties
    echo "logging.level.org.springframework.web.filter.CommonsRequestLoggingFilter=DEBUG" >> $gigapath/di-subscription-manager.properties
    sudo sed -i -e 's|logs/di-subscription-manager.log|'$gigalogpath'/di-iidr/di-subscription-manager.log|g' /etc/systemd/system/di-subscription-manager-iidr.service
    # Use absolute path - cannot cd into /home/gsods/ (mode 700)
    sudo bash $gigapath/di-subscription-manager/$extracted_folder_manager/utils/install_new_version.sh $gigapath/di-subscription-manager.properties
    sudo systemctl daemon-reload
    sudo systemctl enable di-subscription-manager
    sudo systemctl restart di-subscription-manager
    info "\n Installation DI-Subscription-Manager completed.\n"
}

installtelegrafFlag=$1
kafkaBrokerCount=$2
if [ "$kafkaBrokerCount" == 1 ]; then
  echo "Processing for single node installation."
  echo "nodeListSize" $2" kafkaBrokerHost1 "$3" counter ID "$4" installtelegrafFlag "$1" baseFolderLocation "$5" sourceInstallerDirectory"
  kafkaBrokerHost1=$3
  id=$4
  baseFolderLocation=$5
  dataFolderKafka=$6
  dataFolderZK=$7
  logsFolderKafka=$8
  logsFolderZK=$9
  wantInstallJava=${10}
  sourceInstallerDirectory=${11}
  currentHost=${12}
  flinkJobManagerMemoryMetaspaceSize=${13}
  flinkTaskManagerMemoryProcessSize=${14}
  dimMdmFlinkInstallon1bFlag="y"
  zkClientPort=${15}
  zkInitLimit=${16}
  zkSyncLimit=${17}
  zkTickTime=${18}
  iidrHost=${19}
  iidrUsername=${20}
  iidrPassword=${21}
  spaceLookupGroups=${22}
  spaceLookupLocators=${23}

  echo " dataFolderKafka "$6" dataFolderZK "$7" logsFolderKafka "$8" logsFolderZK "$9" currentHost:"$currentHost
fi
if [ "$kafkaBrokerCount" == 3 ]; then
  echo "Processing for 3 node installation"
  echo "nodeListSize" $2" kafkaBrokerHost1 "$3" kafkaBrokerHost2 "$4" kafkaBrokerHost3 "$5" counter ID "$6" installtelegrafFlag "$1" baseFolderLocation "$7
  kafkaBrokerHost1=$3
  kafkaBrokerHost2=$4
  kafkaBrokerHost3=$5
  id=$6
  baseFolderLocation=$7
  dataFolderKafka=$8
  dataFolderZK=$9
  logsFolderKafka=${10}
  logsFolderZK=${11}
  wantInstallJava=${12}
  sourceInstallerDirectory=${13}
  currentHost=${14}
  flinkJobManagerMemoryMetaspaceSize=${15}
  flinkTaskManagerMemoryProcessSize=${16}
  dimMdmFlinkInstallon1bFlag=${17}
  zkClientPort=${18}
  zkInitLimit=${19}
  zkSyncLimit=${20}
  zkTickTime=${21}
  iidrHost=${22}
  iidrUsername=${23}
  iidrPassword=${24}
  spaceLookupGroups=${25}
  spaceLookupLocators=${26}

  echo " dataFolderKafka "$8" dataFolderZK "$9" logsFolderKafka "${10}" logsFolderZK "${11}" currentHost:"$currentHost
  echo "flinkJobManagerMemoryMetaspaceSize $flinkJobManagerMemoryMetaspaceSize, flinkTaskManagerMemoryProcessSize=$flinkTaskManagerMemoryProcessSize"
fi

if [ "$wantInstallJava" == "y" ]; then
    echo "Setup AirGapJava"
    installRemoteJava
fi
echo " dataFolderKafka "$8" dataFolderZK "$9" logsFolderKafka "$logsFolderKafka" logsFolderZK "$logsFolderZK" sourceInstallerDirectory "$sourceInstallerDirectory
# install.tar is SCP'd by root to /root/; rocky user can't read /root/ (mode 700), so use sudo
[ ! -f install.tar ] && sudo cp /root/install.tar . 2>/dev/null || true
tar -xvf install.tar
home_dir=$(pwd)
javaInstalled=$(java -version 2>&1 >/dev/null | egrep "\S+\s+version")
echo "">>setenv.sh

# Step for KAFKA Unzip and Set KAFKAPATH
if [[ $id != 4 ]]; then
    echo "Install AirGapKafka"
    installation_path=$sourceInstallerDirectory/kafka
    echo "InstallationPath="$installation_path
    installation_file=$(find $installation_path -name "*.tgz" -printf "%f\n" | sort -V | tail -1)
    echo "InstallationFile:"$installation_file
    sudo mkdir -p $baseFolderLocation
    sudo mkdir -p $dataFolderKafka
    sudo mkdir -p $logsFolderKafka
    sudo tar -xzf $installation_path"/"$installation_file -C $baseFolderLocation
    # Change ownership to current user for modifications
    current_user=$(whoami)
    sudo chown -R $current_user:$current_user $baseFolderLocation
    var=$installation_file
    echo "var"$var
    replace=""
    extracted_folder=${var//'.tgz'/$replace}
    sed -i '/export KAFKAPATH/d' setenv.sh
    sed -i '/export KAFKA_DATA_PATH/d' setenv.sh
    sed -i '/export KAFKA_LOGS_PATH/d' setenv.sh
    echo "extracted_folder: "$extracted_folder
    kafka_home_path="export KAFKAPATH="$baseFolderLocation$extracted_folder
    sudo ln -s $baseFolderLocation$extracted_folder $gigapath/kafka_latest
    echo "$kafka_home_path">>setenv.sh
    echo "export KAFKA_DATA_PATH="$dataFolderKafka >> setenv.sh
    echo "export KAFKA_LOGS_PATH="$logsFolderKafka >> setenv.sh
fi

#zookeeper setup
    installation_path=$sourceInstallerDirectory/zk
    echo "InstallationPath="$installation_path
    installation_file=$(find $installation_path -name "*.gz" -printf "%f\n" | sort -V | tail -1)
    echo "InstallationFile:"$installation_file
    sudo mkdir -p $baseFolderLocation
    sudo mkdir -p $dataFolderZK
    sudo mkdir -p $logsFolderZK
    sudo tar -xzf $installation_path"/"$installation_file -C $baseFolderLocation
    # Change ownership to current user for modifications
    current_user=$(whoami)
    sudo chown -R $current_user:$current_user $baseFolderLocation
    var=$installation_file
    echo "var"$var
    replace=""
    extracted_folder=${var//'.tar.gz'/$replace}
    zk_home_path="export ZOOKEEPERPATH="$baseFolderLocation$extracted_folder
    sudo ln -s $baseFolderLocation$extracted_folder $gigapath/zookeeper_latest
    echo "$zk_home_path">>setenv.sh
    echo "export ZOOKEEPER_DATA_PATH="$dataFolderZK >> setenv.sh
    echo "export ZOOKEEPER_LOGS_PATH="$logsFolderZK >> setenv.sh

# Configuration of log dir
source setenv.sh
echo "kafkaPath :"$KAFKAPATH

sudo rm -rf $dataFolderZK
sudo rm -rf $logsFolderKafka
sudo rm -rf $dataFolderKafka

sudo mkdir -p $dataFolderZK
sudo mkdir -p $logsFolderKafka
sudo mkdir -p $dataFolderKafka

  # Kafka 4.0+ uses KRaft mode (no ZooKeeper for Kafka).
  # ZooKeeper is still installed below for di-mdm (zookeeper.connectUrl dependency).
  echo "kafkaBrokerCount: "$kafkaBrokerCount

  if [ "$kafkaBrokerCount" == 3 ]; then
    # Write zoo.cfg from scratch — exactly matching QA server config, no default ZK properties
    sudo mkdir -p $ZOOKEEPERPATH/conf
    sudo tee $ZOOKEEPERPATH/conf/zoo.cfg > /dev/null << ZKEOF
clientPort=2181
dataDir=${dataFolderZK}
initLimit=${zkInitLimit}
server.1=${kafkaBrokerHost1}:2888:3888
server.2=${kafkaBrokerHost2}:2888:3888
server.3=${kafkaBrokerHost3}:2888:3888
tickTime=${zkTickTime}
4lw.commands.whitelist=ruok,stat,mntr
ZKEOF
    kraft_quorum_voters="1@${kafkaBrokerHost1}:9093,2@${kafkaBrokerHost2}:9093,3@${kafkaBrokerHost3}:9093"
    offsets_replication=3
    share_replication=3
    share_min_isr=2
    txn_replication=3
    txn_min_isr=3
  fi

  if [ "$kafkaBrokerCount" == 1 ]; then
    # Write zoo.cfg from scratch — exactly matching QA server config, no default ZK properties
    sudo mkdir -p $ZOOKEEPERPATH/conf
    sudo tee $ZOOKEEPERPATH/conf/zoo.cfg > /dev/null << ZKEOF
clientPort=2181
dataDir=${dataFolderZK}
initLimit=${zkInitLimit}
server.1=${kafkaBrokerHost1}:2888:3888
tickTime=${zkTickTime}
4lw.commands.whitelist=ruok,stat,mntr
ZKEOF
    kraft_quorum_voters="1@${kafkaBrokerHost1}:9093"
    offsets_replication=1
    share_replication=1
    share_min_isr=1
    txn_replication=1
    txn_min_isr=1
  fi

  if [[ $id != 4 ]]; then
    # Determine this node's advertised hostname
    if [[ $id == 1 ]]; then
      thisHost=$kafkaBrokerHost1
    elif [[ $id == 2 ]]; then
      thisHost=$kafkaBrokerHost2
    elif [[ $id == 3 ]]; then
      thisHost=$kafkaBrokerHost3
    fi
    # Write server.properties from scratch — exactly matching QA server config, no default Kafka properties
    sudo mkdir -p $KAFKAPATH/config
    sudo tee $KAFKAPATH/config/server.properties > /dev/null << KAFKAEOF
process.roles=broker,controller
node.id=${id}
controller.quorum.voters=${kraft_quorum_voters}
listeners=PLAINTEXT://:9092,CONTROLLER://:9093
advertised.listeners=PLAINTEXT://${thisHost}:9092
listener.security.protocol.map=PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT
inter.broker.listener.name=PLAINTEXT
controller.listener.names=CONTROLLER
log.dirs=${dataFolderKafka}
num.network.threads=3
num.io.threads=8
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600
num.partitions=1
num.recovery.threads.per.data.dir=1
log.segment.bytes=1073741824
log.retention.hours=168
log.retention.check.interval.ms=300000
offsets.topic.replication.factor=${offsets_replication}
transaction.state.log.replication.factor=${txn_replication}
transaction.state.log.min.isr=${txn_min_isr}
share.coordinator.state.topic.replication.factor=${share_replication}
share.coordinator.state.topic.min.isr=${share_min_isr}
KAFKAEOF
    # Patch kafka-server-start.sh for JMX
    source setenv.sh
    sudo sed -i '/^exec \$base_dir/d' $KAFKAPATH/bin/kafka-server-start.sh
    echo "export JMX_PORT=9999" >> $KAFKAPATH/bin/kafka-server-start.sh
    echo "export RMI_HOSTNAME=127.0.0.1" >> $KAFKAPATH/bin/kafka-server-start.sh
    echo 'exec $base_dir/kafka-run-class.sh $EXTRA_ARGS kafka.Kafka "$@"' >> $KAFKAPATH/bin/kafka-server-start.sh
  fi
  # ZooKeeper myid (still needed for di-mdm's ZooKeeper)
  echo "${dataFolderZK}myid"
  echo "$id" | sudo tee "${dataFolderZK}myid" > /dev/null
  echo "added params"

sudo rm -f /var/log/kafka/*
start_kafka_file="start_kafka.sh"
start_zookeeper_file="start_zookeeper.sh"
stop_kafka_file="stop_kafka.sh"
stop_zookeeper_file="stop_zookeeper.sh"
kafka_service_file="odsxkafka.service"
zookeeper_service_file="odsxzookeeper.service"

source setenv.sh
echo "line 149 === $id"
cmd="$ZOOKEEPERPATH/bin/zkServer.sh --config $ZOOKEEPERPATH/conf start"
echo "$cmd">>$start_zookeeper_file

# stop Zookeeper
cmd="$ZOOKEEPERPATH/bin/zookeeper-server-stop.sh --config $ZOOKEEPERPATH/conf stop"
echo "$cmd">>$stop_zookeeper_file

source setenv.sh
home_dir_sh=$(pwd)
source $home_dir_sh/setenv.sh

# ZooKeeper service file: copy from gigashare (fallback to install.tar extract if present)
if [ -f $sourceInstallerDirectory/zk/$zookeeper_service_file ]; then
  sudo cp $sourceInstallerDirectory/zk/$zookeeper_service_file /etc/systemd/system/
elif [ -f $home_dir_sh/install/zookeeper/$zookeeper_service_file ]; then
  sudo cp $home_dir_sh/install/zookeeper/$zookeeper_service_file /etc/systemd/system/
else
  echo "ERROR: $zookeeper_service_file not found in gigashare or install.tar"
fi
sudo mv $home_dir_sh/st*_zookeeper.sh /tmp
sudo mv /tmp/st*_zookeeper.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/st*_zookeeper.sh

if [[ $id != 4 ]]; then
  echo "line 168 === $id"
  cmd="$KAFKAPATH/bin/kafka-server-start.sh $KAFKAPATH/config/server.properties"
  echo "$cmd">>$start_kafka_file

  # stop KAFKA
  cmd="$KAFKAPATH/bin/kafka-server-stop.sh $KAFKAPATH/config/server.properties"
  echo "$cmd">>$stop_kafka_file
  source setenv.sh

  home_dir_sh=$(pwd)
  source $home_dir_sh/setenv.sh
  # Kafka service file: copy from gigashare (fallback to install.tar extract if present)
  # KRaft: no ZooKeeper dependency — service files from gigashare already reflect this
  if [ -f $sourceInstallerDirectory/kafka/$kafka_service_file ]; then
    sudo cp $sourceInstallerDirectory/kafka/$kafka_service_file /etc/systemd/system/
  elif [ -f $home_dir_sh/install/kafka/$kafka_service_file ]; then
    # Fallback: remove ZK dependency from install.tar version before installing
    sed -i '/^Requires=odsxzookeeper.service/d' $home_dir_sh/install/kafka/$kafka_service_file 2>/dev/null || true
    sed -i '/^After=.*odsxzookeeper/d' $home_dir_sh/install/kafka/$kafka_service_file 2>/dev/null || true
    sudo cp $home_dir_sh/install/kafka/$kafka_service_file /etc/systemd/system/
  else
    echo "ERROR: $kafka_service_file not found in gigashare or install.tar"
  fi
  sudo mv $home_dir_sh/st*_kafka.sh /tmp
  sudo mv /tmp/st*_kafka.sh /usr/local/bin/
  sudo chmod +x /usr/local/bin/st*_kafka.sh
  if [ $id == 1 ]; then
    sudo chown gsods:gsods -R $baseFolderLocation
    sudo chown gsods:gsods -R $logsFolderKafka
    sudo chown gsods:gsods -R $dataFolderKafka
    sudo chown gsods:gsods -R $dataFolderZK

    sudo chmod 777 -R $baseFolderLocation
    sudo chmod 777 -R $logsFolderKafka
    sudo chmod 777 -R $dataFolderKafka
    sudo chmod 777 -R $dataFolderZK

    # KRaft: format Kafka storage before first start; save cluster ID to gigashare for other nodes
    KAFKA_CLUSTER_ID=$(sudo -u gsods $KAFKAPATH/bin/kafka-storage.sh random-uuid)
    echo "$KAFKA_CLUSTER_ID" | sudo tee $gigasharepath/kafka-cluster-id > /dev/null
    sudo -u gsods $KAFKAPATH/bin/kafka-storage.sh format -t "$KAFKA_CLUSTER_ID" -c $KAFKAPATH/config/server.properties
    sudo restorecon /etc/systemd/system/odsx* 2>/dev/null || true
    sudo systemctl daemon-reload
    sudo systemctl enable --now odsxzookeeper.service
    sudo systemctl enable --now odsxkafka.service
    sudo systemctl daemon-reload
    installDIMatadata
    # Wait for di-mdm Spring Boot to be ready before installing dependent services
    echo "Waiting for di-mdm to become ready on port 6081..."
    for i in $(seq 1 5); do
      if curl -sf http://${kafkaBrokerHost1}:6081/api/v1/about > /dev/null 2>&1; then
        echo "di-mdm is ready after ${i}x10s"
        break
      fi
      echo "di-mdm not ready yet ($i/5), retrying in 10s..."
      sleep 10
    done
    installDIManager
    installFlink
    installDIProcessor
    installDITransformations
    # Run global_config.sh to configure MDM (flink, space, kafka)
    di_mdm_utils=$gigapath/di-mdm/$(ls -d $gigapath/di-mdm/di-mdm-* 2>/dev/null | head -1 | xargs basename)/utils
    sudo -u gsods bash $di_mdm_utils/global_config.sh $di_mdm_utils/global-${currentHost}.env
  fi
fi



if [[ $id != 1 ]]; then
  sudo chown gsods:gsods -R $baseFolderLocation*
  sudo chown gsods:gsods -R $logsFolderKafka
  sudo chown gsods:gsods -R $dataFolderKafka
  sudo chown gsods:gsods -R $dataFolderZK

  sudo chmod 777 -R $baseFolderLocation
  sudo chmod 777 -R $logsFolderKafka
  sudo chmod 777 -R $dataFolderKafka
  sudo chmod 777 -R $dataFolderZK
  # KRaft: format Kafka storage using same cluster ID as node 1 (required for multi-node cluster)
  if [[ $id != 4 ]]; then
    if [ -f $gigasharepath/kafka-cluster-id ]; then
      KAFKA_CLUSTER_ID=$(cat $gigasharepath/kafka-cluster-id)
    else
      echo "WARNING: $gigasharepath/kafka-cluster-id not found; generating independent ID (multi-node cluster may not form)"
      KAFKA_CLUSTER_ID=$(sudo -u gsods $KAFKAPATH/bin/kafka-storage.sh random-uuid)
    fi
    sudo -u gsods $KAFKAPATH/bin/kafka-storage.sh format -t "$KAFKA_CLUSTER_ID" -c $KAFKAPATH/config/server.properties
  fi
  sudo restorecon /etc/systemd/system/odsx* 2>/dev/null || true
  sudo systemctl daemon-reload
  sudo systemctl enable --now odsxzookeeper.service
  if [[ $id != 4 ]]; then
    sudo systemctl enable --now odsxkafka.service
  fi
  sudo systemctl daemon-reload
fi
