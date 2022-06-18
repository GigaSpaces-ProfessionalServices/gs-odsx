#!/bin/bash

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
    sudo apt install openjdk-8-jdk-headless
elif [[ $DISTRO == *"Red Hat"* && $DISTRO == *"7"* ]]; then
    sudo yum update -y
    sudo yum install -y python36 python36-pip
    sudo yum -y install wget
    sudo yum -y install java-1.8.0-openjdk
    sudo yum install -y nc
else
    sudo yum update -y
    sudo yum install -y python3
    sudo yum -y install wget
    sudo yum -y install java-1.8.0-openjdk
fi

#Remove the earlier entries from files to avoid duplicate entries
sed -i '/export PYTHONPATH=$(dirname $(pwd))/d' ~/.bash_profile

#echo 'export PYTHONPATH=$(dirname $(pwd))' >> ~/.bashrc
project_home_dir=$(dirname $(pwd))
python_path="export PYTHONPATH="$project_home_dir
echo "$python_path" >> ~/.bashrc
odsx_path="export ODSXARTIFACTS=/dbagigashare/current/"
echo "$odsx_path" >> ~/.bashrc

wget https://bootstrap.pypa.io/get-pip.py -P /tmp
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
mkdir -p dbagigawork/sqlite
cd dbagigawork/sqlite
wget https://www.sqlite.org/2022/sqlite-tools-linux-x86-3380000.zip
unzip sqlite-tools-linux-x86-3380000.zip
mv sqlite-tools-linux-x86-3380000/* .
rm -rf sqlite-tools-linux-x86-3380000
