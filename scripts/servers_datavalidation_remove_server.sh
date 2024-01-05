source setenv.sh

systemctl stop odsxdatavalidationserver.service
sleep 2

#yum -y remove java*
#yum -y remove jdk*

rm -rf /dbagiga/datavalidator/server /usr/local/bin/st*_data_validation_server.sh /etc/systemd/system/odsxdatavalidationserver.service
