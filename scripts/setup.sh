#!/bin/bash

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

gigashare=$(read_property "app.gigashare.path")
gigawork=$(read_property "app.gigawork.path")
gigalog=$(read_property "app.gigalog.path")
gigapath=$(read_property "app.giga.path")
gigadatapath=$(read_property "app.gigadata.path")
gigainfluxpath=$(read_property "app.gigainfluxdata.path")

# Determine OS platform
checkOS() {
    UNAME=$(uname | tr "[:upper:]" "[:lower:]")
    # If Linux, try to determine specific distribution
    if [ "$UNAME" == "linux" ]; then
        # If available, use LSB to identify distribution
        if [ -f /etc/lsb-release -o -d /etc/lsb-release.d ]; then
            export DISTRO=$(lsb_release -i | cut -d: -f2 | sed s/'^\t'//)
        # Otherwise, use release info file
        else
            #export DISTRO=$(ls -d /etc/[A-Za-z]*[_-][rv]e[lr]* | grep -v "lsb" | cut -d'/' -f3 | cut -d'-' -f1 | cut -d'_' -f1)
            export DISTRO=$(awk -F'=' '/PRETTY_NAME/{ gsub(/"/,""); print $2}' /etc/os-release)
            export VERSION_ID=$(awk -F'=' '/VERSION_ID/{ gsub(/"/,""); print $2}' /etc/os-release)
        fi
    fi
    # For everything else (or if above failed), just use generic identifier
    [ "$DISTRO" == "" ] && export DISTRO=$UNAME
    unset UNAME
}

checkOS
echo "OS Platform detected: $DISTRO"
echo "OS Version detected: $VERSION_ID"

if [[ $DISTRO == *"Ubuntu"* ]]; then
    sudo apt update -y
    sudo apt upgrade -y
    sudo apt install daemon python3 -y
    sudo apt -y install wget
    sudo apt -y install unzip
    sudo apt install -y openjdk-17-jdk
elif [[ $DISTRO == *"Red Hat"* && $DISTRO == *"7"* ]]; then
    sudo yum update -y
    sudo yum install -y nfs-utils
    sudo yum install -y python3.9
    sudo yum install -y python3-pip
    sudo yum -y install wget
    sudo yum -y install unzip
    sudo yum -y install java-17-openjdk-devel -y
    sudo yum install -y nc
else
    sudo yum update -y
    sudo yum install -y nfs-utils
    sudo yum install -y python3.9
    sudo yum install -y python3-pip
    sudo yum -y install wget
    sudo yum -y install unzip
    sudo yum -y install java-17-openjdk-devel -y
fi

#Remove the earlier entries from files to avoid duplicate entries
sed -i '/export PYTHONPATH=$(dirname $(pwd))/d' ~/.bash_profile

#echo 'export PYTHONPATH=$(dirname $(pwd))' >> ~/.bashrc
project_home_dir=$(dirname $(pwd))
python_path="export PYTHONPATH="$project_home_dir
echo "$python_path" >> ~/.bashrc
odsx_path="export ODSXARTIFACTS="$gigashare"/current/"
echo "$odsx_path" >> ~/.bashrc
#odsx_path="export ENV_CONFIG=$gigashare/env_config/"
#echo "$odsx_path" >> ~/.bashrc

python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ $(echo "$python_version > 3.6" | bc -l) -eq 1 ]]; then
    wget https://bootstrap.pypa.io/pip/get-pip.py -P /tmp
else
    wget https://bootstrap.pypa.io/pip/3.6/get-pip.py -P /tmp
fi

python3 /tmp/get-pip.py

if [[ $DISTRO == *"Ubuntu"* ]]; then
    sed -i '/eval "$(register-python-argcomplete odsx.py)"/d' ~/.profile
    echo 'eval "$(register-python-argcomplete odsx.py)"' >> ~/.profile
    sudo ln -s /home/ubuntu/.local/bin/pip3.8 /usr/local/bin/pip3
    pip3 install -r requirements.txt
    source ~/.profile
else
    #Remove the earlier entries from files to avoid duplicate entries
    sed -i '/eval "$(register-python-argcomplete odsx.py)"/d' ~/.bash_profile

    echo 'eval "$(register-python-argcomplete odsx.py)"' >> ~/.bash_profile
    pip3 install -r requirements.txt
fi

source ~/.bashrc
#SQLite
cd
mkdir -p $gigawork/sqlite
cd $gigawork/sqlite
mkdir $gigalog/
mkdir $gigashare
mkdir $gigawork
mkdir $gigapath
mkdir $gigadatapath
mkdir $gigainfluxpath
touch $gigalog/odsx.log

sudo mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport fs-0ec717f72429b6399.efs.us-east-2.amazonaws.com:/ /testgigashare/
df -h

useradd gsods
chown gsods:gsods /dbagiga
chown gsods:gsods /dbagigadata
chown gsods:gsods /dbagigalogs
chown gsods:gsods /dbagigawork
chown gsods:gsods /dbagigashare
chown gsods:gsods /dbagigainfluxdata
chown -R gsods:gsods /dbagigashare/*
chown -R gsods:gsods /dbagiga/*

# --- Non-root prerequisites ---

# Enable user-level systemd for gsods (persists after logout)
loginctl enable-linger gsods

# Create user-level systemd directory
gsods_home=$(eval echo ~gsods)
mkdir -p "$gsods_home/.config/systemd/user/"
chown -R gsods:gsods "$gsods_home/.config/"

# Create /giga/bin for start/stop scripts (replaces /usr/local/bin)
mkdir -p $gigapath/bin
chown gsods:gsods $gigapath/bin

# Set file descriptor limits for gsods
applicativeUser="gsods"
nofileLimitFile=$(read_property "app.user.nofile.limit")
if [ -z "$nofileLimitFile" ]; then
    nofileLimitFile=50000
fi
sed -i '/hard nofile/d' /etc/security/limits.conf
sed -i '/soft nofile/d' /etc/security/limits.conf
echo "" >> /etc/security/limits.conf
echo "$applicativeUser hard nofile $nofileLimitFile" >> /etc/security/limits.conf
echo "$applicativeUser soft nofile $nofileLimitFile" >> /etc/security/limits.conf

# Sudoers entries for third-party monitoring services (Grafana, InfluxDB, Telegraf)
cat > /etc/sudoers.d/odsx-monitoring << 'SUDOERS'
gsods ALL=(ALL) NOPASSWD: /bin/systemctl start grafana-server.service, /bin/systemctl stop grafana-server.service, /bin/systemctl restart grafana-server.service, /bin/systemctl status grafana-server.service, /bin/systemctl enable grafana-server.service
gsods ALL=(ALL) NOPASSWD: /bin/systemctl start influxdb.service, /bin/systemctl stop influxdb.service, /bin/systemctl restart influxdb.service, /bin/systemctl status influxdb.service, /bin/systemctl enable influxdb.service
gsods ALL=(ALL) NOPASSWD: /bin/systemctl start telegraf.service, /bin/systemctl stop telegraf.service, /bin/systemctl restart telegraf.service, /bin/systemctl status telegraf.service, /bin/systemctl enable telegraf.service
SUDOERS
chmod 0440 /etc/sudoers.d/odsx-monitoring

sed -i -e 's|/dbagigalogs/|'$gigalog'/|g' $gigapath/gs-odsx/config/logging.conf
sed -i -e 's|/dbagigalogs/|'$gigalog'/|g' $gigashare/current/gs/config/scripts/start_gsc.sh
sed -i -e 's|/dbagigalogs/|'$gigalog'/|g' $gigashare/current/gs/config/log/xap_logging.properties
sed -i -e 's|/dbagigalogs/|'$gigalog'/|g' $gigashare/current/telegraf/scripts/space/telegraf_wal-size.sh
sed -i -e 's|/dbagigalogs/|'$gigalog'/|g' $gigashare/current/mq-connector/adabas/config/application.yml
sed -i -e 's|/dbagigalogs/|'$gigalog'/|g' $gigashare/current/mq-connector/config/application.yml
sed -i -e 's|/dbagigainflaxdata/|'$gigainfluxpath'/|g' $gigashare/current/influx/config/influxdb.conf.template

wget https://www.sqlite.org/2022/sqlite-tools-linux-x86-3380000.zip
unzip sqlite-tools-linux-x86-3380000.zip
mv sqlite-tools-linux-x86-3380000/* .
rm -rf sqlite-tools-linux-x86-3380000
