echo "Removing Server - Space"
homeDir=$(pwd)
source setenv.sh
#sudo su
yum -y remove java*
yum -y remove jdk*
echo "Java Remove -Done!"
yum -y remove unzip
echo "unzip Remove -Done!"
yum -y remove wget
echo "wget Remove -Done!"
#rm -r install/*.zip
source setenv.sh
systemctl stop gs.service
sleep 5
rm -rf $GS_HOME
rm -rf setenv.sh gs install install.tar /dbagiga/giga*  /dbagigalogs/* /dbagigawork/* /usr/local/bin/start_gs.sh /usr/local/bin/stop_gs.sh /etc/systemd/system/gs.service
sed -i '/hard nofile/d' /etc/security/limits.conf
sed -i '/soft nofile/d' /etc/security/limits.conf
echo "GS Remove -Done!"

