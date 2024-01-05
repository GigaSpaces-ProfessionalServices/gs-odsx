source setenv.sh

systemctl stop odsxdatavalidationagent.service
sleep 2

#yum -y remove java*
#yum -y remove jdk*

rm -rf /dbagiga/datavalidator/agent /usr/local/bin/st*_data_validation_agent.sh /etc/systemd/system/odsxdatavalidationagent.service
