echo "Removing Server - Space"
removeJava=$1
#echo "removeJava :"$removeJava
removeUnzip=$2
#echo "removeUnzip :"$removeUnzip

homeDir=$(pwd)
source setenv.sh
#sudo su
if [ "$removeJava" == "y" ]; then
  echo "Removing Java"
  yum -y remove java*
  yum -y remove jdk*
  echo "Java Remove -Done!"
fi
if [ "$removeUnzip" == "y" ]; then
  echo "Removing Unzip"
  yum -y remove unzip
  echo "unzip Remove -Done!"
fi
#yum -y remove wget
#echo "wget Remove -Done!"
#rm -r install/*.zip
source setenv.sh
systemctl stop gsc.service
sleep 5
rm -rf $GS_HOME
rm -rf setenv.sh gs install install.tar /dbagiga/giga*  /dbagigalogs/* /dbagigadata/* /dbagigawork/* /usr/local/bin/start_gs*.sh /usr/local/bin/stop_gs*.sh /etc/systemd/system/gs*.service
systemctl daemon-reload
sed -i '/hard nofile/d' /etc/security/limits.conf
sed -i '/soft nofile/d' /etc/security/limits.conf
echo "GS Remove -Done!"

