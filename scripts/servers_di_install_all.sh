#!/bin/bash
#set -x
echo "scripts/servers_di_install_all.sh"
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
#echo "Extracting install.tar to "$targetDir
#echo " installtelegrafFlag "$1

function installAirGapJava {
  installation_path=$sourceInstallerDirectory/jdk
  installation_file=$(find $installation_path -name *.rpm -printf "%f\n")
  echo "Installation File :"$installation_file
  echo $installation_path"/"$installation_file
  rpm -ivh $installation_path"/"$installation_file
  sed -i '/export JAVA_HOME=/d' setenv.sh
  java_home_path="export JAVA_HOME='$(readlink -f /usr/bin/javac | sed "s:/bin/javac::")'"
  echo "$java_home_path">>setenv.sh
  echo "installAirGapJava -Done!"
}

function installFlink() {
  info "\nInstalling Flink\n"
  installation_path_flink=$sourceInstallerDirectory/data-integration/di-flink
  installation_file_flink=$(find $installation_path_flink -name "flink*.tgz" -printf "%f\n")
  info "InstallationFile:"$installation_file_flink"\n"
  mkdir -p /dbagiga/di-flink
  mkdir -p /dbagigalogs/di-iidr/di-flink
  info "Copying file from "$installation_path_flink/$installation_file_flink +" to /dbagiga/di-flink \n"
  cp $installation_path_flink/$installation_file_flink /dbagiga/di-flink
  info "\nExtracting zip file...\n"
  tar -xzf /dbagiga/di-flink/$installation_file_flink --directory /dbagiga/di-flink/
  chown -R gsods:gsods /dbagiga/di-flink/
  extracted_folder_flink=$(ls -I "*.tgz" /dbagiga/di-flink/)
  cd /dbagiga/di-flink/
  ln -snf /dbagiga/di-flink/ /home/gsods/di-flink
  ln -snf /dbagiga/di-flink/$extracted_folder_flink /home/gsods/di-flink/latest-flink
  mkdir -p /home/gsods/di-flink/latest-flink/data/savepoints
  mkdir -p /home/gsods/di-flink/latest-flink/data/checkpoints

  # Flink 2.x renamed flink-conf.yaml to config.yaml; handle both
  flink_conf_dir="/dbagiga/di-flink/$extracted_folder_flink/conf"
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
  echo "env.java.opts: \"--add-opens java.base/java.util=ALL-UNNAMED --add-opens java.base/java.lang=ALL-UNNAMED\"">>$flink_conf_file

  chmod +x /dbagiga/di-flink/$extracted_folder_flink/bin/*
   cp $installation_path_flink/di-flink-jobmanager.service /etc/systemd/system/
   cp $installation_path_flink/di-flink-taskmanager.service /etc/systemd/system/

  # Fix server paths in service files to match this environment
   sed -i 's|latest-di-flink|latest-flink|g' /etc/systemd/system/di-flink-jobmanager.service
   sed -i 's|latest-di-flink|latest-flink|g' /etc/systemd/system/di-flink-taskmanager.service
   sed -i "s|FLINK_LOG_DIR=[^ ]*|FLINK_LOG_DIR=/dbagigalogs/di-iidr/di-flink|g" /etc/systemd/system/di-flink-jobmanager.service
   sed -i "s|FLINK_LOG_DIR=[^ ]*|FLINK_LOG_DIR=/dbagigalogs/di-iidr/di-flink|g" /etc/systemd/system/di-flink-taskmanager.service
  # Copy extra JARs if present in gigashare (optional — skip if missing)
   cp $installation_path_flink/*.jar /dbagiga/di-flink/$extracted_folder_flink/lib/ 2>/dev/null || true
   mkdir -p /home/gsods/latest-flink/data/checkpoints/ /home/gsods/latest-flink/data/savepoints/

  # Set final ownership to gsods
   chown -R gsods:gsods /dbagiga/di-flink/
   chown -R gsods:gsods /home/gsods/di-flink/
   chown -R gsods:gsods /dbagigalogs/di-iidr/di-flink
  restorecon /etc/systemd/system/di-* 2>/dev/null || true
  systemctl daemon-reload
  systemctl restart di-flink-taskmanager.service
  systemctl restart di-flink-jobmanager.service

  rm -f /dbagiga/di-flink/di-flink
  info "\n Installation Flink completed."
}

function installDIMatadata {
  info "\n Installing DI-MDM\n"
  installation_path_mdm=$sourceInstallerDirectory/data-integration/di-mdm
  installation_file_mdm=$(find $installation_path_mdm -name "di-mdm*.gz" -printf "%f\n")
  info "InstallationFile:"$installation_file_mdm"\n"
  mkdir -p /dbagiga/di-mdm
  mkdir -p /dbagigalogs/di-mdm
  chown gsods:gsods /dbagigalogs/di-mdm
  cp $installation_path_mdm/$installation_file_mdm /dbagiga/di-mdm
  info "\nExtracting zip file...\n"
  tar -xzf /dbagiga/di-mdm/$installation_file_mdm --directory /dbagiga/di-mdm/
  chown -R gsods:gsods /dbagiga/di-mdm/
  extracted_folder_mdm=$(ls -I "*.gz" /dbagiga/di-mdm/)
  cd /dbagiga/di-mdm/
  info "Creating symlink for :"$extracted_folder_mdm
  ln -snf /dbagiga/di-mdm/ /home/gsods/di-mdm
  ln -snf /dbagiga/di-mdm/$extracted_folder_mdm /home/gsods/di-mdm/latest-di-mdm
  echo "spring.profiles.active=zookeeper">/dbagiga/di-mdm.properties
  if [ "$kafkaBrokerCount" == 3 ]; then
    echo "zookeeper.connectUrl="$kafkaBrokerHost1":2181,"$kafkaBrokerHost2":2181,"$kafkaBrokerHost3":2181">>/dbagiga/di-mdm.properties
  else
    echo "zookeeper.connectUrl="$kafkaBrokerHost1":2181">>/dbagiga/di-mdm.properties
  fi

  # Set final ownership to gsods
   chown -R gsods:gsods /dbagiga/di-mdm/
   chown -R gsods:gsods /home/gsods/di-mdm/
   sudo bash /dbagiga/di-mdm/$extracted_folder_mdm/utils/install_new_version.sh /dbagiga/di-mdm.properties
  rm -f /dbagiga/di-mdm/di-mdm

  # Create global-${currentHost}.env for di-mdm global_config.sh
   tee /dbagiga/di-mdm/$extracted_folder_mdm/utils/global-${currentHost}.env > /dev/null << ENVEOF
MDM_URL=http://${kafkaBrokerHost1}:6081
FLINK_URL=http://${kafkaBrokerHost1}:8081
SPACE_LOOKUP_GROUPS=${spaceLookupGroups}
SPACE_LOOKUP_LOCATORS=${spaceLookupLocators}
KAFKA_BOOTSTRAP_SERVERS=${kafkaBrokerHost1}:9092$([ "$kafkaBrokerCount" == 3 ] && echo ",${kafkaBrokerHost2}:9092,${kafkaBrokerHost3}:9092")
ENVEOF
   chown gsods:gsods /dbagiga/di-mdm/$extracted_folder_mdm/utils/global-${currentHost}.env
   chown -R gsods:gsods /home/gsods/di-mdm/
  info "\n Created global-${currentHost}.env in di-mdm utils for global_config.sh.\n"
}

function installDIManager {
  info "\n Installing DI-Manager\n"
  installation_path_manager=$sourceInstallerDirectory/data-integration/di-manager
  installation_file_manager=$(find $installation_path_manager -name "di-manager*.gz" -printf "%f\n")
  info "InstallationFile:"$installation_file_manager"\n"
  mkdir -p /dbagiga/di-manager
  mkdir -p /dbagigalogs/di-manager
  chown gsods:gsods /dbagigalogs/di-manager
  info "Copying file from "$installation_path_manager/$installation_file_manager +" to /dbagiga/di-manager \n"
  cp $installation_path_manager/$installation_file_manager /dbagiga/di-manager
  info "\nExtracting zip file...\n"
  tar -xzf /dbagiga/di-manager/$installation_file_manager --directory /dbagiga/di-manager/
  chown -R gsods:gsods /dbagiga/di-manager/
  extracted_folder_manager=$(ls -I "*.gz" /dbagiga/di-manager/)
  cd /dbagiga/di-manager/
  info "Creating symlink for :"$extracted_folder_manager
  ln -snf /dbagiga/di-manager/ /home/gsods/di-manager
  ln -snf /dbagiga/di-manager/$extracted_folder_manager /home/gsods/di-manager/latest-di-manager

  echo "springdoc.api-docs.path=/api-docs">/dbagiga/di-manager.properties
  echo "springdoc.swagger-ui.path=/swagger-ui">>/dbagiga/di-manager.properties
  echo "springdoc.swagger-ui.operationsSorter=method">>/dbagiga/di-manager.properties
  sed -i '/^mdm.server.url/d' /dbagiga/di-manager.properties
  echo "mdm.server.url=http://$kafkaBrokerHost1:6081">>/dbagiga/di-manager.properties
  sed -i '/^mdm.server.fallback-url/d' /dbagiga/di-manager.properties
  echo "mdm.server.fallback-url=http://$kafkaBrokerHost1:6081">>/dbagiga/di-manager.properties
  echo "server.port=6080">>/dbagiga/di-manager.properties
  echo "mdm.client.timeouts.connection.ms=10000">>/dbagiga/di-manager.properties
  echo "mdm.client.timeouts.read.ms=60000">>/dbagiga/di-manager.properties

  # Set final ownership to gsods
   chown -R gsods:gsods /dbagiga/di-manager/
   chown -R gsods:gsods /home/gsods/di-manager/
  # Use absolute path - cannot cd into /home/gsods/ (mode 700)
   sudo bash /dbagiga/di-manager/$extracted_folder_manager/utils/install_new_version.sh /dbagiga/di-manager.properties
  sudo chown -R gsods:gsods /dbagiga/di-manager/
  sudo chown -R gsods:gsods /home/gsods/di-manager/
  rm -f /dbagiga/di-manager/di-manager
  info "\n Installation DI-Manager completed.\n"
}

function installDIProcessor {
    info "\n Installing DI-Processor\n"
    installation_path_manager=$sourceInstallerDirectory/data-integration/di-processor
    installation_file_manager=$(find $installation_path_manager -name "di-processor*.tgz" -printf "%f\n")
    info "InstallationFile:"$installation_file_manager"\n"
    mkdir -p /dbagiga/di-processor
    mkdir -p /dbagigalogs/di-processor
    info "Copying file from "$installation_path_manager/$installation_file_manager +" to /dbagiga/di-processor \n"
    cp $installation_path_manager/$installation_file_manager /dbagiga/di-processor
    info "\nExtracting zip file...\n"
    tar -xzf /dbagiga/di-processor/$installation_file_manager --directory /dbagiga/di-processor/
    chown gsods:gsods /dbagigalogs/di-processor
    extracted_folder_manager=$(ls -I "*.tgz" /dbagiga/di-processor/)
    cd /dbagiga/di-processor/
    info "Creating symlink for :"$extracted_folder_manager
    ln -snf /dbagiga/di-processor/ /home/gsods/di-processor
    ln -snf /dbagiga/di-processor/$extracted_folder_manager /home/gsods/di-processor/latest-di-processor

    echo "mdm.server.url=http://$kafkaBrokerHost1:6081">/dbagiga/di-processor.properties
    echo "mdm.server.fallback-url=http://$kafkaBrokerHost1:6081">>/dbagiga/di-processor.properties

    # Set final ownership to gsods
     chown gsods:gsods /dbagigalogs/di-processor
     chown -R gsods:gsods /dbagiga/di-processor/
     chown -R gsods:gsods /home/gsods/di-processor/
    # Use absolute path - cannot cd into /home/gsods/ (mode 700)
    sudo bash /dbagiga/di-processor/$extracted_folder_manager/utils/install_new_version.sh /dbagiga/di-processor.properties
    sudo chown -R gsods:gsods /dbagiga/di-processor/
    sudo chown -R gsods:gsods /home/gsods/di-processor/
    rm -f /dbagiga/di-processor/di-processor
}

function installDITransformations {
  info "\n Installing DI-Transformations\n"
  installation_path=$sourceInstallerDirectory/data-integration/di-transformations
  installation_file=$(find $installation_path -name "di-transformations*.tgz" -printf "%f\n")
  info "InstallationFile:"$installation_file"\n"
   mkdir -p /dbagiga/di-transformations
   mkdir -p /dbagigalogs/di-transformations
   chown gsods:gsods /dbagigalogs/di-transformations
   cp $installation_path/$installation_file /dbagiga/di-transformations
   info "\nExtracting zip file...\n"
   tar -xzf /dbagiga/di-transformations/$installation_file --directory /dbagiga/di-transformations/
  chown -R gsods:gsods /dbagiga/di-transformations/
  extracted_folder_transformations=$(ls -I "*.tgz" /dbagiga/di-transformations/)
  cd /dbagiga/di-transformations/
  info "Creating symlink for :"$extracted_folder_transformations
   ln -snf /dbagiga/di-transformations/ /home/gsods/di-transformations
   ln -snf /dbagiga/di-transformations/$extracted_folder_transformations /home/gsods/di-transformations/latest-di-transformations

  # Derive XAP manager host from spaceLookupLocators (strip :4174)
  xapManagerHost=${spaceLookupLocators%:4174}

   tee /dbagiga/di-transformations.properties > /dev/null << TRANEOF
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

   chown -R gsods:gsods /dbagiga/di-transformations/
   chown -R gsods:gsods /home/gsods/di-transformations/
   sudo bash /dbagiga/di-transformations/$extracted_folder_transformations/utils/install_new_version.sh /dbagiga/di-transformations.properties
   # Fix log redirect path in deployed service file (install_new_version.sh may write wrong prefix)
  sudo chown -R gsods:gsods /dbagiga/di-transformations/
  sudo chown -R gsods:gsods /home/gsods/di-transformations/
   sed -i 's|1>>.*di-transformations\.log|1>>/dbagigalogs/di-transformations/di-transformations.log|g' /etc/systemd/system/di-transformations.service
   restorecon /etc/systemd/system/di-transformations.service 2>/dev/null || true
   systemctl daemon-reload
   systemctl restart di-transformations.service
  rm -f /dbagiga/di-transformations/di-transformations
  info "\n Installation DI-Transformations completed.\n"
}

function installDIHAdmin {
  info "\n Installing DIH-Admin\n"
  installation_path=$sourceInstallerDirectory/data-integration/dih-admin
  installation_file=$(find $installation_path -name "dih-admin*.tgz" -printf "%f\n" | sort -V | tail -1)
  info "InstallationFile:"$installation_file"\n"
   mkdir -p /dbagiga/dih-admin
   mkdir -p /dbagigalogs/dih-admin
   chown gsods:gsods /dbagigalogs/dih-admin
   cp $installation_path/$installation_file /dbagiga/dih-admin
  info "\nExtracting zip file...\n"
   tar -xzf /dbagiga/dih-admin/$installation_file --directory /dbagiga/dih-admin/

  current_user=$(whoami)
   chown -R gsods:gsods /dbagiga/dih-admin/

  extracted_folder_dih_admin=$(find /dbagiga/dih-admin -maxdepth 1 -type d -name "dih-admin-*" -printf "%f\n" | sort -V | tail -1)
  info "Creating symlink for :"$extracted_folder_dih_admin
   ln -snf /dbagiga/dih-admin/ /home/gsods/dih-admin

  # Derive XAP manager host from spaceLookupLocators (strip :4174)
  xapManagerHost=${spaceLookupLocators%:4174}

   tee /dbagiga/dih-admin.properties > /dev/null << DIHADMINEOF
server.port=7080
bootstrap-servers=${kafkaBrokerHost1}:9092
dimanager.client.timeouts.connection.ms=10000
dimanager.client.timeouts.read.ms=60000
dimanager.server.url=http://${kafkaBrokerHost1}:6080
ditransformations.client.timeouts.connection.ms=10000
ditransformations.client.timeouts.request.ms=30000
ditransformations.server.url=http://${kafkaBrokerHost1}:6090
kafka-topics.retention-task.delay-in-minutes=10
kafka-topics.retention-task.duration-in-hours=168
topic-polling-timeout-ms=2000
task.executor.corePoolSize=5
task.executor.maxPoolSize=10
task.executor.queueCapacity=25
mdm.client.timeouts.connection.ms=10000
mdm.client.timeouts.read.ms=60000
mdm.server.url=http://${kafkaBrokerHost1}:6081
xap.manager.url=http://${xapManagerHost}:8090
security.base.url=http://xap-security-service:9000
service.creator.url=http://${kafkaBrokerHost1}:8080
graphql.url=http://${kafkaBrokerHost1}:18080
service.creator.client.timeouts.connection.ms=10000
service.creator.client.timeouts.read.ms=60000
springdoc.swagger-ui.operationsSorter=method
springdoc.swagger-ui.path=/swagger-ui
springdoc.api-docs.path=/api-docs
graphql.graphiql.enabled=true
graphql.altair.enabled=true
graphql.playground.enabled=true
space-deployment.waiting.timeout.seconds=60
graphql.servlet.exception-handlers-enabled=true
logging.level.com.gigaspaces.di.dihadmin.client=DEBUG
DIHADMINEOF

   chown -R gsods:gsods /dbagiga/dih-admin/
   chown -R gsods:gsods /home/gsods/dih-admin/
   sudo bash /dbagiga/dih-admin/$extracted_folder_dih_admin/utils/install_new_version.sh /dbagiga/dih-admin.properties
   sudo chmod +x /dbagiga/dih-admin/$extracted_folder_dih_admin/lib/*.jar
   sudo chown -R gsods:gsods $gigapath/dih-admin/
   sudo chown -R gsods:gsods /home/gsods/dih-admin/
   restorecon /etc/systemd/system/dih-admin.service 2>/dev/null || true
   systemctl daemon-reload
  rm -f /dbagiga/dih-admin/dih-admin
  info "\n Installation DIH-Admin completed.\n"
}

function installDISubscription {
    info "\n Installing DI-Subscription-Manager\n"
    installation_path_manager=$sourceInstallerDirectory/data-integration/di-subscription-manager
    installation_file_manager=$(find $installation_path_manager -name "di-subscription-manager*.tgz" -printf "%f\n")
    info "InstallationFile:"$installation_file_manager"\n"
    mkdir -p /dbagiga/di-subscription-manager
    mkdir -p /dbagigalogs/di-subscription-manager
    mkdir -p /dbagigalogs/di-iidr
    chown gsods:gsods /dbagigalogs/di-subscription-manager
    chown gsods:gsods /dbagigalogs/di-iidr
    info "Copying file from "$installation_path_manager/$installation_file_manager +" to /dbagiga/di-subscription-manager \n"
    cp $installation_path_manager/$installation_file_manager /dbagiga/di-subscription-manager
    info "\nExtracting zip file...\n"
    tar -xzf /dbagiga/di-subscription-manager/$installation_file_manager --directory /dbagiga/di-subscription-manager/
    chown -R gsods:gsods /dbagiga/di-subscription-manager/
    extracted_folder_manager=$(ls -I "*.tgz" /dbagiga/di-subscription-manager/)
    cd /dbagiga/di-subscription-manager/
    info "Creating symlink for :"$extracted_folder_manager
     ln -snf $extracted_folder_manager /home/gsods/di-subscription-manager
     ln -snf /dbagiga/di-subscription-manager/$extracted_folder_manager /home/gsods/di-subscription-manager/latest-di-subscription-manager

    echo "##iidr.as##" > /dbagiga/di-subscription-manager.properties
    echo "iidr-as.hostname=$iidrHost" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-as.port=10101" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-as.username=$iidrUsername" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-as.password=$iidrPassword" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-as.source-datastore.mirror_auto_restart_interval_seconds=15" >> /dbagiga/di-subscription-manager.properties
    echo "" >> /dbagiga/di-subscription-manager.properties
    echo "datastore.save-credentials-in-mdm=false" >> /dbagiga/di-subscription-manager.properties
    echo "" >> /dbagiga/di-subscription-manager.properties
    echo "###kafka properties" >> /dbagiga/di-subscription-manager.properties
    echo "kafka.host=$kafkaBrokerHost1" >> /dbagiga/di-subscription-manager.properties
    echo "kafka.port=9092" >> /dbagiga/di-subscription-manager.properties
    echo "kafka.topic.prefix=" >> /dbagiga/di-subscription-manager.properties
    echo "" >> /dbagiga/di-subscription-manager.properties
    echo "###iidr kafka properties" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.host=$iidrHost" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.port=11701" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.username=$iidrUsername" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.password=$iidrPassword" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.properties.manager.client.timeouts.connection.ms=10000" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.properties.manager.client.timeouts.read.ms=60000" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.properties.manager.server.url=http://$iidrHost:6085" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.user-exit.properties.file.use-api=false" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.user-exit.properties.file.read-path=/giga/iidr/kafka/instance/KAFKA/conf" >> /dbagiga/di-subscription-manager.properties
    echo "iidr-kafka.user-exit.properties.file.write-path=/giga/iidr/kafka/instance/KAFKA/conf" >> /dbagiga/di-subscription-manager.properties
    echo "" >> /dbagiga/di-subscription-manager.properties
    echo "##mdm##" >> /dbagiga/di-subscription-manager.properties
    echo "mdm.client.timeouts.connection.ms=10000" >> /dbagiga/di-subscription-manager.properties
    echo "mdm.client.timeouts.read.ms=60000" >> /dbagiga/di-subscription-manager.properties
    echo "mdm.url=/api/v1" >> /dbagiga/di-subscription-manager.properties
    echo "mdm.server.url=http://$kafkaBrokerHost1:6081" >> /dbagiga/di-subscription-manager.properties
    echo "" >> /dbagiga/di-subscription-manager.properties
    echo "##subscription manager" >> /dbagiga/di-subscription-manager.properties
    echo "subscription-manager.server.url=http://$iidrHost:6082" >> /dbagiga/di-subscription-manager.properties
    echo "subscription-manager.feature.supports-transaction=true" >> /dbagiga/di-subscription-manager.properties
    echo "#mdm-waiting-timeout is in seconds" >> /dbagiga/di-subscription-manager.properties
    echo "subscription-manager.mdm-availability-waiting-timeout-seconds=300" >> /dbagiga/di-subscription-manager.properties
    echo "server.port=6082" >> /dbagiga/di-subscription-manager.properties

    echo "##swagger-ui##" >> /dbagiga/di-subscription-manager.properties
    echo "springdoc.api-docs.path=/api-docs" >> /dbagiga/di-subscription-manager.properties
    echo "springdoc.swagger-ui.operationsSorter=method" >> /dbagiga/di-subscription-manager.properties
    echo "springdoc.swagger-ui.path=/swagger-ui" >> /dbagiga/di-subscription-manager.properties
    echo "springdoc.swagger-ui.request-timeout=10000 # Timeout value in milliseconds" >> /dbagiga/di-subscription-manager.properties
    echo "" >> /dbagiga/di-subscription-manager.properties
    echo "logging.level.org.springframework.web.filter.CommonsRequestLoggingFilter=DEBUG" >> /dbagiga/di-subscription-manager.properties
    # Use absolute path - cannot cd into /home/gsods/ (mode 700)
     sudo bash /dbagiga/di-subscription-manager/$extracted_folder_manager/utils/install_new_version.sh /dbagiga/di-subscription-manager.properties
    # Fix log path in deployed service file (must run AFTER install_new_version.sh deploys it)
     sed -i -e 's|logs/di-subscription-manager-iidr.log|/dbagigalogs/di-iidr/di-subscription-manager.log|g' /etc/systemd/system/di-subscription-manager-iidr.service
     systemctl daemon-reload
     systemctl enable di-subscription-manager-iidr
     systemctl restart di-subscription-manager-iidr
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
    installAirGapJava
fi
echo " dataFolderKafka "$8" dataFolderZK "$9" logsFolderKafka "$logsFolderKafka" logsFolderZK "$logsFolderZK" sourceInstallerDirectory "$sourceInstallerDirectory
[ ! -f install.tar ] && sudo cp /root/install.tar . 2>/dev/null || true
tar -xvf install.tar
home_dir=$(pwd)
javaInstalled=$(java -version 2>&1 >/dev/null | egrep "\S+\s+version")
echo "">>setenv.sh

# Phase 2 shortcut: for 3-node install, phase 2 installs DI services on node1 only
# (ZK+Kafka already running from phase 1; skip infra setup entirely)
if [ "$kafkaBrokerCount" == 3 ] && [[ $id == 1 ]] && [ "$dimMdmFlinkInstallon1bFlag" == "y" ]; then
  source setenv.sh 2>/dev/null || true
  installDIMatadata
  echo "Waiting for di-mdm to become ready on port 6081..."
  for i in $(seq 1 30); do
    if curl -sf http://${kafkaBrokerHost1}:6081/api/v1/about > /dev/null 2>&1; then
      echo "di-mdm is ready after ${i}x10s"
      break
    fi
    echo "di-mdm not ready yet ($i/30), retrying in 10s..."
    sleep 10
  done
  installDIManager
  installFlink
  installDIProcessor
  installDITransformations
  installDIHAdmin
  di_mdm_utils=/dbagiga/di-mdm/$(ls -d /dbagiga/di-mdm/di-mdm-* 2>/dev/null | head -1 | xargs basename)/utils
  sudo -u gsods bash $di_mdm_utils/global_config.sh $di_mdm_utils/global-${currentHost}.env
  exit 0
fi

# Step for KAFKA Unzip and Set KAFKAPATH
if [[ $id != 4 ]]; then
    echo "Install AirGapKafka"
    installation_path=$sourceInstallerDirectory/kafka
    echo "InstallationPath="$installation_path
    installation_file=$(find $installation_path -name "*.tgz" -printf "%f\n")
    echo "InstallationFile:"$installation_file
    mkdir -p $baseFolderLocation
    mkdir -p $dataFolderKafka
    mkdir -p $logsFolderKafka
    tar -xzf $installation_path"/"$installation_file -C $baseFolderLocation
    chown -R gsods:gsods $baseFolderLocation
    var=$installation_file
    echo "var"$var
    replace=""
    extracted_folder=${var//'.tgz'/$replace}
    sed -i '/export KAFKAPATH/d' setenv.sh
    sed -i '/export KAFKA_DATA_PATH/d' setenv.sh
    sed -i '/export KAFKA_LOGS_PATH/d' setenv.sh
    echo "extracted_folder: "$extracted_folder
    kafka_home_path="export KAFKAPATH="$baseFolderLocation$extracted_folder
    ln -snf $baseFolderLocation$extracted_folder /dbagiga/kafka_latest
    echo "$kafka_home_path">>setenv.sh
    echo "export KAFKA_DATA_PATH="$dataFolderKafka >> setenv.sh
    echo "export KAFKA_LOGS_PATH="$logsFolderKafka >> setenv.sh
fi

#zookeeper setup
    installation_path=$sourceInstallerDirectory/zk
    echo "InstallationPath="$installation_path
    installation_file=$(find $installation_path -name "*.gz" -printf "%f\n")
    echo "InstallationFile:"$installation_file
    mkdir -p $baseFolderLocation
    mkdir -p $dataFolderZK
    mkdir -p $logsFolderZK
    chown gsods:gsods $logsFolderZK
    tar -xzf $installation_path"/"$installation_file -C $baseFolderLocation
    chown -R gsods:gsods $baseFolderLocation
    var=$installation_file
    echo "var"$var
    replace=""
    extracted_folder=${var//'.tar.gz'/$replace}
    zk_home_path="export ZOOKEEPERPATH="$baseFolderLocation$extracted_folder
    ln -snf $baseFolderLocation$extracted_folder /dbagiga/zookeeper_latest
    sed -i '/export ZOOKEEPERPATH/d' setenv.sh
    sed -i '/export ZOOKEEPER_DATA_PATH/d' setenv.sh
    sed -i '/export ZOOKEEPER_LOGS_PATH/d' setenv.sh
    echo "$zk_home_path">>setenv.sh
    echo "export ZOOKEEPER_DATA_PATH="$dataFolderZK >> setenv.sh
    echo "export ZOOKEEPER_LOGS_PATH="$logsFolderZK >> setenv.sh

# Configuration of log dir
source setenv.sh
echo "kafkaPath :"$KAFKAPATH

rm -rf $dataFolderZK
rm -rf $logsFolderKafka
rm -rf $dataFolderKafka

mkdir -p $dataFolderZK
mkdir -p $logsFolderKafka
mkdir -p $dataFolderKafka

  # Kafka 4.0+ uses KRaft mode (no ZooKeeper for Kafka).
  # ZooKeeper is still installed below for di-mdm (zookeeper.connectUrl dependency).
  echo "kafkaBrokerCount: "$kafkaBrokerCount

  if [ "$kafkaBrokerCount" == 3 ]; then
    # Write zoo.cfg from scratch — exactly matching QA server config, no default ZK properties
     mkdir -p $ZOOKEEPERPATH/conf
     tee $ZOOKEEPERPATH/conf/zoo.cfg > /dev/null << ZKEOF
clientPort=2181
dataDir=${dataFolderZK}
initLimit=${zkInitLimit}
syncLimit=${zkSyncLimit}
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
     mkdir -p $ZOOKEEPERPATH/conf
     tee $ZOOKEEPERPATH/conf/zoo.cfg > /dev/null << ZKEOF
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
     mkdir -p $KAFKAPATH/config
     tee $KAFKAPATH/config/server.properties > /dev/null << KAFKAEOF
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
     sed -i '/^exec \$base_dir/d' $KAFKAPATH/bin/kafka-server-start.sh
    echo "export JMX_PORT=9999" >> $KAFKAPATH/bin/kafka-server-start.sh
    echo "export RMI_HOSTNAME=127.0.0.1" >> $KAFKAPATH/bin/kafka-server-start.sh
    echo 'exec $base_dir/kafka-run-class.sh $EXTRA_ARGS kafka.Kafka "$@"' >> $KAFKAPATH/bin/kafka-server-start.sh
  fi
  # ZooKeeper myid (still needed for di-mdm's ZooKeeper)
  echo "${dataFolderZK}myid"
  echo "$id" |  tee "${dataFolderZK}myid" > /dev/null
  echo "added params"

 rm -f /var/log/kafka/*
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
   cp $sourceInstallerDirectory/zk/$zookeeper_service_file /etc/systemd/system/
elif [ -f $home_dir_sh/install/zookeeper/$zookeeper_service_file ]; then
   cp $home_dir_sh/install/zookeeper/$zookeeper_service_file /etc/systemd/system/
else
  echo "ERROR: $zookeeper_service_file not found in gigashare or install.tar"
fi
 mv $home_dir_sh/st*_zookeeper.sh /tmp
 mv /tmp/st*_zookeeper.sh /usr/local/bin/
 chmod +x /usr/local/bin/st*_zookeeper.sh

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
     cp $sourceInstallerDirectory/kafka/$kafka_service_file /etc/systemd/system/
  elif [ -f $home_dir_sh/install/kafka/$kafka_service_file ]; then
    # Fallback: remove ZK dependency from install.tar version before installing
    sed -i '/^Requires=odsxzookeeper.service/d' $home_dir_sh/install/kafka/$kafka_service_file 2>/dev/null || true
    sed -i '/^After=.*odsxzookeeper/d' $home_dir_sh/install/kafka/$kafka_service_file 2>/dev/null || true
     cp $home_dir_sh/install/kafka/$kafka_service_file /etc/systemd/system/
  else
    echo "ERROR: $kafka_service_file not found in gigashare or install.tar"
  fi
   mv $home_dir_sh/st*_kafka.sh /tmp
   mv /tmp/st*_kafka.sh /usr/local/bin/
   chmod +x /usr/local/bin/st*_kafka.sh
  if [ $id == 1 ]; then
     chown gsods:gsods -R $baseFolderLocation
     chown gsods:gsods -R $logsFolderKafka
     chown gsods:gsods -R $dataFolderKafka
     chown gsods:gsods -R $dataFolderZK

     chmod 777 -R $baseFolderLocation
     chmod 777 -R $logsFolderKafka
     chmod 777 -R $dataFolderKafka
     chmod 777 -R $dataFolderZK

    # KRaft: format Kafka storage before first start; save cluster ID to gigashare for other nodes
    KAFKA_CLUSTER_ID=$(sudo -u gsods $KAFKAPATH/bin/kafka-storage.sh random-uuid)
    echo "$KAFKA_CLUSTER_ID" |  tee $sourceInstallerDirectory/kafka-cluster-id > /dev/null
    sudo -u gsods $KAFKAPATH/bin/kafka-storage.sh format -t "$KAFKA_CLUSTER_ID" -c $KAFKAPATH/config/server.properties
     restorecon /etc/systemd/system/odsx* 2>/dev/null || true
     systemctl daemon-reload
     systemctl enable --now odsxzookeeper.service
     systemctl enable --now odsxkafka.service
     systemctl daemon-reload
    # For 3-node installs, DI services are installed in phase 2 (after ZK quorum forms)
    if [ "$kafkaBrokerCount" == 1 ]; then
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
    installDIHAdmin
    # Run global_config.sh to configure MDM (flink, space, kafka)
    di_mdm_utils=/dbagiga/di-mdm/$(ls -d /dbagiga/di-mdm/di-mdm-* 2>/dev/null | head -1 | xargs basename)/utils
    sudo -u gsods bash $di_mdm_utils/global_config.sh $di_mdm_utils/global-${currentHost}.env
    fi
  fi
fi



if [[ $id != 1 ]]; then
   chown gsods:gsods -R $baseFolderLocation*
   chown gsods:gsods -R $logsFolderKafka
   chown gsods:gsods -R $dataFolderKafka
   chown gsods:gsods -R $dataFolderZK

   chmod 777 -R $baseFolderLocation
   chmod 777 -R $logsFolderKafka
   chmod 777 -R $dataFolderKafka
   chmod 777 -R $dataFolderZK
  # KRaft: format Kafka storage using same cluster ID as node 1 (required for multi-node cluster)
  if [[ $id != 4 ]]; then
    if [ -f $sourceInstallerDirectory/kafka-cluster-id ]; then
      KAFKA_CLUSTER_ID=$(cat $sourceInstallerDirectory/kafka-cluster-id)
    else
      echo "WARNING: $sourceInstallerDirectory/kafka-cluster-id not found; generating independent ID (multi-node cluster may not form)"
      KAFKA_CLUSTER_ID=$(sudo -u gsods $KAFKAPATH/bin/kafka-storage.sh random-uuid)
    fi
    sudo -u gsods $KAFKAPATH/bin/kafka-storage.sh format -t "$KAFKA_CLUSTER_ID" -c $KAFKAPATH/config/server.properties
  fi
   restorecon /etc/systemd/system/odsx* 2>/dev/null || true
   systemctl daemon-reload
   systemctl enable --now odsxzookeeper.service
  if [[ $id != 4 ]]; then
     systemctl enable --now odsxkafka.service
  fi
   systemctl daemon-reload
fi
