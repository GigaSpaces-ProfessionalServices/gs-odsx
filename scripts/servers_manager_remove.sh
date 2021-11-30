echo "Removing Server - Manager"
homeDir=$(pwd)
source setenv.sh
sudo su
sudo yum -y remove java*
sudo yum -y remove jdk*
echo "Java Remove -Done!"
sudo yum -y remove unzip
echo "unzip Remove -Done!"
sudo yum -y remove wget
echo "wget Remove -Done!"
#rm -r install/*.zip
source setenv.sh
sudo systemctl stop gs.service
sleep 5
sudo rm -rf $GS_HOME
sudo rm -rf setenv.sh gs install install.tar /dbagiga/giga*  /dbagigalogs/* /dbagigawork/* /usr/local/bin/start_gs.sh /usr/local/bin/stop_gs.sh /etc/systemd/system/gs.service
sudo -u 'root' -H sh -c "sed -i '/hard nofile/d' /etc/security/limits.conf"
sudo -u 'root' -H sh -c "sed -i '/soft nofile/d' /etc/security/limits.conf"
echo "GS Remove -Done!"

