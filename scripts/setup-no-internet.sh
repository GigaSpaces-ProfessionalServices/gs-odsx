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

# cd ../installationpackages/setup
# tar xvfz zlib-1.2.11.tar.gz
# cd zlib-1.2.11
# ./configure
# make
# sudo make install
# cd ..

# tar xvfz Python-3.6.10.tgz
# cd Python-3.6.10
# ./configure --enable-optimizations
# sudo make altinstall
# cd ..

# sudo rpm -i jdk-8u301-linux-aarch64.rpm

# cd ../..

#Remove the earlier entries from files to avoid duplicate entries
sed -i '/export PYTHONPATH=$(dirname $(pwd))/d' ~/.bashrc

#echo 'export PYTHONPATH=$(dirname $(pwd))' >> ~/.bashrc
project_home_dir=$(dirname $(pwd))
python_path="export PYTHONPATH="$project_home_dir
echo "$python_path" >> ~/.bashrc

cd installationpackages/setup
python3 get-pip.py
cd ../..

if [[ $DISTRO == *"Ubuntu"* ]]; then
    sed -i '/eval "$(register-python-argcomplete odsx.py)"/d' ~/.profile
    echo 'eval "$(register-python-argcomplete odsx.py)"' >> ~/.profile
    sudo ln -s /home/ubuntu/.local/bin/pip3.8 /usr/local/bin/pip3
    source ~/.profile
else
    #Remove the earlier entries from files to avoid duplicate entries
    sed -i '/eval "$(register-python-argcomplete odsx.py)"/d' ~/.bashrc
    echo 'eval "$(register-python-argcomplete odsx.py)"' >> ~/.bashrc
fi

cd installationpackages/setup
pip install --no-index --find-links ./pypi -r ../../scripts/requirements.txt

source ~/.bashrc
