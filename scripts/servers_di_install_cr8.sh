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

SCRIPT_RUN="install"

cd /home/dbsh
home_dir=$(pwd)
installation_path=$home_dir/install/cr8

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

#yum update -y
#yum install wget -y
#yum install unzip -y
useradd dbsh

mkdir /root/misc
cd /

info "Total RAM: $totalRAM\n";
info "Total Swap: $totalSwap\n";
info "Required Swap: $requiredSwap\n";

#For Removing Swap
#swapoff -v /swapfile
#sed '/^\/swapfile/d' < /etc/fstab > /tmp/fstab
#mc /tmp/fstab /etc/fstab
#rm -f /swapfile

if [ $totalSwap -eq 0 ]; then
        dd if=/dev/zero of=/swapfile bs=1024k count=$requiredSwap
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        bash -c "echo "/swapfile swap    swap    defaults        0 0" >> /etc/fstab"
fi

cd /root/misc
installation_file=$(find $installation_path -name *.tar.gz -printf "%f\n")
echo $installation_file
mv $installation_path/$installation_file .
# wget https://download-area-us-east.s3.amazonaws.com/dbshLocalInstall/dbshLocalSetup-rehl7.2-14032021.tar.gz
#tar xvfz dbshLocalSetup-rehl7.2-14032021.tar.gz
tar xvfz $installation_file

cd /etc/yum.repos.d
mkdir yum.repos.backup
cp *repo yum.repos.backup/

cd /root/misc/dbshLocalSetup/utils
./build_local_cr8.sh

cd /tmp
#wget http://download-area-us-east.s3.amazonaws.com/cr8-packages/cr8-latest/cr8-2.0.9-245.x86_64.rpm

installation_file=$(find $installation_path -name *.rpm -printf "%f\n")
echo $installation_file
mv $installation_path/$installation_file .
#wget http://download-area-us-east.s3.amazonaws.com/cr8-packages/cr8-latest/cr8-2.0.9-293.x86_64.rpm

#For uninstallation
#yum remove cr8-2.0.9-245.x86_64 -y
rpm -Uvh $installation_file



sleep 10
cr8_service_file="odsxcr8.service"

mv $home_dir/install/$cr8_service_file /tmp
sudo mv -f /tmp/$cr8_service_file /etc/systemd/system/

sed -i '/java_env/d' ~/.bashrc