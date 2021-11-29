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
            export DISTRO=$(ls -d /etc/[A-Za-z]*[_-][rv]e[lr]* | grep -v "lsb" | cut -d'/' -f3 | cut -d'-' -f1 | cut -d'_' -f1)
        fi
    fi
    # For everything else (or if above failed), just use generic identifier
    [ "$DISTRO" == "" ] && export DISTRO=$UNAME
    unset UNAME   
}

checkOS
echo "OS Platform detected: $DISTRO"
#Removed -y option during remove, so user can decide to remove or keep the package
if [[ $DISTRO == *"Ubuntu"* ]]; then
    sudo apt update -y
    sudo apt upgrade -y
    sudo apt remove daemon python3
    sudo apt remove python3-pip
    sudo apt remove wget
    sudo apt remove openjdk-8-jdk-headless
else
    sudo yum update -y
    sudo yum remove python3
    sudo yum remove python3-pip
    sudo yum remove wget
    sudo yum remove java-1.8.0-openjdk
fi

#Remove the earlier entries from files to avoid duplicate entries
sed -i '/export PYTHONPATH=$(dirname $(pwd))/d' ~/.bashrc

if [[ $DISTRO == *"Ubuntu"* ]]; then
    sed -i '/eval "$(register-python-argcomplete odsx.py)"/d' ~/.profile
    FILE=/home/ubuntu/.local/bin/pip3.8
    if [ ! -f "$FILE" ]; then
        sudo rm -f /usr/local/bin/pip3
    fi
    source ~/.profile
else
    #Remove the earlier entries from files to avoid duplicate entries
    sed -i '/eval "$(register-python-argcomplete odsx.py)"/d' ~/.bashrc
fi

source ~/.bashrc
