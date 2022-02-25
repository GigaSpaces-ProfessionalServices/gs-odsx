source /home/gsods/setenv.sh

systemctl stop odsxdatavalidation.service
sleep 2

#yum -y remove java*
#yum -y remove jdk*

rm -rf /home/gsods/install/data-validation /usr/local/bin/st*_data_validation.sh /etc/systemd/system/odsxdatavalidation.service
