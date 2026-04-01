# set -x
# Set XDG_RUNTIME_DIR for systemctl --user over SSH
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus

echo "Installation starting..."
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

#source gs_installation.properties
osDetected=$(cat /etc/os-release|grep "NAME=" | head -n 1 | cut -d "=" -f2 | sed -e 's/^"//' -e 's/"$//')
echo "os: "$osDetected
osType=$osDetected

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
          yum -y install java-1.8.0-openjdk
          yum -y install java-1.8.0-openjdk-devel
    elif [ "$openJdkVersion" == "11" ] ; then
        echo "centos 11"
        yum -y install java-11-openjdk
        yum -y install java-11-openjdk-devel
        fi
    elif [ "$osType" == "ubuntu" ]; then
      if [ "$openJdkVersion" == "1.8" ]  ||  [ "$openJdkVersion" == "8" ]; then
        echo "ubuntu 1.8"
          apt-get update
          apt -y install openjdk-8-jdk
      elif [ "$openJdkVersion" == "11" ]; then
        echo "ubuntu 11"
          apt-get update
          apt -y install openjdk-11-jdk
          #apt-get install openjdk-11-jdk
      fi
    elif [ "$osType" == "awsLinux2" ] || [ "$osType" == "Amazon Linux" ] || [ "$osType" == "Amazon Linux2" ]; then
      if [ "$openJdkVersion" == "1.8" ] ||  [ "$openJdkVersion" == "8" ]; then
        echo "awsLinux2 11"
          amazon-linux-extras enable corretto8
          yum clean metadata
          yum -y install java-1.8.0-amazon-corretto
      elif [ "$openJdkVersion" == "11" ]; then
        echo "elseif awsLinux2 11"
          amazon-linux-extras install -y java-openjdk11
      fi
    else
      if [ "$openJdkVersion" == "1.8" ] ||  [ "$openJdkVersion" == "8" ]; then
        echo "if ubuntu 11"
          yum -y install java-1.8.0-openjdk
          yum -y install java-1.8.0-openjdk-devel
    elif [ "$openJdkVersion" == "11" ]; then
        echo "else ubuntu 11"
        yum -y install java-11-openjdk
        yum -y install java-11-openjdk-devel
    elif [ "$openJdkVersion" == "17" ]; then
        echo "else ubuntu 11"
        yum -y install java-17-openjdk
        yum -y install java-17-openjdk-devel
        fi
  fi
    echo "Installation Remote JDK - Done!"
}

function installZip {
    echo "os:"$osType
    if [ "$osType" == "centos" ]; then
	    yum -y install unzip
    elif [ "$osType" == "ubuntu" ]; then
        apt -y install unzip
    elif [ "$osType" == "awsLinux2" ] || [ "$osType" == "Amazon Linux" ] || [ "$osType" == "Amazon Linux2" ] || [ "$osType" == "Red Hat Enterprise Linux" ]  || [[ "$osType" ==  *"Linux"*  ]]; then
        yum -y install unzip
	else
	   yum -y install unzip
	fi
	echo "install ZIP - Done!"
}
function installWget {
  echo "os:"$osType
    if [ "$osType" == "centos" ]; then
	    yum -y install wget
    elif [ "$osType" == "ubuntu" ]; then
        apt -y install wget
    elif [ "$osType" == "awsLinux2" ] || [ "$osType" == "Amazon Linux" ] || [ "$osType" == "Amazon Linux2" ] || [ "$osType" == "Red Hat Enterprise Linux" ]  || [[ "$osType" ==  *"Linux"*  ]]; then
        yum -y install wget
    else
	    yum -y install wget
	fi
	echo "install wget - Done!"
}
function downloadGS {
  if [ ! -d "install" ]; then
    mkdir "install"
  fi
	#mkdir "install"
	cd install
	if [ -e  gigaspaces-${gsType}-enterprise-${gsVersion}.zip ]; then
	  rm gigaspaces-${gsType}-enterprise-${gsVersion}.zip
	  wget https://gigaspaces-releases-eu.s3.amazonaws.com/${gsType}/${gsVersion}/gigaspaces-${gsType}-enterprise-${gsVersion}.zip
	else
	  wget https://gigaspaces-releases-eu.s3.amazonaws.com/${gsType}/${gsVersion}/gigaspaces-${gsType}-enterprise-${gsVersion}.zip
	fi
	cd
	echo "download GS - Done!"
}
function unzipGS {
  targetDir=$1

  if [ ! -d $targetDir ]; then
    mkdir $targetDir
  fi
  echo $targetDir
  unzip install/gigaspaces-${gsType}-enterprise-${gsVersion}.zip -d  $targetDir  #/home/ec2-user/install/
  echo "unzipping GS - Done!"
  }
function activateGS {
  targetDir=$1
  #if [ "$gsVersion" == "15.8.1" ]; then
  #license="Product=InsightEdge;Version=15.8;Type=ENTERPRISE;Customer=demo_DEV;Expiration=2021-Jul-13;Hash=OSBxNFMO4OVJOFOBwNQF"
  license="export GS_LICENSE='Product=InsightEdge;Version=15.8;Type=ENTERPRISE;Customer=GigaSpaces_Technologies_-_Internal_rajiv_shah_DEV;Expiration=2021-Dec-31;Hash=gSZQ6OSP83VRn0PRQZNH'"
  #fi
  #echo $license>gigaspaces-${gsType}-enterprise-${gsVersion}/gs-license.txt
  sed -i '/export GS_LICENSE/d' $targetDir/gigaspaces-${gsType}-enterprise-${gsVersion}/bin/setenv-overrides.sh
  sed -i '/export GS_MANAGER_SERVERS/d' $targetDir/gigaspaces-${gsType}-enterprise-${gsVersion}/bin/setenv-overrides.sh
  echo "targetDir"$targetDir
  echo  "">>$targetDir/gigaspaces-${gsType}-enterprise-${gsVersion}/bin/setenv-overrides.sh
  echo  "$license">>$targetDir/gigaspaces-${gsType}-enterprise-${gsVersion}/bin/setenv-overrides.sh
  hostCfg="export GS_MANAGER_SERVERS="$gs_clusterhosts
  echo  "$hostCfg">>$targetDir/gigaspaces-${gsType}-enterprise-${gsVersion}/bin/setenv-overrides.sh
	echo "activating GS - Done!"
}
function setGSHome {
    targetDir=$1
    #home_dir=$(pwd)
    #path="export GS_HOME="$home_dir/gigaspaces-${gsType}-enterprise-${gsVersion}
    #rm setenv.sh
    path="export GS_HOME="$targetDir/gigaspaces-smart-ods
    sed -i '/export GS_HOME/d' setenv.sh
    echo "">>setenv.sh
    echo "$path">>setenv.sh
    source setenv.sh
  echo "Set GS_HOME - Done!"
}

function installAirGapJava {
    echo "Installation of AirGapJava"
    home_dir=$(pwd)
    installation_path=$sourceInstallerDirectory/jdk

    installation_file=$(find $installation_path -name *.rpm -printf "%f\n")
    echo "Installation File :"$installation_file
    if [ "$osType" == "centos" ] || [ "$osType" == "Red Hat Enterprise Linux" ] || [ "$osType" == "Amazon Linux" ] || [ "$osType" == "Amazon Linux2" ]  || [[ "$osType" ==  *"Linux"*  ]]; then
      echo $installation_path"/"$installation_file
	      rpm -ivh $installation_path"/"$installation_file
	      java_home_path="export JAVA_HOME='$(readlink -f /usr/bin/javac | sed "s:/bin/javac::")'"
	     echo "">>setenv.sh
	     echo "$java_home_path">>setenv.sh
	    echo "installAirGapJava -Done!"
	  elif [ "$osType" == "ubuntu" ]; then
        sudo dpkg -i $installation_path"/"$installation_file
      java_home_folder=$(ls /usr/lib/jvm/)
      java_home=$java_home_folder
      java_home_path="export JAVA_HOME=/usr/lib/jvm/$java_home"
      java_path="export PATH="'$PATH'":"'${JAVA_HOME}'"/bin"
      echo "Installation AirGapJava -Done!"
      echo "">>setenv.sh
      echo "$java_home_path">>setenv.sh
      echo "$java_path">>setenv.sh
      source setenv.sh
      echo "Set JAVA_HOME -Done!"
    fi

}
function installAirGapUnzip {
   echo "Install AirGapUnzip"
   home_dir=$(pwd)
   installation_path=$sourceInstallerDirectory/unzip
   installation_file=$(find $installation_path -name *.rpm -printf "%f\n")
   if [ "$osType" == "centos" ] || [ "$osType" == "Red Hat Enterprise Linux" ] || [ "$osType" == "Amazon Linux" ] || [ "$osType" == "Amazon Linux2" ] || [[ "$osType" ==  *"Linux"*  ]]; then
      rpm -ivh $installation_path"/"$installation_file
   elif [ "$osType" == "ubuntu"  ]; then
      sudo dpkg -i $installation_path"/"$installation_file
   fi
   echo "Installation zip -Done!"
}
function installAirGapGS {
   targetDir=$1
   #Creating target Directory to install Gigaspaces
   echo "TargetDir:"$targetDir
   cd
   cd /
   dir=$targetDir
   workDir=$gigaworkPath
   logDir=$gigalogpath
   cd
   #sudo -s
   targetConfigDir="$targetDir/gs_config/"
   if [ ! -d "$dir" ]; then
     mkdir /$dir
     chmod 755 /$dir
     mkdir $targetConfigDir
     chmod 755 $targetConfigDir
       : '
       mkdir /$dir"
       chmod 755 $dir
       mkdir $targetConfigDir"
       chmod 755 $targetConfigDir
       pwd
       '
   fi
   if [ ! -d "$targetConfigDir" ]; then
     chmod 755 /$dir
     mkdir $targetConfigDir
     echo "Not Exit created"
     chmod 755 $targetConfigDir
   fi
   if [ ! -d "/$logDir" ]; then
     mkdir /$logDir
     chmod 755 /$logDir
       : '
       mkdir /$logDir"
       chmod 755 $logDir
       pwd
       '
   fi
   if [ ! -d "/$workDir" ]; then
     mkdir /$workDir
     chmod 755 /$workDir
       : '
       mkdir /$workDir"
       chmod 755 $workDir
       '
   fi
   pwd
   cd
   # Taking the installer name and extract to Target Directory
   echo "Installing Gigaspace InsightEdge at "$targetDir
   home_dir=$(pwd)
   echo "homedir: "$home_dir
   installation_path=$sourceInstallerDirectory/gs
   installation_file=$(ls -1 $sourceInstallerDirectory/gs/*.zip)
   installation_file=$(basename $installation_file)
   echo $installation_path"/"$installation_file
   pwd
   #unzip $installation_path"/"$installation_file -d  $targetDir"
   unzip -qq $installation_path"/"$installation_file -d  $targetDir

   # Change ownership of extracted files to current user so we can modify them
   current_user=$(whoami)

   # Configure license and additional params to setenv-override and set GS home
    if [ "$gsNicAddress" == "x" ] ; then   # Replaced dummy param with blank and no required to append GS_NIC_ADDR to setenv.over..
       gsNicAddress=${gsNicAddress//[x]/''}
    fi
   echo "gsNicAddress: "$gsNicAddress

   #license="export GS_LICENSE='Product=InsightEdge;Version=15.8;Type=ENTERPRISE;Customer=GigaSpaces_Technologies_-_Internal_rajiv_shah_DEV;Expiration=2021-Dec-31;Hash=gSZQ6OSP83VRn0PRQZNH'"
   #license="export GS_LICENSE='\"$gsLicenseConfig\"'"
   var=$installation_file
   replace=""
   extracted_folder=${var//'.zip'/$replace}
   echo "extracted_folder: "$extracted_folder

   #sed -i '/export GS_LICENSE/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh"
   #sed -i '/export GS_LICENSE/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh
   #sed -i '/export GS_MANAGER_SERVERS/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh"
   sed -i '/export GS_MANAGER_SERVERS/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh
   #sed -i '/export GS_LOGS_CONFIG_FILE/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh"
   #sed -i '/export GS_LOGS_CONFIG_FILE/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh
   #sed -i '/export GS_MANAGER_OPTIONS/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh"
   sed -i '/export GS_MANAGER_OPTIONS/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh
   #sed -i '/export GS_OPTIONS_EXT/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh"
   sed -i '/export GS_OPTIONS_EXT/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh
   if [  "$gsNicAddress" != "" ]; then
      echo "PRESENT"
      #sed -i '/export GS_NIC_ADDRESS/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh"
      sed -i '/export GS_NIC_ADDRESS/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh
   fi

   #echo "license"$license

   #cd /;echo  "">>$targetDir/$extracted_folder/bin/setenv-overrides.sh"
   echo  "">>$targetDir/$extracted_folder/bin/setenv-overrides.sh
   #if [ $gsLicenseConfig == "tryme" ]; then
   # licenseConfig="export GS_LICENSE="$gsLicenseConfig
   #else
   # licenseConfig="export GS_LICENSE=""\"$gsLicenseConfig"\"
   #fi
   #cd /;echo  export GS_LICENSE='\"$gsLicenseConfig\"'>>$targetDir/$extracted_folder/bin/setenv-overrides.sh"
   #echo  $licenseConfig>>$targetDir/$extracted_folder/bin/setenv-overrides.sh
   cp -f $gsLicenseConfig $targetDir/$extracted_folder/

   hostCfg="export GS_MANAGER_SERVERS="$gs_clusterhosts
   #echo "hostCfg :"$hostCfg
   #cd /;echo  '$hostCfg'>>$targetDir/$extracted_folder/bin/setenv-overrides.sh"
   echo  $hostCfg>>$targetDir/$extracted_folder/bin/setenv-overrides.sh

   gsLogsConfigFile="export GS_LOGS_CONFIG_FILE="$gsLogsConfigFile
   #cd /;echo export GS_LOGS_CONFIG_FILE='\"$gsLogsConfigFile\"'>>$targetDir/$extracted_folder/bin/setenv-overrides.sh"
   echo $gsLogsConfigFile>>$targetDir/$extracted_folder/bin/setenv-overrides.sh

   gsManagerOptions="export GS_MANAGER_OPTIONS="\"$gsManagerOptions\"
   #cd /;echo export GS_MANAGER_OPTIONS='\"$gsManagerOptions\"'>>$targetDir/$extracted_folder/bin/setenv-overrides.sh"
   echo $gsManagerOptions>>$targetDir/$extracted_folder/bin/setenv-overrides.sh

   gsOptionExt="export GS_OPTIONS_EXT="\"$gsOptionExt\"
   #cd /;echo export GS_OPTIONS_EXT='\"$gsOptionExt\"'>>$targetDir/$extracted_folder/bin/setenv-overrides.sh"
   echo $gsOptionExt>>$targetDir/$extracted_folder/bin/setenv-overrides.sh

   #cd /; echo path: $targetDir/$extracted_folder ; export GS_HOME=\'$targetDir/$extracted_folder\'; echo G: $GS_HOME"
   #cd /;echo GS_HOME :$GS_HOME"

   if [ ! "$gsNicAddress" == "" ]; then
     gsNicAddr="export GS_NIC_ADDRESS="$gsNicAddress
     #cd /;echo export GS_NIC_ADDRESS='\"$gsNicAddress\"'>>$targetDir/$extracted_folder/bin/setenv-overrides.sh"
     echo $gsNicAddr>>$targetDir/$extracted_folder/bin/setenv-overrides.sh
   fi
   #set GS_HOME to start stop remove Gigaspaces
   cd
   path="export GS_HOME="$targetDir/gigaspaces-smart-ods
   #sed -i '/export GS_HOME/d' $home_dir/setenv.sh
   echo "">>setenv.sh
   echo "$path">>setenv.sh

   echo "path: "$path
   cd
   # Moving the required files to other folder
   #cd /;  cp $targetDir/$extracted_folder/config/log/xap_logging.properties $targetConfigDir"
   if [ ! -f "$targetConfigDir/xap_logging.properties" ]; then                #Condition added on 02Feb22 if file exist dont override it
     sed -i -e 's/NullBackupPolicy/DeleteBackupPolicy/g' $targetDir/$extracted_folder/config/log/xap_logging.properties
     cd /;  cp $targetDir/$extracted_folder/config/log/xap_logging.properties $targetConfigDir
   fi
   #cd /;  cp $targetDir/$extracted_folder/config/metrics/metrics.xml $targetConfigDir"
   #if [ ! -f "$targetConfigDir/metrics.xml" ]; then                #Condition added on 20Oct21 if file exist dont override it
   # echo "File $targetConfigDir/metrics.xml not exist so copying"
   # cd /;  cp $targetDir/$extracted_folder/config/metrics/metrics.xml $targetConfigDir
   #fi
   cp $sourceInstallerDirectory/gs/config/metrics/metrics.xml.template $gigapath"/gs_config/metrics.xml"

   limitContent="$applicativeUser hard nofile "$nofileLimitFile
   limitContentSoft="$applicativeUser soft nofile "$nofileLimitFile

#    sed -i '/hard nofile/d' /etc/security/limits.conf
#    sed -i '/soft nofile/d' /etc/security/limits.conf

   echo "LimitContent : "$limitContent
#    echo "" | tee -a /etc/security/limits.conf
#    echo $limitContent | tee -a /etc/security/limits.conf
#    echo $limitContentSoft | tee -a /etc/security/limits.conf

   cd $targetDir
   ln -s $extracted_folder gigaspaces-smart-ods

   # Create work directories for GigaSpaces with proper structure
   echo "Creating work directories..."
   mkdir -p $gigaworkPath/manager/zookeeper/data
   mkdir -p $gigaworkPath/manager/zookeeper/log
   mkdir -p $gigalogpath/manager

   # Set ownership and permissions for gsods user
   echo "Setting ownership for $applicativeUser user..."
   chmod -R 755 $gigaworkPath/
   chmod -R 755 $gigalogpath/

   # Fix SELinux contexts if SELinux is enabled
   if [ "$selinux" == "true" ] || [ "$selinux" == "True" ]; then
       echo "Fixing SELinux contexts..."
       chcon -R -t usr_t $gigaworkPath/ 2>/dev/null || true
       chcon -R -t usr_t $gigalogpath/ 2>/dev/null || true
       restorecon -R $gigaworkPath/ $gigalogpath/ 2>/dev/null || true
   fi

   echo "Installation & configuration Gigaspace  -Done!"
}
function loadEnv {
  cd
  home_dir=$(pwd)
  source $home_dir/setenv.sh
}

function installTelegraf {
    if command -v telegraf &> /dev/null; then
        echo "Telegraf already installed."
    else
        echo "WARNING: Telegraf is not installed. Install it via setup.sh as root."
    fi
}

function gsCreateGSServeice {
  echo "GS Creating services started."

  # Set ownership for gsods user
  echo "Setting ownership for $applicativeUser on all GigaSpaces directories..."
  sudo find $gigalogpath -maxdepth 1 ! -regex '^'$gigalogpath'/consul\(/.*\)?' -type d -exec chown $applicativeUser:$applicativeUser {} \;

  # Set proper permissions
  echo "Setting permissions..."
  chmod -R 755 $gigaworkPath/
  chmod -R 755 $gigapath/*

  # Fix SELinux contexts if enabled
  if [ "$selinux" == "true" ] || [ "$selinux" == "True" ]; then
      echo "Applying SELinux contexts..."
      chcon -R -t usr_t $gigaworkPath/ 2>/dev/null || true
      chcon -R -t usr_t $gigalogpath/ 2>/dev/null || true
      chcon -R -t usr_t $gigapath/ 2>/dev/null || true
      restorecon -R $gigaworkPath/ $gigalogpath/ $gigapath/ 2>/dev/null || true
  fi

  start_gsa_file="start_gsa.sh"
  start_gsc_file="start_gsc.sh"
  stop_gsa_file="stop_gsa.sh"
  stop_gsc_file="stop_gsc.sh"
  gsa_service_file="gsa.service"
  #gsc_service_file="gsc.service"

  home_dir_sh=$(pwd)
  echo "homedir: "$home_dir_sh
  source $home_dir_sh/setenv.sh
  echo "GS_HOME :"$GS_HOME
  echo "gs_version_17 :"$gs_version_17

  #cmd="nohup $GS_HOME/bin/gs.sh host run-agent --auto >  /$logDir/console_out.log 2>&1 &" #24-Aug
  if [ "$gs_version_17" == "true" ]; then
      echo "gs_version_17 :inside if"
      cmd="$GS_HOME/bin/gs.sh host run-agent --auto"
      echo "$cmd">>$start_gsa_file
  else
      echo "gs_version_17 :inside else"
      cmd="$GS_HOME/bin/gs.sh host run-agent --auto"
      echo "$cmd">$start_gsa_file
  fi

  #cmd="sudo $GS_HOME/bin/gs.sh host kill-agent --all > /$logDir/console_out.log 2>&1 &"  #24-Aug
  cmd="$GS_HOME/bin/gs.sh host kill-agent --all"
  echo "$cmd">>$stop_gsa_file
  #cmd="$GS_HOME/bin/gs.sh container kill --zones bll;sleep 20;"
  cmd="ps -ef | grep GSC | grep java | awk '{print $2}' | xargs kill -9"
  echo "$cmd">>$stop_gsc_file

  #comment GSC requires param in Manager
  gs_installation_path=$home_dir_sh/install/gs
  sed -i -e 's|Requires = gsc.service|#Requires = gsc.service|g' $gs_installation_path/$gsa_service_file

  mv $home_dir_sh/st*_gs*.sh /tmp
#  chmod 644 $gs_installation_path/$gsa_service_file
  mv $gs_installation_path/$gsa_service_file /tmp
  #mv $home_dir_sh/install/gs/$gsc_service_file /tmp
  # User units must not set User= or Group=; strip if present
  sed -i -E '/^[[:space:]]*User[[:space:]]*=/d; /^[[:space:]]*Group[[:space:]]*=/d' /tmp/$gsa_service_file /tmp/$gsc_service_file /tmp/gs.service 2>/dev/null || true
  mv /tmp/st*_gs*.sh /giga/bin/
  chmod +x /giga/bin/st*_gs*.sh
  mv /tmp/gs*.service $HOME/.config/systemd/user/
  if [ "$selinux" == "true" ]; then
      restorecon $HOME/.config/systemd/user/gs*.service
  fi

  #rm -rf gs.service

  #======================================
  #mkdir $GS_HOME/tools/gs-webui/work
  #chmod 755 -R $GS_HOME/tools/gs-webui/work
  chmod 755 -R $GS_HOME/logs/
  chmod 755 -R $GS_HOME/deploy/
  chmod 755 -R $GS_HOME/deploy/*
  chmod -R +x $gigapath

  systemctl --user daemon-reload
  systemctl --user enable $gsa_service_file
  #systemctl --user enable $gsc_service_file


  : '
  systemctl --user daemon-reload
  systemctl --user start gs.service
  systemctl --user enable gs.service
  systemctl --user is-active gs.service
  =================================
  Stop gs service
  systemctl --user stop gs.service
  '
  echo "GS Creating services -Done!."
}

function copyLogFile {
    echo "xap_logging file copied from source to target"
    cd $gigapath"/gs_config/"
    cp $logSourcePath $logTargetPath
}

#if the airGap true then it will install from user/install dir
targetDir=$2
gs_clusterhosts=$3
#openJdkVersion=$4
#gsType=$5
#gsVersion=$6
gsOptionExt=$4
gsManagerOptions=$5
gsLogsConfigFile=$6
gsLicenseConfig=$7
applicativeUser=$8
nofileLimitFile=$9
wantInstallJava=${10}
wantInstallUnzip=${11}
sourceInstallerDirectory=${12}
logTargetPath=${13}
logSourcePath=${14}
selinux=${15}
gsNicAddress=${16}
gs_version_17=${17}

if [ "$gs_version_17" == 'true' ]; then
  gsLicenseFile_16_4=${18}
fi

echo "param1"$1
echo "param2"$targetDir
echo "param3"$gs_clusterhosts
echo "param4"$gsOptionExt
echo "param5"$gsManagerOptions
echo "param6"$gsLogsConfigFile
echo "param7"$gsLicenseConfig
echo "param8"$applicativeUser
echo "param9"$nofileLimitFile
echo "param10"$wantInstallJava
echo "param11"$wantInstallUnzip
echo "param12"$sourceInstallerDirectory
echo "param13"$gsNicAddress
if [ -z "$targetDir" ]; then
  targetDir=$(pwd)
else
  targetDir=$2
fi
echo "TargetDir:"$targetDir
if [ $1 == 'true' ]; then

  if [ "$wantInstallJava" == "y" ]; then
    echo "Setup AirGapJava"
    installRemoteJava
  fi
  if [ "$wantInstallUnzip" == "y" ]; then
    echo "Setup AirGap unzip"
    installZip
  fi
  echo "Setup AirGap GS InsightEdge "
  installAirGapGS $targetDir
  echo "Load env"
  loadEnv
  echo "Creating GS Services.."
  gsCreateGSServeice
else
  echo "Setup java"
  installRemoteJava
  echo "setup zip"
  installZip
  echo "install wget"
  installWget
  echo "Download GS"
  downloadGS
  echo "unzipping GS"
  unzipGS $targetDir
  echo "activating GS"
  activateGS $targetDir
  echo "Set GS Home"
  setGSHome $targetDir
fi
installTelegraf
copyLogFile
