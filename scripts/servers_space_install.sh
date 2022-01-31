echo "Installation starting..."
#source gs_installation.properties
osDetected=$(cat /etc/os-release|grep "NAME=" | head -n 1 | cut -d "=" -f2 | sed -e 's/^"//' -e 's/"$//')
echo "os: "$osDetected
osType=$osDetected

function installRemoteJava {
  echo "os:"$osType
  if [ "$osType" == "centos" ] || [ "$osType" == "Red Hat Enterprise Linux" ] ; then
      if [ "$openJdkVersion" == "1.8" ] ||  [ "$openJdkVersion" == "8" ]; then
          sudo yum -y install java-1.8.0-openjdk
          sudo yum -y install java-1.8.0-openjdk-devel
    elif [ "$openJdkVersion" == "11" ] ; then
        sudo yum -y install java-11-openjdk
        sudo yum -y install java-11-openjdk-devel
        fi
    elif [ "$osType" == "ubuntu" ]; then
      if [ "$openJdkVersion" == "1.8" ]  ||  [ "$openJdkVersion" == "8" ]; then
          sudo apt-get update
          sudo apt -y install openjdk-8-jdk
      elif [ "$openJdkVersion" == "11" ]; then
          sudo apt-get update
          sudo apt -y install openjdk-11-jdk
          #sudo apt-get install openjdk-11-jdk
      fi
    elif [ "$osType" == "awsLinux2" ] || [ "$osType" == "Amazon Linux" ] || [ "$osType" == "Amazon Linux2" ]; then
      if [ "$openJdkVersion" == "1.8" ] ||  [ "$openJdkVersion" == "8" ]; then
          sudo amazon-linux-extras enable corretto8
          yum clean metadata
          sudo yum -y install java-1.8.0-amazon-corretto
      elif [ "$openJdkVersion" == "11" ]; then
          sudo amazon-linux-extras install -y java-openjdk11
      fi
    else
      if [ "$openJdkVersion" == "1.8" ] ||  [ "$openJdkVersion" == "8" ]; then
          sudo yum -y install java-1.8.0-openjdk
          sudo yum -y install java-1.8.0-openjdk-devel
    elif [ "$openJdkVersion" == "11" ]; then
        sudo yum -y install java-11-openjdk
        sudo yum -y install java-11-openjdk-devel
        fi
  fi
    echo "Installation Remote JDK - Done!"
}

function installZip {
    echo "os:"$osType
    if [ "$osType" == "centos" ]; then
	    sudo yum -y install unzip
    elif [ "$osType" == "ubuntu" ]; then
        sudo apt -y install unzip
    elif [ "$osType" == "awsLinux2" ] || [ "$osType" == "Amazon Linux" ] || [ "$osType" == "Amazon Linux2" ] || [ "$osType" == "Red Hat Enterprise Linux" ]  || [[ "$osType" ==  *"Linux"*  ]]; then
        sudo yum -y install unzip
	else
	   sudo yum -y install unzip
	fi
	echo "install ZIP - Done!"
}
function installWget {
  echo "os:"$osType
    if [ "$osType" == "centos" ]; then
	    sudo yum -y install wget
    elif [ "$osType" == "ubuntu" ]; then
        sudo apt -y install wget
    elif [ "$osType" == "awsLinux2" ] || [ "$osType" == "Amazon Linux" ] || [ "$osType" == "Amazon Linux2" ] || [ "$osType" == "Red Hat Enterprise Linux" ]  || [[ "$osType" ==  *"Linux"*  ]]; then
        sudo yum -y install wget
    else
	    sudo yum -y install wget
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

    path="export GS_HOME="$targetDir/gigaspaces-${gsType}-enterprise-${gsVersion}
    sed -i '/export GS_HOME/d' setenv.sh
    echo "">>setenv.sh
    echo "$path">>setenv.sh
    source setenv.sh
  echo "Set GS_HOME - Done!"
}

function installAirGapJava {
    echo "Installation of AirGapJava"
    home_dir=$(pwd)
    installation_path=$home_dir/install/java
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
       dpkg -i $installation_path"/"$installation_file
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
   installation_path=$home_dir/install/unzip
   installation_file=$(find $installation_path -name *.rpm -printf "%f\n")
   if [ "$osType" == "centos" ] || [ "$osType" == "Red Hat Enterprise Linux" ] || [ "$osType" == "Amazon Linux" ] || [ "$osType" == "Amazon Linux2" ] || [[ "$osType" ==  *"Linux"*  ]]; then
      rpm -ivh $installation_path"/"$installation_file
   elif [ "$osType" == "ubuntu"  ]; then
      dpkg -i $installation_path"/"$installation_file
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
   workDir="dbagigawork"
   logDir="dbagigalogs"
   dataDir="dbagigadata"
   cd
   #sudo -s
   targetConfigDir="$targetDir/gs_config/"
   if [ ! -d "$dir" ]; then
     mkdir /$dir
     chmod 777 /$dir
     mkdir $targetConfigDir
     chmod 777 $targetConfigDir
       : '
       sudo -u 'root' -H sh -c "mkdir /$dir"
       sudo chmod 777 $dir
       sudo -u 'root' -H sh -c "mkdir $targetConfigDir"
       sudo chmod 777 $targetConfigDir
       pwd
       '
   fi
   if [ ! -d "$targetConfigDir" ]; then
     chmod 777 /$dir
     mkdir $targetConfigDir
     echo "Not Exit created"
     chmod 777 $targetConfigDir
   fi
   if [ ! -d "/$logDir" ]; then
     mkdir /$logDir
     chmod 777 /$logDir
       : '
       sudo -u 'root' -H sh -c "mkdir /$logDir"
       sudo chmod 777 $logDir
       pwd
       '
   fi
   if [ ! -d "/$workDir" ]; then
     mkdir /$workDir
     chmod 777 /$workDir
       : '
       sudo -u 'root' -H sh -c "mkdir /$workDir"
       sudo chmod 777 $workDir
       '
   fi
   if [ ! -d "/$dataDir" ]; then
     mkdir /$dataDir
     chmod 777 /$dataDir
       : '
       sudo -u 'root' -H sh -c "mkdir /$workDir"
       sudo chmod 777 $workDir
       '
   fi
   pwd
   cd
   # Taking the installer name and extract to Target Directory
   echo "Installing Gigaspace InsightEdge at "$targetDir
   home_dir=$(pwd)
   echo "homedir: "$home_dir
   installation_path=$home_dir/install/gs
   installation_file=$(find $installation_path -name *.zip -printf "%f\n")
   echo $installation_path"/"$installation_file
   pwd
   #sudo -u 'root' -H sh -c "unzip $installation_path"/"$installation_file -d  $targetDir"
   unzip -qq $installation_path"/"$installation_file -d  $targetDir

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

   #sudo -u 'root' -H sh -c "sed -i '/export GS_LICENSE/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh"
   sed -i '/export GS_LICENSE/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh
   #sudo -u 'root' -H sh -c "sed -i '/export GS_MANAGER_SERVERS/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh"
   sed -i '/export GS_MANAGER_SERVERS/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh
   #sudo -u 'root' -H sh -c "sed -i '/export GS_LOGS_CONFIG_FILE/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh"
   sed -i '/export GS_LOGS_CONFIG_FILE/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh
   #sudo -u 'root' -H sh -c "sed -i '/export GS_MANAGER_OPTIONS/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh"
   sed -i '/export GS_MANAGER_OPTIONS/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh
   #sudo -u 'root' -H sh -c "sed -i '/export GS_OPTIONS_EXT/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh"
   sed -i '/export GS_OPTIONS_EXT/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh
   if [  "$gsNicAddress" != "" ]; then
      echo "PRESENT"
      #sudo -u 'root' -H sh -c "sed -i '/export GS_NIC_ADDRESS/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh"
      sed -i '/export GS_NIC_ADDRESS/d' $targetDir/$extracted_folder/bin/setenv-overrides.sh
   fi

   #echo "license"$license

   #sudo -u 'root' -H sh -c "cd /;echo  "">>$targetDir/$extracted_folder/bin/setenv-overrides.sh"
   echo  "">>$targetDir/$extracted_folder/bin/setenv-overrides.sh
   if [ $gsLicenseConfig == "tryme" ]; then
    licenseConfig="export GS_LICENSE="$gsLicenseConfig
   else
    licenseConfig="export GS_LICENSE=""\"$gsLicenseConfig"\"
   fi
   #sudo -u 'root' -H sh -c "cd /;echo  export GS_LICENSE='\"$gsLicenseConfig\"'>>$targetDir/$extracted_folder/bin/setenv-overrides.sh"
   echo  $licenseConfig>>$targetDir/$extracted_folder/bin/setenv-overrides.sh

   hostCfg="export GS_MANAGER_SERVERS="$gs_clusterhosts
   #echo "hostCfg :"$hostCfg
   #sudo -u 'root' -H sh -c "cd /;echo  '$hostCfg'>>$targetDir/$extracted_folder/bin/setenv-overrides.sh"
   echo  $hostCfg>>$targetDir/$extracted_folder/bin/setenv-overrides.sh

   gsLogsConfigFile="export GS_LOGS_CONFIG_FILE="$gsLogsConfigFile
   #sudo -u 'root' -H sh -c "cd /;echo export GS_LOGS_CONFIG_FILE='\"$gsLogsConfigFile\"'>>$targetDir/$extracted_folder/bin/setenv-overrides.sh"
   echo $gsLogsConfigFile>>$targetDir/$extracted_folder/bin/setenv-overrides.sh

   gsManagerOptions="export GS_MANAGER_OPTIONS="\"$gsManagerOptions\"
   #sudo -u 'root' -H sh -c "cd /;echo export GS_MANAGER_OPTIONS='\"$gsManagerOptions\"'>>$targetDir/$extracted_folder/bin/setenv-overrides.sh"
   echo $gsManagerOptions>>$targetDir/$extracted_folder/bin/setenv-overrides.sh

   gsOptionExt="export GS_OPTIONS_EXT="\"$gsOptionExt\"
   #sudo -u 'root' -H sh -c "cd /;echo export GS_OPTIONS_EXT='\"$gsOptionExt\"'>>$targetDir/$extracted_folder/bin/setenv-overrides.sh"
   echo $gsOptionExt>>$targetDir/$extracted_folder/bin/setenv-overrides.sh

   #sudo -u 'root' -H sh -c "cd /; echo path: $targetDir/$extracted_folder ; export GS_HOME=\'$targetDir/$extracted_folder\'; echo G: $GS_HOME"
   #sudo -u 'root' -H sh -c "cd /;echo GS_HOME :$GS_HOME"

   if [ ! "$gsNicAddress" == "" ]; then
     gsNicAddr="export GS_NIC_ADDRESS="$gsNicAddress
     #sudo -u 'root' -H sh -c "cd /;echo export GS_NIC_ADDRESS='\"$gsNicAddress\"'>>$targetDir/$extracted_folder/bin/setenv-overrides.sh"
     echo $gsNicAddr>>$targetDir/$extracted_folder/bin/setenv-overrides.sh
   fi
   #set GS_HOME to start stop remove Gigaspaces
   cd
   path="export GS_HOME="$targetDir/$extracted_folder
   #sed -i '/export GS_HOME/d' $home_dir/setenv.sh
   echo "">>setenv.sh
   echo "$path">>setenv.sh

   echo "path: "$path
   cd
   # Moving the required files to other folder
   #sudo -u 'root' -H sh -c "cd /;  cp $targetDir/$extracted_folder/config/log/xap_logging.properties $targetConfigDir"
   sed -i -e 's/NullBackupPolicy/DeleteBackupPolicy/g' $targetDir/$extracted_folder/config/log/xap_logging.properties
   cd /;  cp $targetDir/$extracted_folder/config/log/xap_logging.properties $targetConfigDir
   #sudo -u 'root' -H sh -c "cd /;  cp $targetDir/$extracted_folder/config/metrics/metrics.xml $targetConfigDir"
   if [ ! -f "$targetConfigDir/metrics.xml" ]; then                #Condition added on 20Oct21 if file exist dont override it
    echo "File $targetConfigDir/metrics.xml not exist so copying"
    cd /;  cp $targetDir/$extracted_folder/config/metrics/metrics.xml $targetConfigDir
   fi

   limitContent="$applicativeUser hard nofile "$nofileLimitFile
   limitContentSoft="$applicativeUser soft nofile "$nofileLimitFile

   sed -i '/hard nofile/d' /etc/security/limits.conf
   sed -i '/soft nofile/d' /etc/security/limits.conf

   echo "LimitContent : "$limitContent
   echo "">>/etc/security/limits.conf
   echo $limitContent>>/etc/security/limits.conf
   echo $limitContentSoft>>/etc/security/limits.conf
   cd $targetDir
   ln -s $extracted_folder gigaspaces-smart-ods

   echo "Installation & configuration Gigaspace  -Done!"
}
function loadEnv {
  cd
  home_dir=$(pwd)
  source $home_dir/setenv.sh
}

function gsCreateGSServeice {
    echo "GS Creating services started."

  chown -R $applicativeUser:$applicativeUser /dbagigalogs/ /dbagigawork/ /dbagiga/*  /dbagigadata
  #chgrp -R gsods /dbagigalogs/ /dbagigawork/ /dbagiga/*

  start_gsa_file="start_gsa.sh"
  start_gsc_file="start_gsc.sh"
  stop_gsa_file="stop_gsa.sh"
  stop_gsc_file="stop_gsc.sh"
  gsa_service_file="gsa.service"
  gsc_service_file="gsc.service"

  home_dir_sh=$(pwd)
  echo "homedir: "$home_dir_sh
  source $home_dir_sh/setenv.sh
  echo "GS_HOME :"$GS_HOME

  #cmd="nohup $GS_HOME/bin/gs.sh host run-agent --auto >  /$logDir/console_out.log 2>&1 &" #24-Aug
  cmd="$GS_HOME/bin/gs.sh host run-agent --auto"
  echo "$cmd">>$start_gsa_file
  cmd="sleep 20;$GS_HOME/bin/gs.sh container create --count=$gscCount --zone=$zoneGSC --memory=$memoryGSC `hostname`"
  echo "$cmd">>$start_gsc_file

  #cmd="sudo $GS_HOME/bin/gs.sh host kill-agent --all > /$logDir/console_out.log 2>&1 &"  #24-Aug
  cmd="$GS_HOME/bin/gs.sh host kill-agent --all"
  echo "$cmd">>$stop_gsa_file
  cmd="$GS_HOME/bin/gs.sh container kill --zones bll;sleep 20;"
  echo "$cmd">>$stop_gsc_file

  mv $home_dir_sh/st*_gs*.sh /tmp
  mv $home_dir_sh/install/gs/$gsa_service_file /tmp
  mv $home_dir_sh/install/gs/$gsc_service_file /tmp
  mv /tmp/st*_gs*.sh /usr/local/bin/
  chmod +x /usr/local/bin/st*_gs*.sh
  mv /tmp/gs*.service /etc/systemd/system/

  rm -rf gs.service

  #======================================
  #mkdir $GS_HOME/tools/gs-webui/work
  #chmod 777 -R $GS_HOME/tools/gs-webui/work
  chmod 777 -R $GS_HOME/logs/
  chmod 777 -R $GS_HOME/deploy/
  chmod 777 -R $GS_HOME/deploy/*
  chmod 777 -R $GS_HOME/tools/gs-webui/*
  chmod -R +x /dbagiga

  systemctl daemon-reload
  systemctl enable $gsa_service_file
  systemctl enable $gsc_service_file


  : '
  sudo systemctl daemon-reload
  sudo systemctl start gs.service
  sudo systemctl enable gs.service
  sudo systemctl is-active gs.service
  =================================
  Stop gs service
  sudo systemctl stop gs.service
  '
  echo "GS Creating services -Done!."
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
gscCount=${12}
memoryGSC=${13}
zoneGSC=${14}
gsNicAddress=${15}

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
echo "param12"$gscCount
echo "param13"$memoryGSC
echo "param14"$zoneGSC
echo "param15"$gsNicAddress
if [ -z "$targetDir" ]; then
  targetDir=$(pwd)
else
  targetDir=$2
fi
echo "TargetDir:"$targetDir
if [ $1 == 'true' ]; then
  if [ "$wantInstallJava" == "y" ]; then
    echo "Setup AirGapJava"
    installAirGapJava
  fi
  if [ "$wantInstallUnzip" == "y" ]; then
    echo "Setup AirGap unzip"
    installAirGapUnzip
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
