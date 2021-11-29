#!/bin/bash
#CentOS 7.2 Installation Script
#source ./consoleLog.sh

# prints colored text
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

if [[ $EUID -eq 0 ]]; then
	echo "This script MUST NOT be run as root"
	exit 1
fi

SCRIPT_RUN="install"

while [[ $# -ge 1 ]]
do

key="$1"
case $key in
    -d|--dryrun)
    SCRIPT_RUN="dry"
    shift # past argument
    ;;
    *)
            # unknown option
    ;;
esac
shift # past argument or value
done

totalRAM=`free | awk '/Mem/{printf $2}'`
totalSwap=`free | awk '/Swap/{printf $2}'`
requiredSwap=`free | awk '/Mem/{printf("%d"), $2/2000}'`
actualSwap=`free | awk '/Swap/{printf("%d"), $2/2000}'`

availableFreeSpace=`df -m / | awk '/[0-9]%/{print $(NF-2)}'`

if [[ "$SCRIPT_RUN" == "dry" ]]; then
    info "Running the script in dryrun mode\n";
    info "Total RAM: $((totalRAM/1024))G\n";
    info "Total Swap: $((totalSwap/1024))G\n";
    info "Required Swap: $((requiredSwap/1024))G\n";
    info "Swap: $((actualSwap/1024))G\n";

    if [[ $actualSwap -ge $requiredSwap ]]; then
        info "Available Swap: $((availableFreeSpace/1024))G\n";
    elif [[ $availableFreeSpace*1024 -ge $requiredSwap ]]; then
        warning "Current Swap size is $((actualSwap/1024))G, which is less than required Swap size: $((requiredSwap/1024))G\n";
        warning "Current Swap will be deleted and created a Swap with size $((requiredSwap/1024))G\n";
        info "Availab Swap: $((availableFreeSpace/1024))G\n";
    else
        error "Available Swap: $((availableFreeSpace/1024))G\n";
        error "CDC can't be installed as required space to create swap is not enough.\n"
        exit;
    fi

    if [[ $availableFreeSpace -lt 10*1024 ]]; then
        error "Available Disk Space: $((availableFreeSpace/1024))G\n";
        error "CDC can't be installed as minimum required disk space is 10G\n."
        exit;
    fi
    exit;
fi

sudo yum update -y
sudo yum install wget -y
sudo yum install unzip -y
sudo useradd dbsh

sudo mkdir /root/misc
cd /

info "Total RAM: $totalRAM\n";
info "Total Swap: $totalSwap\n";
info "Required Swap: $requiredSwap\n";

#For Removing Swap
#sudo swapoff -v /swapfile
#sudo sed '/^\/swapfile/d' < /etc/fstab > /tmp/fstab
#sudo mc /tmp/fstab /etc/fstab
#sudo rm -f /swapfile

if [ $totalSwap -eq 0 ]; then
        sudo dd if=/dev/zero of=/swapfile bs=1024k count=$requiredSwap
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
        sudo swapon /swapfile
        sudo bash -c "echo "/swapfile swap    swap    defaults        0 0" >> /etc/fstab"
fi

sudo cd /root/misc
sudo wget https://download-area-us-east.s3.amazonaws.com/dbshLocalInstall/dbshLocalSetup-rehl7.2-14032021.tar.gz
sudo tar xvfz dbshLocalSetup-rehl7.2-14032021.tar.gz

sudo cd /etc/yum.repos.d
sudo mkdir yum.repos.backup
sudo cp *repo yum.repos.backup/

sudo cd /root/misc/dbshLocalSetup/utils
sudo ./build_local_cr8.sh

cd /tmp
#wget http://download-area-us-east.s3.amazonaws.com/cr8-packages/cr8-latest/cr8-2.0.9-245.x86_64.rpm
wget https://jay-dalal.s3.us-west-2.amazonaws.com/leumi-odsx/cr8/2.0.9-245/cr8-2.0.9-245.x86_64.rpm

#For uninstallation
#sudo yum remove cr8-2.0.9-245.x86_64 -y
sudo rpm -Uvh cr8-2.0.9-245.x86_64.rpm

